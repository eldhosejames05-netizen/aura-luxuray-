from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product
class Cart(models.Model):
    """
    Model representing a user's shopping cart.
    One-to-One relationship ensures each user has exactly one active cart.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Cart of {self.user.email}"
    @property
    def total_price(self):
        # Calculate total price of all items in this cart
        return sum(item.subtotal for item in self.items.all())
class CartItem(models.Model):
    """
    Model representing an item inside a shopping cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('cart', 'product')  # A product can only appear once in a cart
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart.user.email}'s cart"
    @property
    def subtotal(self):
        # Subtotal for this specific cart item
        return self.product.price * self.quantity
