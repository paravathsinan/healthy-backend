import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import HeroSlide

def seed_hero():
    slides = [
        {
            'title': "Nature's Finest Selection",
            'subtitle': "From the heart of the world's best groves, premium organic quality.",
            'image_url': '/images/hero/hero-1.png',
            'button_text': 'Explore Now',
            'button_link': '/products',
            'display_order': 1
        },
        {
            'title': "Premium Roasted Nuts",
            'subtitle': "Hand-picked almonds and cashews, roasted to perfection.",
            'image_url': '/images/hero/hero-2.png',
            'button_text': 'Explore Nuts',
            'button_link': '/category/nuts',
            'display_order': 2
        },
        {
            'title': "Luxury Gift Boxes",
            'subtitle': "Thoughtful assortments for every special occasion.",
            'image_url': '/images/hero/hero-3.png',
            'button_text': 'View Gifts',
            'button_link': '/category/gifting',
            'display_order': 3
        }
    ]

    for slide_data in slides:
        slide, created = HeroSlide.objects.get_or_create(
            title=slide_data['title'],
            defaults=slide_data
        )
        if created:
            print(f"Created slide: {slide.title}")
        else:
            print(f"Slide already exists: {slide.title}")

if __name__ == '__main__':
    seed_hero()
