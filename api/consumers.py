import json
import random

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Game


class DiceGameConsumer(WebsocketConsumer):
    def connect(self):
        self.game_group_name = self.scope["url_route"]["kwargs"]["id"]
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

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.game_group_name, self.channel_name
        )

        self.accept()

        if not self.game.players.contains(self.user):
            self.game.players.add(self.user)
        self.game.connected_players.add(self.user)
        self.game.save()

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

    def disconnect(self, _code):
        # Leave room group

        if not self.game:
            return

        if not self.user:
            return

        if not self.game.finished:
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {"type": "game.abort"},
            )

        async_to_sync(self.channel_layer.group_discard)(
            self.game_group_name, self.channel_name
        )

        try:
            self.game.refresh_from_db()
            self.game.connected_players.remove(self.user)
            self.game.save()
        except Game.DoesNotExist:
            pass

    # Receive message from WebSocket
    def receive(self, text_data):
        self.game.refresh_from_db()

        # check if two players are connected to the websocket
        # if not, return error message
        if self.game.connected_players.count() != 2:
            self.send(text_data=json.dumps({"message": "waiting for another player"}))
            return

        if self.game.current_player != self.user:
            self.send(text_data=json.dumps({"message": "not your turn"}))
            return

        if self.game.tiebreaker:
            self.game_end_tie(None)
            return

        self.game_main(None)

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

    def game_abort(self, _event):
        self.send(
            text_data=json.dumps({"message": "player disconnected", "abort": True})
        )
        try:
            self.game.delete()
        except Game.DoesNotExist:
            pass
        self.close()

    def game_end(self, event):
        self.game.refresh_from_db()

        if not event["tie"]:
            if self.game.player1_score > self.game.player2_score:
                self.game.winner = self.game.players.first()
                score = self.game.player1_score
            elif self.game.player1_score < self.game.player2_score:
                self.game.winner = self.game.players.last()
                score = self.game.player2_score
            else:
                if not self.game.tiebreaker:
                    self.game.tiebreaker = True
                    self.game.player1_roll = 0
                    self.game.player2_roll = 0
                    self.game.current_player = self.game.players.first()
                    self.game.save()
                # async_to_sync(self.channel_layer.group_send)(
                #     self.game_group_name,
                #     {
                #         "type": "game.end.tie",
                #     },
                # )
                self.game_end_tie(None)
                return
        else:
            score = max(
                self.game.player1_score, self.game.player2_score
            )  # they're the same anyway

        self.game.finished = True
        self.game.save()

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

    def game_end_tie(self, _event):
        self.game.refresh_from_db()

        if not self.game.tiebreaker:
            return

        if self.user != self.game.current_player:
            return

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

    def game_main(self, _event):
        self.game.refresh_from_db()

        if self.user != self.game.current_player:
            return

        roll = [random.randint(1, 6), random.randint(1, 6)]
        if roll[0] == roll[1]:
            roll += [random.randint(1, 6)]

        # increment round if both players have rolled
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

        score = sum(roll)

        if sum(roll[:2]) % 2 == 0:
            score += 10
        else:
            score -= 5

        score = max(score, 0)

        if self.game.current_player == self.game.players.first():
            self.game.player1_score += score
            score = self.game.player1_score
        else:
            self.game.player2_score += score
            score = self.game.player2_score
        self.game.save()

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

        self.game.current_player = self.game.players.exclude(
            username=self.game.current_player.username
        ).first()
        self.game.save()

        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {"type": "game.main"},
        )
