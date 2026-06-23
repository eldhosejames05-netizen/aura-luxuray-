from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product
class Order(models.Model):
    """
    Model representing a customer order.
    """
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"Order #{self.id} - {self.user.email} - Status: {self.status}"
class OrderItem(models.Model):
    """
    Model representing an item in a placed order.
    Stores historical price at the moment of checkout.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Capture product price at purchase time
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} in Order #{self.order.id}"
    @property
    def subtotal(self):
        return self.price * self.quantity
