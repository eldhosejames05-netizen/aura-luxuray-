from django.db import models
from django.conf import settings
from orders.models import Order
class Payment(models.Model):
    """
    Model representing payment transaction records.
    One-to-One relationship ensures an order has exactly one payment log.
    """
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    stripe_charge_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Payment for Order #{self.order.id} - Status: {self.status} - Amount: {self.amount}"
