# Here, models are defined for use throughout the project - these are essentially equivalent to tables in a database, with fields being the columns.


from django.db import models
from django.contrib.auth.models import AbstractUser


# We are using the built-in Django User model, but I have extended it so in future it is easier to add more fields.
# The model supports emails, usernames, and passwords with encryption.
class User(AbstractUser):
    pass


# This is the Game mode, which stores all the information about a game.
class Game(models.Model):
    # The ID is what we use as game codes.
    id = models.CharField(max_length=8, primary_key=True)
    # This contains a list of all the players (User models) in the game.
    players = models.ManyToManyField(User, related_name="games", blank=True)
    # This contains a list of all the players (User models) in the game that are currently connected via websockets.
    connected_players = models.ManyToManyField(
        User, related_name="connected_game", blank=True
    )

    # These are the rolls and scores of each player, they are updated every round.
    player1_roll = models.JSONField(default=list)
    player2_roll = models.JSONField(default=list)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)

    # This is the current round, and the current player - this prevents players from playing out of turn.
    round = models.IntegerField(default=1)
    current_player = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="+", null=True
    )

    # These are some boolean values so the app can check what logic needs to run as well as defining the winner which links to the User model.
    tiebreaker = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    winner = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="won_games", null=True
    )
