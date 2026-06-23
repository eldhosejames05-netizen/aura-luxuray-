import requests
import json
import time
BASE_URL = "http://127.0.0.1:8000"
TIMESTAMP = int(time.time())
def print_section(title):
    print("\n" + "="*80)
    print(f" TESTING: {title}")
    print("="*80)
def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print("Response Body (Raw):", response.text[:200])
def main():
    print("Starting E-Commerce API Verification Script...")
    time.sleep(1) # wait for server to warm up
    # 1. Register a customer
    print_section("1. User Registration")
    reg_url = f"{BASE_URL}/api/accounts/register/"
    customer_email = f"customer_{TIMESTAMP}@example.com"
    customer_data = {
        "email": customer_email,
        "password": "customerpassword123",
        "confirm_password": "customerpassword123",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone_number": "1234567890",
        "address": "456 Customer Ave, Seattle, WA"
    }
    response = requests.post(reg_url, json=customer_data)
    print_response(response)
    
    # 2. Login Admin & Customer
    print_section("2. User Login (Get JWT Tokens)")
    login_url = f"{BASE_URL}/api/accounts/login/"
    
    # Login Admin
    print("\n--- Logging in Admin ---")
    admin_login_data = {
        "email": "admin@example.com",
        "password": "adminpassword"
    }
    admin_res = requests.post(login_url, json=admin_login_data)
    print_response(admin_res)
    admin_tokens = admin_res.json()
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access']}"}
    
    # Login Customer
    print("\n--- Logging in Customer ---")
    customer_login_data = {
        "email": customer_email,
        "password": "customerpassword123"
    }
    cust_res = requests.post(login_url, json=customer_login_data)
    print_response(cust_res)
    cust_tokens = cust_res.json()
    cust_headers = {"Authorization": f"Bearer {cust_tokens['access']}"}
    # 3. Refresh Token
    print_section("3. Refresh Token API")
    refresh_url = f"{BASE_URL}/api/accounts/token/refresh/"
    refresh_data = {"refresh": cust_tokens['refresh']}
    ref_res = requests.post(refresh_url, json=refresh_data)
    print_response(ref_res)
    new_access_token = ref_res.json().get('access')
    new_refresh_token = ref_res.json().get('refresh')
    cust_headers = {"Authorization": f"Bearer {new_access_token}"}
    # 4. View User Profile
    print_section("4. Protected Profile API")
    profile_url = f"{BASE_URL}/api/accounts/profile/"
    prof_res = requests.get(profile_url, headers=cust_headers)
    print_response(prof_res)
    # 5. Categories CRUD (Admin vs Customer check)
    print_section("5. Categories CRUD")
    cat_url = f"{BASE_URL}/api/products/categories/"
    cat_name = f"Electronics_{TIMESTAMP}"
    cat_data = {
        "name": cat_name,
        "description": "Gadgets, smartphones, and laptops."
    }
    
    print("\n--- Attempting to create category as Customer (Should be Forbidden) ---")
    cat_res_fail = requests.post(cat_url, json=cat_data, headers=cust_headers)
    print_response(cat_res_fail)
    
    print("\n--- Creating category as Admin (Should succeed) ---")
    cat_res_success = requests.post(cat_url, json=cat_data, headers=admin_headers)
    print_response(cat_res_success)
    category_slug = cat_res_success.json().get('slug')
    category_id = cat_res_success.json().get('id')
    # 6. Products CRUD, Search, and Filtering
    print_section("6. Products CRUD, Search, & Filtering")
    prod_url = f"{BASE_URL}/api/products/"
    prod_name1 = f"SuperPhone_{TIMESTAMP}"
    prod_data = {
        "category": category_id,
        "name": prod_name1,
        "description": "High performance smartphone with 120Hz display.",
        "price": "999.99",
        "stock": 50,
        "is_active": True
    }
    
    print("\n--- Creating product as Admin ---")
    prod_res = requests.post(prod_url, json=prod_data, headers=admin_headers)
    print_response(prod_res)
    product_slug = prod_res.json().get('slug')
    product_id = prod_res.json().get('id')
    # Add second product for search/filter tests
    prod_name2 = f"BudgetPhone_{TIMESTAMP}"
    prod_data2 = {
        "category": category_id,
        "name": prod_name2,
        "description": "An affordable Android smartphone.",
        "price": "199.99",
        "stock": 100,
        "is_active": True
    }
    requests.post(prod_url, json=prod_data2, headers=admin_headers)
    # Upload product image link
    print("\n--- Adding product image as Admin ---")
    img_url = f"{BASE_URL}/api/products/images/"
    img_data = {
        "product": product_id,
        "image_url": "https://example.com/images/superphone.jpg"
    }
    img_res = requests.post(img_url, json=img_data, headers=admin_headers)
    print_response(img_res)
    print(f"\n--- Public Product Search ('{prod_name2}') ---")
    search_res = requests.get(f"{prod_url}?search={prod_name2}")
    print_response(search_res)
    print("\n--- Public Product Filtering (Price range) ---")
    filter_res = requests.get(f"{prod_url}?price__gte=500.00&price__lte=1200.00")
    print_response(filter_res)
    # 7. Reviews
    print_section("7. Product Reviews")
    review_url = f"{BASE_URL}/api/products/reviews/"
    review_data = {
        "product": product_id,
        "rating": 5,
        "comment": "Incredible battery life and screen!"
    }
    review_res = requests.post(review_url, json=review_data, headers=cust_headers)
    print_response(review_res)
    # 8. Wishlist
    print_section("8. Wishlist Module")
    wishlist_url = f"{BASE_URL}/api/products/wishlist/"
    wishlist_data = {"product": product_id}
    
    print("\n--- Adding product to Wishlist ---")
    wish_add_res = requests.post(wishlist_url, json=wishlist_data, headers=cust_headers)
    print_response(wish_add_res)
    wishlist_item_id = wish_add_res.json().get('id')
    print("\n--- Viewing Wishlist ---")
    wish_view_res = requests.get(wishlist_url, headers=cust_headers)
    print_response(wish_view_res)
    print("\n--- Removing from Wishlist ---")
    requests.delete(f"{wishlist_url}{wishlist_item_id}/", headers=cust_headers)
    print("Wishlist item deleted. Current Wishlist:")
    wish_view_res2 = requests.get(wishlist_url, headers=cust_headers)
    print_response(wish_view_res2)
    # 9. Cart
    print_section("9. Cart Module")
    cart_url = f"{BASE_URL}/api/cart/"
    
    print("\n--- Adding product to Cart (SuperPhone x2) ---")
    cart_add_res = requests.post(f"{cart_url}add/", json={"product": product_id, "quantity": 2}, headers=cust_headers)
    print_response(cart_add_res)
    cart_item_id = cart_add_res.json().get('id')
    print("\n--- Viewing Cart ---")
    cart_view_res = requests.get(cart_url, headers=cust_headers)
    print_response(cart_view_res)
    print("\n--- Updating Cart Item Quantity (Update to 3) ---")
    cart_upd_res = requests.put(f"{cart_url}update/{cart_item_id}/", json={"quantity": 3}, headers=cust_headers)
    print_response(cart_upd_res)
    # 10. Orders (Checkout)
    print_section("10. Orders Module (Checkout)")
    order_url = f"{BASE_URL}/api/orders/"
    order_data = {
        "shipping_address": "123 E-Commerce Way, Cupertino, CA 95014"
    }
    
    print("\n--- Checking out (Creating Order from Cart) ---")
    order_create_res = requests.post(order_url, json=order_data, headers=cust_headers)
    print_response(order_create_res)
    order_id = order_create_res.json().get('id')
    print("\n--- Viewing Order History ---")
    order_hist_res = requests.get(order_url, headers=cust_headers)
    print_response(order_hist_res)
    # 11. Payments (Stripe Checkout Simulation)
    print_section("11. Payments Module (Stripe Integration)")
    pay_url = f"{BASE_URL}/api/payments/"
    
    print("\n--- Creating Stripe Payment Intent ---")
    intent_res = requests.post(f"{pay_url}create-intent/", json={"order_id": order_id}, headers=cust_headers)
    print_response(intent_res)
    payment_intent_id = intent_res.json().get('payment_intent_id')
    print("\n--- Verifying Stripe Payment ---")
    verify_res = requests.post(f"{pay_url}verify/", json={"payment_intent_id": payment_intent_id}, headers=cust_headers)
    print_response(verify_res)
    print("\n--- Viewing Payment History ---")
    pay_hist_res = requests.get(f"{pay_url}history/", headers=cust_headers)
    print_response(pay_hist_res)
    # 12. Cancel Order Check (Let's create another order and cancel it)
    print_section("12. Order Cancellation & Stock Restoration")
    print("\n--- Adding item to cart again ---")
    requests.post(f"{cart_url}add/", json={"product": product_id, "quantity": 1}, headers=cust_headers)
    
    print("\n--- Creating second order ---")
    order_res2 = requests.post(order_url, json={"shipping_address": "Cancelled Lane"}, headers=cust_headers)
    order_id2 = order_res2.json().get('id')
    print(f"Created Order #{order_id2}")
    
    # View product stock before cancellation
    prod_before = requests.get(f"{prod_url}{product_slug}/").json()
    print(f"Stock before cancelling Order #{order_id2}: {prod_before.get('stock')}")
    
    print("\n--- Cancelling Order ---")
    cancel_res = requests.post(f"{order_url}{order_id2}/cancel/", headers=cust_headers)
    print_response(cancel_res)
    
    # View product stock after cancellation
    prod_after = requests.get(f"{prod_url}{product_slug}/").json()
    print(f"Stock after cancelling Order #{order_id2}: {prod_after.get('stock')} (Should increase by 1)")
    # 13. User Logout (Blacklist Token)
    print_section("13. User Logout (Blacklist Refresh Token)")
    logout_url = f"{BASE_URL}/api/accounts/logout/"
    logout_data = {"refresh": new_refresh_token}
    logout_res = requests.post(logout_url, json=logout_data, headers=cust_headers)
    print_response(logout_res)
    print("\nAll tests completed successfully!")
if __name__ == "__main__":
    main()
