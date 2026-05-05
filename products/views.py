from django.http import JsonResponse
from rest_framework import viewsets, generics, filters, views, permissions, pagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ShadowOrderLog, HeroSlide
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

class CreateOrderLogView(generics.CreateAPIView):
    """Endpoint to log when someone clicks the WhatsApp button"""
    queryset = ShadowOrderLog.objects.all()
    serializer_class = ShadowOrderLogSerializer

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        from orders.models import Order
        from .models import VisitorLog
        
        # Count unique IPs across all time for a "Total Unique Visitors" metric
        total_unique_visitors = VisitorLog.objects.values('ip_address').distinct().count()
        
        return Response({
            'product_count': Product.objects.count(),
            'category_count': Category.objects.count(),
            'whatsapp_clicks': Order.objects.count(),
            'total_visitors': total_unique_visitors,
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
