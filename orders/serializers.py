from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product, ProductVariant

from django.db import transaction
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False, allow_null=True)
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), required=False, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'variant', 'product_name', 'variant_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_phone', 
            'customer_address', 'total_amount', 'status', 'created_at', 
            'confirmed_at', 'processed_at', 'shipped_at', 'delivered_at',
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)
            return order
