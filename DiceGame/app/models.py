from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Game(models.Model):
    id = models.CharField(max_length=8, primary_key=True)
    players = models.ManyToManyField(User, related_name="games")
    player1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="player1", null=True
    )
    player2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="player2", null=True
    )
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    turn = models.IntegerField(default=1)
