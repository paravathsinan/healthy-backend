import os
from django.http import JsonResponse
from rest_framework import viewsets, generics, filters, views, permissions, pagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from django.db.models import Count, Q
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ShadowOrderLog, HeroSlide, BrowserVisitor
from .serializers import (
    CategorySerializer, 
    ProductListSerializer, 
    AdminProductListSerializer,
    ProductDetailSerializer, 
    ShadowOrderLogSerializer,
    HeroSlideSerializer
)

def ping(request):
    """
    Extremely lightweight endpoint for health checks/keeping service awake.
    Pure Django view to bypass DRF overhead.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    response = JsonResponse({"status": "ok", "message": "Pong!"})
    response["Cache-Control"] = "no-store"
    return response

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None and (user.is_staff or user.is_superuser):
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "message": "Login successful",
            "token": token.key,
            "user": {
                "username": user.username,
                "email": user.email
            }
        })
    else:
        return Response({"error": "Invalid credentials or unauthorized access"}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({"error": "Unauthorized access"}, status=403)
        
    return Response({
        "status": "valid",
        "user": {
            "username": request.user.username,
            "email": request.user.email
        }
    })

class ProductPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

class HeroSlideViewSet(viewsets.ModelViewSet):
    queryset = HeroSlide.objects.all()
    serializer_class = HeroSlideSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = HeroSlide.objects.all().order_by('display_order')
        if self.action == 'list':
            # Limit to 10 active slides for the public view
            return queryset.filter(is_active=True)[:10]
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        queryset = Category.objects.all().order_by('display_order')
        if self.action == 'list':
            # Limit to 20 categories for the list view to keep response light
            return queryset[:20]
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Returns the top 6 categories that have the most products added (and are not hidden).
        """
        queryset = Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_hidden=False))
        ).order_by('-product_count', 'display_order')[:6]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    lookup_field = 'slug'
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category__slug', 'is_featured', 'is_best_seller', 'is_new_arrival']
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = Product.objects.all().prefetch_related('images', 'variants').order_by('-created_at')
        
        # Optimize memory by not loading description for list views
        if self.action == 'list':
            queryset = queryset.defer('description')
            
        # If user is not an admin, only show non-hidden products
        if not (self.request.user and (self.request.user.is_staff or self.request.user.is_superuser)):
            queryset = queryset.filter(is_hidden=False)
            
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        # Return detail serializer for single product, list for multiple
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ProductDetailSerializer
        
        # If user is admin, use detailed list serializer
        if self.request.user and (self.request.user.is_staff or self.request.user.is_superuser):
            return AdminProductListSerializer
            
        return ProductListSerializer

    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """
        Returns all dynamic data needed to populate the storefront filter dropdowns:
        - Availability counts (in stock / out of stock)
        - Price range (min and max across all active variants)
        - Categories with their active product counts
        - Distinct variant weights with product counts
        """
        from django.db.models import Min, Max
        from .models import ProductVariant

        base_qs = Product.objects.filter(is_hidden=False)

        # --- Availability ---
        in_stock_count = base_qs.filter(is_sold_out=False).count()
        out_of_stock_count = base_qs.filter(is_sold_out=True).count()

        # --- Price range (from variants of visible products) ---
        price_agg = ProductVariant.objects.filter(
            product__is_hidden=False
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )

        # --- Categories with product counts ---
        categories = (
            Category.objects
            .annotate(product_count=Count('products', filter=Q(products__is_hidden=False)))
            .filter(product_count__gt=0)
            .order_by('display_order', 'name')
            .values('name', 'slug', 'product_count')
        )

        # --- Variant weights with distinct product counts ---
        weights = (
            ProductVariant.objects
            .filter(product__is_hidden=False)
            .values('weight')
            .annotate(product_count=Count('product', distinct=True))
            .order_by('weight')
        )

        return Response({
            'availability': {
                'in_stock': in_stock_count,
                'out_of_stock': out_of_stock_count,
            },
            'price': {
                'min': float(price_agg['min_price'] or 0),
                'max': float(price_agg['max_price'] or 0),
            },
            'categories': list(categories),
            'weights': list(weights),
        })

class CreateOrderLogView(generics.CreateAPIView):
    """Endpoint to log when someone clicks the WhatsApp button"""
    queryset = ShadowOrderLog.objects.all()
    serializer_class = ShadowOrderLogSerializer

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from orders.models import Order
        # Count unique browser UUIDs — one per device/browser (accurate)
        total_unique_visitors = BrowserVisitor.objects.count()

        return Response({
            'product_count': Product.objects.count(),
            'category_count': Category.objects.count(),
            'whatsapp_clicks': Order.objects.count(),
            'total_visitors': total_unique_visitors,
        })


class TrackVisitView(APIView):
    """
    Called once per browser/device when the storefront loads.
    The frontend generates a UUID and stores it in localStorage so it
    only calls this endpoint once per browser — no repeat counting.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import uuid as uuid_lib
        visitor_id_raw = request.data.get('visitor_id', '')

        if not visitor_id_raw:
            return Response({'error': 'visitor_id is required'}, status=400)

        try:
            visitor_id = uuid_lib.UUID(str(visitor_id_raw))
        except (ValueError, AttributeError):
            return Response({'error': 'Invalid visitor_id format'}, status=400)

        # get_or_create ensures we never double-count the same browser
        _, created = BrowserVisitor.objects.get_or_create(visitor_id=visitor_id)

        return Response({'tracked': created}, status=201 if created else 200)


class VisitorListView(APIView):
    """
    Returns a paginated list of unique browser visitors for the admin dashboard.
    Admin-only endpoint.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        offset = (page - 1) * page_size

        total = BrowserVisitor.objects.count()
        visitors = BrowserVisitor.objects.order_by('-first_seen')[offset:offset + page_size]

        data = [
            {
                'id': str(v.visitor_id)[:8] + '...',  # Short display ID
                'visitor_id': str(v.visitor_id),
                'first_seen': v.first_seen.isoformat(),
                'last_seen': v.last_seen.isoformat(),
            }
            for v in visitors
        ]

        return Response({
            'count': total,
            'results': data,
            'page': page,
            'total_pages': (total + page_size - 1) // page_size,
        })

class HomePageView(APIView):
    """
    Combined endpoint for storefront homepage to reduce multiple API calls.
    Returns hero slides, categories, and specific product collections.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(cache_page(10)) # Reduced to 10 seconds for faster updates
    def get(self, request):
        # 1. Hero Slides
        hero_slides = HeroSlide.objects.filter(is_active=True).order_by('display_order')
        
        # 2. Categories
        categories = Category.objects.all().order_by('display_order')
        
        # 3. Product Collections
        # We use ProductListSerializer with optimized queries
        base_queryset = Product.objects.filter(is_hidden=False).prefetch_related('images', 'variants').defer('description')
        
        featured_products = base_queryset.filter(is_featured=True)[:8]
        new_arrivals = base_queryset.filter(is_new_arrival=True)[:8]
        chocolate_products = base_queryset.filter(category__slug='chocolates')[:8]
        
        # Serialize data
        return Response({
            'hero': HeroSlideSerializer(hero_slides, many=True).data,
            'categories': CategorySerializer(categories, many=True, context={'request': request}).data,
            'featured': ProductListSerializer(featured_products, many=True).data,
            'new_arrivals': ProductListSerializer(new_arrivals, many=True).data,
            'chocolates': ProductListSerializer(chocolate_products, many=True).data,
        })


class CloudinarySignatureView(APIView):
    """
    Generates a short-lived Cloudinary upload signature for direct browser-to-Cloudinary uploads.
    Admin-only — keeps the API secret server-side at all times.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        import time
        import hashlib

        folder = request.query_params.get('folder', 'dates_nuts/products')
        timestamp = int(time.time())

        api_secret = os.getenv('CLOUDINARY_API_SECRET', '')
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME', '')
        api_key = os.getenv('CLOUDINARY_API_KEY', '')

        # Build the string-to-sign (params must be alphabetically sorted)
        params_to_sign = f"folder={folder}&timestamp={timestamp}"
        signature = hashlib.sha256(f"{params_to_sign}{api_secret}".encode()).hexdigest()

        return Response({
            'signature': signature,
            'timestamp': timestamp,
            'cloud_name': cloud_name,
            'api_key': api_key,
            'folder': folder,
        })
