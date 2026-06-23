from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from cart.models import Cart


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for placing, viewing, and cancelling orders.
    - Regular users can only access their own orders.
    - Admin users can view and update the status of any order.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Admin users can view all orders; regular users only view their own
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @transaction.atomic
    def perform_create(self, serializer):
        """
        Create order from cart items.
        Automatically assigns user and calculates total amount.
        """
        cart = get_object_or_404(Cart, user=self.request.user)
        
        if not cart.items.exists():
            raise ValueError("Cannot create order from empty cart")
        
        # Calculate total amount
        total_amount = cart.total_price
        
        # Create the order
        order = serializer.save(user=self.request.user, total_amount=total_amount)
        
        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.price,
                quantity=cart_item.quantity
            )
        
        # Clear the cart
        cart.items.all().delete()
    
    @action(detail=False, methods=['post'])
    def create_from_cart(self, request):
        """
        Create an order directly from the user's cart.
        POST /api/orders/create_from_cart/
        
        Expected payload:
        {
            "shipping_address": "123 Main St, City, State 12345"
        }
        """
        cart = get_object_or_404(Cart, user=request.user)
        
        if not cart.items.exists():
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            total_amount = cart.total_price
            
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_amount=total_amount,
                    shipping_address=serializer.validated_data['shipping_address']
                )
                
                # Create order items from cart items
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        price=cart_item.product.price,
                        quantity=cart_item.quantity
                    )
                
                # Clear the cart
                cart.items.all().delete()
            
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Custom endpoint to cancel an order.
        URL: POST /api/orders/{id}/cancel/
        """
        # Admin can cancel any order; standard users can only cancel their own
        if request.user.is_staff:
            order = get_object_or_404(Order, pk=pk)
        else:
            order = get_object_or_404(Order, pk=pk, user=request.user)
        
        # Check if the order can be cancelled
        if order.status in ['Shipped', 'Delivered']:
            return Response(
                {"error": f"Cannot cancel order because it is already {order.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.status == 'Cancelled':
            return Response(
                {"message": "Order is already cancelled."},
                status=status.HTTP_200_OK
            )
        # Atomic transaction to cancel and restore stock
        with transaction.atomic():
            order.status = 'Cancelled'
            order.save()
            # Restore product stock
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save()
        return Response(
            {"message": "Order cancelled successfully. Stock has been restored.", "status": order.status},
            status=status.HTTP_200_OK
        )
