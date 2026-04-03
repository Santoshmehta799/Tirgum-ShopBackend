from os import access
from typing import Any
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404, redirect




from ..models import Product, SimilarTread, Tread_Character, Size, Brand, Tread, Pair, New_Tread_Depth, SelectedProductFilter
from .serializers import (
    AdvanceFilterProductSerializer,
    ProductSearchSerailizer,
    ProductSerializer,
    LiteProductSerializer,
    SimilarProductSerializer,
    Tread_CharacterSerializer,
    # OLXAdvertSerializer,
    SizeSerializer,
    BrandSerializer,
    TreadSerializer,
    PairSerializer,
    TreadNameIdSerializer,
    TyreClassSerializer,
    New_Tread_DepthSerializer,
    SelectedProductFilterSerializer,
    # OLXAdvertPairSerializer,
)
from ..filters import ProductFilter, BrandFilter
from rest_framework import viewsets, status
from olx.client import OlxClient
from rest_framework.validators import ValidationError
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import F, Count
from rest_framework import generics
from rest_framework import viewsets, filters
olx_client = OlxClient()


# class OLXAdvertViewSet(viewsets.ViewSet):

#     def access_token(self):
#         access_token = olx_client.get_access_token()
#         return access_token

#     def get_response(self, olx_response, expected_status_code=200):
#         response = olx_response
#         if response.status_code != 204:
#             json_response = response.json()
#             data = (
#                 json_response["data"]
#                 if response.status_code == expected_status_code
#                 else json_response.get("error")
#             )
#             status_code = (
#                 status.HTTP_200_OK
#                 if response.status_code == expected_status_code
#                 else status.HTTP_400_BAD_REQUEST
#             )
#         else:
#             data = {"success": True, "message": "Removed Successfully"}
#             status_code = status.HTTP_200_OK

#         return Response(data=data, status=status_code)

#     def create(self, request):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         serializer = OLXAdvertSerializer(data=request.data)
#         if serializer.is_valid():
#             product = serializer.validated_data["product"]
#             if product.is_olx == True:
#                 raise ValidationError("Adverts already in OLX.")

#             # olx_response = olx_client.add_advert(product, access_token)
#             olx_response = None
#             return self.get_response(olx_response)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def list(self, request):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         olx_response = olx_client.get_advert_list(access_token)
#         return self.get_response(olx_response)

#     def retrieve(self, request, pk=None):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         product = get_object_or_404(Product, id=pk)
#         olx_response = olx_client.get_advert_info(
#             product.olx_advert_id, access_token
#         )
#         return self.get_response(olx_response)

#     def update(self, request, pk=None):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         product = get_object_or_404(Product, id=pk)
#         olx_response = olx_client.get_advert_info(
#             product.olx_advert_id, access_token
#         )
#         return self.get_response(olx_response)

#     def destroy(self, request, pk=None):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         product = get_object_or_404(Product, id=pk)
#         olx_response = olx_client.remove_advert(
#             product.olx_advert_id, access_token
#         )
#         product.is_olx = False
#         product.save()
#         return self.get_response(olx_response, expected_status_code=204)



class TyreSearchView(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSearchSerailizer
    filter_backends = [filters.SearchFilter]
    search_fields = ['tread__name', 'get_tyre_class']

    def get(self, request):
        treads = Tread.objects.values_list('name', flat=True).distinct()
        return Response(treads, status=status.HTTP_200_OK)
    

class TyreNameView(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSearchSerailizer
    filter_backends = [filters.SearchFilter]
    search_fields = ['tread__name', 'get_tyre_class']

    def get(self, request):
        treads = Tread.objects.values_list('name', flat=True).distinct()
        return Response(treads, status=status.HTTP_200_OK)

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     tread = self.request.query_params.get('tread')
    #     tyre_class = self.request.query_params.get('tyre_class')

    #     if tread and tyre_class:
    #         queryset = [
    #             product for product in queryset
    #             if product.tread.name == tread and str(product.get_tyre_class) == tyre_class
    #         ]
    #     elif tread:
    #         queryset = queryset.filter(tread__name__icontains=tread)
    #     elif tyre_class:
    #         queryset = [product for product in queryset if str(product.get_tyre_class) == tyre_class]
        
    #     return queryset

class TyreClassIdView(viewsets.ModelViewSet):
    # authentication_classes=[TokenAuthentication,]
    # permission_classes=[IsAuthenticated,]
    serializer_class = TyreClassSerializer
    queryset = Product.objects.filter()
    filterset_class = ProductFilter

class ProductViewSet(viewsets.ModelViewSet):
    # authentication_classes=[TokenAuthentication,]
    # permission_classes=[IsAuthenticated,]
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(status=Product.StatusChoices.ON_SALE)
    filterset_class = ProductFilter

    def list(self, request, *args, **kwargs):
        """
        Default product filter + fallback to Size model if no products found
        """
        queryset = self.filter_queryset(self.get_queryset())
        if queryset.exists():

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        size_name = request.GET.get("size", "").strip()
        if size_name:
            size_obj = Size.objects.filter(size__iexact=size_name).first()
            if size_obj:
                return Response({
                    "message": "No products found, but size exists.",
                    "size": size_obj.size,
                    "size_description": getattr(size_obj, "description", None)
                })
        return Response([])

    @action(detail=False, methods=["get"], url_path="similar-products")
    def similar_products(self, request):
        brand_name = request.GET.get("brand", "").strip()
        tread_name = request.GET.get("tread", "").strip()
        size_name = request.GET.get("size", "").strip()
        exclude_id = request.GET.get("exclude_id")

        if not all([brand_name, tread_name, size_name]):
            return Response(
                {"error": "brand, tread, and size are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        brand_qs = Brand.objects.filter(name__iexact=brand_name)
        tread_qs = Tread.objects.filter(name__iexact=tread_name)
        size_qs = Size.objects.filter(size__iexact=size_name)

        if not brand_qs.exists() or not tread_qs.exists() or not size_qs.exists():
            return Response(
                {"message": "brand, tread, or size not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        brand = brand_qs.first()
        tread = tread_qs.first()
        size = size_qs.first()

        products = Product.objects.filter(
            brand__name=brand,
            tread__name=tread,
            size__size=size
        ).exclude(status=Product.StatusChoices.SOLD)

        if exclude_id:
            products = products.exclude(id=exclude_id)

        serializer = SimilarProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

class AdvanceFilterViewSet(viewsets.ViewSet):
    def list(self, request):
        tread_depth_min = request.query_params.get('tread_depth_min')

        products = Product.objects.all()

        if tread_depth_min:
            try:
                tread_depth_min = int(tread_depth_min)
                products = products.filter(tread_depth_min__gte=tread_depth_min)
            except ValueError:
                return Response({"error": "tread_depth_min must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdvanceFilterProductSerializer(products, many=True)
        return Response(serializer.data)


class BrandViewSet(viewsets.ModelViewSet):
    # authentication_classes=[TokenAuthentication,]
    # permission_classes=[IsAuthenticated,]
    pagination_class = None
    serializer_class = BrandSerializer
    queryset = Brand.objects.filter()
    filterset_class = BrandFilter


class SizeViewSet(viewsets.ModelViewSet):
    # authentication_classes=[TokenAuthentication,]
    # permission_classes=[IsAuthenticated,]
    pagination_class = None
    serializer_class = SizeSerializer
    queryset = Size.objects.filter()


class PairViewSet(viewsets.ModelViewSet):
    # authentication_classes=[]
    # permission_classes=[]
    pagination_class = None
    serializer_class = PairSerializer
    queryset = Pair.objects.filter()

    def remove_pairs_without_products(self, list_response):
        data = list_response.data
        print(data)
        for item in data:
            print(item)
            if not item.get("products"):
                data.remove(item)
        list_response.data = data

    def get_queryset(self):
        # return Pair with product count greater than 0
        return Pair.objects.annotate(product_count=Count('product')).filter(product_count__gt=0)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        # Filter out None values which represent pairs with no products
        data = [item for item in serializer.data if item is not None]
        return Response(data, status=status.HTTP_200_OK)

    # def list(self, request, *args, **kwargs):
    #     # products=ProductFilter(request.GET, queryset=Product.objects.filter(pair__isnull=False)).qs.select_related("pair","tread","brand")
    #     # pairs={product.pair_id:{"id":product.pair_id,"name":product.pair.name,"products":[]} for product in products}
    #     #
    #     # for product in products:
    #     #     pairs[product.pair_id]["products"].append(LiteProductSerializer(instance=product,context={'request': request}).data)
    #     #
    #     # data=[value for key,value in pairs.items()]
    #
    #     return Response(data)


class TreadViewSet(viewsets.ModelViewSet):
    # authentication_classes=[]
    # permission_classes=[]
    pagination_class = None
    serializer_class = TreadSerializer
    queryset = Tread.objects.all()

class TreadNameViewSet(viewsets.ModelViewSet):
    # authentication_classes=[]
    # permission_classes=[]
    pagination_class = None
    serializer_class = TreadNameIdSerializer
    queryset = Tread.objects.all()

    def get_queryset(self):
        return Tread.objects.values('name').distinct()


@api_view(["GET"])
def product_list(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(["GET"])
def product_detail(request, pk):
    product = Product.objects.get(pk=pk)
    serializer = ProductSerializer(product)
    return Response(serializer.data)


@api_view(["GET"])
def tread_char(request):
    tread_chars = Tread_Character.objects.all()
    serializer = Tread_CharacterSerializer(tread_chars, many=True)
    return Response(serializer.data)



@api_view(["GET"])
def tread_char_detail(request, pk):
    tread_chars = Tread_Character.objects.get(pk=pk)
    serializer = Tread_CharacterSerializer(tread_chars)
    return Response(serializer.data)


@api_view(["GET"])
def new_tread_depth(request):
    new_tread_depth = New_Tread_Depth.objects.all()
    serializer = New_Tread_DepthSerializer(new_tread_depth, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def new_tread_depth_detail(request, pk):
    new_tread_depth = New_Tread_Depth.objects.get(pk=pk)
    serializer = New_Tread_DepthSerializer(new_tread_depth)
    return Response(serializer.data)




# class OLXAdvertPairViewSet(viewsets.ViewSet):
#     def access_token(self):
#         access_token = olx_client.get_access_token()
#         return access_token
#     def get_response(self, olx_response, expected_status_code=200):
#         response = olx_response
#         if response.status_code != 204:
#             json_response = response.json()
#             data = (
#                 json_response["data"]
#                 if response.status_code == expected_status_code
#                 else json_response.get("error")
#             )
#             status_code = (
#                 status.HTTP_200_OK
#                 if response.status_code == expected_status_code
#                 else status.HTTP_400_BAD_REQUEST
#             )
#         else:
#             data = {"success": True, "message": "Removed Successfully"}
#             status_code = status.HTTP_200_OK
#         return Response(data=data, status=status_code)
#     def create(self, request):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         serializer = OLXAdvertPairSerializer(data=request.data)
#         if serializer.is_valid():
#             pair = serializer.validated_data["pair"]
#             print("SERIALIZER DATA :: ",serializer)
#             if pair.pair_is_olx == True:
#                 raise ValidationError("Adverts already in OLX.")
#             olx_response = olx_client.add_pair_advert(pair, access_token)
#             return self.get_response(olx_response)
#         else:
#             print("ELSE SERIALIZER DATA :: ",serializer)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def retrieve(self, request, pk=None):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         pair = get_object_or_404(Pair, id=pk)
#         olx_response = olx_client.get_advert_info(
#             pair.pair_olx_advert_id, access_token
#         )
#         return self.get_response(olx_response)
#     def update(self, request, pk=None):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         pair = get_object_or_404(Pair, id=pk)
#         olx_response = olx_client.get_advert_info(
#             pair.pair_olx_advert_id, access_token
#         )
#         return self.get_response(olx_response)
#     def destroy(self, request, pk=None):
#         access_token = self.access_token()
#         if not access_token:
#             return redirect(olx_client.OLX_AUTH_URL)
#         pair = get_object_or_404(Pair, id=pk)
#         olx_response = olx_client.remove_advert(
#             pair.pair_olx_advert_id, access_token
#         )
#         pair.is_olx = False
#         pair.save()
#         return self.get_response(olx_response, expected_status_code=204)
class SizeDetailApiView(APIView):
    def get(self, request, slug):
        try:
            size = Size.objects.get(slug=slug)
            products = size.product_set.all()
            serializer = ProductSerializer(products, many=True)
            return Response({
                'size': size.size,
                'description': size.description,
                'tyres': serializer.data
            })
        except Size.DoesNotExist:
            return Response({'error': 'Size not found'}, status=status.HTTP_404_NOT_FOUND)
        
class SimilarProductAPIView(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            similar_tread_entry = SimilarTread.objects.get(brand=product.brand, tread=product.tread)
        except SimilarTread.DoesNotExist:
            return Response({"similar_products": []})  # No similar treads defined

        similar_combos = similar_tread_entry.similar_tread_combinations.all()

        similar_products = Product.objects.filter(
            brand__in=[sc.brand for sc in similar_combos],
            tread__in=[sc.tread for sc in similar_combos],
            size=product.size
        ).exclude(id=product.id)

        serializer = SimilarProductSerializer(similar_products, many=True, context={'request': request})
        return Response({"similar_products": serializer.data})

#view for setting filter"
# class MySelectedProductFilterView(generics.RetrieveUpdateAPIView):
#     serializer_class = SelectedProductFilterSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         obj, _ = SelectedProductFilter.objects.get_or_create(user=self.request.user)
#         return obj



#Create & List Filters
class SelectedProductFilterListCreateView(generics.ListCreateAPIView):
    serializer_class = SelectedProductFilterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SelectedProductFilter.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

#Update / Retrieve / Delete a specific filter
class SelectedProductFilterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SelectedProductFilterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SelectedProductFilter.objects.filter(user=self.request.user)



# #view displaying products based on filters"
# class MySelectedFilteredProductsView(generics.ListAPIView):
#     serializer_class = ProductSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user
#         filter_id = self.kwargs['filter_id']

#         filt = get_object_or_404(SelectedProductFilter, id=filter_id, user=user)

#         queryset = Product.objects.all()

#         if filt.brand:
#             queryset = queryset.filter(brand=filt.brand)
#         if filt.tread:
#             queryset = queryset.filter(tread=filt.tread)
#         if filt.size:
#             queryset = queryset.filter(size=filt.size)
#         # if filt.only_on_sale:
#         #     queryset = queryset.filter(status=Product.StatusChoices.ON_SALE)

#         # bool_fields = [
#         #     'is_tire_bead_damaged', 'is_front_heat_repair', 'is_side_repair',
#         #     'is_visible_cracks', 'is_braked', 'is_braked_repair',
#         #     'is_shoulder_repair', 'is_cosmetology', 'is_toothed_out',
#         #     'is_retreaded', 'is_ruts', 'is_circumventional_cut'
#         # ]

#         # for field in bool_fields:
#         #     if getattr(filter_obj, field):
#         #         queryset = queryset.filter(**{field: True})

#         return queryset


from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from datetime import datetime

from .serializers import ProductSerializer

class MySelectedFilteredProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        filter_id = self.kwargs['filter_id']

        filt = get_object_or_404(SelectedProductFilter, id=filter_id, user=user)
        queryset = Product.objects.all()

        # Podstawowe filtry
        if filt.brand:
            queryset = queryset.filter(brand=filt.brand)
        if filt.tread:
            queryset = queryset.filter(tread=filt.tread)
        if filt.size:
            queryset = queryset.filter(size=filt.size)

        # oldest_dot -> wiek
        if filt.oldest_dot:
            current_year = datetime.now().year
            age = current_year - int(filt.oldest_dot)
            queryset = queryset.filter(dot__gte=age)

        # tread_depth_min
        if filt.tread_depth_min:
            queryset = queryset.filter(tread_depth_min__gte=filt.tread_depth_min)

        # issteer / isdrive / istrailer
        if filt.issteer is not None:
            queryset = queryset.filter(issteer=filt.issteer)
        if filt.isdrive is not None:
            queryset = queryset.filter(isdrive=filt.isdrive)
        if filt.istrailer is not None:
            queryset = queryset.filter(istrailer=filt.istrailer)

        # Pola boolean - wykluczenia jeśli wartość == True
        boolean_fields = [
            'is_tire_bead_damaged',
            'is_front_heat_repair',
            'is_side_repair',
            'is_visible_cracks',
            'is_braked',
            'is_braked_repair',
            'is_shoulder_repair',
            'is_cosmetology',
            'is_toothed_out',
            'is_retreaded',
            'is_ruts',
            'is_circumventional_cut',
        ]

        for field in boolean_fields:
            value = getattr(filt, field)
            if value is True:
                queryset = queryset.exclude(**{field: True})

        return queryset

    
