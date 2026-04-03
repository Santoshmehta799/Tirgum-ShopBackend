from rest_framework import serializers

from .models import Order, OrderItem, OrderPayment


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPayment
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = OrderPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('total_amount', 'shipping_amount', 'tax_fee', 'order_status', 'payment_status')
