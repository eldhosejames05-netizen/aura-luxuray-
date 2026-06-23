from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, ProfileView, LogoutView
urlpatterns = [
    # User registration endpoint
    path('register/', RegisterView.as_view(), name='register'),
    
    # Login endpoint using Simple JWT (obtains access and refresh token)
    path('login/', TokenObtainPairView.as_view(), name='login'),
    
    # Refresh token endpoint to obtain a new access token using a valid refresh token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Logout endpoint (blacklists the refresh token)
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Authenticated user profile endpoint (GET, PUT, PATCH)
    path('profile/', ProfileView.as_view(), name='profile'),
]
