from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage, ShadowOrderLog

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_featured', 'is_best_seller')
    list_filter = ('category', 'is_featured')
    inlines = [ProductImageInline, ProductVariantInline]
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ShadowOrderLog)
class ShadowOrderLogAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'variant_details', 'quantity', 'total_price', 'clicked_at')
    readonly_fields = ('product_name', 'variant_details', 'quantity', 'total_price', 'clicked_at')

admin.site.register(ProductVariant)
admin.site.register(ProductImage)
