import random
import string

from rest_framework import serializers as serialisers  # love being British

from .models import Game, User


class UserSerialiser(serialisers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password", "games"]
        read_only_fields = ["id", "games"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class GameSerialiser(serialisers.ModelSerializer):
    # players = serialisers.PrimaryKeyRelatedField(
    #     many=True, queryset=User.objects, allow_null=False
    # )

    class Meta:
        model = Game
        fields = [
            "id",
            "players",
            "player1_score",
            "player2_score",
            "finished",
            "winner",
        ]
        read_only_fields = [
            "id",
            "players",
            "player1_score",
            "player2_score",
            "finished",
            "winner",
        ]

    def create(self, validated_data):
        id = "".join(random.choices(string.digits, k=6))  # Output is like as 'XDCxVAJl'

        #     # validated_data["player1"] = validated_data["players"][0]
        #     # validated_data["player2"] = validated_data["players"][1]

        game = Game.objects.create(id=id)
        game.players.add(validated_data["user"])
        game.save()
        game.refresh_from_db()
        return game
