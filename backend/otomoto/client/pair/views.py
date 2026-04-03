from tyreadderapp.models import Pair
from otomoto.models import PairOtoMotoAdvertData
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import JsonResponse
import json
import requests
from requests.exceptions import RequestException
from otomoto.models import OtomotoAuthData
from otomoto.client.otomoto_client import OtomotoClient
from .otomoto_pair_ad import OtomotoPairAd
from django.http import Http404
from django.http import HttpResponse
from django.db.models import F, Count
from django.db.models import Case, When, IntegerField




def inactive_otomoto_pairs(request):
    
    BASE_MEDIA_URL = "https://www.tirgumpanel.pl/media/pair_images"
    
    pairs = Pair.objects.exclude(
        otomoto_advert__otomoto_advert_status__in =['active', 'new']
    ).annotate(
        product_count=Count('products')
    ).filter(
        product_count__gt=0
    ).order_by(
        F('otomoto_advert__otomoto_advert_id').asc(nulls_last=True)
    )
    
    # ad = OtomotoPairAd()
    # for pair in pairs:
    #     images = ad.get_images(pair)
    #     pair.main_img = images.get("1")
    
    
    for pair in pairs:
        # Build main image filename from save_pair_image pattern
        main_filename = f"pair_{pair.id}_combined.jpg"
        main_img_url = f"{BASE_MEDIA_URL}/{main_filename}"        
        pair.main_img = main_img_url
        pair.product_ids = list(pair.products.values_list('id', flat=True))
        
        
        
    paginator = Paginator(pairs, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "otomoto/inactive_otomoto_pairs.html", {"page_obj": page_obj})


from django.db.models import Case, When, IntegerField
from django.core.paginator import Paginator


def active_otomoto_pairs(request):
    # Filter only pairs with activated advert AND related OtomotoAdvert exists
    pairs = Pair.objects.filter(
        # is_otomoto_pair_advert_activated=True,
        # otomoto_advert__isnull=False
        otomoto_advert__otomoto_advert_status__in= ['active', 'new'],
        otomoto_advert__isnull=False).order_by(F('otomoto_advert__valid_to').asc(nulls_last=True))

    


    BASE_MEDIA_URL = "https://www.tirgumpanel.pl/media/pair_images"

    for pair in pairs:
        main_filename = f"pair_{pair.id}_combined.jpg"
        pair.main_img = f"{BASE_MEDIA_URL}/{main_filename}"
        pair.product_ids = list(pair.products.values_list('id', flat=True))

    paginator = Paginator(pairs, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "otomoto/active_otomoto_pairs.html",
        {"page_obj": page_obj}
    )

# def active_otomoto_pairs(request):
#     # Filter only pairs with activated advert AND related OtomotoAdvert exists
#     pairs = Pair.objects.filter(
#         # is_otomoto_pair_advert_activated=True,
#         otomoto_advert__isnull=False
#     ).select_related('otomoto_advert').annotate(
#         status_order=Case(
#             When(otomoto_advert__otomoto_advert_status='outdated', then=1),
#             When(otomoto_advert__otomoto_advert_status='unpaid', then=2),
#             When(otomoto_advert__otomoto_advert_status='removed_by_user', then=3),
#             When(otomoto_advert__otomoto_advert_status='active', then=4),
#             default=5,
#             output_field=IntegerField()
#         )
#     ).order_by('status_order', 'created_at')

#     BASE_MEDIA_URL = "https://www.tirgumpanel.pl/media/pair_images"

#     for pair in pairs:
#         main_filename = f"pair_{pair.id}_combined.jpg"
#         pair.main_img = f"{BASE_MEDIA_URL}/{main_filename}"
#         pair.product_ids = list(pair.products.values_list('id', flat=True))

#     paginator = Paginator(pairs, 30)
#     page_number = request.GET.get("page")
#     page_obj = paginator.get_page(page_number)

#     return render(
#         request,
#         "otomoto/active_otomoto_pairs.html",
#         {"page_obj": page_obj}
#     )


# def active_otomoto_pairs(request):

#     pairs = Pair.objects.filter(
#         is_otomoto_pair_advert_activated=True,otomoto_advert__isnull=False).select_related('otomoto_advert').annotate(
#         status_order=Case(
#             When(otomoto_advert__otomoto_advert_status='outdated', then=1),
#             When(otomoto_advert__otomoto_advert_status='unpaid', then=2),
#             When(otomoto_advert__otomoto_advert_status='removed_by_user', then=3),
#             When(otomoto_advert__otomoto_advert_status='active', then=4),
#             default=5,
#             output_field=IntegerField()
#         )
#     ).order_by('status_order', 'created_at')

#     # Ensure every pair has advert data BEFORE select_related
#     # for pair in pairs:
#     #     PairOtoMotoAdvertData.objects.get_or_create(pair=pair)

#     # Refetch with select_related to avoid cached None
#     pairs = Pair.objects.filter(
#         is_otomoto_pair_advert_activated=True,
#     ).select_related('otomoto_advert').order_by('created_at')

#     BASE_MEDIA_URL = "https://www.tirgumpanel.pl/media/pair_images"

#     for pair in pairs:
#         main_filename = f"pair_{pair.id}_combined.jpg"
#         pair.main_img = f"{BASE_MEDIA_URL}/{main_filename}"
#         pair.product_ids = list(pair.products.values_list('id', flat=True))

#     paginator = Paginator(pairs, 30)
#     page_number = request.GET.get("page")
#     page_obj = paginator.get_page(page_number)
    
#     for pair in page_obj:
#         print(pair.pk, getattr(pair.otomoto_advert, 'otomoto_advert_status', None), getattr(pair.otomoto_advert, 'valid_to', None))

#     return render(
#         request,
#         "otomoto/active_otomoto_pairs.html",
#         {"page_obj": page_obj}
#     )


########################

# ACTIVATE OTOMOTO ADS
def activate_otomoto_pair_ads(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    pair_ids = data.get("pair_ids", [])

    if not isinstance(pair_ids, list) or not pair_ids:
        return JsonResponse({"success": False, "error": "No product IDs provided"}, status=400)

    # ensure ints
    pair_ids = [int(pk) for pk in pair_ids if str(pk).isdigit()]

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return JsonResponse({"success": False, "error": "Otomoto auth not configured"}, status=400)

    client = OtomotoClient(auth_data)
    access_token = client.get_valid_access_token()

    pairs_to_activate = Pair.objects.filter(
        id__in=pair_ids,
        is_otomoto_pair_advert_activated=False
    ).select_related('otomoto_advert')
    # print("products_to_activate:", products_to_activate)

    if not pairs_to_activate.exists():
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

    for pair in pairs_to_activate:
        advert_data = getattr(pair, "otomoto_advert", None)
        if not advert_data:
            failed.append({
                "pair_id": pair.id,
                "error": "Otomoto advert data does not exist"
            })
            continue

        otomoto_advert_id = getattr(
            pair.otomoto_advert, "otomoto_advert_id", None)
        print("Otomoto advert ID:", otomoto_advert_id)

        if not otomoto_advert_id:
            failed.append({
                "pair_id": pair.id,
                "pair_advert_id": pair.otomoto_advert_id,
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
                pair.is_otomoto_pair_advert_activated = True
                pair.save(update_fields=["is_otomoto_pair_advert_activated"])
                # Product.objects.filter(id__in=success).update(is_otomoto_advert_activated=True)

                success.append(pair.id)
                print("success:", success)
            else:
                failed.append({
                    "pair_id": pair.id,
                    # "status_code": response.status_code,
                    # "response": response.text
                    "pair_id": pair.id,
                    "error": "Otomoto advert ID missing"
                })
                print("Failed to activate:", response.text)

        except RequestException as e:
            failed.append({
                "pair_id": pair.id,
                "error": str(e)
            })
            print("Exception:", str(e))

    return JsonResponse({
        "success": len(failed) == 0,
        "activated_pairs": success,
        "failed_pairs": failed
    })
#################################################
# DEACTIVATE OTOMOTO ADS

def deactivate_otomoto_pair_ads_manually(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    # product_ids = data.get("product_ids", [])
    pair_ids = data.get("product_ids", [])

    # if not isinstance(product_ids, list) or not product_ids:
    #     return JsonResponse({"success": False, "error": "No product IDs provided"}, status=400)
    
    if not isinstance(pair_ids, list) or not pair_ids:
        return JsonResponse({"success": False, "error": "No product IDs provided"}, status=400)

    # ensure ints
    # product_ids = [int(pk) for pk in product_ids if str(pk).isdigit()]
    pair_ids = [int(pk) for pk in pair_ids if str(pk).isdigit()]
    print("*****************************pair_ids to deactivate:", pair_ids)

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return JsonResponse({"success": False, "error": "Otomoto auth not configured"}, status=400)

    client = OtomotoClient(auth_data)
    access_token = client.get_valid_access_token()

    pairs_to_deactivate = Pair.objects.filter(
        id__in=pair_ids,
        is_otomoto_pair_advert_activated=True
    ).select_related('otomoto_advert')
    # print("products_to_activate:", products_to_activate)
    

    if not pairs_to_deactivate.exists():
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

    for pair in pairs_to_deactivate:
        advert_data = getattr(pair, "otomoto_advert", None)
        if not advert_data:
            failed.append({
                "pair_id": pair.id,
                "error": "Otomoto advert data does not exist"
            })
            continue
        
        otomoto_advert_id = getattr(
            pair.otomoto_advert, "otomoto_advert_id", None)
        
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
                pair.is_otomoto_pair_advert_activated = False
                pair.save(update_fields=["is_otomoto_pair_advert_activated"])
                success.append(pair.id)
                print("success:", success)
            else:
                failed.append({
                    "pair_id": pair.id,
                    "status_code": response.status_code,
                    "response": response.text
                })
                print("Failed to deactivate:", response.text)

        except RequestException as e:
            failed.append({
                "pair_id": pair.id,
                "error": str(e)
            })
            print("Exception:", str(e))

    return JsonResponse({
        "success": len(failed) == 0,
        "deactivated_pairs": success,
        "failed_products": failed
    })
    

##### PROLONG OTOMOTO ADS - SAME AS ACTIVATE FOR NOW, SINCE OTOMOTO DOES NOT HAVE SEPARATE ENDPOINT FOR PROLONGING, IT'S JUST ANOTHER ACTIVATE CALL ONCE EXPIRED

import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from otomoto.models import Pair  # adjust if needed


@require_POST
def prolong_otomoto_pair_ads(request):
    try:
        data = json.loads(request.body)
        pair_ids = data.get("pair_ids", [])

        if not pair_ids:
            return JsonResponse(
                {"success": False, "error": "No pair IDs provided."},
                status=400
            )

        activated_pairs = []
        failed_pairs = []
        
        auth_data = OtomotoAuthData.objects.first()
        if not auth_data:
            return JsonResponse({"success": False, "error": "Otomoto auth not configured"}, status=400)
        
        client = OtomotoClient(auth_data)
        access_token = client.get_valid_access_token()

        base_url = "https://www.otomoto.pl/api/open/account/adverts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        pairs = Pair.objects.filter(
            id__in=pair_ids,
            is_otomoto_pair_advert_activated=True
        )

        for pair in pairs:
            otomoto_advert_id = pair.otomoto_advert.otomoto_advert_id
            
            if not otomoto_advert_id:
                failed_pairs.append(pair.id)
                continue

            activate_url = f"{base_url}/{otomoto_advert_id}/activate"

            try:
                response = requests.post(activate_url, headers=headers)

                if response.status_code in [200, 201, 204]:
                    activated_pairs.append(pair.id)
                else:
                    failed_pairs.append(pair.id)

            except Exception as e:
                print(f"Activation error for pair {pair.id}: {str(e)}")
                failed_pairs.append(pair.id)

        return JsonResponse({
            "success": len(failed_pairs) == 0,
            "activated_pairs": activated_pairs,
            "failed_pairs": failed_pairs,
        })

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": str(e)},
            status=500
        )



# ACTIVATE OTOMOTO ADS IS THIS NECESSARY HERE?
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
        is_otomoto_advert_activated=False
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


#################################################
# CREATE OTOMOTO ADS
def create_otomoto_pair_ads(request):
    print("[DEBUG] create_otomoto_pair_ads called")
    otomoto_ad_client = OtomotoPairAd()

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    pair_ids = data.get("pair_ids", [])

    if not isinstance(pair_ids, list) or not pair_ids:
        return JsonResponse({"success": False, "error": "No product IDs provided"}, status=400)

    # ensure ints
    pair_ids = [int(pk) for pk in pair_ids if str(pk).isdigit()]

    auth_data = OtomotoAuthData.objects.first()
    if not auth_data:
        return JsonResponse({"success": False, "error": "Otomoto auth not configured"}, status=400)

    client = OtomotoClient(auth_data)
    access_token = client.get_valid_access_token()

    pairs_to_create = Pair.objects.filter(
        id__in=pair_ids,
        is_otomoto_pair_advert_created=False
    ).select_related('otomoto_advert')
    # print("products_to_activate:", products_to_activate)

    if not pairs_to_create.exists():
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

    for pair in pairs_to_create:
        # Ensure otomoto_advert exists
        advert_data, created = PairOtoMotoAdvertData.objects.get_or_create(
            pair=pair,
            # defaults={
            # set required default fields here if any
            # example:
            # "status": "draft",
            # }
        )

        payload = otomoto_ad_client.prepare_pair_advert_data(pair)

        activate_url = "https://www.otomoto.pl/api/open/account/adverts"

        try:
            response = requests.post(
                base_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 201:
                data = response.json()
                otomoto_advert_id = data.get("id")

                if not otomoto_advert_id:
                    failed.append({
                        "pair_id": pair.id,
                        "error": "Missing advert ID in response",
                        "response": data
                    })
                    continue

                advert_data.otomoto_advert_id = otomoto_advert_id
                advert_data.save(update_fields=["otomoto_advert_id"])

                pair.is_otomoto_pair_advert_created = True
                pair.save(update_fields=["is_otomoto_pair_advert_created"])

                success.append(pair.id)

            else:
                failed.append({
                    "pair_id": pair.id,
                    "status_code": response.status_code,
                    "response": response.text
                })

        except RequestException as e:
            failed.append({
                "pair_id": pair.id,
                "error": str(e)
            })

    return JsonResponse({
        "success": True if success else False,
        "created": success,
        "failed": failed,
    })

    #     try:
    #         response = requests.post(
    #             activate_url,
    #             headers=headers,
    #             json=payload,  # Otomoto expects empty body
    #             timeout=10
    #         )

    #         if response.status_code in (200, 204, 201):
    #             pair.is_otomoto_pair_advert_created = True
    #             pair.save(update_fields=["is_otomoto_pair_advert_created"])
    #             # Product.objects.filter(id__in=success).update(is_otomoto_advert_activated=True)

    #             success.append(pair.id)
    #             print("success:", success)
    #         else:
    #             failed.append({
    #                 "pair_id": pair.id,
    #                 # "status_code": response.status_code,
    #                 # "response": response.text
    #                 "pair_id": pair.id,
    #                 "error": "Otomoto advert ID missing"
    #             })
    #             print("Failed to create:", response.text)

    #     except RequestException as e:
    #         failed.append({
    #             "pair_id": pair.id,
    #             "error": str(e)
    #         })
    #         print("Exception:", str(e))

    # return JsonResponse({
    #     "success": len(failed) == 0,
    #     "created_pairs": success,
    #     "failed_pairs": failed
    # })
