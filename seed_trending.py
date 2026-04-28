import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Category, Product, ProductVariant, ProductImage
from decimal import Decimal

# Helper to get or create category
def get_cat(name):
    cat, _ = Category.objects.get_or_create(name=name)
    return cat

# Data from the storefront fallback
trending_products = [
    {
        'name': 'Ajwa Dates',
        'category': 'Dates',
        'price': 1200.00,
        'image': '/images/products/ajwa-dates.png',
        'desc': 'Premium Ajwa dates from Madinah. Known for their unique texture and health benefits.'
    },
    {
        'name': 'Premium Medjool King Dates',
        'category': 'Dates',
        'price': 1499.00,
        'image': '/images/products/medjool-king copy.png',
        'desc': 'Large, sweet and succulent Medjool dates. Often called the King of Dates.'
    },
    {
        'name': 'Exotic Macadamia Nuts',
        'category': 'Nuts',
        'price': 1899.00,
        'image': '/images/products/macadamia copy.png',
        'desc': 'Creamy, crunchy and rich Macadamia nuts. A true exotic delicacy.'
    },
    {
        'name': 'Luxury Persian Saffron (1g)',
        'category': 'Spices',
        'price': 599.00,
        'image': '/images/products/saffron copy.png',
        'desc': 'Pure Grade A Persian saffron. The most precious spice in the world.'
    }
]

print("Starting to seed trending products...")

for item in trending_products:
    cat = get_cat(item['category'])
    product, created = Product.objects.get_or_create(
        name=item['name'],
        defaults={
            'category': cat,
            'description': item['desc'],
            'is_featured': True
        }
    )
    if created:
        # Add variants
        base = Decimal(str(item['price']))
        ProductVariant.objects.create(product=product, weight='250 G', price=base * Decimal('0.30'), stock_count=100)
        ProductVariant.objects.create(product=product, weight='500 G', price=base * Decimal('0.55'), stock_count=100)
        ProductVariant.objects.create(product=product, weight='1000 G', price=base, stock_count=100)
        # Add image
        ProductImage.objects.create(product=product, image_url=item['image'], is_primary=True)
        print(f"Created: {item['name']}")
    else:
        product.is_featured = True
        product.save()
        print(f"Updated: {item['name']} (Set to Featured)")

print("Seeding completed!")
