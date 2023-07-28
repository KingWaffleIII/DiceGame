from django.urls import path
from . import views

app_name = "app"
urlpatterns = [
    path("", views.home, name="home"),
    path("game/<str:id>/", views.game, name="game"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
]
