from django.contrib import admin
from .models import Order, OrderItem
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price', 'quantity', 'subtotal')
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'id')
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered']
    def mark_as_paid(self, request, queryset):
        queryset.update(status='Paid')
    mark_as_paid.short_description = "Mark selected orders as Paid"
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='Shipped')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='Delivered')
    mark_as_delivered.short_description = "Mark selected orders as Delivered"
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
