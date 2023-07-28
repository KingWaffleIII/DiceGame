import random
import string
from django.contrib import messages
from django.contrib.auth import authenticate, login as login_user, logout as logout_user
from django.shortcuts import render, redirect

from . import forms, models


def home(request):
    if not request.user.is_authenticated:
        messages.error(request, "You must be authenticated to do that!")
        return redirect("app:login")

    return render(request, "app/home.html")


def game(request, id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be authenticated to do that!")
        return redirect("app:login")

    try:
        match id:
            case "local":
                return render(request, "app/localgame.html")
            case "new":
                game = models.Game.objects.create(
                    id="".join(
                        random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(8)
                    )
                )
                return redirect("app:game", id=game.id)
            case _:
                game = models.Game.objects.get(id=id)
                if request.user not in game.players.all():
                    game.players.add(request.user)
                    game.save()
                return render(request, "app/game.html", {"game": game})
    except models.Game.DoesNotExist:
        messages.error(request, "That game doesn't exist!")
        return redirect("app:home")


def login(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            form = forms.LoginForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data["name"]
                password = form.cleaned_data["password"]

                user = authenticate(request, username=name, password=password)

                login_user(request, user)

                messages.success(request, "Logged in successfully.")
                return redirect("app:home")

            return render(request, "app/login.html", {"form": form})

        form = forms.LoginForm()
        return render(
            request,
            "app/login.html",
            {"form": form},
        )

    return redirect("app:home")


def signup(request):
    if request.method == "POST":
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            password = form.cleaned_data["password"]
            user = models.User.objects.create_user(username=name, password=password)
            user.save()
            login_user(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("app:home")

        return render(
            request,
            "app/signup.html",
            {"form": form},
        )

    form = forms.SignUpForm()

    return render(
        request,
        "app/signup.html",
        {"form": form},
    )


def logout(request):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to do that!")
    else:
        logout_user(request)
        messages.success(request, "You have been logged out.")
        return redirect("app:login")
