import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product

def check_product():
    try:
        p = Product.objects.get(id=4)
        print(f"--- DATABASE STATUS FOR '{p.name}' ---")
        print(f"ID: {p.id}")
        print(f"SKU: {p.sku}")
        print(f"Category ID: {p.category_id}")
        print(f"Category Name: {p.category.name if p.category else 'None'}")
        print(f"Price: {p.variants.first().price if p.variants.exists() else 'No Variants'}")
        print("-----------------------------------")
    except Exception as e:
        print(f"Error checking product: {e}")

if __name__ == "__main__":
    check_product()
