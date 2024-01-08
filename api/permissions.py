from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    """
    Custom permission class for the User viewset.
    Users cannot list all the accounts but they can view their account and other accounts.
    Users can only update or delete their own account.
    """

    def has_permission(self, request, view):
        if view.action == "create":
            return True
        if view.action in ["retrieve", "partial_update", "destroy"]:
            return request.user.is_authenticated
        return False

    def has_object_permission(self, request, view, obj):
        if view.action in ["retrieve", "partial_update", "destroy"]:
            return request.user == obj
        return False


class GamePermission(permissions.BasePermission):
    """
    Custom permission class for the Game viewset.
    Users can only view games they are a player in.
    These are only read-only.
    """

    def has_permission(self, request, view):
        if view.action in ["retrieve", "create"]:
            # return request.user.is_authenticated
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if view.action == "create":
            return request.user.is_authenticated
        if view.action in ["retrieve"]:
            # return request.user in obj.players.all()
            return True
        return False
