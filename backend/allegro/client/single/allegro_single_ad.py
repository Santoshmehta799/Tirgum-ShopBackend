from django.utils import timezone

from .tyre_data import widths, profiles, diameters


from .single_description import get_product_description
# from .description import create_allegro_advert_description
from allegro.client.client import AllegroClient
import requests
from allegro.models import Allegroauthdata
import logging
import json
from django.http import JsonResponse
from tyreadderapp.models import Product
from allegro.models import AllegroAdvertData
from django.utils.dateparse import parse_datetime
from ..policies import fetch_return_policy, fetch_implied_warranties, fetch_warranties
from .single_description import get_product_description


logger = logging.getLogger(__name__)


# def get_ean(product):
#     return [str(product.ean) if hasattr(product, 'ean') and product.ean else ""]

def get_ean(product):
    if hasattr(product, 'ean') and product.ean:
        return [str(product.ean)]
    return [""]


def get_width_field(product):
    target_width = str(product.size.width)
    width_info = next(
        (item for item in widths if item["width"] == target_width), None)

    if width_info:
        return [f"345_{width_info['id']}"]
    else:
        return ["345_inna"]


def get_profile_field(product):
    target_profile = str(product.size.profile)
    profile_info = next(
        (item for item in profiles if item["profile"] == target_profile), None)
    if profile_info:
        return [f"344_{profile_info['id']}"]
    else:
        return [f"344_inny"]


def get_diameter_field(product):
    # remove trailing zeros
    target_diameter = str(product.size.diameter.normalize())
    diameter_info = next(
        (item for item in diameters if item["diameter"] == target_diameter),
        None
    )
    if diameter_info:
        return [diameter_info["id"]]
    else:
        # fallback to "Inna"
        inna = next(item for item in diameters if item["diameter"] == "Inna")
        return [inna["id"]]




def get_dot_info(product):
    if not product.dot:
        return None

    dot = int(product.dot)

    if dot < 100:  # 2-digit year
        year = 2000 + dot
    else:
        year = dot

    return [year]


def get_axis(axis):
    # Mapping from keys to output dictionaries
    axis_map = {
        "is_trailer": "24209_4",
        "is_drive": "24209_2",
        "is_steer": "24209_1",
        "is_all": "24209_8"
    }

    # Determine which key to return
    if all(axis.values()):
        return [axis_map["is_all"]]

    for key, value in axis.items():
        if value:
            return [axis_map[key]]

    return None  # If none are True


def get_additional_info(product):
    values = []
    if product.tread.is_3pmsf:
        values.append("200981_868933")
    if product.tread.is_m_s:
        values.append("200981_1798534")
    return values


def get_images(product):
    return list(
        product.images
        .filter(allegro_image_url__isnull=False)
        .exclude(allegro_image_url='')
        .values_list('allegro_image_url', flat=True)
    )


def prepare_allegro_advert_data(product, return_policy, implied_warranty, warranty):
    product_id = product.id
    product_name = product.advert_title
    brand = product.brand.name
    allegro_brand_id = product.brand.allegro_brand_id
    allegro_brand_value = product.brand.name.capitalize()
    model = product.tread.name
    category_id = "257701"
    net_price = str(product.net_price)
    stock = 1
    domain = "tirgumpanel.pl"
    is_retreaded = product.is_retreaded
    # ean = product.ean if product.ean else None
    dot = product.dot if product.dot else None
    is_3pmsf = product.tread.is_3pmsf
    is_m_s = product.tread.is_m_s

    profile = product.size.profile
    diameter = float(product.size.diameter)
    axis = {
        "is_steer": product.tread.is_steer,
        "is_drive": product.tread.is_drive,
        "is_trailer": product.tread.is_trailer
    }
    after_sales_services = {
        "impliedWarranty": implied_warranty or {"id": "default_implied_id"},
        "returnPolicy": return_policy or {"id": "default_return_id"},
        "warranty": warranty or {"id": "default_warranty_id"}
    }

    parameters = [

        {
            "id": "248811",
            "valuesIds": [product.brand.allegro_brand_id],
        },
        {
            "id": "237206",
            "name": "Model",
            "values": [model],  # używane
        },
        {
            "id": "345",
            # "name": "Szerokość opony",
            "valuesIds": get_width_field(product)
        },
        {
            "id": "344",
            "name": "Profil opony",
            "valuesIds": get_profile_field(product)
        },
        {
            "id": "127088",
            "name": "Średnica",
            "valuesIds": get_diameter_field(product)
        },

        {
            "id": "24209",
            "name": "Oś",
            "valuesIds": get_axis(axis),
        },
        {
            "id": "200981",
            "name": "Informacje dodatkowe",
            "valuesIds": get_additional_info(product),
        },
        {
            "id": "225693",
            "name": "EAN",
            "values": get_ean(product)
        }

    ]
    

    offer_parameters = [
        {
            "id": "11323",
            "valuesIds": ["11323_2"]
        },
        {
            "id": "128844",
            "name": "Liczba opon w ofercie",
            # Convert width to string
            "valuesIds": ["128844_1"]
        },

    ]

    dot_values = get_dot_info(product)
    if dot_values:
        offer_parameters.append({
            "id": "249825",
            # "name": "Rok produkcji",
            "values": dot_values
        })

    

    payload = {
        "productSet": [
            {
                "product": {
                    "name": product_name,  # max 75 characters
                    "category": {
                        "id": category_id,
                    },
                    "parameters": parameters,

                    "images": get_images(product)
                },
                "quantity": {
                    "value": 1
                },
                
                "safetyInformation": {
                    "type": "TEXT",
                    "description": "Example safety information for the product"
                },
                
                "marketedBeforeGPSRObligation": False,                
            }
        ],






        "b2b": {
            "buyableOnlyByBusiness": False
        },
        "stock": {
            "available": 1,
            "unit": "UNIT"
        },
        "delivery": {
            "handlingTime": "PT24H",
            "shippingRates": {
                "id": "6e6cbc6a-a186-4a38-a001-e7d9ec59687c",
                # "name": "europaleta 100 kg",
                # "marketplaces": [
                #     {
                #         "id": "allegro-pl"
                #     },
                #     {
                #         "id": "allegro-business-pl"
                #     }
                # ],
                # "features": {
                #     "managedByAllegro": False,
                #     "isFulfillment": False
                # }
            },
            # "additionalInfo": "Example additional info",
            # "shipmentDate": "2019-08-24T14:15:22Z"
            },
        # "delivery": {
        #     "handlingTime": "PT24H",
        #     "shippingRates": {
        #         "id": "6e6cbc6a-a186-4a38-a001-e7d9ec59687c"
        #     },
        #     "additionalInfo": "Example additional info",
        #     "shipmentDate": "2019-08-24T14:15:22Z"
        # },
        
        # "additionalMarketplaces": {
        #     "allegro-cz": {
        #         "sellingMode": {
        #             "price": {
        #                 "amount": "233.01",
        #                 "currency": "CZK"
        #             }
        #         }
        #     }
        # },
        # "compatibilityList": {
        #     "items": [
        #         {
        #             "type": "TEXT",
        #             "text": "CITROËN C6 (TD_) 2005/09-2011/12 2.7 HDi 204KM/150kW"
        #         }
        #     ]
        # },
        "language": "pl-PL",
        # "category": {
        #     "id": "257931"
        # },
        "name": product_name,
        "parameters": offer_parameters,

        "afterSalesServices": after_sales_services,
        # "sizeTable": {
        #     "id": "string",
        #     "name": "Nike shoes size table"
        # },
        # "contact": {
        #     "id": "11a2df7f-8237-4625-baa2-cb7541f39946",
        #     "name": "Piotr"
        # },
        # "discounts": {
        #     "wholesalePriceList": {
        #         "id": "5637592a-0a24-4771-b527-d89b2767d821",
        #         "name": "Wholesale example"
        #     }
        # },
        "payments": {
            "invoice": "VAT"
        },
        "sellingMode": {
            "format": "BUY_NOW",
            "price": {
                "amount": net_price,
                "currency": "PLN"
            },
            "minimalPrice": {
                "amount": "123.45",
                "currency": "PLN"
            },
            "startingPrice": {
                "amount": "123.45",
                "currency": "PLN"
            }
        },
        "location": {
            "city": "Boruszowice",
            "countryCode": "PL",
            "postCode": "42-690",
            "province": "SLASKIE"
        },

        # "images": "[\"https://a.allegroimg.com/original/12068b/359d04074521b79df1b2807a6727\"]",
        "description": get_product_description(product),
        "external": {
            "id": product_id
        },
        # "publication": {      
        #     "status": "DRAFT",            
        # },
        # "taxSettings": {
        #     "rates": [
        #         {
        #             "rate": "23.00",
        #             "countryCode": "PL",
        #         }
        #         ],
        #     "subject": "GOODS",
        #     "exemption": "MONEY_EQUIVALENT"
        #     }
            # "subject": "GOODS",
            # "exemption": "NONE"
        
        # "messageToSellerSettings": {
        #     "mode": "OPTIONAL",
        #     "hint": "Choose size"
        # }
    }
    # --------------------------------------------
    # LOGGER: Check types of critical fields to catch 422 errors
    try:
        images = payload["productSet"][0]["product"]["images"]
        # parameters = payload["productSet"][0]["product"]["parameters"]
        parameters = payload["productSet"][0]["product"]["parameters"]

        logger.debug(
            "Images type: %s, element types: %s",
            type(images),
            [type(url) for url in images]
        )

        for param in parameters:
            if "valuesIds" in param:
                logger.debug(
                    "Parameter '%s' valuesIds type: %s, element types: %s",
                    param["name"],
                    type(param["valuesIds"]),
                    [type(v) for v in param["valuesIds"]]
                )
            if "values" in param:
                logger.debug(
                    "Parameter '%s' values type: %s, element types: %s",
                    param["name"],
                    type(param["values"]),
                    [type(v) for v in param["values"]]
                )
    except Exception as e:
        logger.exception("Error while logging payload types: %s", e)
    logger.debug(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def create_advert_for_product(product):
    """
    Creates an advert on Otomoto and saves the advert ID and status to the Product.
    Provides detailed error logging for failed POST requests.
    """
    logger.info("Creating advert for product %s", product.id)
    # advert_data = prepare_allegro_advert_data(product)

    # Get the first auth record (assuming single-user setup)
    auth_data = Allegroauthdata.objects.first()
    if not auth_data:
        logger.error("No Allegro auth data found")
        return None

    client = AllegroClient(auth_data)

    try:
        # Make sure token is valid / refreshed
        client.ensure_authenticated()
        access_token = client.get_valid_access_token()
        return_policy = fetch_return_policy(access_token)
        implied_warranty = fetch_implied_warranties(access_token)
        warranty = fetch_warranties(access_token)
        logger.debug("Access token and return policy obtained")
    except Exception as e:
        logger.exception("Failed to obtain access token or return policy")
        return None

    # Build the payload with the dynamic return policy
    advert_data = prepare_allegro_advert_data(
        product, return_policy, implied_warranty, warranty)

    # Set headers for POST request
    session = requests.Session()
    # session.headers.update({
    #     'Authorization': f'Bearer {access_token}',
    #     'Content-Type': 'application/json',
    #     "Accept": "application/vnd.allegro.public.v1+json",
    #     "Accept-Language": "pl-PL",
    # })
    session.headers.update({
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "Content-Type": "application/vnd.allegro.public.v1+json",
        "Accept-Language": "pl-PL",
    })

    # adverts_url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"
    adverts_url = "https://api.allegro.pl/sale/product-offers"
    # adverts_url = "https://api.allegro.pl/sale/offers"

    # https://api.allegro.pl/sale/product-offers

    try:
        response = session.post(
            adverts_url,
            json=advert_data,
            timeout=15
        )
        logger.info("Allegro response status: %s", response.status_code)

        # Handle successful responses
        if response.status_code in (201, 202):

            try:
                data = response.json()
            except ValueError:
                logger.error(
                    "Invalid JSON response from Allegro: %s", response.text)
                logger.info(response.status_code)
                return {"success": False, "status": response.status_code}

            publication = data.get("publication", {})

            AllegroAdvertData.objects.update_or_create(
                product=product,
                defaults={
                    "allegro_advert_id": data.get("id"),
                    "created_at": data.get("createdAt"),
                    "updated_at": data.get("updatedAt"),
                    "status": publication.get("status") or "UNKNOWN",
                    "valid_to": publication.get("endingAt"),
                    "raw_response": data,
                }
            )

            logger.info(
                "Saved Allegro advert data for product %s (advert_id=%s)",
                product.id,
                data.get("id"),
            )
            return {"success": True, "status": response.status_code, "data": data}

        # Handle client / server errors
        elif response.status_code in (400, 403, 422):
            try:
                return {"success": False, "status": response.status_code, "errors": response.json().get("errors")}
            except ValueError:
                return {"success": False, "status": response.status_code, "errors": "Invalid JSON in response"}

        # Handle unauthorized
        elif response.status_code == 401:
            try:
                return {"success": False, "status": 401, "error": response.json()}
            except ValueError:
                return {"success": False, "status": 401, "error": "Unauthorized access"}

        else:
            # Unexpected status
            logger.warning("Unexpected response for product %s: %s",
                           product.id, response.text)
            return {"success": False, "status": response.status_code, "response_text": response.text}

    # -------------------------------
    # Network / Request exceptions
    # -------------------------------
    except requests.exceptions.Timeout:
        logger.error(
            "Timeout while creating advert for product %s", product.id)
        return {"success": False, "error": "Timeout", "product_id": product.id}

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error for product %s: %s", product.id, e)
        return {"success": False, "error": f"ConnectionError: {e}", "product_id": product.id}

    except requests.exceptions.RequestException as e:
        logger.error("Request exception for product %s: %s", product.id, e)
        return {"success": False, "error": f"RequestException: {e}", "product_id": product.id}


def create_ad(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    product_ids = body.get("product_ids", [])

    results = []

    for product in Product.objects.filter(id__in=product_ids):
        try:
            result = create_advert_for_product(product)
        except Exception as e:
            result = {
                "success": False,
                "product_id": product.id,
                "error": str(e)
            }
        results.append(result)

    return JsonResponse({"results": results})


# def create_advert_for_product(product):
#     """
#     Creates an advert on Otomoto and saves the advert ID and status to the Product.
#     Provides detailed error logging for failed POST requests.
#     """
#     logger.info("Creating advert for product %s", product.id)
#     advert_data = prepare_allegro_advert_data(product)

#     # Get the first auth record (assuming single-user setup)
#     auth_data = Allegroauthdata.objects.first()
#     if not auth_data:
#         logger.error("No Allegro auth data found")
#         return None

#     client =AllegroClient(auth_data)

#     try:
#         # Make sure token is valid / refreshed
#         client.ensure_authenticated()
#         access_token = client.get_valid_access_token()
#         logger.debug("Access token obtained")
#     except Exception as e:
#         logger.exception("Failed to obtain access token")
#         return None

#     # Set headers for POST request
#     session = requests.Session()
#     session.headers.update({
#         'Authorization': f'Bearer {access_token}',
#         'Content-Type': 'application/json',
#         "Accept-Language": "pl-PL",
#     })

#     adverts_url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"

#     # https://api.allegro.pl/sale/product-offers


#     try:
#         response = session.post(
#             adverts_url,
#             json=advert_data,
#             timeout=15
#         )
#         logger.info("Allegro response status: %s", response.status_code)

#         # Handle successful responses
#         if response.status_code in (201, 202):
#             return {"success": True, "status": response.status_code, "data": response.json()}

#         # Handle client / server errors
#         elif response.status_code in (400, 403, 422):
#             try:
#                 return {"success": False, "status": response.status_code, "errors": response.json().get("errors")}
#             except ValueError:
#                 return {"success": False, "status": response.status_code, "errors": "Invalid JSON in response"}

#         # Handle unauthorized
#         elif response.status_code == 401:
#             try:
#                 return {"success": False, "status": 401, "error": response.json()}
#             except ValueError:
#                 return {"success": False, "status": 401, "error": "Unauthorized access"}

#         else:
#             # Unexpected status
#             logger.warning("Unexpected response for product %s: %s", product.id, response.text)
#             return {"success": False, "status": response.status_code, "response_text": response.text}


#     # -------------------------------
#     # Network / Request exceptions
#     # -------------------------------
#     except requests.exceptions.Timeout:
#         logger.error("Timeout while creating advert for product %s", product.id)
#         return {"success": False, "error": "Timeout", "product_id": product.id}

#     except requests.exceptions.ConnectionError as e:
#         logger.error("Connection error for product %s: %s", product.id, e)
#         return {"success": False, "error": f"ConnectionError: {e}", "product_id": product.id}


#     except requests.exceptions.RequestException as e:
#         logger.error("Request exception for product %s: %s", product.id, e)
#         return {"success": False, "error": f"RequestException: {e}", "product_id": product.id}

    # -------------------------------
    # Successful case
    # -------------------------------

    # created_at_str = data.get("created_at")
    # valid_to_str = data.get("valid_to")
    # otomoto_advert_status = data.get("status")
    # otomoto_advert_id = data.get("id")

    # from django.utils.dateparse import parse_datetime

    # product.save()

    # def make_aware_if_needed(dt):
    #     if dt and timezone.is_naive(dt):
    #         return timezone.make_aware(dt, timezone.get_current_timezone())
    #     return dt

    # created_at = make_aware_if_needed(parse_datetime(created_at_str))
    # valid_to = make_aware_if_needed(parse_datetime(valid_to_str))

    # # Save OtoMotoAdvertData
    # OtoMotoAdvertData.objects.update_or_create(
    #     product=product,
    #     defaults={
    #         "otomoto_advert_id": otomoto_advert_id,
    #         "created_at": created_at,
    #         "valid_to": valid_to,
    #         "otomoto_advert_status": otomoto_advert_status,
    #     }
    # )

    # return data


def republish_ended_offers():
    ended_offers = AllegroAdvertData.objects.filter(status="ENDED")

    for advert in ended_offers:
        product = advert.product

        result = create_advert_for_product(product)

        if result and result.get("success"):
            logger.info(
                "Republished product %s with new advert",
                product.id
            )
        else:
            logger.warning(
                "Failed to republish product %s",
                product.id
            )
