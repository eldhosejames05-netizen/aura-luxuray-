from rest_framework import serializers
from django.contrib.auth import get_user_model
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
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'is_staff']
        read_only_fields = ['email', 'is_staff']
