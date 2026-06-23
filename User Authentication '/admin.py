from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
class CustomUserAdmin(UserAdmin):
    """
    Configure Django Admin for the Custom User model.
    Overrides standard UserAdmin to reflect fields of our custom model.
    """
    model = User
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('email',)
admin.site.register(User, CustomUserAdmin)
