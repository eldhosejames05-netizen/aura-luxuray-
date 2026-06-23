from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, LoyaltyPoints

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user registration.
    Includes password and password confirmation matching.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name', 'phone_number', 'address']

    def validate(self, attrs):
        # Validate that the two password fields match
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields must match."})
        return attrs

    def create(self, validated_data):
        # Remove confirm_password as it's not a model field
        validated_data.pop('confirm_password')
        # Create user using the custom manager helper to ensure password hashing
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            address=validated_data.get('address', '')
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer to view and update the logged-in user's profile.
    The email field is read-only since it is the unique login identifier.
    Exposes and handles writable nested profile details.
    """
    profile_picture = serializers.ImageField(source='profile.profile_picture', required=False, allow_null=True)
    full_name = serializers.CharField(source='profile.full_name', required=False, allow_blank=True)
    city = serializers.CharField(source='profile.city', required=False, allow_null=True, allow_blank=True)
    state = serializers.CharField(source='profile.state', required=False, allow_null=True, allow_blank=True)
    country = serializers.CharField(source='profile.country', required=False, allow_null=True, allow_blank=True)
    postal_code = serializers.CharField(source='profile.postal_code', required=False, allow_null=True, allow_blank=True)
    date_of_birth = serializers.DateField(source='profile.date_of_birth', required=False, allow_null=True)
    gender = serializers.CharField(source='profile.gender', required=False, allow_null=True, allow_blank=True)
    bio = serializers.CharField(source='profile.bio', required=False, allow_null=True, allow_blank=True)

    wishlist_count = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    loyalty_points_balance = serializers.IntegerField(source='loyalty_points', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number', 'address',
            'profile_picture', 'full_name', 'city', 'state', 'country',
            'postal_code', 'date_of_birth', 'gender', 'bio',
            'wishlist_count', 'order_count', 'loyalty_points_balance', 'is_staff'
        ]
        read_only_fields = ['id', 'email', 'loyalty_points_balance', 'is_staff']

    def get_wishlist_count(self, obj):
        return obj.wishlist.count()

    def get_order_count(self, obj):
        return obj.orders.count()

    def validate_date_of_birth(self, value):
        import datetime
        if value and value >= datetime.date.today():
            raise serializers.ValidationError("Date of birth must be in the past.")
        return value

    def validate_gender(self, value):
        choices = ['Male', 'Female', 'Other']
        if value and value not in choices:
            raise serializers.ValidationError("Gender must be one of Male, Female, or Other.")
        return value

    def update(self, instance, validated_data):
        # Update user fields
        user_fields = ['first_name', 'last_name', 'phone_number', 'address']
        for field in user_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        # Update profile fields
        profile_data = validated_data.pop('profile', {})
        profile, created = UserProfile.objects.get_or_create(user=instance)
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        
        # Avoid cached relation issues in serialized response
        instance.profile = profile
        return instance


class LoyaltyPointsSerializer(serializers.ModelSerializer):
    """
    Serializer for loyalty points transaction logs.
    """
    class Meta:
        model = LoyaltyPoints
        fields = ['id', 'points', 'transaction_type', 'order', 'description', 'created_at']
        read_only_fields = fields


from .models import LoyaltySettings

class LoyaltySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltySettings
        fields = ['earning_rate', 'redemption_rate', 'daily_points_min', 'daily_points_max', 'terms_and_conditions']


