from django.urls import path, include
from users.api.views import UserViewSet, CustomObtainAuthToken, PasswordReset, LogOut, PasswordResetRequestView, \
    PasswordResetConfirmView,NIPLookupView
from rest_framework import routers

route = routers.DefaultRouter()
route.register("", UserViewSet, basename="UserViewSet")

urlpatterns = [
    path('pass-reset/', PasswordReset.as_view()),
    path('logout/', LogOut.as_view()),
    path('login/', CustomObtainAuthToken.as_view()),

    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path("", include(route.urls)),
    
    # Get Nip Detail
    path('nip-lookup/<str:nip>/', NIPLookupView.as_view(), name='nip-lookup'),


]
