# is_allegro_active
from tyreadderapp.models import Product
from allegro.models import Allegroauthdata, AllegroAdvertData
from allegro.client.client import AllegroClient
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import Http404,HttpResponse, JsonResponse
from tyreadderapp.models import Product
import logging
import json
from allegro.client.services import AllegroAuthService
from django.db.models import Exists, OuterRef
from tyreadderapp.models import Image
import requests
from django.utils.dateparse import parse_datetime





logger = logging.getLogger(__name__)





ALLEGRO_UPLOAD_URL = "https://upload.allegro.pl/sale/images"

def upload_images(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    data = json.loads(request.body)
    product_ids = data.get("product_ids", [])

    products = Product.objects.filter(id__in=product_ids).prefetch_related("images")

    # Use AllegroClient for robust token handling
    auth_data = Allegroauthdata.objects.first()
    if not auth_data:
        return JsonResponse({"error": "Allegro not connected"}, status=400)

    client = AllegroClient(auth_data)
    try:
        access_token = client.get_valid_access_token()
    except Exception as e:
        return JsonResponse({"error": f"Failed to get valid token: {str(e)}"}, status=500)
    
    logger.info("Full Allegro access token: %s", access_token)

    headers = {
        "Accept": "application/vnd.allegro.public.v1+json",
        "Accept-Language": "pl-PL",
        "Content-Type": "application/vnd.allegro.public.v1+json",
        "Authorization": f"Bearer {access_token}",
    }

    results = []

    for product in products:
        for img in product.images.all():
            image_url = request.build_absolute_uri(img.image.url)
            try:
                response = requests.post(
                    ALLEGRO_UPLOAD_URL,
                    headers=headers,
                    json={"url": image_url},
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()

                allegro_url = data.get("location")
                expires_at = parse_datetime(data.get("expiresAt"))

                img.allegro_image_url = allegro_url
                img.allegro_expires_at = expires_at
                img.save(update_fields=["allegro_image_url", "allegro_expires_at"])

                results.append({
                    "image_id": img.id,
                    "allegro_url": allegro_url,
                    "expires_at": expires_at,
                })

            except requests.HTTPError:
                results.append({
                    "image_id": img.id,
                    "error": response.text,
                })
            except Exception as e:
                results.append({
                    "image_id": img.id,
                    "error": f"Unexpected error: {str(e)}",
                })

    return JsonResponse({"results": results})




def inactive_allegro(request):
    products = Product.objects.filter(status=Product.StatusChoices.ON_SALE).prefetch_related('images')

    # Subquery: checks if there exists an image for this product with allegro_image_url not null
    uploaded_images = Image.objects.filter(product=OuterRef('pk'), allegro_image_url__isnull=False)
    products = products.annotate(
        has_uploaded_image=Exists(uploaded_images)
    ).order_by('-has_uploaded_image', 'id')  # Products with uploaded images first
    
    
    paginator = Paginator(products, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    auth_data = Allegroauthdata.objects.first()
    if not auth_data:
        return HttpResponse("Allegro auth data missing", status=500)

    # Create client and ensure token is valid
    try:
        allegro_client = AllegroClient(auth_data)
        allegro_client.ensure_authenticated()
    except Exception:
        logger.exception("Failed to authenticate with Allegro")
        return HttpResponse("Allegro authentication failed", status=500)



    return render(request, "allegro/inactive_allegro.html", {
        "page_obj": page_obj,
        # "allegro_products": allegro_products,
    })
    


def active_allegro(request):
    # Get Allegro auth data
    auth_data = Allegroauthdata.objects.first()
    if not auth_data:
        return HttpResponse("Allegro auth data missing", status=500)
    
    # Create Allegro client and ensure token is valid
    try:
        allegro_client = AllegroClient(auth_data)
        allegro_client.ensure_authenticated()
    except Exception as e:
        logger.exception("Failed to authenticate with Allegro")
        return HttpResponse("Allegro authentication failed", status=500)

    # Fetch active offers from Allegro
    try:
        active_offer_ids = allegro_client.get_active_offer_ids()
        
        # Optionally, fetch full offer details if needed
        access_token = allegro_client.get_valid_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json",
        }

        offers = []
        for offer_id in active_offer_ids:
            url = f"https://api.allegro.pl/sale/offers/{offer_id}"
            resp = allegro_client.session.get(url, headers=headers)
            resp.raise_for_status()
            offers.append(resp.json())

    except Exception as e:
        logger.exception("Failed to fetch offers from Allegro API")
        return HttpResponse(f"Failed to fetch offers: {str(e)}", status=500)

    return render(request, "allegro/active_allegro.html", {
        "offers": offers
    })




def delete_draft(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    data = json.loads(request.body)
    product_ids = data.get("product_ids", [])

    products = Product.objects.filter(id__in=product_ids)

    auth_data = Allegroauthdata.objects.first()
    if not auth_data:
        return JsonResponse({"error": "Allegro not connected"}, status=400)

    client = AllegroClient(auth_data)
    try:
        access_token = client.get_valid_access_token()
    except Exception as e:
        return JsonResponse({"error": f"Failed to get valid token: {str(e)}"}, status=500)

    headers = {
        "Accept": "application/vnd.allegro.public.v1+json",
        "Accept-Language": "pl-PL",
        "Content-Type": "application/vnd.allegro.public.v1+json",
        "Authorization": f"Bearer {access_token}",
    }

    DELETE_DRAFT_URL = "https://api.allegro.pl/sale/offers/{}"

    results = []

    for product in products:
        try:
            advert = product.allegro_single_advert_data
        except AllegroAdvertData.DoesNotExist:
            results.append({
                "product_id": product.id,
                "status": "no_advert_data"
            })
            continue

        offer_id = advert.allegro_advert_id
        if not offer_id:
            results.append({
                "product_id": product.id,
                "status": "no_offer_id"
            })
            continue

        url = DELETE_DRAFT_URL.format(offer_id)

        try:
            response = requests.delete(url, headers=headers)

            if response.status_code in [200, 204]:
                results.append({
                    "product_id": product.id,
                    "offer_id": offer_id,
                    "status": "deleted"
                })

                # Optional: clear local data
                advert.allegro_advert_id = None
                advert.status = "deleted"
                advert.save()

            else:
                results.append({
                    "product_id": product.id,
                    "offer_id": offer_id,
                    "status": "error",
                    "response": response.text
                })

        except Exception as e:
            results.append({
                "product_id": product.id,
                "offer_id": offer_id,
                "status": "exception",
                "error": str(e)
            })

    return JsonResponse({"results": results})



from .single_description import get_product_description  # assuming your function is here

def update_ads(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    product_ids = data.get("product_ids", [])
    if not product_ids:
        return JsonResponse({"error": "No product IDs provided"}, status=400)

    products = Product.objects.filter(id__in=product_ids)

    auth_data = Allegroauthdata.objects.first()
    if not auth_data:
        return JsonResponse({"error": "Allegro not connected"}, status=400)

    client = AllegroClient(auth_data)
    try:
        access_token = client.get_valid_access_token()
    except Exception as e:
        return JsonResponse({"error": f"Failed to get valid token: {str(e)}"}, status=500)

    results = []

    headers = {
        "Accept": "application/vnd.allegro.public.v1+json",
        "Accept-Language": "pl-PL",
        "Content-Type": "application/vnd.allegro.public.v1+json",
        "Authorization": f"Bearer {access_token}",
    }

    for product in products:
        try:
            advert_data = product.allegro_single_advert_data
        except AllegroAdvertData.DoesNotExist:
            results.append({
                "product_id": product.id,
                "status": "error",
                "message": "No Allegro advert data found"
            })
            continue

        if not advert_data.allegro_advert_id:
            results.append({
                "product_id": product.id,
                "status": "error",
                "message": "No Allegro offer ID"
            })
            continue

        # Build the dynamic description
        description_json = get_product_description(product)

        url = f"https://api.allegro.pl/sale/product-offers/{advert_data.allegro_advert_id}"

        response = requests.patch(url, headers=headers, json={"description": description_json})

        if response.status_code == 200:
            results.append({
                "product_id": product.id,
                "status": "success",
                "message": "Description updated successfully"
            })
        else:
            results.append({
                "product_id": product.id,
                "status": "error",
                "message": response.json()
            })

    return JsonResponse({"results": results})