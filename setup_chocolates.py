import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Category, Product, ProductVariant, ProductImage
from decimal import Decimal

def setup_chocolates():
    # Ensure Chocolates category exists
    choc_category, created = Category.objects.get_or_create(
        name='Chocolates',
        defaults={'slug': 'chocolates', 'display_order': 10}
    )
    if created:
        print("Created Chocolates category")

    # Product data from screenshot
    products_to_add = [
        {
            'name': 'Premium Medjool King Dates',
            'price': Decimal('1499.00'),
            'image': '/images/products/medjool-king copy.png',
            'is_featured': True
        },
        {
            'name': 'Exotic Macadamia Nuts',
            'price': Decimal('1899.00'),
            'image': '/images/products/macadamia copy.png',
            'is_featured': True
        },
        {
            'name': 'Luxury Persian Saffron (1g)',
            'price': Decimal('599.00'),
            'image': '/images/products/saffron copy.png',
            'is_featured': True
        },
        {
            'name': 'Royal Baklava Gift Selection',
            'price': Decimal('2499.00'),
            'image': '/images/products/baklava-gift copy.png',
            'is_featured': True
        }
    ]

    for p_data in products_to_add:
        # Check if product already exists to avoid duplicates
        p, created = Product.objects.get_or_create(
            name=p_data['name'],
            defaults={
                'category': choc_category,
                'description': f"Premium quality {p_data['name']} sourced globally.",
                'is_featured': p_data['is_featured']
            }
        )
        
        if created:
            # Add image
            ProductImage.objects.create(
                product=p,
                image_url=p_data['image'],
                is_primary=True
            )
            # Add variants (using the auto-create logic would be nice, but let's do it manually here for precision)
            ProductVariant.objects.create(product=p, weight='250 G', price=p_data['price'] * Decimal('0.30'), stock_count=100)
            ProductVariant.objects.create(product=p, weight='500 G', price=p_data['price'] * Decimal('0.55'), stock_count=100)
            ProductVariant.objects.create(product=p, weight='1000 G', price=p_data['price'], stock_count=100)
            print(f"Added product: {p_data['name']}")
        else:
            print(f"Product already exists: {p_data['name']}")

if __name__ == '__main__':
    setup_chocolates()

    