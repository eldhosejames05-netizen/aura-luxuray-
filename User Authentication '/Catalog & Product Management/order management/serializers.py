from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    Includes nested product details and computed subtotal.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_details', 'price', 'quantity', 'subtotal']
        read_only_fields = ['product_details', 'subtotal']
    
    def get_subtotal(self, obj):
        return str(obj.subtotal)


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    Includes nested order items and user information.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_email', 'status', 'total_amount', 
            'shipping_address', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'user_email', 'created_at', 'updated_at', 'total_amount']


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders from cart.
    Requires shipping_address; user and total_amount are set automatically.
    """
    
    class Meta:
        model = Order
        fields = ['shipping_address']
