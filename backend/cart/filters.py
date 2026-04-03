import django_filters
from cart.models import Cart


class CartFilter(django_filters.FilterSet):

    class Meta:
        model = Cart
        fields = "__all__"
