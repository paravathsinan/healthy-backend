import secrets
from django.db import models
from django.utils import timezone
from products.models import Product, ProductVariant

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONTACTED', 'Contacted'),
        ('AWAITING_PAY', 'Awaiting Payment'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Milestone Timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:
                now = timezone.now()
                
                # Logic to backfill timestamps if steps are skipped
                if self.status == 'CONTACTED':
                    if not self.confirmed_at: self.confirmed_at = now
                
                elif self.status == 'AWAITING_PAY' or self.status == 'PAID':
                    if not self.confirmed_at: self.confirmed_at = now
                    if not self.processed_at: self.processed_at = now
                
                elif self.status == 'SHIPPED':
                    if not self.confirmed_at: self.confirmed_at = now
                    if not self.processed_at: self.processed_at = now
                    if not self.shipped_at: self.shipped_at = now
                
                elif self.status == 'COMPLETED':
                    if not self.confirmed_at: self.confirmed_at = now
                    if not self.processed_at: self.processed_at = now
                    if not self.shipped_at: self.shipped_at = now
                    if not self.delivered_at: self.delivered_at = now

        if not self.order_number:
            date_str = timezone.now().strftime('%d%m%y')
            # Generate random 4-character hex code
            random_str = secrets.token_hex(2).upper()
            self.order_number = f"HDN-{date_str}-{random_str}"
            
            # Uniqueness check
            while Order.objects.filter(order_number=self.order_number).exists():
                random_str = secrets.token_hex(2).upper()
                self.order_number = f"HDN-{date_str}-{random_str}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)  # Snapshot of name
    variant_name = models.CharField(max_length=255)  # Snapshot of variant
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.variant_name})"
