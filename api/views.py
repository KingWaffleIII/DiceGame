from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status, viewsets

from . import models, permissions, serialisers


class UserViewSet(viewsets.ViewSet):
    """
    User view set containing views for creating, partial updating, and deleting users.
    See the permission classes for the access configuration.
    """

    permission_classes = [permissions.UserPermission]

    def retrieve(self, request, pk=None):
        """Retrieves details on the supplied user."""
        queryset = models.User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, user)
        serialiser = serialisers.UserSerialiser(user, context={"request": request})
        return Response(serialiser.data)

    def create(self, request):
        """Creates a new user."""
        serialiser = serialisers.UserSerialiser(
            data=request.data, context={"request": request}
        )
        serialiser.is_valid(raise_exception=True)
        serialiser.save()
        return Response(serialiser.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        """Partially updates the supplied user."""
        queryset = models.User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, user)
        serialiser = serialisers.UserSerialiser(
            user, data=request.data, context={"request": request}, partial=True
        )
        serialiser.is_valid(raise_exception=True)
        serialiser.save()
        # Return the updated user.
        serialiser = serialisers.UserSerialiser(user, context={"request": request})
        return Response(serialiser.data)

    def destroy(self, request, pk=None):
        """Deletes the supplied user."""
        queryset = models.User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, user)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GameViewSet(viewsets.ViewSet):
    """
    Gane view set containing views for retrieving games.
    See the permission classes for the access configuration.
    """

    permission_classes = [permissions.GamePermission]

    def retrieve(self, request, pk=None):
        """Retrieves details on the supplied game."""
        queryset = models.Game.objects.all()
        game = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, game)
        serialiser = serialisers.GameSerialiser(game, context={"request": request})
        return Response(serialiser.data)

    def create(self, request):
        """Creates a new game."""
        serialiser = serialisers.GameSerialiser(
            data=request.data, context={"request": request}
        )
        serialiser.is_valid(raise_exception=True)
        serialiser.save(user=request.user)
        return Response(serialiser.data, status=status.HTTP_201_CREATED)
