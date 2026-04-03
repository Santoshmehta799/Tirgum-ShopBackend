"""
URL configuration for backend project. 

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from otomoto import views as otomoto_views

urlpatterns = [

    path('admin/', admin.site.urls),
    path("tyreadderapp/", include("tyreadderapp.urls")),
    path("api/tyreadderapp/", include("tyreadderapp.api.urls")),
    path("api/carts/", include("cart.urls")),
    path("api/users/", include("users.api.urls")),
    path("users/", include("users.urls")),
    path('olx/', include('olx.urls', namespace='olx')),
    path("api/orders/", include("orders.api.urls")),
    path("allegro/",include("allegro.urls")),
    path("api/libs/", include("libs.urls")),
    path('orders/', include('orders.urls')),
    path('wishlist/',include('wishlist.urls')),
    
    path('otomoto/', include('otomoto.urls', namespace='otomoto')),
    

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns += [
    # YOUR PATTERNS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns += [
#     path("otomoto/authorize", otomoto_views.otomoto_authorize, name="otomoto_authorize"),
#     path("otomoto/callback", otomoto_views.otomoto_callback, name="otomoto_callback"),
# ]