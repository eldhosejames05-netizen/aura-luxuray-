from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet
router = DefaultRouter()
# Register the OrderViewSet. This creates routes for:
# GET /api/orders/ - List orders
# POST /api/orders/ - Create order
# GET /api/orders/{id}/ - Retrieve order
# PUT/PATCH /api/orders/{id}/ - Update order status (Admins only)
# POST /api/orders/{id}/cancel/ - Cancel order
router.register(r'', OrderViewSet, basename='order')
urlpatterns = [
    path('', include(router.urls)),
]
