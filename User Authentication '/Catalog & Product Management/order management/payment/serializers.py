from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model.
    Displays payment transaction details and status.
    """
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_id', 'stripe_payment_intent_id', 
            'stripe_charge_id', 'amount', 'status', 'created_at'
        ]
        read_only_fields = [
            'id', 'stripe_payment_intent_id', 'stripe_charge_id', 'created_at'
        ]


class StripePaymentIntentSerializer(serializers.Serializer):
    """
    Serializer for creating Stripe payment intent.
    Used during checkout process.
    """
    order_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='INR', max_length=3)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class PaymentVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying Stripe payment after callback.
    Expects Stripe payment intent ID and client secret.
    """
    payment_intent_id = serializers.CharField()
    client_secret = serializers.CharField()
