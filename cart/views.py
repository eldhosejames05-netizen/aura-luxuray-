from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product

class BaseCartView(APIView):
    """
    Base view containing helper method to retrieve or create the user's cart.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_user_cart(self, user):
        # Get or create a cart for the logged-in user
        cart, created = Cart.objects.get_or_create(user=user)
        return cart


class CartView(BaseCartView):
    """
    View to retrieve the logged-in user's cart.
    GET /api/cart/
    """
    def get(self, request):
        cart = self.get_user_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartAddItemView(BaseCartView):
    """
    View to add an item to the user's cart.
    POST /api/cart/add/
    Request Body: {"product": <product_id>, "quantity": <quantity>}
    """
    def post(self, request):
        cart = self.get_user_cart(request.user)
        
        # We can pass data to CartItemSerializer for validation
        # We inject the cart ID into the serializer context/data
        data = request.data.copy()
        product_id = data.get('product')
        quantity = int(data.get('quantity', 1))

        if not product_id:
            return Response({"error": "Product field is required."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        # Check if item is already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            # If item already exists, increment the quantity
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
