from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CartItem model.
    Includes nested product details for display purposes.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_details', 'quantity', 'subtotal', 'created_at']
        read_only_fields = ['created_at', 'product_details', 'subtotal']
    
    def get_subtotal(self, obj):
        return str(obj.subtotal)
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model.
    Includes nested cart items and computed total price.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'user_email', 'items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['user', 'user_email', 'created_at', 'updated_at']
    
    def get_total_price(self, obj):
        return str(obj.total_price)
