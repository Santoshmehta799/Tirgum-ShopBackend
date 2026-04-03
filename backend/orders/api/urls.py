from django.urls import path, include
from orders.api.views import *
from rest_framework import routers

route = routers.DefaultRouter()
route.register("invoice", InvoiceViewSet, basename="UserViewSet")

urlpatterns = [
    path('user-orders-details/', OrdersDetailsByUser.as_view()),
    path("", include(route.urls)),
]
