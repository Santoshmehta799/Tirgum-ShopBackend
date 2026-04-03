from ..base import OtomotoClientBase
from otomoto.models import OtoMotoAdvertData

from django.utils import timezone
import requests
from otomoto.api_brands import api_brands
from otomoto.parsers import extract_aspect_ratio, extract_rim_diameter, extract_tire_width, extract_tyre_inches, extract_tyre_profile
from tyreadderapp.models import Image
import logging
# from ..auth import OtomotoAuthMixin
# from otomoto.client.otomoto_client import OtomotoClient
from otomoto.client.auth import OtomotoAuthMixin

logger = logging.getLogger(__name__)

class OtomotoSingleAd(OtomotoAuthMixin):   
    
            
    def prepare_advert_data(self, product):
        # print("******Preparing advert data...")
        from .description import create_otomoto_advert_description
        """
        Tworzy słownik gotowy do wysłania do Otomoto API na podstawie obiektu Product.
        Struktura została dopasowana do przykładowej odpowiedzi Otomoto.
        """
        domain = f"{OtomotoClientBase.domain}"
        
        images = list(Image.objects.filter(product=product)[:9])

        # Sort so the image ending with '1.jpg' comes first
        images.sort(
            key=lambda item: not item.image.url.endswith("1.jpg")
        )

        all_images = {
            str(i + 1): domain + item.image.url
            for i, item in enumerate(images)
        }

        
        # IMAGES LOGIC
        all_images = {str(i+1): domain + item.image.url 
              for i, item in enumerate(Image.objects.filter(product=product)[:9])}


        # all_images = {
        #     "1": "https://tirgumpanel.pl/media/images/Goodyear-KMAX_S_GEN-2-315-70_R22.5-171-8_9j3mpvn.jpg",
        #     "2": "https://tirgumpanel.pl/media/images/Goodyear-KMAX_S_GEN-2-315-70_R22.5-171-6.jpg",
        #     "3": "https://tirgumpanel.pl/media/images/Goodyear-KMAX_S_GEN-2-315-70_R22.5-171-8_JHzCels.jpg"
        # }

        # --- BRAND SELECTION LOGIC ---
        # brand = (product.brand or "").strip().lower()
        brand = (getattr(product.brand, "name", "") or "").strip().lower()
        api_brands_set = {b.lower() for b in api_brands}
        tire_brand = brand if brand in api_brands_set else "others"

        size_value = str(product.size) if product.size else ""
        tyres_inches = str(extract_tyre_inches(size_value))
        tyres_profile = str(extract_tyre_profile(size_value))
        tread = product.tread_name if product.tread_name else ""

        advert_data = {
            
            "description":create_otomoto_advert_description(product),
            "images": all_images,
            # "category_id": 163,
            "region_id": 6,
            "city_id": 60821,
            # "district_id":0,
            # "names":"Części",


            "municipality": "Tworóg",
            "city": {
                "pl": "Boruszowice",
                "en": "Boruszowice"
            },
            # "street": "ul. Armii Krajowej 6",
            # "postal_code":"42-690",

            "coordinates": {
                
                "latitude": 50.51188,
                "longitude": 18.77311,
                "radius": 0,
                "zoom_level": 12
            },

            "advertiser_type": "business",

            
            "contact": {
                "name": "Tirgum Mateusz Celej",
                "phone": "733-456-474",
            },

            "params": {
                "title": str(product.advert_title[:70]) if product.advert_title else "",
                "delivery": "1",
                "parts-category": "opony",  # ???????
                "parts-type": "opony",
                
                "price": {
                    "0": "price",
                    # "1": float(product.net_price) * 1.23 if product.net_price else 0,
                    "1": float(product.net_price),
                    "currency": "PLN",
                    "gross_net": "net"
                },

                
                "tire-brand": tire_brand,
                # "tire-width": extract_tire_width(size_value),
                "tire-width": extract_tire_width(size_value) or None,
                "height-aspect-ratio": extract_aspect_ratio(size_value),
                "tyres-inches":tyres_inches,
                "tyres-profile":tyres_profile,
            },
            
            "new_used": "used",
            "category_id": 167,
            "visible_in_profile": "1",
        }
        print(f"******Prepared advert data: {advert_data}")
        return advert_data
    
    
    def create_and_save_advert(self, product):
        print("******Creating and saving advert...")
        """
        Creates an advert on Otomoto and saves the advert ID and status to the Product.
        Provides detailed error logging for failed POST requests.
        """
        advert_data = self.prepare_advert_data(product)
        # auth = OtomotoAuthMixin()

        try:
        # Make sure token is valid / refreshed
            self.ensure_authenticated()
        
        # Get the latest access token
            access_token = self.get_valid_access_token()
            print(f"used_access_token: {access_token}")
        except Exception as e:
            print(f"[ERROR] Failed to obtain access token: {e}")
            return None


        # Update session headers once
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'User-Agent': OtomotoAuthMixin.OTOMOTO_USERNAME
        })

        adverts_url = "https://www.otomoto.pl/api/open/account/adverts"

        try:
            response = self.session.post(
                adverts_url,
                json=advert_data,
                timeout=15
            )

        # Raise exception for 4xx/5xx
            response.raise_for_status()

        # Try parsing JSON
            try:
                data = response.json()
            except ValueError:
                print(
                    f"[ERROR] Non-JSON response received for product {product.id}")
                print(f"Response body: {response.text}")
                return None

    # -------------------------------
    # Network / Request exceptions
    # -------------------------------
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] Request timed out for product {product.id}.")
            return None

        except requests.exceptions.ConnectionError as e:
            print(f"[CONNECTION ERROR] Failed to connect: {e}")
            return None

        except requests.exceptions.HTTPError as e:
            # Server returned 4xx or 5xx
            print(
                f"[HTTP ERROR] Failed to create advert for product {product.id}: {e}")
            print(f"Status code: {response.status_code}")
            print(f"Response body: {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            # Catch-all for unexpected errors
            print(
                f"[REQUEST ERROR] Unexpected error for product {product.id}: {e}")
            return None

    # -------------------------------
    # Successful case
    # -------------------------------

        # otomoto_advert_id = data.get("id")
        # otomoto_advert_status = str(
        #     data.get("status")) if "status" in data else None

        created_at_str = data.get("created_at")
        valid_to_str = data.get("valid_to")
        otomoto_advert_status = data.get("status")
        otomoto_advert_id = data.get("id")

        from django.utils.dateparse import parse_datetime
        # Example field names from Otomoto API - verify what they return!

        product.save()

        def make_aware_if_needed(dt):
            if dt and timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return dt

        created_at = make_aware_if_needed(parse_datetime(created_at_str))
        valid_to = make_aware_if_needed(parse_datetime(valid_to_str))

        # Save OtoMotoAdvertData
        OtoMotoAdvertData.objects.update_or_create(
            product=product,
            defaults={
                "otomoto_advert_id": otomoto_advert_id,
                "created_at": created_at,
                "valid_to": valid_to,
                "otomoto_advert_status": otomoto_advert_status,
            }
        )

        return data
