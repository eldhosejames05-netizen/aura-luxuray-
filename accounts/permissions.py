from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to view/edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Safe methods (GET, HEAD, OPTIONS) are allowed if the user is authenticated
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return obj == request.user

        # Write permissions are only allowed to the owner or admin
        if request.user and request.user.is_staff:
            return True
            
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        return obj == request.user
