from django.contrib import admin
from .models import Payment

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'stripe_payment_intent_id', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__id', 'stripe_payment_intent_id', 'order__user__email')

admin.site.register(Payment, PaymentAdmin)
