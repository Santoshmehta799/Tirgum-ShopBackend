from ..single.otomoto_single_ad import OtomotoSingleAd
from django.utils import timezone
import requests
from otomoto.parsers import extract_aspect_ratio, extract_rim_diameter, extract_tire_width, extract_tyre_inches, extract_tyre_profile
from otomoto.api_brands import api_brands
from otomoto.models import PairOtoMotoAdvertData
from tyreadderapp.models import Product, Image, PairImage
import logging
from django.utils.dateparse import parse_datetime
import json
import logging
from django.utils.dateparse import parse_datetime


logger = logging.getLogger(__name__)

    
    
class OtomotoPairAd(OtomotoSingleAd):
    # def get_pair_brand(self, pair):
    #     pass
    
    # def get_pair_title(self, pair):
    #     pass
    
    def get_images(self, pair):
        domain = "https://www.tirgumpanel.pl"
        BASE_MEDIA_URL = "https://www.tirgumpanel.pl/media/pair_images"
        
        main_img = PairImage.objects.filter(pair=pair).first()
        
               
        all_images = {}

        index_counter = 1  # start indexing from 1

        # Add main image first, if it exists
        if main_img:
            filename = f"pair_{pair.id}_combined.jpg"
            main_img_url = f"{BASE_MEDIA_URL}/{filename}"
            # all_images[str(index_counter)] = domain + main_img.image.url
            all_images[str(index_counter)] = main_img_url
            index_counter += 1
        
        # print(f"all_images----{all_images[1]}")

        # Get all products in the pair
        products = list(Product.objects.filter(pair=pair))
        num_products = len(products)

        images_per_product = 1
        if num_products == 2:
            images_per_product = 3
        elif num_products == 4:
            images_per_product = 2
        elif num_products == 6:
            images_per_product = 1
        elif num_products == 8:
            images_per_product = 1  # special logic below

        for idx, product in enumerate(products):
            # Special rules
            if num_products == 4 and idx == num_products - 1:
                limit = 1
            elif num_products == 8 and idx >= 7:
                break
            else:
                limit = images_per_product

            product_images = product.images.order_by('id')[:limit]

            for img in product_images:
                all_images[str(index_counter)] = domain + img.image.url
                index_counter += 1
        print(f"++++++++all images {all_images}")
        return all_images
    
    def get_otomoto_pair_title(self, pair):
        """
        Builds advert title based on product data.
        If quantity == 2, title length <55 and any tread >80,
        adds 'Okazja' at the beginning and appends tread %.
        If result exceeds 70 chars, removes 'Okazja'.
        Otherwise adds 'Komplet opon'.
        Max length: 70 chars.
        """
        
        tread_percents = pair.get_tread_remaining_percent_per_product_for_pair()
        high_tread_values = [v for v in tread_percents.values() if v > 75]

        products = Product.objects.filter(pair=pair)
        quantity = products.count()

        product = products.first()
        if not product:
            return ""

        product_size = product.size
        product_brand = product.brand
        product_tread = product.tread

        base_title = f"{quantity} x {product_size} {product_brand}"

        bargain_text = "Mega Okazja"
        normal_text = "Komplet opon"

        if len(base_title) < 55 and quantity == 2 and high_tread_values:
            tread_str = ", ".join(str(v) for v in high_tread_values)

            # Try with bargain text first
            title = f"{bargain_text} - {base_title} - {tread_str}% bieżnika"

            # If too long → remove bargain text
            if len(title) > 70:
                title = f"{base_title} ({tread_str}% bieżnika)"
        else:
            title = f"{normal_text} - {base_title}"

        # Final safety trim (only if still too long)
        if len(title) > 70:
            title = title[:70]

        return title
            





    def prepare_pair_advert_data(self, pair):
        
        from .pair_description import create_otomoto_advert_pair_description
        """
        Tworzy słownik gotowy do wysłania do Otomoto API na podstawie obiektu Product.
        Struktura została dopasowana do przykładowej odpowiedzi Otomoto.
        """
        # domain = f"{OtomotoSingleAd.domain}"
        
        domain = "https://www.tirgumpanel.pl"
        
        
            
        
        first_tire_size = pair.get_first_tire_size()
        
        size_value = str(first_tire_size) if first_tire_size else ""
        # title = (pair.get_pair_advert_title() or "")
        
        
        pair_width = pair.get_first_tire_width()
        pair_aspect_ratio = pair.get_first_tire_aspect_ratio()
        
        total_net_price = pair.get_pair_advert_price()
        
        brand = str(pair.get_pair_brand()).lower() 
        
        api_brands_set = {b.lower() for b in api_brands}
        brand = brand if brand in api_brands_set else "others"
        print(f"**********brand: {brand}")
        
        
        tyres_inches = str(extract_tyre_inches(size_value))
        tyres_profile = str(extract_tyre_profile(size_value))
        
        title = self.get_otomoto_pair_title(pair)
        
        all_images = self.get_images(pair)
        # print(f"++++++++all images {all_images}")
        
        # all_images = {
        #     "1": "https://tirgumpanel.pl/media/images/Goodyear-KMAX_S_GEN-2-315-70_R22.5-171-8_9j3mpvn.jpg",
        #     "2": "https://tirgumpanel.pl/media/images/Goodyear-KMAX_S_GEN-2-315-70_R22.5-171-6.jpg",
        #     "3": "https://tirgumpanel.pl/media/images/Goodyear-KMAX_S_GEN-2-315-70_R22.5-171-8_JHzCels.jpg"
        # }
        
        # Convert images to a list of URLs (Otomoto expects a list)
        images_list = list(all_images.values()) if isinstance(all_images, dict) else all_images

        advert_data = {
            
            # "title": str(title[:70]) if title else "",
            "description":create_otomoto_advert_pair_description(pair),
            "images": all_images,
            # "category_id": 163,
            "region_id": 6,
            "city_id": 60821,
            # "district_id":0,


            "municipality": "Tworóg",
            "city": {
                "pl": "Boruszowice",
                "en": "Boruszowice"
            },

            "coordinates": {
                "latitude": 50.51188,
                "longitude": 18.77311,
                "radius": 0,
                "zoom_level": 12
            },

            "advertiser_type": "business",

            "contact": {
                "person": "Mateusz Celej",
                "phones": ["+48733456474", "+48794746906"]
            },

            "params": {
                "title":title,
                # "title_parts": "Hahaha",
                
                "delivery": "1",
                "parts-category": "opony",  
                "parts-type": "opony",
                
           
                "price": {
                    "0": "price",
                    "1": float(total_net_price) if total_net_price else 0,
                    "currency": "PLN",
                    "gross_net": "net"
                },
                
                "tire-brand": f"{brand}",
                
                "tire-width": f"{pair_width}-mm",
                
                "height-aspect-ratio": pair_aspect_ratio,
                "tyres-inches":tyres_inches,
                "tyres-profile":tyres_profile,
            },
            # "title": str(pair.advert_title[:70]) if pair.advert_title else "",
            # "title":"To jest tytuł",
            "new_used": "used",
            "category_id": 167,
            "visible_in_profile": "1",
        }
        

        return advert_data
    
    
    def create_and_save_pair_advert(self, pair):
        
        """
        Creates an advert on Otomoto if none exists, or updates missing data locally
        for existing adverts. Saves the advert ID, status, and dates to the local database.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        
        def make_aware_if_needed(dt):
            if dt and timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return dt
        
        # Prepare payload
        advert_data = self.prepare_pair_advert_data(pair)
        
        # --- DEBUG: show payload ---
        print(f"[DEBUG] === Payload for pair {pair.id} ===")
        print(json.dumps(advert_data, indent=2, ensure_ascii=False))
        logger.debug("Payload for pair %s: %s", pair.id, json.dumps(advert_data, ensure_ascii=False))

        # Ensure token is valid
        try:
        # Make sure token is valid / refreshed
            self.ensure_authenticated()        
        # Get the latest access token
            access_token = self.get_valid_access_token()
            
        except Exception as e:
            msg = f"Authentication failed for pair {pair.id}: {e}"
            print(f"[ERROR] {msg}")
            logger.error(msg)           
            return None


        # Update session headers once
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'User-Agent': self.OTOMOTO_USERNAME
        })

        adverts_url = "https://www.otomoto.pl/api/open/account/adverts"

        
        print(f"[DEBUG] Payload for pair {pair.id}:")
        print(json.dumps(advert_data, indent=2, ensure_ascii=False))
        
        # Send request
        try:
            response = self.session.post(
                adverts_url,
                json=advert_data,
                timeout=15
            )
            print(f"[DEBUG] Response status code: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text}")
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                msg = f"Failed to parse JSON from response for pair {pair.id}: {response.text}"
                print(f"[ERROR] {msg}")
                logger.error(msg)
                return None
        
        # -------------------------------
    # Network / Request exceptions
    # -------------------------------
        except requests.exceptions.Timeout:
            msg = f"Timeout for pair {pair.id}"
            print(f"[ERROR] {msg}")
            logger.error(msg)
            return None
        
        except requests.exceptions.ConnectionError as e:
            msg = f"ConnectionError for pair {pair.id}: {e}"
            print(f"[ERROR] {msg}")
            logger.error(msg)
            return None
        
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTPError: {e}, Response: {getattr(e.response, 'text', '')}")
            return None
        
        except requests.exceptions.RequestException as e:
            msg = f"Unexpected RequestException for pair {pair.id}: {e}"
            print(f"[ERROR] {msg}")
            if hasattr(e, "response") and e.response:
                print(f"[ERROR] Response text: {e.response.text}")
                logger.error("Response text: %s", e.response.text)
            logger.error(msg)
            return None

        # Raise exception for 4xx/5xx
            

        # Check for API validation errors
        if response.status_code >= 400 or "errors" in data:
            msg = f"Otomoto API rejected payload for pair {pair.id}: {json.dumps(data, indent=2, ensure_ascii=False)}"
            print(f"[ERROR] {msg}")
            logger.error(msg)
            return None
    # -------------------------------
    # Successful case
    # -------------------------------
    # Only save if POST succeeded and returned an ID
        if response.status_code == 201 and data.get("id"):
            otomoto_advert_id = data.get("id")
            otomoto_advert_status = data.get("status")
            created_at = make_aware_if_needed(parse_datetime(data.get("created_at")))
            valid_to = make_aware_if_needed(parse_datetime(data.get("valid_to")))
            
            # Save OtoMotoAdvertData
            PairOtoMotoAdvertData.objects.update_or_create(
                pair=pair,
                defaults={
                    "otomoto_advert_id": otomoto_advert_id,
                    "created_at": created_at,
                    "valid_to": valid_to,
                    "otomoto_advert_status": otomoto_advert_status,
                }
            )
            msg = f"[SUCCESS] Pair {pair.id} advert created. Otomoto ID: {otomoto_advert_id}"
            print(msg)
            logger.info(msg)      

               
            
        
        return data    
