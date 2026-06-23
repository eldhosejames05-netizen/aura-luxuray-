from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts import views as accounts_views

urlpatterns = [
    # Serve the Single-Page Application frontend at the root URL
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Custom Admin Sales Report Redirect (handles SSO to frontend)
    path('admin/sales-report/', accounts_views.admin_sales_report_redirect, name='admin_sales_report_redirect'),
    
    # Django Admin site
    path('admin/', admin.site.urls),
    
    # Accounts/Auth module APIs
    path('api/accounts/', include('accounts.urls')),
    
    # Products module APIs (includes Catalog, Search, Categories, Reviews, and Wishlist)
    path('api/products/', include('products.urls')),
    
    # Cart module APIs (View, Add, Update, Remove)
    path('api/cart/', include('cart.urls')),
    
    # Orders module APIs (Create, History, Details, Cancel)
    path('api/orders/', include('orders.urls')),
    
    # Payments module APIs (Stripe integration, Verification, History)
    path('api/payments/', include('payments.urls')),
]
