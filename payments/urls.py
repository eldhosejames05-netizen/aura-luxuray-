from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    CreatePaymentIntentView,
    PaymentVerificationView,
    PaymentHistoryView,
    MockPaymentGatewayView
)

urlpatterns = [
    # Create Stripe Checkout Session (Redirect flow)
    path('create-session/', CreateCheckoutSessionView.as_view(), name='create_checkout_session'),
    
    # Create Stripe Payment Intent for an order (Legacy support)
    path('create-intent/', CreatePaymentIntentView.as_view(), name='create_payment_intent'),
    
    # Verify Stripe payment after checkout (either session or intent)
    path('verify/', PaymentVerificationView.as_view(), name='payment_verify'),
    
    # Retrieve user's payment history
    path('history/', PaymentHistoryView.as_view(), name='payment_history'),
    
    # Mock checkout secure sandbox gateway template
    path('mock-gateway/', MockPaymentGatewayView.as_view(), name='mock_gateway'),
]
