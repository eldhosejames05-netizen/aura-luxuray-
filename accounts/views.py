from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserRegisterSerializer, UserProfileSerializer
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required

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
        
        # Send Welcome Email (Fail-Silently via Celery)
        try:
            from .tasks import send_welcome_email_task
            send_welcome_email_task.delay(user.id)
        except Exception:
            pass


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


class LoyaltyTransactionHistoryView(APIView):
    """
    API view to retrieve current loyalty points balance and transaction history.
    GET /api/accounts/loyalty/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        from .models import LoyaltyPoints
        from .serializers import LoyaltyPointsSerializer
        transactions = LoyaltyPoints.objects.filter(user=user)
        serializer = LoyaltyPointsSerializer(transactions, many=True)
        return Response({
            "loyalty_points_balance": user.loyalty_points,
            "transactions": serializer.data
        }, status=status.HTTP_200_OK)


class UserDashboardView(APIView):
    """
    API view to retrieve consolidated User Dashboard information.
    GET /api/accounts/dashboard/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # 1. Profile Details
        profile_serializer = UserProfileSerializer(user, context={'request': request})
        
        # 2. Loyalty Transactions
        from .models import LoyaltyPoints
        from .serializers import LoyaltyPointsSerializer
        recent_transactions = LoyaltyPoints.objects.filter(user=user)[:5]
        transactions_serializer = LoyaltyPointsSerializer(recent_transactions, many=True)
        
        # 3. Order History
        from orders.models import Order
        from orders.serializers import OrderSerializer
        recent_orders = Order.objects.filter(user=user)[:5]
        orders_serializer = OrderSerializer(recent_orders, many=True, context={'request': request})
        
        # 4. Wishlist Items
        from products.models import Wishlist
        from products.serializers import WishlistSerializer
        wishlist_items = Wishlist.objects.filter(user=user)
        wishlist_serializer = WishlistSerializer(wishlist_items, many=True, context={'request': request})
        
        return Response({
            "profile": profile_serializer.data,
            "loyalty_points_balance": user.loyalty_points,
            "recent_loyalty_transactions": transactions_serializer.data,
            "recent_orders": orders_serializer.data,
            "wishlist_items": wishlist_serializer.data
        }, status=status.HTTP_200_OK)


class ClaimDailyPointsView(APIView):
    """
    API view for claiming daily loyalty points.
    POST /api/accounts/claim-daily/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        import random
        from django.utils import timezone
        user = request.user
        from .models import LoyaltyPoints
        
        # Check if user has already claimed points today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        has_claimed = LoyaltyPoints.objects.filter(
            user=user, 
            transaction_type='Earned', 
            description='Daily login reward',
            created_at__gte=today_start
        ).exists()

        if has_claimed:
            return Response({"error": "You have already claimed your daily reward today. Come back tomorrow!"}, status=status.HTTP_400_BAD_REQUEST)

        # Award a random number of points based on Loyalty Settings
        from .models import LoyaltySettings
        settings = LoyaltySettings.get_settings()
        points_awarded = random.randint(settings.daily_points_min, settings.daily_points_max)
        
        # Create transaction
        LoyaltyPoints.objects.create(
            user=user,
            points=points_awarded,
            transaction_type='Earned',
            description='Daily login reward'
        )
        
        # Update user balance
        user.loyalty_points += points_awarded
        user.save(update_fields=['loyalty_points'])

        return Response({
            "message": f"Successfully claimed {points_awarded} loyalty points!",
            "points_awarded": points_awarded,
            "new_balance": user.loyalty_points
        }, status=status.HTTP_200_OK)


@staff_member_required
def admin_sales_report_redirect(request):
    """
    Generate JWT tokens for the logged-in staff user and redirect them
    to the frontend SPA's Sales Analytics dashboard.
    """
    user = request.user
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    redirect_url = f"/?access_token={access_token}&refresh_token={refresh_token}&screen=analytics"
    return redirect(redirect_url)


from .models import LoyaltySettings
from .serializers import LoyaltySettingsSerializer

class LoyaltySettingsView(APIView):
    """
    API view to retrieve and update the loyalty points settings.
    GET /api/accounts/loyalty-settings/ - AllowAny
    PUT /api/accounts/loyalty-settings/ - IsAdminUser
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get(self, request):
        settings = LoyaltySettings.get_settings()
        serializer = LoyaltySettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        settings = LoyaltySettings.get_settings()
        serializer = LoyaltySettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)



