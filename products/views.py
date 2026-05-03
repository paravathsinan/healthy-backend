from rest_framework import viewsets, generics, filters, views, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ShadowOrderLog, HeroSlide
from .serializers import (
    CategorySerializer, 
    ProductListSerializer, 
    ProductDetailSerializer, 
    ShadowOrderLogSerializer,
    HeroSlideSerializer
)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ping(request):
    return Response({"status": "ok", "message": "Pong!"})

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

class HeroSlideViewSet(viewsets.ModelViewSet):

    queryset = HeroSlide.objects.all()
    serializer_class = HeroSlideSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category__slug', 'is_featured', 'is_best_seller', 'is_new_arrival']
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = Product.objects.all().prefetch_related('images', 'variants')
        
        # If user is not an admin, only show non-hidden products
        if not (self.request.user and (self.request.user.is_staff or self.request.user.is_superuser)):
            queryset = queryset.filter(is_hidden=False)
            
        return queryset

    def get_serializer_class(self):
        # Return detail serializer for single product, list for multiple
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ProductDetailSerializer
        return ProductListSerializer

class CreateOrderLogView(generics.CreateAPIView):
    """Endpoint to log when someone clicks the WhatsApp button"""
    queryset = ShadowOrderLog.objects.all()
    serializer_class = ShadowOrderLogSerializer

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):

        from orders.models import Order
        return Response({
            'product_count': Product.objects.count(),
            'category_count': Category.objects.count(),
            'whatsapp_clicks': Order.objects.count(),
            'active_visitors': 1, # Minimal realistic value
        })
