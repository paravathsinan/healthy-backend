import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import ProductImage, Category, HeroSlide
from products.utils import upload_image_to_cloudinary

def migrate_images():
    print("Starting Image Migration to Cloudinary...")

    # 1. Migrate Product Images
    product_images = ProductImage.objects.filter(image_url__startswith='data:image')
    print(f"Found {product_images.count()} Product images in Base64.")
    for img in product_images:
        print(f"  Uploading Product Image ID {img.id}...")
        new_url = upload_image_to_cloudinary(img.image_url, folder="dates_nuts/products")
        if new_url and new_url.startswith('http'):
            img.image_url = new_url
            img.save()
            print(f"  Done: {new_url[:50]}...")

    # 2. Migrate Categories
    categories = Category.objects.filter(image_url__startswith='data:image')
    print(f"Found {categories.count()} Categories in Base64.")
    for cat in categories:
        print(f"  Uploading Category {cat.name}...")
        new_url = upload_image_to_cloudinary(cat.image_url, folder="dates_nuts/categories")
        if new_url and new_url.startswith('http'):
            cat.image_url = new_url
            cat.save()
            print(f"  Done.")

    # 3. Migrate Hero Slides
    hero_slides = HeroSlide.objects.filter(image_url__startswith='data:image')
    print(f"Found {hero_slides.count()} Hero Slides in Base64.")
    for slide in hero_slides:
        print(f"  Uploading Hero Slide {slide.title}...")
        new_url = upload_image_to_cloudinary(slide.image_url, folder="dates_nuts/hero")
        if new_url and new_url.startswith('http'):
            slide.image_url = new_url
            slide.save()
            print(f"  Done.")

    print("\nMigration Finished! All Base64 images are now hosted on Cloudinary.")

if __name__ == "__main__":
    migrate_images()
