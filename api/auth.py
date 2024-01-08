import base64
import binascii

from channels.db import database_sync_to_async
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user(username, password):
    return authenticate(username=username, password=password)


class BasicAuthMiddleware:
    """
    Custom middleware that decodes a Base64 encoded basic auth header and sets the user on the scope.
    If the user has already been set (other middleware), it will remain untouched.
    If the user cannot be authenticated, it is set as an AnonymousUser.
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            return await self.app(scope, receive, send)

        if scope["user"] in scope.keys() and not scope["user"].is_anonymous:
            return await self.app(scope, receive, send)

        headers = scope["headers"]
        for header in headers:
            if header[0].decode() == "authorization":
                try:
                    encoded_credentials = header[1].decode().split(" ")[1]
                    username, password = (
                        base64.b64decode(encoded_credentials).decode("utf-8").split(":")
                    )
                    scope["user"] = await get_user(username, password)
                except binascii.Error:  # invalid base64
                    pass

        if not "user" in scope.keys():
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
