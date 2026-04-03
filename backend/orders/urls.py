from django.urls import path, include
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/<uuid:cart_id>/', views.create_order_from_cart),
    path('<int:order_id>/confirm', views.order_confirmation),

    path('refund/<str:order_id>/', views.payu_refund_form, name='payu_refund_form'),
    path('refund/processss', views.process_refund, name='process_refund'),
]
