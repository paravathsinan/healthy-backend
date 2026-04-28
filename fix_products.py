import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product, ProductVariant, ProductImage

def fix_products():
    print("Starting product fix...")
    for p in Product.objects.all():
        # Fix missing variants
        if p.variants.count() == 0:
            ProductVariant.objects.create(
                product=p, 
                weight='Standard', 
                price=999, 
                stock_count=100
            )
            print(f"Added default variant to {p.name}")
        
        # Fix broken blob images
        for img in p.images.all():
            if img.image_url.startswith('blob:'):
                img.delete()
                print(f"Deleted broken blob image for {p.name}")
    print("Done!")

if __name__ == "__main__":
    fix_products()
