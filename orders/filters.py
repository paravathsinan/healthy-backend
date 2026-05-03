from django_filters import rest_framework as filters
from .models import Order

class OrderFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="total_amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="total_amount", lookup_expr='lte')
    start_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    status = filters.CharFilter(field_name="status", lookup_expr='exact')

    class Meta:
        model = Order
        fields = [] # Custom filters are already declared as attributes
