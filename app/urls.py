from django.urls import include, path
from . import views

app_name = "app"
urlpatterns = [
    path("", views.home, name="home"),
    path("game/<str:id>/", views.play, name="game"),
    path("game/<str:id>/results/", views.game_results, name="game_results"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("sign-up/", views.signup, name="sign-up"),
]
