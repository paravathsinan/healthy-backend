from rest_framework import viewsets, status, pagination, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order
from .serializers import OrderSerializer
from .filters import OrderFilter

class OrderPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = OrderFilter
    search_fields = ['customer_name', 'customer_phone', 'id', 'items__product_name']
    
    def perform_create(self, serializer):
        return serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def track(self, request):
        order_id = request.query_params.get('order_id')
        phone = request.query_params.get('phone')
        
        if not order_id or not phone:
            return Response(
                {"error": "Order ID and Phone number are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Clean phone number (remove spaces etc)
        phone = phone.replace(' ', '').replace('-', '')
        
        # Search by order_number or ID
        order = None
        
        # Try finding by HDN order_number first
        order = Order.objects.filter(order_number=order_id, customer_phone__icontains=phone).first()
        
        # If not found, try ORD-X format
        if not order and order_id.startswith('ORD-'):
            try:
                pk = order_id.split('-')[1]
                order = Order.objects.filter(id=pk, customer_phone__icontains=phone).first()
            except (IndexError, ValueError):
                pass
        
        # If still not found, try raw ID
        if not order:
            try:
                order = Order.objects.filter(id=order_id, customer_phone__icontains=phone).first()
            except (ValueError, TypeError):
                pass
            
        if not order:
            return Response(
                {"error": "Order not found. Please check your Order ID or phone number."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = OrderSerializer(order)
        return Response(serializer.data)


