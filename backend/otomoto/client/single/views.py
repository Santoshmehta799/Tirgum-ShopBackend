from tyreadderapp.models import Product
import requests
from django.shortcuts import render,redirect
from django.core.paginator import Paginator
from otomoto.models import OtomotoAuthData
from otomoto.client.otomoto_client import OtomotoClient
from django.http import Http404,HttpResponse, JsonResponse
import json
from otomoto.models import OtoMotoAdvertData
from otomoto.client.otomoto_client import AuthOtomotoClient
from .otomoto_single_ad import OtomotoSingleAd
import json
from django.shortcuts import redirect
from django.http import Http404, JsonResponse
from tyreadderapp.models import Pair, Product
from django.core.paginator import Paginator
import requests
from requests.exceptions import RequestException
from django.shortcuts import render
from django.http import HttpResponse
# from .models import OtomotoAuthData
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db.models import F, Q
# from .utils import update_otomoto_stats
# from .client import OtomotoClient
# from otomoto.client.client import BaseOtomotoClient

# from .models import OtoMotoAdvertData,PairOtoMotoAdvertData
from django.core.exceptions import ObjectDoesNotExist



# from otomoto.client.client import BaseOtomotoClient


#ACTIVE OTOMOTO
def active_otomoto(request):
    products = Product.objects.filter(
        status=Product.StatusChoices.ON_SALE,
        # is_otomoto_advert_activated=True,
        otomoto_data__otomoto_advert_status__in= ['active', 'new']
    ).select_related('otomoto_data').order_by('otomoto_data__valid_to').prefetch_related('images')
    
    #Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    #End of Pagination

    # for product in page_obj.object_list:
    #     OtoMotoAdvertData.objects.get_or_create(product=product)

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return HttpResponse("Otomoto auth data missing", status=500)   
    

    otomoto_client = OtomotoClient(auth_data=auth_data)
    # Client internally ensures valid access token
    otomoto_client.ensure_authenticated()
    # token = otomoto_client.get_access_token()    

    # Update stats only for visible products

    return render(request, "otomoto/active_otomoto.html", {
        "page_obj": page_obj
    })
    




#INACTIVE OTOMOTO
# def inactive_otomoto(request):
#     products = Product.objects.filter(
#         status=Product.StatusChoices.ON_SALE,
#         is_otomoto_advert_activated=False,
#     ).select_related('otomoto_data').order_by('-created').prefetch_related('images')
    
#     #Pagination
#     paginator = Paginator(products, 20)
#     page_number = request.GET.get("page")
#     page_obj = paginator.get_page(page_number)
#     #End of Pagination

#     # Ensure every product has OtomotoAdvertData
#     for product in products:
#         OtoMotoAdvertData.objects.get_or_create(product=product)
    

#     return render(request, "otomoto/inactive_otomoto.html", {"page_obj": page_obj})


# def inactive_otomoto(request):
#     inactive_statuses = ['outdated', 'unpaid'] 
#     products = Product.objects.filter(
#         status=Product.StatusChoices.ON_SALE,
#         # is_otomoto_advert_activated=True,
        
#     ).filter(
#         Q(otomoto_data__otomoto_advert_status__in=inactive_statuses) |
#         Q(otomoto_data__otomoto_advert_status__isnull=True)
#     ).order_by(F('otomoto_data__otomoto_advert_id').asc(nulls_last=True))

from django.db.models import Q, F

def inactive_otomoto(request):
    products = Product.objects.filter(
        status=Product.StatusChoices.ON_SALE
    ).exclude(
        otomoto_data__otomoto_advert_status__in =['active', 'new']
    ).order_by(
        F('otomoto_data__otomoto_advert_id').asc(nulls_last=True)
    )

    # Ensure Otomoto data exists
    # for product in base_qs:
    #     OtoMotoAdvertData.objects.get_or_create(product=product)

    # products = (
    #     base_qs
    #     .select_related('otomoto_data')
    #     .prefetch_related('images')
    #     .order_by('otomoto_data__otomoto_advert_id')
    #     # .order_by('-created')
    # )

    paginator = Paginator(products, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "otomoto/inactive_otomoto.html",
        {"page_obj": page_obj}
    )

# ACTIVATE OTOMOTO ADS
def activate_otomoto_ads(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    product_ids = data.get("product_ids", [])

    if not isinstance(product_ids, list) or not product_ids:
        return JsonResponse({"success": False, "error": "No product IDs provided"}, status=400)

    # ensure ints
    product_ids = [int(pk) for pk in product_ids if str(pk).isdigit()]

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return JsonResponse({"success": False, "error": "Otomoto auth not configured"}, status=400)

    client = OtomotoClient(auth_data)
    access_token = client.get_valid_access_token()

    products_to_activate = Product.objects.filter(
        id__in=product_ids,
        # is_otomoto_advert_activated=False
    ).select_related('otomoto_data')
    # print("products_to_activate:", products_to_activate)

    if not products_to_activate.exists():
        return JsonResponse({"success": False, "error": "Products not found"}, status=404)

    headers = {
        "User-Agent": client.OTOMOTO_USERNAME,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Version": "2.0"
    }
    print("Headers:", headers)

    base_url = "https://www.otomoto.pl/api/open/account/adverts"

    success = []
    failed = []

    for product in products_to_activate:
        otomoto_advert_id = getattr(
            product.otomoto_data, "otomoto_advert_id", None)
        print("Otomoto advert ID:", otomoto_advert_id)

        if not otomoto_advert_id:
            failed.append({
                "product_id": product.id,
                "product_advert_id": product.otomoto_advert_id,
                "error": "Otomoto advert ID missing"
            })
            continue
        print("failed:", failed)
        activate_url = f"{base_url}/{otomoto_advert_id}/activate"

        try:
            response = requests.post(
                activate_url,
                headers=headers,
                json={},  # Otomoto expects empty body
                timeout=10
            )

            
            if response.status_code in (200, 204):
                product.is_otomoto_advert_activated = True
                product.save(update_fields=["is_otomoto_advert_activated"])
                # Product.objects.filter(id__in=success).update(is_otomoto_advert_activated=True)

                success.append(product.id)
                print("success:", success)
            else:
                failed.append({
                    "product_id": product.id,
                    "status_code": response.status_code,
                    "response": response.text
                })
                print("Failed to activate:", response.text)

        except RequestException as e:
            failed.append({
                "product_id": product.id,
                "error": str(e)
            })
            print("Exception:", str(e))

    return JsonResponse({
        "success": len(failed) == 0,
        "activated_products": success,
        "failed_products": failed
    })




def deactivate_otomoto_ads(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    product_ids = data.get("product_ids", [])

    if not isinstance(product_ids, list) or not product_ids:
        return JsonResponse({"success": False, "error": "No product IDs provided"}, status=400)

    # ensure ints
    product_ids = [int(pk) for pk in product_ids if str(pk).isdigit()]

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return JsonResponse({"success": False, "error": "Otomoto auth not configured"}, status=400)

    client = OtomotoClient(auth_data)
    access_token = client.get_valid_access_token()

    products_to_deactivate = Product.objects.filter(
        id__in=product_ids,
        is_otomoto_advert_activated=True
    ).select_related('otomoto_data')
    # print("products_to_activate:", products_to_activate)

    if not products_to_deactivate.exists():
        return JsonResponse({"success": False, "error": "Products not found"}, status=404)

    headers = {
        "User-Agent": client.OTOMOTO_USERNAME,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Version": "2.0"
    }
    print("Headers:", headers)

    base_url = "https://www.otomoto.pl/api/open/account/adverts"

    success = []
    failed = []

    for product in products_to_deactivate:
        otomoto_advert_id = getattr(
            product.otomoto_data, "otomoto_advert_id", None)
        print("Otomoto advert ID:", otomoto_advert_id)

        if not otomoto_advert_id:
            failed.append({
                "product_id": product.id,
                "product_advert_id": product.otomoto_advert_id,
                "error": "Otomoto advert ID missing"
            })
            continue
        print("failed:", failed)
        activate_url = f"{base_url}/{otomoto_advert_id}/deactivate"
        payload = {
            "reason": {
                "id": 13,
                "description": "false"
            }
        }

        try:
            response = requests.post(
                activate_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            # Log for debugging
            print("activate_url:", activate_url)
            print("*****Response status code:", response.status_code)
            print("*****Response text:", response.text)

            if response.status_code == 204:
                product.is_otomoto_advert_activated = False
                product.save(update_fields=["is_otomoto_advert_activated"])
                success.append(product.id)
                print("success:", success)
            else:
                failed.append({
                    "product_id": product.id,
                    "status_code": response.status_code,
                    "response": response.text
                })
                print("Failed to deactivate:", response.text)

        except RequestException as e:
            failed.append({
                "product_id": product.id,
                "error": str(e)
            })
            print("Exception:", str(e))

    return JsonResponse({
        "success": len(failed) == 0,
        "deactivated_products": success,
        "failed_products": failed
    })



import requests
from django.shortcuts import render
from django.http import Http404


def active_single_ad_detail(request, otomoto_advert_id):
    url = f"https://www.otomoto.pl/api/open/account/adverts/{otomoto_advert_id}"
    
    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return HttpResponse("Otomoto auth data missing", status=500) 
    
    otomoto_client = OtomotoClient(auth_data=auth_data)
    otomoto_client.ensure_authenticated()
    
    headers = {
        "User-Agent": otomoto_client.OTOMOTO_USERNAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {otomoto_client.get_valid_access_token()}",
    }
    
    try:
        response = requests.get(url,headers=headers, timeout=5)
        response.raise_for_status()  # raises error for 4xx/5xx
    except requests.HTTPError as e:
        if response.status_code == 404:
            raise Http404("Ad not found")
        return HttpResponse(f"Error fetching ad: {e}", status=response.status_code)
    except requests.RequestException as e:
        return HttpResponse(f"Network error: {e}", status=500)

    ad = response.json()

    return render(request, "otomoto/otomoto_ad_single_detail.html", {
        "ad": ad
    })




import requests
from django.shortcuts import render, redirect
from otomoto.forms import AdvertForm
from django.conf import settings
from django.contrib import messages

# API_URL = "https://example.com/account/adverts/"

def update_single_ad_detail(request, otomoto_advert_id):   
    url = f"https://www.otomoto.pl/api/open/account/adverts/{otomoto_advert_id}"
    
    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return HttpResponse("Otomoto auth data missing", status=500) 
    
    otomoto_client = OtomotoClient(auth_data=auth_data)
    otomoto_client.ensure_authenticated()
    
    headers = {
        "User-Agent": otomoto_client.OTOMOTO_USERNAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {otomoto_client.get_access_token()}",
    }

    # Fetch existing advert (needed for both GET and POST)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return render(request, 'otomoto/update_advert.html', {'error': 'Failed to fetch ad'})
    
    data = response.json()
    
    if request.method == "POST":
        form = AdvertForm(request.POST)
        if form.is_valid():
            payload = {
                "title": form.cleaned_data.get("title", data["title"]),
                "description": form.cleaned_data.get("description", data["description"]),
                "category_id": data["category_id"],
                "region_id": data["region_id"],
                "city_id": data["city_id"],
                "district_id": data.get("district_id"),
                "coordinates": data["coordinates"],
                "contact": {"person": form.cleaned_data.get("contact_person", data["contact"].get("person"))},
                "params": data["params"],
                "image_collection_id": data.get("image_collection_id"),
                "advertiser_type": data.get("advertiser_type"),
                "new_used": data.get("new_used"),
                "brand_program_id": data.get("brand_program_id")
            }

            # Convert Decimal price to float if needed
            if form.cleaned_data.get("price") is not None:
                payload["params"]["price"]["1"] = float(form.cleaned_data["price"])

            put_response = requests.put(url, headers=headers, json=payload)
            if put_response.status_code == 200:
                messages.success(request, "Advert updated successfully.")
            else:
                errors = put_response.json().get('error', {}).get('details', {})
                messages.error(request, "Failed to update advert.")
                return render(request, 'otomoto/update_advert.html', {'form': form, 'errors': errors})

            return render(request, 'otomoto/update_advert.html', {'form': form})

        else:
            # Form invalid → render with errors
            return render(request, 'otomoto/update_advert.html', {'form': form})

    else:
        # GET request → prefill form
        initial = {
            "id": data['id'],
            "title": data['title'],
            "description": data['description'],
            "url": data['url'],
            "title_parts": data['params'].get('title_parts', ''),
            "price": data['params'].get('price', {}).get('1', None),
            "category_id": data['category_id'],
            "region_id": data['region_id'],
            "city_id": data['city_id'],
            "district_id": data.get('district_id'),
            "latitude": data['coordinates']['latitude'],
            "longitude": data['coordinates']['longitude'],
            "contact_person": data['contact'].get('person'),
            "advertiser_type": data.get('advertiser_type'),
            "new_used": data.get('new_used'),
            "brand_program_id": data.get('brand_program_id'),
            "image_collection_id": data.get('image_collection_id'),
        }   
        form = AdvertForm(initial=initial)
        return render(request, 'otomoto/update_advert.html', {'form': form})




from django.http import JsonResponse
import json

def create_otomoto_ads(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "POST request required"},
            status=405
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON body"},
            status=400
        )

    product_ids = data.get("product_ids", [])

    if not isinstance(product_ids, list) or not product_ids:
        return JsonResponse(
            {"success": False, "error": "No product IDs provided"},
            status=400
        )

    # Ensure integers
    product_ids = [int(pk) for pk in product_ids if str(pk).isdigit()]

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return JsonResponse(
            {"success": False, "error": "Otomoto auth not configured"},
            status=400
        )

    # client = OtomotoClient(auth_data)
    
    client = OtomotoSingleAd()
    
        

    products_to_create = (
        Product.objects
        .filter(
            id__in=product_ids,
            is_otomoto_advert_created=False
        )
        .select_related("otomoto_data")
    )

    if not products_to_create.exists():
        return JsonResponse(
            {"success": False, "error": "Products not found"},
            status=404
        )

    success = []
    failed = []

    for product in products_to_create:
        try:
            result = client.create_and_save_advert(product)
            

            if result is None:
                failed.append({
                    "product_id": product.id,
                    "error": "Advert creation failed (see server logs)"
                })
                continue

            # Mark product as created
            product.is_otomoto_advert_created = True
            product.save(update_fields=["is_otomoto_advert_created"])

            success.append({
                "product_id": product.id,
                "otomoto_advert_id": result.get("id"),
                "status": result.get("status"),
            })

        except Exception as e:
            failed.append({
                "product_id": product.id,
                "error": str(e)
            })

    return JsonResponse({
        "success": len(failed) == 0,
        "created_products": success,
        "failed_products": failed
    })


def auth_active_otomoto(request):
    auth_data = OtomotoAuthData.objects.first()

    client = AuthOtomotoClient(auth_data=auth_data)

    adverts_response = client.get_my_adverts()
    adverts = adverts_response.get("items", [])

    return render(
        request,
        "otomoto/active_otomoto.html",
        {"adverts": adverts},
    )