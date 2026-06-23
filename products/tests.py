from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Category, Product, Review, Wishlist

User = get_user_model()

class ProductsAPITests(APITestCase):
    """
    Test suite for products, categories, reviews, and wishlist APIs.
    """
    def setUp(self):
        # Create user accounts
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123"
        )
        self.customer_user = User.objects.create_user(
            email="customer@example.com",
            password="customerpassword123"
        )
        
        # Create a sample Category
        self.category = Category.objects.create(
            name="Books",
            description="All kinds of books"
        )
        
        # Create a sample Product
        self.product = Product.objects.create(
            category=self.category,
            name="Django for Beginners",
            description="Learn Django web development step-by-step.",
            price="39.99",
            stock=10,
            is_active=True
        )
        
        # Endpoints
        self.category_list_url = reverse('category-list')
        self.product_list_url = reverse('product-list')
        self.review_list_url = reverse('review-list')
        self.wishlist_list_url = reverse('wishlist-list')

    def test_category_list_public(self):
        response = self.client.get(self.category_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_category_create_admin_only(self):
        cat_data = {"name": "Fashion", "description": "Trendy clothes"}
        
        # Customer should be forbidden
        self.client.force_authenticate(user=self.customer_user)
        response_cust = self.client.post(self.category_list_url, cat_data)
        self.assertEqual(response_cust.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin should succeed
        self.client.force_authenticate(user=self.admin_user)
        response_admin = self.client.post(self.category_list_url, cat_data)
        self.assertEqual(response_admin.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_admin.data["name"], "Fashion")

    def test_product_search_and_filter(self):
        # Add another product
        Product.objects.create(
            category=self.category,
            name="React Cookbook",
            description="Recipes for React developers.",
            price="49.99",
            stock=5,
            is_active=True
        )
        
        # Test Search (should match "React")
        search_url = f"{self.product_list_url}?search=React"
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Result is paginated, so count check is in 'count'
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "React Cookbook")

        # Test Price Filter (price <= 45.00)
        filter_url = f"{self.product_list_url}?price__lte=45.00"
        response_filter = self.client.get(filter_url)
        self.assertEqual(response_filter.status_code, status.HTTP_200_OK)
        self.assertEqual(response_filter.data["count"], 1)
        self.assertEqual(response_filter.data["results"][0]["name"], "Django for Beginners")

    def test_review_creation(self):
        self.client.force_authenticate(user=self.customer_user)
        review_data = {
            "product": self.product.id,
            "rating": 5,
            "comment": "Awesome book!"
        }
        response = self.client.post(self.review_list_url, review_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["comment"], "Awesome book!")
        self.assertEqual(response.data["user_email"], self.customer_user.email)

    def test_wishlist_add_and_remove(self):
        self.client.force_authenticate(user=self.customer_user)
        wishlist_data = {"product": self.product.id}
        
        # Add to wishlist
        response = self.client.post(self.wishlist_url_for_post() if hasattr(self, 'wishlist_url_for_post') else self.wishlist_list_url, wishlist_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        wishlist_id = response.data["id"]

        # View wishlist
        response_view = self.client.get(self.wishlist_list_url)
        self.assertEqual(response_view.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_view.data), 1)

        # Delete from wishlist
        detail_url = reverse('wishlist-detail', kwargs={'pk': wishlist_id})
        response_del = self.client.delete(detail_url)
        self.assertEqual(response_del.status_code, status.HTTP_204_NO_CONTENT)
