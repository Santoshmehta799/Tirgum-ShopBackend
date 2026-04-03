import json
from django.shortcuts import redirect
from django.http import Http404, JsonResponse
from tyreadderapp.models import Pair, Product
from django.core.paginator import Paginator
import requests
from requests.exceptions import RequestException
from django.shortcuts import render
from django.http import HttpResponse
from .models import OtomotoAuthData
from django.views.decorators.http import require_POST
from .utils import update_otomoto_stats
from .client import OtomotoClient
# from otomoto.client.client import BaseOtomotoClient
import logging
logger = logging.getLogger(__name__)

from .models import OtoMotoAdvertData,PairOtoMotoAdvertData
from django.core.exceptions import ObjectDoesNotExist

from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from otomoto.parsers import sync_all_active_otomoto_adverts







    
    


#####################################



#####################################
def toggle_autorefresh(request):
    if request.method == "POST":
        product_ids = request.POST.get("product_ids", "")

        # Validate product IDs
        product_ids = [int(pk)
                       for pk in product_ids.split(",") if pk.isdigit()]
        if not product_ids:
            return JsonResponse({"success": False, "error": "No product IDs provided"})

        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            return JsonResponse({"success": False, "error": "Products not found"})

        updated_count = 0
        new_states = {}

        for product in products:
            if hasattr(product, "otomoto_data") and product.otomoto_data:
                product.otomoto_data.is_autorefresh = not product.otomoto_data.is_autorefresh
                product.otomoto_data.save()
                new_states[product.id] = product.otomoto_data.is_autorefresh

            updated_count += 1

        return JsonResponse({
            "success": True,
            "updated_count": updated_count,
            "new_states": new_states  # Optional: shows new values for each product
        })

    # Fallback for non-POST requests
    return JsonResponse({"success": False, "error": "Invalid request method"})





    
def export_to_olx(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    import json, requests
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    product_ids = data.get("product_ids", [])
    product_ids = [int(pk) for pk in product_ids if str(pk).isdigit()]
    print("******product_ids:", product_ids)
    if not product_ids:
        return JsonResponse({"success": False, "error": "No product IDs provided"}, status=400)

    products_to_olx = Product.objects.filter(
        id__in=product_ids,
        is_otomoto_advert_activated=True
    ).select_related('otomoto_data')

    if not products_to_olx.exists():
        return JsonResponse({"success": False, "error": "Products not found"}, status=404)

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return JsonResponse({"success": False, "error": "Otomoto auth not configured"}, status=400)

    client = OtomotoClient(auth_data)
    access_token = client.get_access_token()

    headers = {
        "User-Agent": client.OTOMOTO_USERNAME,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Version": "2.0"
    }

    base_url = "https://www.otomoto.pl/api/open/account/adverts"
    updated_count = 0

    for product in products_to_olx:
        otomoto_advert_id = getattr(product.otomoto_data, "otomoto_advert_id", None)
        if not otomoto_advert_id:
            continue

        activate_url = f"{base_url}/{otomoto_advert_id}/promotions"
        print("activate_url:", activate_url)
        payload = {"payment_type": "account", "promotion_ids": [49]}

        try:
            response = requests.post(activate_url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                product.otomoto_data.is_exported_to_olx = True
                product.otomoto_data.save(update_fields=["is_exported_to_olx"])
                updated_count += 1
            else:
                print(f"Failed to put on OLX: {response.text}")
        except requests.RequestException as e:
            print(f"Request failed for product {product.pk}: {e}")

    return JsonResponse({"success": True, "updated_count": updated_count})


#################################




import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import OtoMotoAdvertData,PairOtoMotoAdvertData  # adjust this import

def sync_ads_view(request):
    
    return sync_ads()


def sync_ads():
    # account_url = "https://www.otomoto.pl/api/open/warsztatboruszowice@gmail.com/adverts"
    account_url = "https://www.otomoto.pl/api/open/account/adverts"
    
    
    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return HttpResponse("Otomoto auth data missing", status=500) 
    
    otomoto_client = OtomotoClient(auth_data=auth_data)
    otomoto_client.ensure_authenticated()
    
        
    
    headers = {
        "User-Agent": otomoto_client.OTOMOTO_USERNAME,
        "Authorization": f"Bearer {otomoto_client.get_valid_access_token()}",
        "Content-Type": "application/json",
        "Version": "2.0"
    }
    
    # params = {
    # "limit": 10,
    # "page": 1
    # }

    try:
        response = requests.get(account_url, headers=headers)
        response.raise_for_status()
        adverts = response.json()
        print("RAW RESPONSE:", adverts)
    except requests.RequestException as e:
        print(f"Failed to fetch adverts: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

    # adverts_list = adverts.get("data", adverts) if isinstance(adverts, dict) else adverts
    
    adverts_list = [
    advert for advert in (adverts.get("results", []) if isinstance(adverts, dict) else adverts)
    if isinstance(advert, dict)
    ]
    
    logger.info("RAW RESPONSE: %s", adverts)
    
    logger.info("ADVERTS LIST: %s", adverts_list)
    print("ADVERTS LIST:", adverts_list)
    
    logger.info("ADVERTS LIST COUNT: %s", len(adverts_list))
    print("COUNT:", len(adverts_list))
    
    updated_singles = 0
    updated_pairs = 0

    for advert in adverts_list:
        if not isinstance(advert, dict):
            logger.warning("Skipping invalid advert: %s", advert)
            continue

        advert_id = advert.get("id")
        if not advert_id:
            logger.warning("Skipping advert without ID: %s", advert)
            continue

        valid_to = advert.get("valid_to")
        if valid_to:
            valid_to = parse_datetime(valid_to)
            if valid_to and timezone.is_naive(valid_to):
                valid_to = timezone.make_aware(valid_to)
        
        created_at = advert.get("created_at")
        if created_at:
            created_at = parse_datetime(created_at)
            if created_at and timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
    
        defaults = {
            "valid_to": valid_to,
            "otomoto_advert_status": advert.get("status"),
            "created_at": created_at,
        }

        singles = OtoMotoAdvertData.objects.filter(otomoto_advert_id=advert_id).update(**defaults)
        pairs = PairOtoMotoAdvertData.objects.filter(otomoto_advert_id=advert_id).update(**defaults)
        
        updated_singles += singles
        updated_pairs += pairs

        logger.info("Advert %s updated: %s product rows, %s pair rows", advert_id, singles, pairs)
    
    return JsonResponse({
        "success": True,
        "total_adverts": len(adverts_list),
        "updated_singles": updated_singles,
        "updated_pairs": updated_pairs,
        "adverts": adverts_list
    })
    
    
# views.py

import json
import requests

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Product, OtoMotoAdvertData, PairOtoMotoAdvertData


@require_POST
def sync_ad_stats(request):

    base_url = "https://www.otomoto.pl/api/open/account/adverts/{}/stats/details"
    
    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return HttpResponse("Otomoto auth data missing", status=500) 
    
    otomoto_client = OtomotoClient(auth_data=auth_data)
    otomoto_client.ensure_authenticated()
    
        
    
    headers = {
        "User-Agent": otomoto_client.OTOMOTO_USERNAME,
        "Authorization": f"Bearer {otomoto_client.get_valid_access_token()}",
        "Content-Type": "application/json",
        "Version": "2.0"
    }

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON body"},
            status=400
        )

    product_ids = data.get("product_ids", [])
    product_ids = [int(pk) for pk in product_ids if str(pk).isdigit()]

    if not product_ids:
        return JsonResponse(
            {"success": False, "error": "No product IDs provided"},
            status=400
        )

    products_to_sync = Product.objects.filter(
        id__in=product_ids
    ).select_related("otomoto_data")

    if not products_to_sync.exists():
        return JsonResponse(
            {"success": False, "error": "Products not found"},
            status=404
        )

    results = []

    for product in products_to_sync:

        if not product.otomoto_data or not product.otomoto_data.otomoto_advert_id:
            results.append({
                "product_id": product.id,
                "success": False,
                "error": "Missing otomoto_advert_id"
            })
            continue

        advert_id = product.otomoto_data.otomoto_advert_id
        url = base_url.format(advert_id)

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            stats_data = response.json()

            totals = {
                "ad_views_total": 0,
                "ad_visits_total": 0,
                "phone_views_total": 0,
                "phone_calls_total": 0,
                "messages_total": 0
            }
            logger.info(f"Totals before updating: {totals}")
            # logger.error(f"Failed to update product {product.id}")

            for item in stats_data:
                totals["ad_views_total"] += int(item.get("adViews", 0))
                totals["ad_visits_total"] += int(item.get("adVisits", 0))
                totals["phone_views_total"] += int(item.get("phoneViews", 0))
                totals["phone_calls_total"] += int(item.get("phoneCalls", 0))
                totals["messages_total"] += int(item.get("messages", 0))

            
            updated = OtoMotoAdvertData.objects.filter(product=product).update(**totals)

            if updated == 0:
                results.append({
                    "product_id": product.id,
                    "success": False,
                    "error": "Stats record does not exist"
                })
                continue
            

            results.append({
                "product_id": product.id,
                "advert_id": advert_id,
                "success": True,
                "totals": totals
            })

        except requests.RequestException as e:
            results.append({
                "product_id": product.id,
                "advert_id": advert_id,
                "success": False,
                "error": str(e)
            })

    return JsonResponse({
        "success": True,
        "results": results
    })
