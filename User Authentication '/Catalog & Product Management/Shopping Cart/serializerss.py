from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer
from products.models import Product
class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CartItem model.
    Includes full product details (read-only) for GET requests.
    Validates quantity against available product stock.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_details', 'quantity', 'subtotal']
        read_only_fields = ['cart', 'subtotal']
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value
    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)
        # If updating an existing cart item, retrieve the product from instance if not provided
        if not product and self.instance:
            product = self.instance.product
        # Validate against product stock
        if product.stock < quantity:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} units of {product.name} are in stock."}
            )
        return attrs
class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model.
    Includes list of items in the cart and computed total price.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'user_email', 'items', 'total_price']
        read_only_fields = ['user', 'user_email']
