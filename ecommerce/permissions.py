from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow administrators to edit or delete objects,
    while allowing read-only access to everyone.
    """
    def has_permission(self, request, view):
        # Read-only permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users (staff)
        return bool(request.user and request.user.is_staff)
