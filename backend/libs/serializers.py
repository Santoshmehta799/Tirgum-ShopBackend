from rest_framework import serializers

from .models import PayUAuth


class PayUAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayUAuth
        fields = "__all__"
