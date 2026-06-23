from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from ecommerce.permissions import IsAdminOrReadOnly
from .models import Category, Product, ProductImage, Review, Wishlist
from .serializers import (
    CategorySerializer, 
    ProductSerializer, 
    ProductImageSerializer, 
    ReviewSerializer, 
    WishlistSerializer
)

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for products and search results.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD.
    Admin can edit, others can only read.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD.
    Admin can edit, others can only read.
    Supports search, filtering, and pagination.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'slug'

    # Configure search, filter and ordering backends
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter by category, and check stock/activity status
    filterset_fields = {
        'category__slug': ['exact'],
        'price': ['gte', 'lte'],
        'is_active': ['exact'],
    }
    
    # Search by product name and description
    search_fields = ['name', 'description']
    
    # Order by price, stock, and creation date
    ordering_fields = ['price', 'stock', 'created_at']
    ordering = ['-created_at']  # Default sorting


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Product Images.
    Admin can edit, others can only read.
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product reviews.
    Anyone can view, only authenticated users can write, update or delete reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        # GET, HEAD, OPTIONS allowed for anyone; others require authentication
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Automatically assign the logged-in user as the review author
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Optionally filter reviews by product ID
        queryset = Review.objects.all()
        product_id = self.request.query_params.get('product')
        if product_id is not None:
            queryset = queryset.filter(product_id=product_id)
        return queryset


class WishlistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing, adding, and removing wishlist items.
    Access restricted to the owner of the wishlist.
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # A user can only see their own wishlist items
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Save with the current authenticated user
        serializer.save(user=self.request.user)
