from django.urls import re_path

from api.consumers import DiceGameConsumer

websocket_urlpatterns = [
    re_path(r"^ws/game/(?P<id>\w+)/$", DiceGameConsumer.as_asgi()),
]
