from django.urls import path, include
from tyreadderapp.api.views import AdvanceFilterViewSet, SelectedProductFilterDetailView, SelectedProductFilterListCreateView, SimilarProductAPIView, TreadNameViewSet, TyreClassIdView, TyreNameView, TyreSearchView, product_list, \
    tread_char, ProductViewSet, SizeViewSet, BrandViewSet, TreadViewSet, PairViewSet, new_tread_depth
from tyreadderapp.views import PalletesAPIView, SizeDetailApiView, SummarizeTyreSizeAPIView, CartSummaryAPIView, ApplyDiscountsAPIView, \
    GetTransportationPalletAPIView, TyreSizeListAPIView
from rest_framework import routers
from .. import views as pallete_views
from olx.views import OLXAdvertViewSet, OLXAdvertPairViewSet

route = routers.DefaultRouter()
route.register("products", ProductViewSet, basename="ProductViewSet")
route.register("advance_filter", AdvanceFilterViewSet, basename="AdvanceFilterViewSet")
route.register("treads", TreadViewSet, basename="TreadViewSet")
route.register("treads_list_name_id", TreadNameViewSet, basename="TreadNameViewSet")
route.register("sizes", SizeViewSet, basename="SizeViewSet")
route.register("brands", BrandViewSet, basename="BrandViewSet")
route.register("pairs", PairViewSet, basename="PairViewSet")
route.register("tyre_search", TyreSearchView, basename="TyreSearchView")
route.register("tread_name", TyreNameView, basename="TyreNameView")
route.register("tyre_class_or_id", TyreClassIdView, basename="TyreClassIdView")

route.register("olx-adverts", OLXAdvertViewSet, basename="OLXAdvertViewSet")
route.register("olx-pairadverts", OLXAdvertPairViewSet, basename="OLXAdvertPairViewSet")


urlpatterns = [
    path('similar-products/<int:product_id>/', SimilarProductAPIView.as_view(), name='similar-products'),
    
    path('api/', product_list, name ='api' ),
    path('tread_char/', tread_char, name ='tread_char' ),
    path('new_tread_depth/', new_tread_depth, name ='new_tread_depth' ),
    path("", include(route.urls)),

    path('palletes', PalletesAPIView.as_view(), name='palette-list-create'),
    path('palletes/<int:pk>', PalletesAPIView.as_view(), name='palette-detail'),

    path('palletes', pallete_views.PalletesAPIView.as_view(), name='palette-list-create'),
    path('palletes/<int:pk>', pallete_views.PalletesAPIView.as_view(), name='palette-detail'),

    path('cart/summarize-tyre-sizes/<int:cart_id>', pallete_views.SummarizeTyreSizeAPIView.as_view(),
         name='summarize_tyre_sizes'),
    path('cart/cart-summary/<int:cart_id>', pallete_views.CartSummaryAPIView.as_view(), name='summarize_tyre_sizes'),
    path('cart/apply_discount/<int:cart_id>', pallete_views.ApplyDiscountsAPIView.as_view(), name='apply_discount'),
    path('cart/transportation-pallet/<int:cart_id>', pallete_views.GetTransportationPalletAPIView.as_view(),
         name='transportation_pallet'),

    path('tyre-sizes/', TyreSizeListAPIView.as_view(), name='tyre-size-list'),
    path('sizes/<slug:slug>/tyres', SizeDetailApiView.as_view(), name='size-detail-api'),

    # List all filters (GET) and Create new filter (POST)
    path('api/my-filters/', SelectedProductFilterListCreateView.as_view(), name='my-filters'),

    # Retrieve / Update / Delete a specific filter by id
    path('api/my-filters/<int:pk>/', SelectedProductFilterDetailView.as_view(), name='my-filter-detail'),
]
