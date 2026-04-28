import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Category

def setup_categories():
    categories_data = [
        { 'name': 'Dates', 'image': '/images/categories/organic-premium-dates.png', 'order': 1 },
        { 'name': 'Nuts', 'image': '/images/categories/premium-california-nuts.png', 'order': 2 },
        { 'name': 'Dried Fruits', 'image': '/images/categories/healthy-mixed-dry-fruits.png', 'order': 3 },
        { 'name': 'Spices', 'image': '/images/categories/authentic-indian-spices.png', 'order': 4 },
        { 'name': 'Chocolates', 'image': '/images/categories/premium-assorted-chocolates.png', 'order': 5 },
        { 'name': 'Beverages', 'image': '/images/categories/healthy-beverages-bottles.png', 'order': 6 },
        { 'name': 'Imported', 'image': '/images/categories/premium-imported-products.png', 'order': 7 },
        { 'name': 'Gift Box', 'image': '/images/categories/luxury-gift-boxes-hampers.png', 'order': 8 },
    ]

    for data in categories_data:
        cat, created = Category.objects.update_or_create(
            name=data['name'],
            defaults={
                'image_url': data['image'],
                'display_order': data['order']
            }
        )
        status = "Created" if created else "Updated"
        print(f"{status} category: {data['name']}")

if __name__ == '__main__':
    setup_categories()
