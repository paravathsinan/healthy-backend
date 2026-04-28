from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductImage, ShadowOrderLog, HeroSlide

class HeroSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSlide
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url', 'display_order', 'products_count', 'prefix']


    def get_products_count(self, obj):
        return obj.products.count()

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image_url', 'is_primary']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'weight', 'price', 'discount_price', 'stock_count']

class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for the grid view (Home/Category pages)"""
    primary_image = serializers.SerializerMethodField()
    cheapest_variant_price = serializers.SerializerMethodField()
    category_name = serializers.ReadOnlyField(source='category.name')
    category_slug = serializers.ReadOnlyField(source='category.slug')
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'slug', 'primary_image', 'cheapest_variant_price', 
            'is_featured', 'is_best_seller', 'is_new_arrival', 'category', 'category_name', 'category_slug',
            'is_sold_out', 'badge_text', 'variants', 'images'
        ]



    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first()
        return img.image_url if img else None

    def get_cheapest_variant_price(self, obj):
        variant = obj.variants.order_by('price').first()
        return variant.price if variant else None

class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for the Product Detail Page (PDP) and Admin CRUD"""
    images = ProductImageSerializer(many=True, required=False)
    variants = ProductVariantSerializer(many=True, required=False)
    category_name = serializers.ReadOnlyField(source='category.name')
    cheapest_variant_price = serializers.SerializerMethodField()
    
    # Write-only fields for simpler CRUD
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
    base_discount_price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False, allow_null=True)
    image_url = serializers.CharField(write_only=True, required=False)
    gallery_images = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'slug', 'description', 'category', 
            'category_name', 'images', 'variants', 
            'is_featured', 'is_best_seller', 'is_new_arrival', 'cheapest_variant_price',
            'base_price', 'base_discount_price', 'image_url', 'gallery_images', 'is_sold_out', 'badge_text'
        ]

        extra_kwargs = {
            'slug': {'required': False}
        }

    def get_cheapest_variant_price(self, obj):
        variant = obj.variants.order_by('price').first()
        return variant.price if variant else None

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        base_price = validated_data.pop('base_price', None)
        base_discount_price = validated_data.pop('base_discount_price', None)
        image_url = validated_data.pop('image_url', None)
        gallery_images = validated_data.pop('gallery_images', [])

        product = Product.objects.create(**validated_data)
        
        if base_price:
            from decimal import Decimal
            # Auto-create the 3 standard weights if base_price is given
            # 1000G
            ProductVariant.objects.create(
                product=product, weight='1000 G', 
                price=base_price, 
                discount_price=base_discount_price,
                stock_count=100
            )
            # 500G (55% of 1kg price)
            ProductVariant.objects.create(
                product=product, weight='500 G', 
                price=base_price * Decimal('0.55'), 
                discount_price=base_discount_price * Decimal('0.55') if base_discount_price else None,
                stock_count=100
            )
            # 250G (30% of 1kg price)
            ProductVariant.objects.create(
                product=product, weight='250 G', 
                price=base_price * Decimal('0.30'), 
                discount_price=base_discount_price * Decimal('0.30') if base_discount_price else None,
                stock_count=100
            )
        elif variants_data:
            for variant_data in variants_data:
                ProductVariant.objects.create(product=product, **variant_data)
        
        if image_url:
            ProductImage.objects.create(product=product, image_url=image_url, is_primary=True)
            
        if gallery_images:
            for img in gallery_images:
                ProductImage.objects.create(product=product, image_url=img, is_primary=False)
        elif images_data:
            for image_data in images_data:
                ProductImage.objects.create(product=product, **image_data)
            
        return product

    def update(self, instance, validated_data):
        base_price = validated_data.pop('base_price', None)
        base_discount_price = validated_data.pop('base_discount_price', None)
        image_url = validated_data.pop('image_url', None)
        gallery_images = validated_data.pop('gallery_images', None)
        
        # Update variants if base_price sent
        if base_price:
            from decimal import Decimal
            instance.variants.all().delete()
            # 1000G
            ProductVariant.objects.create(
                product=instance, weight='1000 G', 
                price=base_price, 
                discount_price=base_discount_price,
                stock_count=100
            )
            # 500G
            ProductVariant.objects.create(
                product=instance, weight='500 G', 
                price=base_price * Decimal('0.55'), 
                discount_price=base_discount_price * Decimal('0.55') if base_discount_price else None,
                stock_count=100
            )
            # 250G
            ProductVariant.objects.create(
                product=instance, weight='250 G', 
                price=base_price * Decimal('0.30'), 
                discount_price=base_discount_price * Decimal('0.30') if base_discount_price else None,
                stock_count=100
            )
            
        # Update images if image_url or gallery_images sent
        if image_url is not None or gallery_images is not None:
            instance.images.all().delete()
            if image_url:
                ProductImage.objects.create(product=instance, image_url=image_url, is_primary=True)
            if gallery_images:
                for img in gallery_images:
                    ProductImage.objects.create(product=instance, image_url=img, is_primary=False)

        return super().update(instance, validated_data)

class ShadowOrderLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShadowOrderLog
        fields = '__all__'
