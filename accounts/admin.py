from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, LoyaltyPoints, LoyaltySettings

class CustomUserAdmin(UserAdmin):
    """
    Configure Django Admin for the Custom User model.
    Overrides standard UserAdmin to reflect fields of our custom model.
    """
    model = User
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'loyalty_points', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'address', 'loyalty_points')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone_number', 'city', 'state', 'country')
    search_fields = ('user__email', 'full_name', 'phone_number')

@admin.register(LoyaltyPoints)
class LoyaltyPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'transaction_type', 'order', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__email', 'order__id', 'description')

@admin.register(LoyaltySettings)
class LoyaltySettingsAdmin(admin.ModelAdmin):
    list_display = ('earning_rate', 'redemption_rate', 'daily_points_min', 'daily_points_max')


