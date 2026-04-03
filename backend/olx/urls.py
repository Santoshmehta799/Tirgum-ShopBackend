
from olx import views
from django.urls import path
from rest_framework import routers
from django.urls import path, include
# from olx.views import OLXAdvertViewSet, OLXAdvertPairViewSet

app_name = 'olx'

# route = routers.DefaultRouter()
# route.register("adverts", OLXAdvertViewSet, basename="OLXAdvertViewSet")
# route.register("pairadverts", OLXAdvertPairViewSet, basename="OLXAdvertPairViewSet")

urlpatterns = [
    # path("", include(route.urls)),
    path("updaterefreshtoken/", views.update_refresh_token, name="update_refresh_token"),
    # path("olx-product-update", views.product_update_with_olx_token, name="olx-product-update"),
    path("olx-product-update", views.product_update_with_olx_token, name="olx-product-update"),
    # OLX
    path('select/bulk-product-olx', views.selected_bulk_olx_product, name="bulk-product-olx"),
    path("dashboard", views.olx_dashboard, name="olx-dashboard"),
    path('refresh-olx-product/<int:product_id>/', views.refresh_olx_product, name='refresh_olx_product'),
]