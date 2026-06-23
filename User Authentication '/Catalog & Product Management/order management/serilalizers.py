from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from products.models import Product
from products.serializers import ProductSerializer
class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    Includes nested product details (read-only) for presentation.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_details', 'price', 'quantity', 'subtotal']
class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer to display full Order details.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'user_email', 'status', 'total_amount', 'shipping_address', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_email', 'status', 'total_amount', 'created_at', 'updated_at']
class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to handle order creation (checkout).
    Reads the user's active cart and performs checkout atomically.
    """
    class Meta:
        model = Order
        fields = ['id', 'shipping_address']
    def validate(self, attrs):
        user = self.context['request'].user
        
        # Check if cart exists and has items
        cart = Cart.objects.filter(user=user).first()
        if not cart or not cart.items.exists():
            raise serializers.ValidationError("Your cart is empty. Add items to cart before placing an order.")
        # Check stock availability for all items in the cart
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                raise serializers.ValidationError(
                    f"Only {item.product.stock} units of '{item.product.name}' are in stock, but you requested {item.quantity}."
                )
        return attrs
    def create(self, validated_data):
        user = self.context['request'].user
        shipping_address = validated_data['shipping_address']
        # Retrieve cart
        cart = Cart.objects.get(user=user)
        cart_items = cart.items.all()
        # Wrap checkout logic in a database transaction to ensure atomicity
        with transaction.atomic():
            # Create Order placeholder
            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                status='Pending',
                total_amount=Decimal('0.00')
            )
            total_amount = Decimal('0.00')
            for cart_item in cart_items:
                product = cart_item.product
                quantity = cart_item.quantity
                price = product.price
                
                # Create OrderItem
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=price,
                    quantity=quantity
                )
                # Deduct stock from Product
                product.stock -= quantity
                product.save()
                # Add to total
                total_amount += price * quantity
            # Update final total order amount
            order.total_amount = total_amount
            order.save()
            # Empty the user's cart
            cart_items.delete()
        return order
