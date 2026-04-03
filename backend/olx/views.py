import requests
from .models import OLXAuthData
from django.urls import reverse
from olx.client import OlxClient
from django.utils import timezone
from allegro.views import Allegro
from django.http import HttpResponse
from django.utils.timezone import now
from django.shortcuts import redirect
# from allegro.models import Allegroauthdata
from rest_framework import viewsets, status
from rest_framework.response import Response
from tyreadderapp.models import Pair, Product
from tyreadderapp.filters import ProductFilter
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.validators import ValidationError
from django.db.models import Case, When, BooleanField
from django.views.decorators.http import require_POST
from django.db.models import BooleanField, Case, When, Value
from django.shortcuts import get_object_or_404, render,redirect
from olx.serializers import OLXAdvertPairSerializer, OLXAdvertSerializer

import logging
logger = logging.getLogger(__name__)

olx_client=OlxClient()
allegro_client = Allegro()

def update_refresh_token(request):
    auth_url = olx_client.get_authorization_url()
   
    return render(request,"olx/update_refreshtoken.html",{"auth_url":auth_url})


def product_update_with_olx_token(request):
    code=request.GET.get("code")
    if code:
        olx_client.save_tokens(code)
    access_token=olx_client.get_access_token()

    if not access_token:
        redirect_url=olx_client.OLX_AUTH_URL 
        return redirect(redirect_url)
    
    # olx_add_products = list(Product.objects.filter(is_olx=True,olx_advert_id__isnull=True))
    # olx_remove_products=list(Product.objects.filter(is_olx=False,olx_advert_id__isnull=False))
    

    # for product in olx_add_products:
    #     olx_client.add_advert(product,access_token)
    # for product in olx_remove_products:
    #     olx_client.remove_advert(product,access_token)
    return redirect(reverse("tyreadderapp:thank-you"))


@csrf_exempt
@require_POST
def refresh_olx_product(request, product_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

    try:
        logger.info(f"[🔄] Starting refresh for product_id={product_id}")
        product = get_object_or_404(Product, id=product_id)
        logger.info(f"[✅] Found product: {product.id} | OLX Ad ID: {product.olx_advert_id}")

        access_token = olx_client.get_access_token()
        logger.info("[🔑] Access token fetched (truncated): %s", access_token[:10])

        # Fetch advert from OLX
        response = requests.get(
            url=f"https://www.olx.pl/api/partner/adverts/{product.olx_advert_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Version": "2.0",
                "Content-Type": "application/json",
            },
        )
        logger.debug(f"[🌐] OLX GET Response: {response.status_code} - {response.text}")

        if response.status_code == 404:
            logger.warning(f"[❌] OLX Ad not found for product ID={product.id}, resetting...")

            # Reset fields
            product.is_olx = False
            product.is_olx_active = False
            product.olx_advert_id = None
            product.product_listing_status = Product.ProductStatusChoice.NEW.value
            product.save()

            logger.info(f"[🔁] Retrying OLX add for product ID={product.id}")
            olx_client.add_advert(product, access_token)

            return JsonResponse({"status": "success", "message": "Refreshed and re-added OLX advert."})

        elif response.status_code == 200:
            return JsonResponse({"status": "success", "message": "OLX advert already exists."})

        else:
            return JsonResponse({"status": "error", "message": "Unexpected response from OLX."}, status=500)

    except requests.exceptions.RequestException as e:
        logger.error(f"OLX GET Error: {e}")
        return JsonResponse({"status": "error", "message": "Network error while contacting OLX"}, status=500)
    except Exception as e:
        logger.exception(f"[🔥] Exception while refreshing product: {e}")
        return JsonResponse({"status": "error", "message": "Internal server error"}, status=500)

def selected_bulk_olx_product(request):
    current_date_time = timezone.now()
    olx_auth_data = OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)
    if not olx_auth_data.exists():
        return redirect("olx:update_refresh_token")
    allegro_auth_data = Allegroauthdata.objects.filter(refresh_token_expired_time__gt=current_date_time)
    if not allegro_auth_data.exists():
        return redirect("allegro:updatetoken")
    
    if request.method == 'POST':
        product_olx_list = request.POST.getlist('bulk-product-olx', None)
        action_type = request.POST.get('action_type', None)
        print("====ACTION TYPE======",action_type)

        if not product_olx_list:
            on_workspace = Product.StatusChoices.TO_ADD
            products = Product.objects.filter(status=on_workspace)
            products = products.annotate(
                is_olx_order=Case(
                    When(is_olx=True, then=True),
                    default=False,
                    output_field=BooleanField(),
                )
            ).order_by('-is_olx_order')
            quantity = Product.objects.filter(status=on_workspace).count()
            filters = ProductFilter(request.GET, queryset=products)
            context = {'filters': filters, 'quantity': quantity}
            return render(request, 'olx/multiple_seleted_olx.html', context)

        product_obj = Product.objects.filter(id__in=product_olx_list)

        if action_type == 'bulk_save_olx':
            logger.info("======== [OLX ADD STARTED] ==========")
            access_token = olx_client.get_access_token()

            for bulk_product in product_obj:
                logger.debug(
                    f"[OLX_ADD] Checking product ID={bulk_product.id}, "
                    f"is_olx_active={bulk_product.is_olx_active}, "
                    f"status={bulk_product.product_listing_status}, "
                    f"is_olx={bulk_product.is_olx}"
                )

                if (
                    not bulk_product.is_olx_active 
                    and bulk_product.product_listing_status == Product.ProductStatusChoice.NEW.value
                    and not bulk_product.is_olx
                ):
                    logger.info(f"[OLX_ADD] Creating advert for product ID={bulk_product.id}")
                    response = olx_client.add_advert(bulk_product, access_token)
                    logger.debug(
                        f"[OLX_ADD_RESPONSE] Product ID={bulk_product.id}, "
                        f"Status Code={response.status_code}, Response={response.text}"
                    )
                else:
                    logger.warning(f"[OLX_ADD_SKIPPED] Product ID={bulk_product.id} - Condition not met")

            logger.info("======== [OLX ADD COMPLETED] ==========")

        elif action_type == 'allegro':
            print("======== Alegro ==========")
            # allegro_access_token = allegro_client.get_allegro_access_token()
            for bulk_product in product_obj:
                allegro_client.advert_send_allegro(bulk_product)
        elif action_type == 'Update_Olx':
            logger.info("======== [OLX UPDATE STARTED] ==========")
            access_token = olx_client.get_access_token()

            for bulk_product in product_obj:
                logger.debug(
                    f"[OLX_UPDATE] Checking product ID={bulk_product.id}, "
                    f"is_olx_active={bulk_product.is_olx_active}, "
                    f"status={bulk_product.product_listing_status}, "
                    f"is_olx={bulk_product.is_olx}"
                )

                if (
                    bulk_product.is_olx_active  
                    and bulk_product.product_listing_status == Product.ProductStatusChoice.LISTED.value
                    and bulk_product.is_olx  
                ):
                    logger.info(f"[OLX_UPDATE] Updating product ID={bulk_product.id}")
                    response = olx_client.update_advert(bulk_product, access_token)
                    logger.debug(f"[OLX_UPDATE_RESPONSE] Product ID={bulk_product.id}, Response Code={response.status_code}, Response={response.text}")
                else:
                    logger.warning(f"[OLX_UPDATE_SKIPPED] Product ID={bulk_product.id} - Condition not met")

            logger.info("======== [OLX UPDATE COMPLETED] ==========")
        elif action_type == 'Olx_Remove':
            print("======== OLX REMOVE ==========")
            # allegro_access_token = allegro_client.get_allegro_access_token()
            access_token = olx_client.get_access_token()
            for bulk_product in product_obj:
                print(":::==::",bulk_product)
                olx_client.remove_advert(bulk_product, access_token)


        return redirect(reverse("tyreadderapp:thank-you"))

    on_workspace_statuses = [
        Product.StatusChoices.TO_ADD,
        Product.StatusChoices.ON_SALE
    ]
    products = Product.objects.filter(status__in=on_workspace_statuses)
    products = products.annotate(
        is_olx_order=Case(
            When(is_olx=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        has_pair=Case(
            When(pair__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        no_pair=Case(
            When(pair__isnull=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    ).order_by(
        '-is_olx_order',
        '-no_pair',
        '-has_pair'
    )

    quantity = products.count()
    filters = ProductFilter(request.GET, queryset=products)
    context = {'filters': filters, 'quantity': quantity}
    return render(request, 'olx/multiple_seleted_olx.html', context)

 
def olx_dashboard(request):
    products=Product.objects.filter().order_by("id")
    return render(request, "olx/olx_dashboard.html", {"products":products})



class OLXAdvertViewSet(viewsets.ViewSet):
    def access_token(self):
        access_token = olx_client.get_access_token()
        logger.debug(f"[OLXAdvertViewSet] Access token retrieved: {bool(access_token)}")
        return access_token

    def get_response(self, olx_response, expected_status_code=200):
        logger.debug(f"[OLXAdvertViewSet] get_response() called. Expected={expected_status_code}")
        if olx_response is None:
            logger.error("[OLXAdvertViewSet] OLX response is None.")
            return Response(
                data={"error": "No response from OLX API."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.debug(f"[OLXAdvertViewSet] OLX raw response: Status={olx_response.status_code}, Body={olx_response.text}")

        if olx_response.status_code != 204:
            try:
                json_response = olx_response.json()
            except Exception as e:
                logger.error(f"[OLXAdvertViewSet] Failed to parse OLX JSON response: {e}")
                return Response(
                    data={"error": "Invalid JSON from OLX API"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            data = (
                json_response.get("data")
                if olx_response.status_code == expected_status_code
                else json_response.get("error", json_response)
            )
            status_code = (
                status.HTTP_200_OK
                if olx_response.status_code == expected_status_code
                else status.HTTP_400_BAD_REQUEST
            )
        else:
            data = {"success": True, "message": "Removed Successfully"}
            status_code = status.HTTP_200_OK

        return Response(data=data, status=status_code)

    def create(self, request):
        logger.info("[OLXAdvertViewSet] Create advert request received.")
        access_token = self.access_token()
        if not access_token:
            logger.warning("[OLXAdvertViewSet] No access token found. Redirecting to OLX auth URL.")
            return redirect(olx_client.OLX_AUTH_URL)

        serializer = OLXAdvertSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data["product"]
            logger.debug(f"[OLXAdvertViewSet] Target product ID={product.id}, is_olx={product.is_olx}")

            if product.is_olx:
                logger.warning(f"[OLXAdvertViewSet] Product ID={product.id} already on OLX.")
                raise ValidationError("Adverts already in OLX.")

            logger.info(f"[OLXAdvertViewSet] Sending product ID={product.id} to OLX API...")
            olx_response = olx_client.add_advert(product, access_token)

            logger.info(f"[OLXAdvertViewSet] OLX API responded with status {olx_response.status_code}")
            return self.get_response(olx_response)
        else:
            logger.error(f"[OLXAdvertViewSet] Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

    def list(self, request):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        olx_response = olx_client.get_advert_list(access_token)
        return self.get_response(olx_response)

    def retrieve(self, request, pk=None):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        product = get_object_or_404(Product, id=pk)
        olx_response = olx_client.get_advert_info(
            product.olx_advert_id, access_token
        )
        return self.get_response(olx_response)

    def update(self, request, pk=None):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        product = get_object_or_404(Product, id=pk)
        olx_response = olx_client.get_advert_info(
            product.olx_advert_id, access_token
        )
        return self.get_response(olx_response)

    def destroy(self, request, pk=None):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        product = get_object_or_404(Product, id=pk)
        olx_response = olx_client.remove_advert(
            product.olx_advert_id, access_token
        )
        product.is_olx = False
        product.save()
        return self.get_response(olx_response, expected_status_code=204)
    


class OLXAdvertPairViewSet(viewsets.ViewSet):
    def access_token(self):
        access_token = olx_client.get_access_token()
        return access_token
    def get_response(self, olx_response, expected_status_code=200):
        response = olx_response
        if response.status_code != 204:
            json_response = response.json()
            data = (
                json_response["data"]
                if response.status_code == expected_status_code
                else json_response.get("error")
            )
            status_code = (
                status.HTTP_200_OK
                if response.status_code == expected_status_code
                else status.HTTP_400_BAD_REQUEST
            )
        else:
            data = {"success": True, "message": "Removed Successfully"}
            status_code = status.HTTP_200_OK
        return Response(data=data, status=status_code)
    def create(self, request):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        serializer = OLXAdvertPairSerializer(data=request.data)
        if serializer.is_valid():
            pair = serializer.validated_data["pair"]
            print("SERIALIZER DATA :: ",serializer)
            if pair.pair_is_olx == True:
                raise ValidationError("Adverts already in OLX.")
            olx_response = olx_client.add_pair_advert(pair, access_token)
            return self.get_response(olx_response)
        else:
            print("ELSE SERIALIZER DATA :: ",serializer)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        pair = get_object_or_404(Pair, id=pk)
        olx_response = olx_client.get_advert_info(
            pair.pair_olx_advert_id, access_token
        )
        return self.get_response(olx_response)
    def update(self, request, pk=None):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        pair = get_object_or_404(Pair, id=pk)
        olx_response = olx_client.get_advert_info(
            pair.pair_olx_advert_id, access_token
        )
        return self.get_response(olx_response)
    def destroy(self, request, pk=None):
        access_token = self.access_token()
        if not access_token:
            return redirect(olx_client.OLX_AUTH_URL)
        pair = get_object_or_404(Pair, id=pk)
        olx_response = olx_client.remove_advert(
            pair.pair_olx_advert_id, access_token
        )
        pair.is_olx = False
        pair.save()
        return self.get_response(olx_response, expected_status_code=204)




def olx_advert_sync(request):
    current_date_time = now()
    olx_auth_data = OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)
    
    if olx_auth_data.exists():
        for data in olx_auth_data:
            difference = (data.refresh_token_expired_time - current_date_time).days
            if difference <= 4:
                return redirect("olx:update_refresh_token")
    else:
        return redirect("olx:update_refresh_token")
    
    # Get access token
    access_token = olx_client.get_access_token()
    if not access_token:
        return HttpResponse("Failed to get access token", status=500)
    
    # Fixed indentation here - this was causing issues
    olx_response = olx_client.get_advert_list(access_token)
    response = olx_response.json()
    
    active_olx_advert_ids = set()
    
    if response.get('data'):
        for advert in response['data']:
            olx_advert_id = advert.get('id')
            status = advert.get('status')
            
            # Update product status based on OLX advert status
            Product.objects.filter(olx_advert_id=olx_advert_id).update(
                olx_advert_status=status
                
            )
            # Track active adverts
            if status == 'active':
                active_olx_advert_ids.add(olx_advert_id)
    
    # Update pairs with active olx adverts
    if active_olx_advert_ids:
        Pair.objects.filter(pair_olx_advert_id__in=active_olx_advert_ids).update(
            pair_is_olx=True, 
            pair_is_olx_active=True,  
            pair_listing_status=Pair.PairStatusChoice.LISTED
        )
        
        # Update products with active olx adverts
        Product.objects.filter(olx_advert_id__in=active_olx_advert_ids).update(
            is_olx=True, 
            is_olx_active=True,
            product_listing_status=Product.ProductStatusChoice.LISTED
        )
        
        # Update products that are not active on OLX
        Product.objects.filter(olx_advert_id__isnull=False).exclude(
            olx_advert_id__in=active_olx_advert_ids
        ).update(
            olx_advert_status="",
            is_olx_active=False,
            product_listing_status=Product.ProductStatusChoice.NEW
        )
    
    return redirect("tyreadderapp:main")



def addpair_olx_bulk(request):
    current_date_time = timezone.now()
    olx_auth_data = OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)
    
    if not olx_auth_data.exists():
        return redirect("olx:update_refresh_token")
    
    if request.method == "POST":
        selected_pair_ids = request.POST.getlist('pair_ids')
        action_type = request.POST.get('action_type', None)  # Get the action type
        print("===== ACTION TYPE ===== :: ",action_type)
        if selected_pair_ids:
            pairs_to_update = Pair.objects.filter(id__in=selected_pair_ids)
            access_token = olx_client.get_access_token()
            
            if not access_token:
                return HttpResponse("Failed to get access token", status=500)
            
            for pair in pairs_to_update:
                try:
                    if action_type == 'bulk_save_olx':
                        # Action to add pair advert on OLX
                        olx_client.add_pair_advert(pair, access_token)
                    elif action_type == 'Olx_update':
                        # Action to update pair advert on OLX
                        olx_client.update_pair_advert(pair, access_token)
                    elif action_type == 'Allegro':
                        pass
                        # Action to delete pair advert on OLX
                        # olx_client.delete_pair_advert(pair, access_token)
                    else:
                        return HttpResponse("Invalid action type specified.", status=400)

                except Exception as e:
                    return HttpResponse(f"Failed to process pair {pair.id}: {str(e)}", status=500)

            return redirect('tyreadderapp:pairadverts')

        return HttpResponse("No pairs selected.", status=400)

    return redirect('tyreadderapp:pairadverts')