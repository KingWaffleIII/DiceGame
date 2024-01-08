# Here, the logic when a user connects to the websocket is defined. This is where all the game logic takes place.
# Everything is generated server-side to prevent cheating on the client-side (e.g. if RNG was done on the client side, the user could modify the code to roll a 6 every time).

import json
import random

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Game


class DiceGameConsumer(WebsocketConsumer):
    # This is the logic that runs when a user connects to the websocket.
    def connect(self):
        # This defines a channel name (game code) so the server can ping out events to the correct game.
        self.game_group_name = self.scope["url_route"]["kwargs"]["id"]

        # The following is some error handling to make sure the game exists and the user is authorised to play it.
        try:
            self.game = Game.objects.get(id=self.game_group_name)
        except Game.DoesNotExist:
            self.game = None
            self.accept()
            self.send(text_data=json.dumps({"message": "game does not exist"}))
            self.close()
            return
        if self.game.finished:
            self.accept()
            self.send(text_data=json.dumps({"message": "game has finished"}))
            self.close()
            return

        self.user = self.scope["user"]

        if self.user.is_anonymous:
            # or not self.game.players.contains(self.user)
            self.user = None
            self.accept()
            self.send(text_data=json.dumps({"message": "unauthorised"}))
            self.close()
            return

        # The consumer is added to a group with the other player so events can be pinged out.
        async_to_sync(self.channel_layer.group_add)(
            self.game_group_name, self.channel_name
        )

        self.accept()

        # We add the player to the list of players and the connected_players.
        if not self.game.players.contains(self.user):
            self.game.players.add(self.user)
        self.game.connected_players.add(self.user)
        self.game.save()

        # If we have 2 players, we start the game.
        if self.game.connected_players.count() == 2:
            if not self.game.current_player:
                self.game.current_player = self.game.players.first()
                self.game.save()

            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {"type": "game.ready"},
            )

            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {"type": "game.main"},
            )
        else:
            self.send(text_data=json.dumps({"message": "waiting for another player"}))
            return

    # This is the logic that runs when a player disconnects.
    def disconnect(self, _code):
        # If the user is disconnecting because they joined an invalid game, we don't need to do anything.
        if not self.game:
            return

        if not self.user:
            return

        # If the game isn't finished, to avoid things being messy we simply delete the game and disconnect the other player.
        # This is handled in the game.abort event.
        if not self.game.finished:
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {"type": "game.abort"},
            )

        async_to_sync(self.channel_layer.group_discard)(
            self.game_group_name, self.channel_name
        )

        # The user is removed from the connected_players list.
        try:
            self.game.refresh_from_db()
            self.game.connected_players.remove(self.user)
            self.game.save()
        except Game.DoesNotExist:
            pass

    # This is the logic that runs when the server receives a message from the client.
    # This only is used so the client acknowledges their roll so the game can progress.
    # If they take too long, they are automatically disconnected.
    def receive(self, text_data):
        self.game.refresh_from_db()

        # We check if there are 2 players connected.
        if self.game.connected_players.count() != 2:
            self.send(text_data=json.dumps({"message": "waiting for another player"}))
            return

        # We check if it is the user's turn.
        if self.game.current_player != self.user:
            self.send(text_data=json.dumps({"message": "not your turn"}))
            return

        # If the game is in "tiebreaker mode", we want to run the tiebreaker logic, else just run the main game loop.
        if self.game.tiebreaker:
            self.game_end_tie(None)
            return

        self.game_main(None)

    # This logic is run when the game ends early (a user disconnects) and terminates the game.
    def game_abort(self, _event):
        # This sends a message to the client to handle the abort client-side (e.g. redirecting to the home page).
        self.send(
            text_data=json.dumps({"message": "player disconnected", "abort": True})
        )
        try:
            self.game.delete()
        except Game.DoesNotExist:
            pass
        self.close()

    # This logic is run when 2 players are connected and the clients are notified of the other player's username.
    def game_ready(self, _event):
        self.send(
            text_data=json.dumps(
                {
                    "message": "ready",
                    "player1": self.game.players.first().username,
                    "player2": self.game.players.last().username,
                }
            )
        )

    # This is the main game loop, it handles rolling and score calculation.
    def game_main(self, _event):
        self.game.refresh_from_db()

        # Since this is called on both consumers (players), we need to make sure the user is the current player.
        if self.user != self.game.current_player:
            return

        # The roll is calculated as a list.\
        # If it's a double, we append a 3rd roll.
        roll = [random.randint(1, 6), random.randint(1, 6)]
        if roll[0] == roll[1]:
            roll += [random.randint(1, 6)]

        # If both players have rolled and the current player is back to the first player, we reset the rolls and increment the round.
        if (
            self.game.player1_roll
            and self.game.player2_roll
            and self.game.current_player == self.game.players.first()
        ):
            if self.game.round == 5:
                async_to_sync(self.channel_layer.group_send)(
                    self.game_group_name,
                    {"type": "game.end", "tie": False},
                )
                return

            self.game.round += 1
            self.game.player1_roll = 0
            self.game.player2_roll = 0
            self.game.save()

        # If the current player hasn't rolled, we send them their roll and wait for them to acknowledge it.
        if (
            self.game.current_player == self.game.players.first()
            and not self.game.player1_roll
        ) or (
            self.game.current_player == self.game.players.last()
            and not self.game.player2_roll
        ):
            self.send(
                text_data=json.dumps(
                    {
                        "message": "your roll",
                        "roll": roll,
                        "double": roll[0] == roll[1],
                        "tiebreaker": False,
                    }
                )
            )

            if self.user == self.game.players.first():
                self.game.player1_roll = roll
            else:
                self.game.player2_roll = roll
            self.game.save()

            return

        # If the current player has rolled and sent an acknowledgement, we send the other player their roll so they can see it with the pre_update event.
        if self.game.current_player == self.game.players.first():
            roll = self.game.player1_roll
        else:
            roll = self.game.player2_roll

        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "game.pre_update",
                "player": self.user.username,
                "roll": roll,
                "double": roll[0] == roll[1],
                "tiebreaker": False,
            },
        )

        # We calculate the score and update the database.
        score = sum(roll)

        # If it's a double, we add 10 points, else we subtract 5.
        if sum(roll[:2]) % 2 == 0:
            score += 10
        else:
            score -= 5

        # If the score is negative, we set it to 0.
        score = max(score, 0)

        if self.game.current_player == self.game.players.first():
            self.game.player1_score += score
            score = self.game.player1_score
        else:
            self.game.player2_score += score
            score = self.game.player2_score
        self.game.save()

        # We send both players the round number and the score so they can update.
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "round": self.game.round,
                "type": "game.update",
                "player": self.user.username,
                "roll": roll,
                "score": score,
            },
        )

        # We switch the current player.
        self.game.current_player = self.game.players.exclude(
            username=self.game.current_player.username
        ).first()
        self.game.save()

        # We call the main game loop again for the next roll.
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {"type": "game.main"},
        )

    # This logic is called when the current player receives their roll and acknowledges it.
    # It provides the other player with the current player's roll so they can display it however the client can.
    def game_pre_update(self, event):
        self.game.refresh_from_db()

        if self.user.username == event["player"]:
            return

        self.send(
            text_data=json.dumps(
                {
                    "message": f"{event['player']}'s roll",
                    "roll": event["roll"],
                    "double": event["double"],
                    "tiebreaker": event["tiebreaker"],
                }
            )
        )

    # This logic is called when the score has been calculated and sends the round number, player, roll, and score to both players.
    def game_update(self, event):
        self.game.refresh_from_db()

        self.send(
            text_data=json.dumps(
                {
                    "message": "update",
                    "round": event["round"],
                    "player": event["player"],
                    "roll": event["roll"],
                    "score": event["score"],
                }
            )
        )

    # This logic is run when the game ends normally, deciding a winner or runs the tiebreaker logic.
    # It is also called if the game ends in a tie but the tiebreaker has finished because this contains some of the same logic.
    def game_end(self, event):
        self.game.refresh_from_db()

        # If this code isn't being called after finishing the tiebraker, we proceed as normal.
        if not event["tie"]:
            # The winner is decided from who has the higher score.
            if self.game.player1_score > self.game.player2_score:
                self.game.winner = self.game.players.first()
                score = self.game.player1_score
            elif self.game.player1_score < self.game.player2_score:
                self.game.winner = self.game.players.last()
                score = self.game.player2_score
            # If the players, have the same score, the tiebraker code is triggered.
            else:
                if not self.game.tiebreaker:
                    self.game.tiebreaker = True
                    self.game.player1_roll = 0
                    self.game.player2_roll = 0
                    self.game.current_player = self.game.players.first()
                    self.game.save()
                self.game_end_tie(None)
                return
        # If this code has been called after a tiebraker, we need to set the score for the later code.
        else:
            score = max(
                self.game.player1_score, self.game.player2_score
            )  # they're the same anyway

        self.game.finished = True
        self.game.save()

        # The winner is sent to both players.
        self.send(
            text_data=json.dumps(
                {
                    "message": "end",
                    "winner": self.game.winner.username,
                    "score": score,
                    "tie": event["tie"],
                }
            )
        )

        self.close()

    # This logic is called if the game ends in a tie.
    # It runs very similar to the main game loop in that it generates a roll, waits for acknowledgement and rotates the players.
    # But it only generates one roll and checks if they're the same.
    def game_end_tie(self, _event):
        self.game.refresh_from_db()

        if not self.game.tiebreaker:
            return

        if self.user != self.game.current_player:
            return

        # If the current player has not rolled yet, we generate a roll and send it to them.
        if (
            self.game.current_player == self.game.players.first()
            and not self.game.player1_roll
        ) or (
            self.game.current_player == self.game.players.last()
            and not self.game.player2_roll
        ):
            roll = [random.randint(1, 6)]

            if self.game.current_player == self.game.players.first():
                self.game.player1_roll = roll
            else:
                self.game.player2_roll = roll

            self.game.save()

            self.send(
                text_data=json.dumps(
                    {
                        "message": "your roll",
                        "roll": roll,
                        "double": False,
                        "tiebreaker": True,
                    }
                )
            )

            return

        # If the current player has rolled and acknowledged, we send the other player their roll.

        if self.game.current_player == self.game.players.first():
            roll = self.game.player1_roll
        else:
            roll = self.game.player2_roll

        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "game.pre_update",
                "player": self.game.current_player.username,
                "roll": roll,
                "double": False,
                "tiebreaker": True,
            },
        )

        # If both players have rolled, we compare them and see if the tiebraker is over.
        # Else, we switch the current player and call the tiebreaker logic again.
        if self.game.player1_roll != 0 and self.game.player2_roll != 0:
            if self.game.player1_roll > self.game.player2_roll:
                self.game.winner = self.game.players.first()
                self.game.save()
            elif self.game.player1_roll < self.game.player2_roll:
                self.game.winner = self.game.players.last()
                self.game.save()
            else:
                self.game.player1_roll = 0
                self.game.player2_roll = 0
                self.game.current_player = self.game.players.first()
                self.game.save()
                async_to_sync(self.channel_layer.group_send)(
                    self.game_group_name,
                    {
                        "type": "game.end.tie",
                    },
                )
                return

            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "game.end",
                    "tie": True,
                },
            )
            return

        self.game.current_player = self.game.players.exclude(
            username=self.game.current_player.username
        ).first()
        self.game.save()

        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {"type": "game.end.tie"},
        )
