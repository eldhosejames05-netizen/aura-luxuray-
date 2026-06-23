from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductImageViewSet, ReviewViewSet, WishlistViewSet
# Initialize DefaultRouter
router = DefaultRouter()
# Register ViewSets in order of specificity to avoid URL routing collisions
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'images', ProductImageViewSet, basename='productimage')
router.register(r'', ProductViewSet, basename='product')  # Matches root-level /api/products/
urlpatterns = [
    path('', include(router.urls)),
]
