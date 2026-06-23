from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class AccountsAPITests(APITestCase):
    """
    Test suite for the accounts/authentication API endpoints.
    """
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user_data["email"])

    def test_user_registration_password_mismatch(self):
        data = self.user_data.copy()
        data["confirm_password"] = "differentpassword"
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        # Register user first
        User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"]
        )
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_profile_retrieval(self):
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            first_name="Jane",
            last_name="Doe"
        )
        # Login and authenticate client
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)
        self.assertEqual(response.data["first_name"], "Jane")

    def test_profile_update(self):
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            first_name="Jane",
            last_name="Doe"
        )
        self.client.force_authenticate(user=user)
        
        update_data = {
            "first_name": "JaneNew",
            "last_name": "DoeNew",
            "full_name": "Jane New Doe New",
            "city": "Seattle",
            "country": "USA",
            "gender": "Female",
            "date_of_birth": "1995-05-15",
            "bio": "Developer bio"
        }
        response = self.client.put(self.profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "JaneNew")
        self.assertEqual(response.data["full_name"], "Jane New Doe New")
        self.assertEqual(response.data["city"], "Seattle")
        self.assertEqual(response.data["gender"], "Female")
        self.assertEqual(response.data["bio"], "Developer bio")

    def test_dashboard_api(self):
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            first_name="Jane",
            last_name="Doe"
        )
        self.client.force_authenticate(user=user)
        
        dashboard_url = reverse('dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("profile", response.data)
        self.assertIn("loyalty_points_balance", response.data)
        self.assertIn("recent_loyalty_transactions", response.data)
        self.assertIn("recent_orders", response.data)
        self.assertIn("wishlist_items", response.data)

    def test_claim_daily_points(self):
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            first_name="Jane",
            last_name="Doe"
        )
        self.client.force_authenticate(user=user)
        
        claim_url = reverse('claim_daily')
        
        # 1. First claim should succeed
        response = self.client.post(claim_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("points_awarded", response.data)
        self.assertIn("new_balance", response.data)
        points_awarded = response.data["points_awarded"]
        self.assertTrue(50 <= points_awarded <= 150)
        
        user.refresh_from_db()
        self.assertEqual(response.data["new_balance"], user.loyalty_points)
        self.assertEqual(response.data["points_awarded"], points_awarded)

        # 2. Second claim on the same day should fail
        response2 = self.client.post(claim_url)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response2.data)

    def test_admin_sales_report_redirect_anonymous(self):
        redirect_url = reverse('admin_sales_report_redirect')
        response = self.client.get(redirect_url)
        # Should redirect anonymous user to django admin login page
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('/admin/login/', response.url)

    def test_admin_sales_report_redirect_staff(self):
        # Create a staff user
        staff_user = User.objects.create_user(
            email="admin_staff@example.com",
            password="staffpassword",
            is_staff=True
        )
        # Log in via Django session
        self.client.login(email="admin_staff@example.com", password="staffpassword")
        
        redirect_url = reverse('admin_sales_report_redirect')
        response = self.client.get(redirect_url)
        
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('/?access_token=', response.url)
        self.assertIn('&refresh_token=', response.url)
        self.assertIn('&screen=analytics', response.url)

    def test_profile_contains_is_staff(self):
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            first_name="Jane",
            last_name="Doe",
            is_staff=True
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_staff"], True)
        
        # Test that is_staff is read-only
        update_data = {
            "first_name": "JaneNew",
            "is_staff": False
        }
        response = self.client.put(self.profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should remain True because it's read-only
        self.assertEqual(response.data["is_staff"], True)
        
        user.refresh_from_db()
        self.assertEqual(user.is_staff, True)

    def test_get_loyalty_settings_anonymous(self):
        settings_url = reverse('loyalty_settings')
        response = self.client.get(settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("earning_rate", response.data)
        self.assertIn("redemption_rate", response.data)
        self.assertIn("daily_points_min", response.data)
        self.assertIn("daily_points_max", response.data)
        self.assertIn("terms_and_conditions", response.data)

    def test_update_loyalty_settings_anonymous(self):
        settings_url = reverse('loyalty_settings')
        response = self.client.put(settings_url, {"earning_rate": 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_loyalty_settings_non_staff(self):
        user = User.objects.create_user(
            email="regular@example.com",
            password="password123"
        )
        self.client.force_authenticate(user=user)
        settings_url = reverse('loyalty_settings')
        response = self.client.put(settings_url, {"earning_rate": 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_loyalty_settings_staff(self):
        staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            is_staff=True
        )
        self.client.force_authenticate(user=staff)
        settings_url = reverse('loyalty_settings')
        update_data = {
            "earning_rate": 2,
            "redemption_rate": "1.50",
            "daily_points_min": 100,
            "daily_points_max": 200,
            "terms_and_conditions": "New loyalty terms."
        }
        response = self.client.put(settings_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["earning_rate"], 2)
        self.assertEqual(float(response.data["redemption_rate"]), 1.50)
        self.assertEqual(response.data["daily_points_min"], 100)
        self.assertEqual(response.data["daily_points_max"], 200)
        self.assertEqual(response.data["terms_and_conditions"], "New loyalty terms.")



