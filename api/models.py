from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Game(models.Model):
    id = models.CharField(max_length=8, primary_key=True)
    players = models.ManyToManyField(User, related_name="games", blank=True)
    connected_players = models.ManyToManyField(
        User, related_name="connected_game", blank=True
    )
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    round = models.IntegerField(default=1)
    current_player = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="+", null=True
    )
    player1_roll = models.JSONField(default=list)
    player2_roll = models.JSONField(default=list)
    tiebreaker = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    winner = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="won_games", null=True
    )
