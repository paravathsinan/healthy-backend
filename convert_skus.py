import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product, Category

def convert_to_professional_skus():
    print("Starting SKU conversion to HDN-PREFIX-000 format...")
    products = Product.objects.all()
    for p in products:
        p_prefix = "P"
        if p.category:
            p_prefix = p.category.prefix or p.category.name[0].upper()
        
        # Clear existing SKU to trigger fresh generation in save()
        # but we'll do it manually here to ensure the pattern is exact
        category_products = Product.objects.filter(category=p.category)
        
        # We need a unique number. Let's use the ID for existing ones to be perfectly safe
        # Or we can use the sequence. Let's use sequence for a cleaner look.
        
        count = 1
        new_sku = f"HDN-{p_prefix}-{count:03d}"
        
        # Check if this product already has the right format (maybe it was just created)
        if p.sku and p.sku.startswith("HDN-"):
            print(f"Skipping '{p.name}' - already has professional SKU: {p.sku}")
            continue

        while Product.objects.filter(sku=new_sku).exists():
            count += 1
            new_sku = f"HDN-{p_prefix}-{count:03d}"
        
        old_sku = p.sku
        p.sku = new_sku
        p.save()
        print(f"Converted '{p.name}': {old_sku} -> {p.sku}")

    print("SKU conversion complete.")

if __name__ == "__main__":
    convert_to_professional_skus()
