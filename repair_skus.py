import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product, Category

def repair_skus():
    print("Starting SKU repair...")
    products = Product.objects.all()
    for p in products:
        if not p.sku:
            print(f"Product '{p.name}' (ID: {p.id}) is missing a SKU. Generating one...")
            # Trigger the save logic to generate SKU
            try:
                p.save()
                print(f"Successfully generated SKU '{p.sku}' for '{p.name}'")
            except Exception as e:
                print(f"Failed to generate SKU for '{p.name}': {e}")
                # Manual fallback if save() fails due to unique constraint
                if "UNIQUE constraint failed" in str(e):
                    print("Attempting manual SKU generation...")
                    p_prefix = "P"
                    if p.category:
                        p_prefix = p.category.prefix or p.category.name[0].upper()
                    
                    count = 1
                    while Product.objects.filter(sku=f"{p_prefix}{count}").exists():
                        count += 1
                    p.sku = f"{p_prefix}{count}"
                    p.save()
                    print(f"Manually assigned SKU '{p.sku}' to '{p.name}'")

    print("SKU repair complete.")

if __name__ == "__main__":
    repair_skus()
