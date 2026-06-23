from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product


class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shopping cart.
    Only authenticated users can access their own cart.
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own cart
        return Cart.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        """
        Retrieve the current user's cart or create one if it doesn't exist.
        """
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        Add a product to the cart or update quantity if already exists.
        
        Expected payload:
        {
            "product_id": 1,
            "quantity": 2
        }
        """
        cart, created = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if quantity < 1:
            return Response(
                {'error': 'Quantity must be at least 1'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantity > product.stock:
            return Response(
                {'error': f'Only {product.stock} items available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity = quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """
        Remove a product from the cart.
        
        Expected payload:
        {
            "product_id": 1
        }
        """
        cart = get_object_or_404(Cart, user=request.user)
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        cart_item.delete()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        """
        Remove all items from the cart.
        """
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
            new_quantity = cart_item.quantity + quantity
            
            # Use serializer to validate the new combined quantity
            serializer = CartItemSerializer(
                cart_item, 
                data={'quantity': new_quantity}, 
                partial=True,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # If created, validate the item using the serializer
        serializer = CartItemSerializer(cart_item, context={'request': request})
        # Check if quantity exceeds stock
        if product.stock < quantity:
            # Clean up the created item if invalid
            cart_item.delete()
            return Response(
                {"error": f"Only {product.stock} units of {product.name} are in stock."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response(serializer.data, status=status.HTTP_201_CREATED)
class CartUpdateItemView(BaseCartView):
    """
    View to update the quantity of a specific cart item.
    PUT /api/cart/update/{item_id}/
    Request Body: {"quantity": <new_quantity>}
    """
    def put(self, request, item_id):
        cart = self.get_user_cart(request.user)
        
        # Fetch the cart item belonging to this user's cart
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        serializer = CartItemSerializer(
            cart_item, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class CartRemoveItemView(BaseCartView):
    """
    View to remove an item from the user's cart.
    DELETE /api/cart/remove/{item_id}/
    """
    def delete(self, request, item_id):
        cart = self.get_user_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        return Response(
            {"message": "Item successfully removed from cart."}, 
            status=status.HTTP_200_OK
        )
