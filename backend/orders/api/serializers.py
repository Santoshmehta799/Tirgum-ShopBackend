from orders.models import *
from rest_framework import serializers

class OrderInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInvoice
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    invoice = OrderInvoiceSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)

    class Meta:
        model = Order
        fields = '__all__'