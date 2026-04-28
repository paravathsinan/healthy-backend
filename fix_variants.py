import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product, ProductVariant
from decimal import Decimal

def fix_products():
    products_fixed = 0
    for p in Product.objects.all():
        standard = p.variants.filter(weight='Standard').first()
        if standard:
            price = standard.price
            standard.delete()
            ProductVariant.objects.create(product=p, weight='250 G', price=price * Decimal('0.30'), stock_count=100)
            ProductVariant.objects.create(product=p, weight='500 G', price=price * Decimal('0.55'), stock_count=100)
            ProductVariant.objects.create(product=p, weight='1000 G', price=price, stock_count=100)
            products_fixed += 1
            print(f'Fixed {p.name}')
    
    print(f'Total products fixed: {products_fixed}')

if __name__ == '__main__':
    fix_products()
