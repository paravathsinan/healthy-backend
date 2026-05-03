from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    prefix = models.CharField(max_length=10, null=True, blank=True)


    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    name = models.CharField(max_length=200)

    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_sold_out = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    badge_text = models.CharField(max_length=50, null=True, blank=True) # e.g., "16% OFF"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            
        if not self.sku and self.category:
            p_prefix = self.category.prefix or self.category.name[0].upper()
            
            # Count products in this category to generate next number
            # Using count is simple but we'll check for uniqueness to be safe
            category_products = Product.objects.filter(category=self.category)
            count = category_products.count() + 1
            
            sku_code = f"HDN-{p_prefix}-{count:03d}"
            while Product.objects.filter(sku=sku_code).exists():
                count += 1
                sku_code = f"HDN-{p_prefix}-{count:03d}"
                
            self.sku = sku_code
                
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    weight = models.CharField(max_length=50) # e.g., "500g"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.weight}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image_url = models.TextField() # Can be Cloudinary URL or Base64
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"

class ShadowOrderLog(models.Model):
    """Logs when someone clicks the WhatsApp button for analytics"""
    product_name = models.CharField(max_length=255)
    variant_details = models.CharField(max_length=255)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    clicked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order click for {self.product_name} at {self.clicked_at}"

class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField(null=True, blank=True)
    image_url = models.TextField() # Base64 or URL
    button_text = models.CharField(max_length=50, default="Explore Now")
    button_link = models.CharField(max_length=200, default="/category/all")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField()
    visited_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visit from {self.ip_address} at {self.visited_at}"

