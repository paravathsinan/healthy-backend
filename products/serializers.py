from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import Category, Product, ProductVariant, ProductImage, ShadowOrderLog, HeroSlide
from .utils import upload_image_to_cloudinary

class HeroSlideSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField() # Accept Base64 or URL

    class Meta:
        model = HeroSlide
        fields = '__all__'

    def create(self, validated_data):
        image_url = validated_data.get('image_url')
        if image_url:
            validated_data['image_url'] = upload_image_to_cloudinary(image_url, folder="dates_nuts/hero")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_url = validated_data.get('image_url')
        if image_url:
            validated_data['image_url'] = upload_image_to_cloudinary(image_url, folder="dates_nuts/hero")
        return super().update(instance, validated_data)


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    image_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url', 'display_order', 'products_count', 'prefix']

    def create(self, validated_data):
        image_url = validated_data.get('image_url')
        if image_url:
            validated_data['image_url'] = upload_image_to_cloudinary(image_url, folder="dates_nuts/categories")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_url = validated_data.get('image_url')
        if image_url:
            validated_data['image_url'] = upload_image_to_cloudinary(image_url, folder="dates_nuts/categories")
        return super().update(instance, validated_data)


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
    """Optimized minimal serializer for the grid view (Home/Category pages)"""
    primary_image = serializers.SerializerMethodField()
    cheapest_variant_price = serializers.SerializerMethodField()
    on_sale = serializers.SerializerMethodField()
    category_name = serializers.ReadOnlyField(source='category.name')
    category_slug = serializers.ReadOnlyField(source='category.slug')
    variants = ProductVariantSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'primary_image', 'cheapest_variant_price', 'on_sale',
            'is_featured', 'is_best_seller', 'is_new_arrival', 'category_name', 'category_slug',
            'is_sold_out', 'is_hidden', 'badge_text', 'tags', 'variants', 'updated_at'
        ]

    def _get_thumbnail(self, url):
        if not url: return None
        # Optimization: If Cloudinary, return a optimized thumbnail instead of full res
        if 'res.cloudinary.com' in url:
            # Injecting thumbnail parameters (c_thumb, w_400)
            return url.replace('/upload/', '/upload/c_thumb,w_400,q_auto,f_auto/')
        return url

    def get_primary_image(self, obj):
        # Optimized to use prefetched images
        images = getattr(obj, 'images', None)
        url = None
        if images is not None:
            # If prefetched, find in memory
            for img in obj.images.all():
                if img.is_primary:
                    url = img.image_url
                    break
            if not url:
                first = obj.images.all().first()
                url = first.image_url if first else None
        else:
            # Fallback to query if not prefetched
            img = obj.images.filter(is_primary=True).first()
            url = img.image_url if img else None
            
        return self._get_thumbnail(url)

    def get_cheapest_variant_price(self, obj):
        # Optimized to use prefetched variants
        variants = getattr(obj, 'variants', None)
        if variants is not None:
            v_list = list(obj.variants.all())
            if v_list:
                return min(v.price for v in v_list)
        
        # Fallback to query
        variant = obj.variants.order_by('price').first()
        return variant.price if variant else None

    def get_on_sale(self, obj):
        # Optimized to use prefetched variants
        variants = getattr(obj, 'variants', None)
        if variants is not None:
            return any(v.discount_price is not None for v in obj.variants.all())
        
        # Fallback to query
        return obj.variants.filter(discount_price__isnull=False).exists()




class AdminProductListSerializer(serializers.ModelSerializer):
    """Serializer for Admin Dashboard product table"""
    primary_image = serializers.SerializerMethodField()
    admin_price = serializers.ReadOnlyField(source='base_price')
    admin_discount_price = serializers.ReadOnlyField(source='base_discount_price')
    admin_weight = serializers.SerializerMethodField()
    cheapest_variant_price = serializers.SerializerMethodField()
    category_name = serializers.ReadOnlyField(source='category.name')
    category_slug = serializers.ReadOnlyField(source='category.slug')

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'slug', 'primary_image', 'admin_price', 'admin_discount_price', 'admin_weight',
            'base_price', 'base_discount_price', 'cheapest_variant_price',
            'is_featured', 'is_best_seller', 'is_new_arrival', 'category', 'category_name', 'category_slug',
            'is_sold_out', 'is_hidden', 'variants', 'updated_at'
        ]

    def get_cheapest_variant_price(self, obj):
        # Use prefetched variants if available
        variants = getattr(obj, 'variants', None)
        if variants is not None:
            v_list = list(obj.variants.all())
            if v_list:
                return min(v.price for v in v_list)
        
        variant = obj.variants.order_by('price').first()
        return variant.price if variant else None

    def _get_admin_variant(self, obj):
        # Optimization: Use prefetched variants
        variants = getattr(obj, 'variants', None)
        if variants is not None:
            v_list = list(obj.variants.all())
            # Find 1000G
            for v in v_list:
                if '1000' in v.weight: return v
            # Find Unit
            for v in v_list:
                if 'unit' in v.weight.lower(): return v
            # Cheapest
            if v_list: return min(v_list, key=lambda x: x.price)
            return None
            
        variant = obj.variants.filter(weight__icontains='1000').first()
        if not variant:
            variant = obj.variants.filter(weight__icontains='unit').first()
        if not variant:
            variant = obj.variants.order_by('price').first()
        return variant

    def get_primary_image(self, obj):
        images = getattr(obj, 'images', None)
        if images is not None:
            for img in obj.images.all():
                if img.is_primary: return img.image_url
            first = obj.images.all().first()
            return first.image_url if first else None
        
        img = obj.images.filter(is_primary=True).first()
        return img.image_url if img else None

    def get_admin_price(self, obj):
        return obj.base_price

    def get_admin_discount_price(self, obj):
        return obj.base_discount_price

    def get_admin_weight(self, obj):
        variant = self._get_admin_variant(obj)
        return variant.weight if variant else None

class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for the Product Detail Page (PDP) and Admin CRUD"""
    images = ProductImageSerializer(many=True, required=False)
    variants = ProductVariantSerializer(many=True, required=False)
    category_name = serializers.ReadOnlyField(source='category.name')
    admin_price = serializers.ReadOnlyField(source='base_price')
    admin_discount_price = serializers.ReadOnlyField(source='base_discount_price')
    admin_weight = serializers.SerializerMethodField()
    
    # Write-only fields for simpler CRUD
    image_url = serializers.CharField(write_only=True, required=False)
    gallery_images = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'slug', 'description', 'category', 
            'category_name', 'images', 'variants', 
            'is_featured', 'is_best_seller', 'is_new_arrival', 'admin_price', 'admin_discount_price', 'admin_weight',
            'base_price', 'base_discount_price', 'image_url', 'gallery_images', 'is_sold_out', 'is_hidden', 'badge_text', 'tags', 'updated_at'
        ]

    def _get_admin_variant(self, obj):
        variant = obj.variants.filter(weight__icontains='1000').first()
        if not variant:
            variant = obj.variants.filter(weight__icontains='unit').first()
        if not variant:
            variant = obj.variants.order_by('price').first()
        return variant

    def get_admin_price(self, obj):
        return obj.base_price

    def get_admin_discount_price(self, obj):
        return obj.base_discount_price

    def get_admin_weight(self, obj):
        variant = self._get_admin_variant(obj)
        return variant.weight if variant else None

    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        image_url = validated_data.pop('image_url', None)
        gallery_images = validated_data.pop('gallery_images', [])
        
        # Keep base prices in validated_data so they are saved to the Product model
        base_price = validated_data.get('base_price')
        base_discount_price = validated_data.get('base_discount_price')

        # Upload images to Cloudinary if they are Base64
        if image_url:
            image_url = upload_image_to_cloudinary(image_url)
            
        if gallery_images:
            uploaded_gallery = []
            for img in gallery_images:
                uploaded_url = upload_image_to_cloudinary(img)
                if uploaded_url:
                    uploaded_gallery.append(uploaded_url)
            gallery_images = uploaded_gallery

        # Create the product with base_price and base_discount_price
        product = Product.objects.create(**validated_data)
        
        # Handle variant creation from base_price
        if base_price:
            bp = Decimal(str(base_price))
            bdp = Decimal(str(base_discount_price)) if base_discount_price else None
            
            # Determine if it's a unit-based product (Chocolates, Gifts, etc.)
            is_unit = any(x in product.name.lower() for x in ['chocolate', 'gift', 'box', 'pack', 'jar', 'unit', 'hamper'])
            
            if is_unit:
                # Create 1 Unit variant
                ProductVariant.objects.create(
                    product=product, weight='1 Unit', 
                    price=bp, 
                    discount_price=bdp,
                    stock_count=100
                )
            else:
                # Default to weighted variants for Dates/Nuts
                # 1000G
                ProductVariant.objects.create(
                    product=product, weight='1000 G', 
                    price=bp, 
                    discount_price=bdp,
                    stock_count=100
                )
                # 500G (50%)
                ProductVariant.objects.create(
                    product=product, weight='500 G', 
                    price=(bp * Decimal('0.50')).quantize(Decimal('0.01')), 
                    discount_price=(bdp * Decimal('0.50')).quantize(Decimal('0.01')) if bdp else None,
                    stock_count=100
                )
                # 250G (25%)
                ProductVariant.objects.create(
                    product=product, weight='250 G', 
                    price=(bp * Decimal('0.25')).quantize(Decimal('0.01')), 
                    discount_price=(bdp * Decimal('0.25')).quantize(Decimal('0.01')) if bdp else None,
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
        image_url = validated_data.pop('image_url', None)
        gallery_images = validated_data.pop('gallery_images', None)
        
        # Keep base prices in validated_data so they are saved to the model
        base_price = validated_data.get('base_price')
        base_discount_price = validated_data.get('base_discount_price')

        # Upload images to Cloudinary if they are Base64
        if image_url:
            image_url = upload_image_to_cloudinary(image_url)
        
        if gallery_images:
            uploaded_gallery = []
            for img in gallery_images:
                uploaded_url = upload_image_to_cloudinary(img)
                if uploaded_url:
                    uploaded_gallery.append(uploaded_url)
            gallery_images = uploaded_gallery

        # Update model fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update variants only if a valid base_price is provided
        if base_price:
            bp = Decimal(str(base_price))
            bdp = Decimal(str(base_discount_price)) if base_discount_price else None
            
            instance.variants.all().delete()
            
            is_unit = any(x in instance.name.lower() for x in ['chocolate', 'gift', 'box', 'pack', 'jar', 'unit', 'hamper'])
            
            if is_unit:
                ProductVariant.objects.create(
                    product=instance, weight='1 Unit', 
                    price=bp, 
                    discount_price=bdp,
                    stock_count=100
                )
            else:
                # 1000G
                ProductVariant.objects.create(
                    product=instance, weight='1000 G', 
                    price=bp, 
                    discount_price=bdp,
                    stock_count=100
                )
                # 500G (50%)
                ProductVariant.objects.create(
                    product=instance, weight='500 G', 
                    price=(bp * Decimal('0.50')).quantize(Decimal('0.01')), 
                    discount_price=(bdp * Decimal('0.50')).quantize(Decimal('0.01')) if bdp else None,
                    stock_count=100
                )
                # 250G (25%)
                ProductVariant.objects.create(
                    product=instance, weight='250 G', 
                    price=(bp * Decimal('0.25')).quantize(Decimal('0.01')), 
                    discount_price=(bdp * Decimal('0.25')).quantize(Decimal('0.01')) if bdp else None,
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
