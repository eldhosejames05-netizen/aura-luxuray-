from rest_framework import serializers
from .models import Category, Product, ProductImage, Review, Wishlist
from django.db.models import Avg

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at']
        read_only_fields = ['slug', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductImage model.
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'created_at']
        read_only_fields = ['created_at']


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    Includes user email as a read-only field for presentation.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'user_email', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'user_email', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        # A user can only review a product once
        request = self.context.get('request')
        if not request or not request.user:
            return attrs
            
        product = attrs.get('product')
        # Check if review already exists for this user and product (only on creation)
        if self.instance is None:
            if Review.objects.filter(product=product, user=request.user).exists():
                raise serializers.ValidationError("You have already reviewed this product.")
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    Includes nested images, category details, reviews, and computed average rating.
    """
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'name', 'slug', 
            'description', 'price', 'stock', 'is_active', 
            'images', 'average_rating', 'reviews', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_average_rating(self, obj):
        # Aggregate and compute average rating from associated reviews
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else 0.0


class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializer for Wishlist model.
    Includes full product details when serializing (GET requests).
    """
    product_details = ProductSerializer(source='product', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'user_email', 'product', 'product_details', 'created_at']
        read_only_fields = ['user', 'user_email', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user:
            return attrs

        product = attrs.get('product')
        # Check if already wishlisted (only on creation)
        if self.instance is None:
            if Wishlist.objects.filter(user=request.user, product=product).exists():
                raise serializers.ValidationError("This product is already in your wishlist.")
        return attrs
