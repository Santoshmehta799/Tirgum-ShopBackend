from django import views
from cart.filters import CartFilter
from django.shortcuts import render
from django.http import Http404, JsonResponse
from cart.models import Cart, CartItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, NotFound
from cart.serializers import CartSerializer, CreateCartSerializer, CartSerializers
from tyreadderapp.models import Pair, Product

import logging
logger = logging.getLogger(__name__)

# Create your views here. 

class SuperuserCartViewSet(viewsets.ViewSet):
    """
    A ViewSet to allow superusers to access carts by ID.
    """
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def retrieve(self, request, pk=None):
        print('ccccccheck')
        user = request.user
        if not user.is_superuser:
            raise PermissionDenied("You do not have permission to access this resource.")

        # Fetch the cart by primary key (id)
        try:
            cart = Cart.objects.prefetch_related("items").get(pk=pk)
        except Cart.DoesNotExist:
            raise NotFound("Cart with the given ID does not exist.")
        print('filtered ->', cart)
        # Serialize the cart
        serializer = CartSerializers(cart, context={'request': request})
        return Response(serializer.data)  
class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    filterset_class = CartFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return CreateCartSerializer
        return CartSerializers

    def get_queryset(self):
        try:
            session_id = (
                self.request.query_params.get('session_id')
                or self.request.data.get('session_id')
            )
            user = self.request.user if self.request.user.is_authenticated else None

            logger.info(f"Session ID received: {session_id}")
            logger.info(f"User authenticated: {user}")

            if session_id:
                queryset = Cart.objects.filter(session_id=session_id).prefetch_related("items")
                logger.info(f"Found {queryset.count()} carts for session_id={session_id}")
                return queryset

            elif user:
                queryset = Cart.objects.filter(user=user).prefetch_related("items")
                logger.info(f"Found {queryset.count()} carts for user={user}")
                return queryset

            else:
                logger.warning("No session_id or user found, returning empty queryset")
                return Cart.objects.none()

        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}", exc_info=True)
            return Cart.objects.none()

    def create(self, request, *args, **kwargs):
        data = request.data
        full_name = data.get("full_name", "")
        session_id = data.get("session_id", "")
        user = self.request.user if self.request.user.is_authenticated else None
        
        if user is None and session_id == "":
            return Response({
                "status": "error",
                "message": "Please provide authorized user token or session id.",
                "data": ""
            }, status=status.HTTP_400_BAD_REQUEST)

        if full_name and len(full_name) > 555:
            return Response({
                "status": "error",
                "message": "limit cannot exceed 555 characters.",
                "data": ""
            }, status=status.HTTP_400_BAD_REQUEST)

        if session_id and Cart.objects.filter(session_id=session_id).exists():
            return Response({
                "status": "error",
                "message": "cart already exist in this session! for create time",
                "data": ""
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            if user and Cart.objects.filter(user=user).exists():
                return Response({
                    "status": "error",
                    "message": "cart already exist in this authorized user! for create time",
                    "data": ""
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = self.request.user if self.request.user.is_authenticated else None
            # serializer.save(user=user)
            cart = serializer.save(user=user)
            full_serializer = CartSerializers(cart, context=self.get_serializer_context())
            return Response({
                "status": "success",
                "message": "cart created successfully!",
                "data": serializer.data,
                "cart_full": full_serializer.data 
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "error",
                "message": "No valid serilizer passsed.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        data = request.data
        full_name = data.get("full_name", "")
        session_id = data.get("session_id", "")        
        user = self.request.user if self.request.user.is_authenticated else None
        # AUTHENTICATION/AUTHORIZATION CHECK
        if user and user.is_authenticated:
            if instance.user and instance.user != user:
                return Response({
                    "status": "error",
                    "message": "You don't have permission to update this cart",
                    "data": ""
                }, status=status.HTTP_403_FORBIDDEN)
        elif session_id:
            if instance.session_id != session_id:
                return Response({
                    "status": "error",
                    "message": "Cart session ID does not match provided Correct session ID",
                    "data": ""
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                "status": "error",
                "message": "Please provide authorized user token or valid session ID",
                "data": ""
            }, status=status.HTTP_400_BAD_REQUEST)

        if full_name and len(full_name) > 555:
            return Response({
                "status": "error",
                "message": "Full name cannot exceed 555 characters",
                "data": ""
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance, data=data, partial=True)
        if serializer.is_valid():
            # serializer.save(user=user)
            cart = serializer.save(user=user)
            full_serializer = CartSerializers(cart, context=self.get_serializer_context())
            return Response({
                "status": "success",
                "message": "Cart updated successfully!",
                "data": serializer.data,
                "cart_full": full_serializer.data 
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Invalid data provided",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        obj_id = kwargs.get('pk') 
        try:
            obj = Cart.objects.get(id=obj_id)
            obj.delete()
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Object not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put'])
    def update_cart_field(self, request):
        user = request.user if request.user.is_authenticated else None
        session_id = request.data.get('session_id')
        if not user and not session_id:
            return Response({
                "status": "error",
                "message": "Please provide authorized user token or session id",
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            if user:
                try:
                    cart = Cart.objects.get(user=user)
                except Cart.DoesNotExist:
                    return Response({
                        "status": "error",
                        "message": "No cart found for the authenticated user",
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                if not session_id:
                    return Response({
                        "status": "error",
                        "message": "session_id is required when not authenticated",
                    }, status=status.HTTP_400_BAD_REQUEST)
                try:
                    cart = Cart.objects.get(session_id=session_id)
                except Cart.DoesNotExist:
                    return Response({
                        "status": "error",
                        "message": "No cart found with the provided session_id",
                    }, status=status.HTTP_404_NOT_FOUND)
            update_data = {k: v for k, v in request.data.items()}
            
            serializer = self.get_serializer(cart, data=update_data, partial=True)
            if serializer.is_valid():
                if not serializer.validated_data:
                    for field in update_data:
                        if hasattr(cart, field) and field != 'session_id':
                            setattr(cart, field, update_data[field])
                    cart.save()
                else:
                    cart = serializer.save()
                full_serializer = CartSerializers(cart, context=self.get_serializer_context())
                
                return Response({
                    "status": "success",
                    "message": "Cart details updated successfully",
                    "data": self.get_serializer(cart).data,
                    "cart_full": full_serializer.data  
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "error",
                    "message": "Invalid data provided",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST) 
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class RemovePairItemFromCart(views.APIView):
    def post(self, request, pair_id, format=None):
        pair = Pair.objects.filter(id=pair_id)
        pair_product_lst = []
        user = request.user if request.user.is_authenticated else None
        session_id = request.data.get("session_id", "")
        print('user -->', user)
        print('session_id -->', session_id)
        if not user and session_id == "":
            return Response({
                "status": "error",
                "message": "Please provide authorized user token or session id.",
            }, status=status.HTTP_400_BAD_REQUEST)


        if not pair:
            return Response({
                "status": "error",
                "message": "Pair ID does not exist.",
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if pair:
            pair_product_lst = [product.pk for product in Product.objects.filter(pair=pair.first())]
            
            # print("pair exist with this", pair_product_lst)


        if user:
            user_cart = Cart.objects.filter(user=user)
        elif session_id:
            user_cart = Cart.objects.filter(session_id=session_id)
        if not user_cart:
            return Response({
                "status": "error",
                "message": "Cart does not exist for user",
            }, status=status.HTTP_401_UNAUTHORIZED)
        # print("user cart exist with this", user_cart)

        CartItem.objects.filter(cart=user_cart.first(), product_id__in=pair_product_lst).delete()
        # print("user cart items exist with this", user_cart_item, len(user_cart_item))

        return Response({
            "status": "success",
            "message": f"Pair ID pair id: {pair_id} pair products: {pair_product_lst} user_cart: {user_cart.first().pk} removed successfully."
        }, status=status.HTTP_200_OK)



class RemoveItemCart(views.APIView):
    def delete(self, request, cart_id, cart_item_id, format=None):
        cart = get_object_or_404(Cart, id=cart_id)
        user = request.user if request.user.is_authenticated else None
        session_id = request.query_params.get("session_id", "")

        if user is None and not session_id:
            return Response({
                "status": "error",
                "message": "Please provide authorized user token or session id.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if user:
                cart = get_object_or_404(Cart, id=cart_id, user=user)
            elif session_id:
                cart = get_object_or_404(Cart, id=cart_id, session_id=session_id)
            else:
                return Response({
                    "status": "error",
                    "message": "Authentication failed.",
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Http404:
            return Response({
                "status": "error",
                "message": f"Cart {cart_id} not found or you don't have permission to access it.",
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Find the CartItem in this cart
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
            
            # Delete the item
            cart_item.delete()
            
            return Response({
                "status": "success",
                "message": f"Item removed successfully from cart",
            }, status=status.HTTP_200_OK)
                           
        except CartItem.DoesNotExist:
            return Response({
                "status": "error",
                "message": f"Item {cart_item_id} not found in cart {cart_id}",
            }, status=status.HTTP_404_NOT_FOUND)

