from django.contrib.auth import authenticate
from django.contrib.auth import login as login_user
from django.contrib.auth import logout as logout_user
from django.contrib import messages
from django.shortcuts import redirect, render
from api.models import Game, User


def get_top_five_games():
    top_games = Game.objects.filter(finished=True).order_by("-player1_score")[:5]
    top_games2 = Game.objects.filter(finished=True).order_by("-player2_score")[:5]

    # combine the two lists, sort by score, and get the top 5

    combined = set(list(top_games) + list(top_games2))
    top_games = sorted(
        combined,
        key=lambda x: x.player1_score
        if x.player1_score > x.player2_score
        else x.player2_score,
        reverse=True,
    )[:5]

    games = []

    for game in top_games:
        games.append(
            (
                game.id,
                game.winner,
                game.player1_score
                if game.player1_score > game.player2_score
                else game.player2_score,
            )
        )

    return games


def login(request):
    if request.user.is_authenticated:
        messages.error(request, "You are already logged in.")
        return redirect("app:home")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if not username or not password:
            messages.error(request, "Please fill out all fields.")
            return redirect("app:login")
        user = authenticate(username=username, password=password)
        if not user:
            messages.error(request, "Invalid username or password.")
            return redirect("app:login")
        login_user(request, user)
        return redirect("app:home")
    return render(request, "app/login.html", {"title": "Login"})


def logout(request):
    logout_user(request)
    return redirect("app:login")


def signup(request):
    if request.user.is_authenticated:
        messages.error(request, "You are already logged in.")
        return redirect("app:home")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")
        if not username or not password:
            messages.error(request, "Please fill out all fields.")
            return redirect("app:sign-up")
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect("app:sign-up")
        user = authenticate(username=username, password=password)
        if user:
            messages.error(request, "That username is already taken.")
            return redirect("app:sign-up")
        user = User.objects.create_user(username=username, password=password)
        login_user(request, user)
        return redirect("app:home")
    return render(request, "app/sign-up.html", {"title": "Sign-up"})


def home(request):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view this page.")
        return redirect("app:login")

    games = get_top_five_games()

    return render(
        request,
        "app/home.html",
        {
            "title": "Home",
            "games": games,
        },
    )


def play(request, id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view this page.")
        return redirect("app:login")
    try:
        Game.objects.get(id=id)
    except Game.DoesNotExist:
        messages.error(request, "That game does not exist.")
        return redirect("app:home")

    return render(request, "app/game.html", {"title": id, "id": id})


def game_results(request, id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view this page.")
        return redirect("app:login")
    try:
        game = Game.objects.get(id=id)
    except Game.DoesNotExist:
        messages.error(request, "That game does not exist.")
        return redirect("app:home")

    # if not game.players.contains(request.user):
    #     messages.error(request, "You are not a player in this game.")
    #     return redirect("app:home")

    if not game.finished:
        messages.error(request, "This game is not finished yet.")
        return redirect("app:home")

    if game.player1_score > game.player2_score:
        winner = game.players.first().username
        winning_score = game.player1_score
        loser = game.players.last().username
        losing_score = game.player2_score
    else:
        winner = game.players.last().username
        winning_score = game.player2_score
        loser = game.players.first().username
        losing_score = game.player1_score

    games = get_top_five_games()
    top_5 = game.id in map(lambda x: x[0], games)

    return render(
        request,
        "app/game_results.html",
        {
            "title": id,
            "id": id,
            "game": game,
            "winner": winner,
            "loser": loser,
            "winning_score": winning_score,
            "losing_score": losing_score,
            "top_5": top_5,
        },
    )
