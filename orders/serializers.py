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
        fields = [
            'id', 'user', 'user_email', 'status', 'total_amount', 'shipping_address',
            'points_redeemed', 'discount_applied', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'status', 'total_amount', 'points_redeemed', 'discount_applied', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to handle order creation (checkout).
    Reads the user's active cart and performs checkout atomically.
    Supports loyalty points redemption.
    """
    redeem_points = serializers.IntegerField(write_only=True, required=False, default=0, min_value=0)

    class Meta:
        model = Order
        fields = ['id', 'shipping_address', 'redeem_points']

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

        redeem_points = attrs.get('redeem_points', 0)
        if redeem_points > 0:
            if user.loyalty_points < redeem_points:
                raise serializers.ValidationError(
                    f"Insufficient loyalty points. Available balance is {user.loyalty_points}."
                )
            
            # Check if redeem_points exceeds order subtotal
            subtotal = sum(item.product.price * item.quantity for item in cart.items.all())
            if redeem_points > subtotal:
                raise serializers.ValidationError(
                    f"Cannot redeem more points than the order total (₹{subtotal})."
                )

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        shipping_address = validated_data['shipping_address']
        redeem_points = validated_data.get('redeem_points', 0)

        # Retrieve cart
        cart = Cart.objects.get(user=user)
        cart_items = cart.items.all()

        from accounts.services import LoyaltyService

        # Wrap checkout logic in a database transaction to ensure atomicity
        with transaction.atomic():
            # Create Order placeholder
            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                status='Pending',
                total_amount=Decimal('0.00'),
                points_redeemed=0,
                discount_applied=Decimal('0.00')
            )

            subtotal = Decimal('0.00')

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
                subtotal += price * quantity

            # Apply points redemption discount if any
            discount = Decimal('0.00')
            if redeem_points > 0:
                try:
                    LoyaltyService.redeem_points(user, order, redeem_points)
                except Exception as e:
                    raise serializers.ValidationError({"redeem_points": str(e)})
                
                from accounts.models import LoyaltySettings
                settings = LoyaltySettings.get_settings()
                discount = Decimal(redeem_points) * Decimal(settings.redemption_rate)
                order.points_redeemed = redeem_points
                order.discount_applied = discount

            # Update final total order amount (subtotal - discount)
            order.total_amount = max(Decimal('0.00'), subtotal - discount)
            order.save()

            # Empty the user's cart
            cart_items.delete()

        return order
