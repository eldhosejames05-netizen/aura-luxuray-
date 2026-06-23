from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'total_price')
    inlines = [CartItemInline]
    search_fields = ('user__email',)

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
