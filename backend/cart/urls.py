from django.urls import path, include
from cart.views import CartViewSet, RemoveItemCart, SuperuserCartViewSet, RemovePairItemFromCart
from rest_framework import routers

route = routers.DefaultRouter()
route.register("", CartViewSet, basename="CartViewSet"),
route.register('superuser-cart', SuperuserCartViewSet, basename='superuser-cart')

urlpatterns = [
    # path('<int:cart_id>/item/', RemoveItemCart.as_view()),
    path('<int:cart_id>/item/<int:cart_item_id>/', RemoveItemCart.as_view()),
    path('remove/pair-items/<int:pair_id>/', RemovePairItemFromCart.as_view()),
    path("", include(route.urls)),
    

]
