from django.contrib import admin
from django.urls import path,include
from users import views
from django.contrib.auth.views import LoginView,LogoutView

# from rest_framework.routers import DefaultRouter

# from product import views

# router = DefaultRouter()
# router.register(r"brand",views.BrandViewSet)
# router.register(r"category",views.CategoryViewSet)
# router.register(r"tire",TireViewSet)

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('contact/', views.ContactUsAPIView.as_view(), name='contact-us')

]