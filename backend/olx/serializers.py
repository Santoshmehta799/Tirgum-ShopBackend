from rest_framework import serializers
from tyreadderapp.models import Product, Pair


class OLXAdvertSerializer(serializers.Serializer):
    code = serializers.CharField(allow_null=True, required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter())


class OLXAdvertPairSerializer(serializers.Serializer):
    code = serializers.CharField(allow_null=True, required=False)
    pair = serializers.PrimaryKeyRelatedField(queryset=Pair.objects.filter())