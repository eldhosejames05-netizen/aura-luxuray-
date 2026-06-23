from django.urls import path
from .views import (
    CartView,
    CartAddItemView,
    CartUpdateItemView,
    CartRemoveItemView
)
urlpatterns = [
    # View current user's cart
    path('', CartView.as_view(), name='cart_view'),
    
    # Add item to cart
    path('add/', CartAddItemView.as_view(), name='cart_add'),
    
    # Update quantity of a cart item
    path('update/<int:item_id>/', CartUpdateItemView.as_view(), name='cart_update'),
    
    # Remove item from cart
    path('remove/<int:item_id>/', CartRemoveItemView.as_view(), name='cart_remove'),
]
