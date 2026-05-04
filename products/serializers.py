from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
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
        request = self.context.get('request')
        if request and (request.user and (request.user.is_staff or request.user.is_superuser)):
            return obj.products.count()
        return obj.products.filter(is_hidden=False).count()

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
    admin_price = serializers.SerializerMethodField()
    admin_weight = serializers.SerializerMethodField()
    category_name = serializers.ReadOnlyField(source='category.name')
    category_slug = serializers.ReadOnlyField(source='category.slug')
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'slug', 'primary_image', 'admin_price', 'admin_weight',
            'is_featured', 'is_best_seller', 'is_new_arrival', 'category', 'category_name', 'category_slug',
            'is_sold_out', 'is_hidden', 'badge_text', 'variants', 'images', 'updated_at'
        ]



    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first()
        return img.image_url if img else None

    def _get_admin_variant(self, obj):
        # Try to find 1000 G variant first
        variant = obj.variants.filter(weight__icontains='1000').first()
        if not variant:
            # Fallback to Unit variant
            variant = obj.variants.filter(weight__icontains='unit').first()
        if not variant:
            # Final fallback to cheapest
            variant = obj.variants.order_by('price').first()
        return variant

    def get_admin_price(self, obj):
        variant = self._get_admin_variant(obj)
        return variant.price if variant else None

    def get_admin_weight(self, obj):
        variant = self._get_admin_variant(obj)
        return variant.weight if variant else None

class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for the Product Detail Page (PDP) and Admin CRUD"""
    images = ProductImageSerializer(many=True, required=False)
    variants = ProductVariantSerializer(many=True, required=False)
    category_name = serializers.ReadOnlyField(source='category.name')
    admin_price = serializers.SerializerMethodField()
    admin_weight = serializers.SerializerMethodField()
    
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
            'is_featured', 'is_best_seller', 'is_new_arrival', 'admin_price', 'admin_weight',
            'base_price', 'base_discount_price', 'image_url', 'gallery_images', 'is_sold_out', 'is_hidden', 'badge_text', 'updated_at'
        ]

    def _get_admin_variant(self, obj):
        variant = obj.variants.filter(weight__icontains='1000').first()
        if not variant:
            variant = obj.variants.filter(weight__icontains='unit').first()
        if not variant:
            variant = obj.variants.order_by('price').first()
        return variant

    def get_admin_price(self, obj):
        variant = self._get_admin_variant(obj)
        return variant.price if variant else None

    def get_admin_weight(self, obj):
        variant = self._get_admin_variant(obj)
        return variant.weight if variant else None

    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        base_price = validated_data.pop('base_price', None)
        base_discount_price = validated_data.pop('base_discount_price', None)
        image_url = validated_data.pop('image_url', None)
        gallery_images = validated_data.pop('gallery_images', [])

        product = Product.objects.create(**validated_data)
        
        if base_price:
            bp = Decimal(str(base_price))
            bdp = Decimal(str(base_discount_price)) if base_discount_price else None
            
            # 1000G
            ProductVariant.objects.create(
                product=product, weight='1000 G', 
                price=bp, 
                discount_price=bdp,
                stock_count=100
            )
            # 500G
            ProductVariant.objects.create(
                product=product, weight='500 G', 
                price=(bp * Decimal('0.55')).quantize(Decimal('0.01')), 
                discount_price=(bdp * Decimal('0.55')).quantize(Decimal('0.01')) if bdp else None,
                stock_count=100
            )
            # 250G
            ProductVariant.objects.create(
                product=product, weight='250 G', 
                price=(bp * Decimal('0.30')).quantize(Decimal('0.01')), 
                discount_price=(bdp * Decimal('0.30')).quantize(Decimal('0.01')) if bdp else None,
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

    @transaction.atomic
    def update(self, instance, validated_data):
        base_price = validated_data.pop('base_price', None)
        base_discount_price = validated_data.pop('base_discount_price', None)
        image_url = validated_data.pop('image_url', None)
        gallery_images = validated_data.pop('gallery_images', None)
        
        # Update model fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update variants only if a valid base_price is provided
        if base_price:
            bp = Decimal(str(base_price))
            bdp = Decimal(str(base_discount_price)) if base_discount_price else None
            
            instance.variants.all().delete()
            # 1000G
            ProductVariant.objects.create(
                product=instance, weight='1000 G', 
                price=bp, 
                discount_price=bdp,
                stock_count=100
            )
            # 500G
            ProductVariant.objects.create(
                product=instance, weight='500 G', 
                price=(bp * Decimal('0.55')).quantize(Decimal('0.01')), 
                discount_price=(bdp * Decimal('0.55')).quantize(Decimal('0.01')) if bdp else None,
                stock_count=100
            )
            # 250G
            ProductVariant.objects.create(
                product=instance, weight='250 G', 
                price=(bp * Decimal('0.30')).quantize(Decimal('0.01')), 
                discount_price=(bdp * Decimal('0.30')).quantize(Decimal('0.01')) if bdp else None,
                stock_count=100
            )
            
        # Update images only if image_url or non-empty gallery provided
        if image_url or (gallery_images is not None and len(gallery_images) > 0):
            instance.images.all().delete()
            if image_url:
                ProductImage.objects.create(product=instance, image_url=image_url, is_primary=True)
            if gallery_images:
                for img in gallery_images:
                    ProductImage.objects.create(product=instance, image_url=img, is_primary=False)

        return instance

class ShadowOrderLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShadowOrderLog
        fields = '__all__'
