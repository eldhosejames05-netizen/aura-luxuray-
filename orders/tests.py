from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from products.models import Category, Product
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from payments.models import Payment

User = get_user_model()

class OrdersAPITests(APITestCase):
    """
    Test suite for placing orders, managing stock, cancellation,
    calculating loyalty points, and generating sales reports.
    """
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123"
        )
        self.customer_user = User.objects.create_user(
            email="customer@example.com",
            password="customerpassword123"
        )
        
        # Create categories and products
        self.category = Category.objects.create(
            name="Accessories",
            description="Luxury accessories"
        )
        
        # Pen costing ₹150,000 to earn 150 points
        self.luxury_pen = Product.objects.create(
            category=self.category,
            name="Aura Gold Fountain Pen",
            description="Premium 24k gold fountain pen.",
            price=Decimal("150000.00"),
            stock=10,
            is_active=True
        )
        
        # Cheap notebook costing ₹500
        self.cheap_notebook = Product.objects.create(
            category=self.category,
            name="Notebook",
            description="Plain leather notebook.",
            price=Decimal("500.00"),
            stock=20,
            is_active=True
        )

        # Endpoints
        self.order_list_url = reverse('order-list')
        self.sales_report_url = reverse('order-sales-report')

    def test_order_creation_success(self):
        """
        Test placing an order clears the cart and reduces stock.
        """
        self.client.force_authenticate(user=self.customer_user)
        
        # Add items to user's cart
        cart, _ = Cart.objects.get_or_create(user=self.customer_user)
        CartItem.objects.create(cart=cart, product=self.luxury_pen, quantity=2)
        CartItem.objects.create(cart=cart, product=self.cheap_notebook, quantity=3)
        
        # Verify initial stocks
        self.assertEqual(self.luxury_pen.stock, 10)
        self.assertEqual(self.cheap_notebook.stock, 20)

        # Place order
        order_data = {"shipping_address": "123 Aura Lane, Bangalore, KA - 560001"}
        response = self.client.post(self.order_list_url, order_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order details in DB
        order_obj = Order.objects.get(id=response.data["id"])
        self.assertEqual(order_obj.status, "Pending")
        self.assertEqual(float(order_obj.total_amount), 301500.00) # (150000 * 2) + (500 * 3)
        
        # Verify cart is empty
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())

        # Verify stock is reduced
        self.luxury_pen.refresh_from_db()
        self.cheap_notebook.refresh_from_db()
        self.assertEqual(self.luxury_pen.stock, 8)
        self.assertEqual(self.cheap_notebook.stock, 17)

    def test_order_creation_empty_cart(self):
        """
        Placing an order with an empty cart should fail.
        """
        self.client.force_authenticate(user=self.customer_user)
        order_data = {"shipping_address": "123 Aura Lane"}
        response = self.client.post(self.order_list_url, order_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cart is empty", str(response.data))

    def test_order_creation_insufficient_stock(self):
        """
        Placing an order with quantity exceeding stock should fail.
        """
        self.client.force_authenticate(user=self.customer_user)
        
        # Set stock to 1
        self.luxury_pen.stock = 1
        self.luxury_pen.save()

        # Try to buy 2
        cart, _ = Cart.objects.get_or_create(user=self.customer_user)
        CartItem.objects.create(cart=cart, product=self.luxury_pen, quantity=2)

        order_data = {"shipping_address": "123 Aura Lane"}
        response = self.client.post(self.order_list_url, order_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("units of 'Aura Gold Fountain Pen' are in stock", str(response.data))

    def test_order_cancellation_restores_stock(self):
        """
        Cancelling a pending order restores product stock.
        """
        self.client.force_authenticate(user=self.customer_user)
        
        cart, _ = Cart.objects.get_or_create(user=self.customer_user)
        CartItem.objects.create(cart=cart, product=self.luxury_pen, quantity=2)
        
        # Create order (reduces stock by 2, remaining: 8)
        order_data = {"shipping_address": "123 Aura Lane"}
        order_res = self.client.post(self.order_list_url, order_data)
        order_id = order_res.data["id"]
        
        self.luxury_pen.refresh_from_db()
        self.assertEqual(self.luxury_pen.stock, 8)

        # Cancel order
        cancel_url = reverse('order-cancel', args=[order_id])
        response = self.client.post(cancel_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "Cancelled")

        # Verify stock is restored
        self.luxury_pen.refresh_from_db()
        self.assertEqual(self.luxury_pen.stock, 10)

    def test_sales_report_authorization_and_calculations(self):
        """
        Admin sales report is protected and aggregates correct stats.
        """
        # Create some orders
        # Order 1: Paid (150,500 INR)
        order1 = Order.objects.create(
            user=self.customer_user,
            shipping_address="Address 1",
            status="Paid",
            total_amount=Decimal("150500.00")
        )
        # Order 2: Cancelled (500 INR)
        order2 = Order.objects.create(
            user=self.customer_user,
            shipping_address="Address 2",
            status="Cancelled",
            total_amount=Decimal("500.00")
        )
        
        # 1. Customer user attempts to fetch report -> Forbidden
        self.client.force_authenticate(user=self.customer_user)
        response_cust = self.client.get(self.sales_report_url)
        self.assertEqual(response_cust.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin user fetches report -> Success
        self.client.force_authenticate(user=self.admin_user)
        response_admin = self.client.get(self.sales_report_url)
        
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(response_admin.data["total_sales"], 150500.00) # Only counts Paid/Shipped/Delivered
        self.assertEqual(response_admin.data["total_orders"], 2) # Counts all orders
        self.assertEqual(response_admin.data["avg_order_value"], 150500.00)
        self.assertEqual(len(response_admin.data["orders"]), 2)

    def test_loyalty_points_accrual_on_payment(self):
        """
        Verifies loyalty points are credited correctly when payment is verified.
        ₹150,500 order total => 150 points earned.
        """
        self.client.force_authenticate(user=self.customer_user)
        
        # Create a paid order
        order = Order.objects.create(
            user=self.customer_user,
            shipping_address="Aura Mansion",
            status="Pending",
            total_amount=Decimal("150500.00")
        )
        
        # Create associated Payment log in Pending state
        payment = Payment.objects.create(
            order=order,
            stripe_payment_intent_id="mock_session_9999",
            amount=Decimal("150500.00"),
            status="Pending"
        )

        # Initially customer has 0 points
        self.assertEqual(self.customer_user.loyalty_points, 0)

        # Verify payment using payments verify API
        verify_url = reverse('payment-verify') if hasattr(self, 'payment_verify_url') else '/api/payments/verify/'
        verify_data = {"session_id": "mock_session_9999"}
        
        response = self.client.post(verify_url, verify_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Order should be marked Paid
        order.refresh_from_db()
        self.assertEqual(order.status, "Paid")
        
        # Payment should be success
        payment.refresh_from_db()
        self.assertEqual(payment.status, "Success")

        # Customer loyalty points should increase: 150500 // 100 = 1505
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.loyalty_points, 1505)

    def test_loyalty_points_redemption_on_checkout(self):
        """
        Verifies loyalty points can be redeemed during checkout.
        """
        self.client.force_authenticate(user=self.customer_user)
        
        # Give customer 100 points
        self.customer_user.loyalty_points = 100
        self.customer_user.save()

        # Add item costing ₹500 to cart
        cart, _ = Cart.objects.get_or_create(user=self.customer_user)
        CartItem.objects.create(cart=cart, product=self.cheap_notebook, quantity=1)

        # Place order with 50 points redemption
        order_data = {
            "shipping_address": "Aura Lane 123",
            "redeem_points": 50
        }
        response = self.client.post(self.order_list_url, order_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify points deducted from user
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.loyalty_points, 50)

        # Verify discount applied to order
        order_obj = Order.objects.get(id=response.data["id"])
        self.assertEqual(order_obj.points_redeemed, 50)
        self.assertEqual(float(order_obj.discount_applied), 50.00)
        self.assertEqual(float(order_obj.total_amount), 450.00) # 500 - 50 = 450

    def test_loyalty_points_redemption_validation(self):
        """
        Verifies points redemption validation works for insufficient points or exceeding subtotal.
        """
        self.client.force_authenticate(user=self.customer_user)
        
        # Give customer 10 points
        self.customer_user.loyalty_points = 10
        self.customer_user.save()

        # Add item costing ₹500 to cart
        cart, _ = Cart.objects.get_or_create(user=self.customer_user)
        CartItem.objects.create(cart=cart, product=self.cheap_notebook, quantity=1)

        # 1. Try redeeming 50 points (insufficient balance)
        order_data = {"shipping_address": "Aura Lane 123", "redeem_points": 50}
        response1 = self.client.post(self.order_list_url, order_data)
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)

        # Give customer 1000 points
        self.customer_user.loyalty_points = 1000
        self.customer_user.save()

        # 2. Try redeeming 600 points (exceeds order total of ₹500)
        order_data = {"shipping_address": "Aura Lane 123", "redeem_points": 600}
        response2 = self.client.post(self.order_list_url, order_data)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_loyalty_points_reversal_on_cancellation(self):
        """
        Verifies cancelled orders refund redeemed points and reverse earned points.
        """
        self.client.force_authenticate(user=self.customer_user)

        # Give customer 200 points
        self.customer_user.loyalty_points = 200
        self.customer_user.save()

        # Place order redeeming 50 points
        cart, _ = Cart.objects.get_or_create(user=self.customer_user)
        CartItem.objects.create(cart=cart, product=self.cheap_notebook, quantity=1) # ₹500
        
        order_data = {"shipping_address": "Aura Lane", "redeem_points": 50}
        order_res = self.client.post(self.order_list_url, order_data)
        order_id = order_res.data["id"]

        # Points should be 150 now
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.loyalty_points, 150)

        # Let's pay/verify this order to earn points: 450 // 100 = 4 points
        order_obj = Order.objects.get(id=order_id)
        payment = Payment.objects.create(
            order=order_obj,
            stripe_payment_intent_id="mock_session_cancel_test",
            amount=order_obj.total_amount,
            status="Pending"
        )
        
        verify_url = '/api/payments/verify/'
        self.client.post(verify_url, {"session_id": "mock_session_cancel_test"})

        # User earned 4 points => total 154
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.loyalty_points, 154)

        # Cancel the order -> should refund 50 points and reverse 4 points -> user balance should go back to 200
        cancel_url = reverse('order-cancel', args=[order_id])
        cancel_res = self.client.post(cancel_url)
        self.assertEqual(cancel_res.status_code, status.HTTP_200_OK)

        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.loyalty_points, 200)

    def test_sales_report_expanded_metrics(self):
        """
        Verifies that the sales report contains all the new, expanded dashboard metrics.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.sales_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check overview cards
        self.assertIn("total_revenue", response.data)
        self.assertIn("total_sales_count", response.data)
        self.assertIn("total_customers", response.data)
        self.assertIn("total_products", response.data)
        self.assertIn("pending_orders_count", response.data)
        
        # Check analytics ranges
        self.assertIn("sales_by_week", response.data)
        self.assertIn("sales_by_month", response.data)
        self.assertIn("sales_by_year", response.data)
        self.assertIn("revenue_growth_percentage", response.data)
        self.assertIn("profit_loss", response.data)
        
        # Check sales/customer distribution
        self.assertIn("sales_by_region", response.data)
        self.assertIn("top_categories", response.data)
        self.assertIn("new_customers_this_month", response.data)
        self.assertIn("returning_customers", response.data)
        self.assertIn("customer_growth", response.data)
        self.assertIn("top_customers", response.data)
        
        # Check inventory/payment stats
        self.assertIn("total_stock", response.data)
        self.assertIn("low_stock_count", response.data)
        self.assertIn("out_of_stock_count", response.data)
        self.assertIn("inventory_value", response.data)
        self.assertIn("total_payments_received", response.data)
        self.assertIn("pending_payments", response.data)
        self.assertIn("failed_payments", response.data)
        self.assertIn("method_distribution", response.data)
        self.assertIn("refund_statistics", response.data)


