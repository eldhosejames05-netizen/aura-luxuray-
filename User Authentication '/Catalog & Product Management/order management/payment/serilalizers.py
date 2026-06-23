from rest_framework import serializers
from .models import Payment
class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer to serialize and validate Payment records.
    """
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'stripe_payment_intent_id', 
            'stripe_charge_id', 'amount', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

