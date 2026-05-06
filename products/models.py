from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
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
    is_featured = models.BooleanField(default=False, db_index=True)
    is_best_seller = models.BooleanField(default=False, db_index=True)
    is_new_arrival = models.BooleanField(default=False, db_index=True)
    is_sold_out = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False, db_index=True)
    badge_text = models.CharField(max_length=50, null=True, blank=True) # e.g., "16% OFF"
    tags = models.JSONField(default=list, blank=True) # e.g., ["Organic", "No Added Sugar"]
    
    # Simple pricing fields for easy syncing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def generate_sku(self):
        p_prefix = self.category.prefix or self.category.name[0].upper()
        
        last_product = (
            Product.objects
            .filter(category=self.category, sku__startswith=f"HDN-{p_prefix}-")
            .order_by("-id")
            .first()
        )

        if last_product and last_product.sku:
            try:
                last_number = int(last_product.sku.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"HDN-{p_prefix}-{new_number:03d}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            
        if not self.sku and self.category:
            self.sku = self.generate_sku()
                
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    weight = models.CharField(max_length=50, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.weight}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500) # Must be a Cloudinary/External URL
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"

class ShadowOrderLog(models.Model):
    """Logs when someone clicks the WhatsApp button for analytics"""
    product_name = models.CharField(max_length=255)
    variant_details = models.CharField(max_length=255)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    @classmethod
    def cleanup(cls, days=30):
        """Removes logs older than specified days to prevent DB bloat (default 30 days)"""
        cls.objects.filter(
            clicked_at__lt=timezone.now() - timedelta(days=days)
        ).delete()

    def __str__(self):
        return f"Order click for {self.product_name} at {self.clicked_at}"

class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField(null=True, blank=True)
    image_url = models.URLField(max_length=500) # Must be a URL
    button_text = models.CharField(max_length=50, default="Explore Now")
    button_link = models.CharField(max_length=200, default="/category/all")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField(db_index=True)
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)

    @classmethod
    def cleanup(cls, days=365):
        """Removes logs older than 365 days to prevent DB bloat"""
        cls.objects.filter(
            visited_at__lt=timezone.now() - timedelta(days=days)
        ).delete()

    def __str__(self):
        return f"Visit from {self.ip_address} at {self.visited_at}"


class BrowserVisitor(models.Model):
    """
    Tracks unique visitors via a UUID stored in the browser's localStorage.
    One row per unique device/browser — far more accurate than IP-based tracking.
    VPNs, shared WiFi, and mobile network changes do NOT inflate this count.
    """
    visitor_id = models.UUIDField(unique=True, db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Browser Visitor"
        verbose_name_plural = "Browser Visitors"

    def __str__(self):
        return f"Visitor {self.visitor_id} (first seen {self.first_seen:%Y-%m-%d})"

