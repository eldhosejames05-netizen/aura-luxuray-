from django.contrib import admin
from .models import Category, Product, ProductImage, Review, Wishlist
# Inline editor for product images inside the Product view
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment', 'user__email', 'product__name')
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name')
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Wishlist, WishlistAdmin)
