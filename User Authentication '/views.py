from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserRegisterSerializer, UserProfileSerializer
User = get_user_model()
class RegisterView(generics.CreateAPIView):
    """
    View for registering a new user.
    Uses Class-Based Views (CreateAPIView) and DRF Serializer.
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User registered successfully.",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }, status=status.HTTP_201_CREATED)
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve and update the authenticated user's profile.
    Uses IsAuthenticated permission, protecting this endpoint from anonymous access.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        # Always return the current authenticated user object
        return self.request.user
class LogoutView(APIView):
    """
    View to logout a user by blacklisting their Refresh Token.
    Requires authentication.
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            # Extract refresh token from request data
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required in body."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Instantiating the RefreshToken will parse it, and calling blacklist()
            # will add it to the blacklisted tokens database (requires rest_framework_simplejwt.token_blacklist)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logged out successfully (token blacklisted)."}, 
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
