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
    description = models.TextField()
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_sold_out = models.BooleanField(default=False)
    badge_text = models.CharField(max_length=50, null=True, blank=True) # e.g., "16% OFF"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            
        if not self.sku and self.category:
            # Use category prefix or first letter of category name
            p_prefix = self.category.prefix or self.category.name[0].upper()
            
            # Find all products in this category to get the next sequence number
            # We look for the highest existing number for this prefix
            from django.db.models import Max
            category_products = Product.objects.filter(category=self.category, sku__startswith=p_prefix)
            
            if category_products.exists():
                # This is a bit naive but works for standard cases like D1, D2...
                # For better robustness we'd need to parse the numeric part
                # But let's keep it simple for now as requested
                count = category_products.count() + 1
                self.sku = f"{p_prefix}{count}"
                
                # Check for collision (just in case)
                while Product.objects.filter(sku=self.sku).exists():
                    count += 1
                    self.sku = f"{p_prefix}{count}"
            else:
                self.sku = f"{p_prefix}1"
                
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

