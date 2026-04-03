# from .models import productOLX
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import redirect
import requests
import json
from django.core.cache import cache
from rest_framework.serializers import ValidationError
from tyreadderapp.models import Product,Image, Pair, PairImage
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from olx.models import OLXAuthData
from django.utils import timezone
import os
from django.utils.lorem_ipsum import paragraphs
import logging
from urllib.parse import urlencode

logger = logging.getLogger('logfile')


class OlxClient:
    auth_url = "https://www.olx.pl/oauth/authorize"  
    url = "https://www.olx.pl/api"
    grant_type = "authorization_code"
    client_id = os.environ.get("olx_client_id")
    client_secret = os.environ.get("olx_client_secret")
    scope = "v2 read write"
    redirect_uri = "http://www.tirgumpanel.pl/olx/olx-product-update"
    access_token = ""
    last_request = None
    #OLX_AUTH_URL=f"https://www.olx.pl/oauth/authorize/?client_id={client_id}&response_type=code&state=x93ld3v&scope=read+write+v2&redirect_uri="
    OLX_AUTH_URL=f"https://www.olx.pl/oauth/authorize/?client_id={client_id}&response_type=code&state=x93ld3v&scope={scope}&redirect_uri={redirect_uri}"
    
    def get_valid_access_token(self):
        current_date_time=timezone.now()
        olx_auth_data=OLXAuthData.objects.filter(access_token_expired_time__gt=current_date_time).first()
        if olx_auth_data:
            return olx_auth_data.access_token
        else:
            self.get_access_token_from_refresh_token()
    
    def get_access_token(self):
        access_token=self.get_valid_access_token()
        if not access_token:
            access_token = self.get_access_token_from_refresh_token()
        return access_token

    def get_valid_refresh_token(self):
        current_date_time=timezone.now()
        olx_auth_data=OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time).first()
        if olx_auth_data:
            return olx_auth_data.refresh_token
        
            

    def get_authorization_url(self):
        auth_data = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": self.scope,
            "redirect_uri": self.redirect_uri,
        }      
        url = f"{self.auth_url}?{urlencode(auth_data)}"
    
        return url


    
    def get_access_token_from_refresh_token(self):
        refresh_token = self.get_valid_refresh_token()
        url = f"{self.url}/open/oauth/token"
        auth_data={
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
            }
        r = requests.post(url=url, data=auth_data)
        if r.status_code==200:
            response=r.json()
            access_token=response.get("access_token")
            expires_in = response.get("expires_in")
            self.update_access_token(refresh_token,access_token,expires_in)
            return access_token
    
    def update_access_token(self,refresh_token,access_token,expires_in):
        current_date_time=timezone.now() 
        access_token_expired_time=current_date_time + timedelta(seconds=expires_in-10)  
        OLXAuthData.objects.filter(refresh_token=refresh_token).update(access_token=access_token, access_token_expired_time=access_token_expired_time)


    def code_auth(self, code):
        auth_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri" : "http://www.tirgumpanel.pl/olx/olx-product-update",
        }
        r = requests.post(url=f"{self.url}/open/oauth/token", data=auth_data)
        response = r.json()
        print("===>",response)
        if r.status_code != 200:
            raise ValidationError("token not found")
        return response
    
    def save_tokens(self,code):
        response=self.code_auth(code)
        current_date_time=timezone.now()
        access_token=response.get("access_token")
        expires_in = response.get("expires_in")
        refresh_token=response.get("refresh_token")
        refresh_token_expired_time=current_date_time + timedelta(seconds=2591900) 
        access_token_expired_time=current_date_time + timedelta(seconds=expires_in-10)  
        OLXAuthData.objects.create(
            access_token=access_token,
            refresh_token=refresh_token,
            refresh_token_expired_time=refresh_token_expired_time,
            access_token_expired_time=access_token_expired_time

        )
    

    def refesh_token(self, token):
        auth_data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": token,
        }
        r = requests.post(url=f"{self.url}/open/oauth/token", data=auth_data)
        response = r.json()
        return response

    def get_category_attributs(self):
        self.last_request = requests.get(
            url=f"{self.url}/partner/categories/1383/attributes",
            headers={"Authorization": f"Bearer {self.access_token}", "Version": "2.0"},
        )
        response = self.last_request.json()
        return response

    def _get_size(self, diameter):
        sizes = ['12', '13', '14', '15', '16', '17',
                '18', '19', '20', '21', '22']
        
        if float(diameter) <= 12:
            return 's_12'
        elif float(diameter) >=22:
            return 's_22'
        elif float(diameter)==16.5:
            return "s_165"
        elif float(diameter)==17.5:
            return "s_175"
        elif str(diameter) in sizes:
            return 's_' + str(diameter)
        else:
            return "inny"
        
                



    def _get_width(self, width):
        sizes = [
            "w_125",
            "w_135",
            "w_145",
            "w_155",
            "w_165",
            "w_175",
            "w_185",
            "w_195",
            "w_205",
            "w_215",
            "w_225",
            "w_235",
            "w_245",
            "w_255",
            "w_265",
            "w_275",
            "w_285",
            "w_295",
            "w_305",
            "w_315",
            "w_325",
            "w_335",
            "w_345",
            "w_355",
            "w_30",
            "w_31",
            "w_32",
            "w_33",
            "w_35",
            "w_37",
            "w_500",
            "w_600",
            "w_640",
            "w_650",
            "w_700",
            "w_750",
        ]

        if f"w_{width}" in sizes:
            return f"w_{width}"

        return "inny"

    def _get_profile(self, profile):
        sizes = [
            "7",
            "9.5",
            "9.50",
            "10.5",
            "10.50",
            "11.50",
            "12.50",
            "25",
            "30",
            "35",
            "40",
            "45",
            "50",
            "55",
            "60",
            "65",
            "70",
            "75",
            "80",
            "85",
        ]

        profile=str(profile).replace(".","")

        if str(profile) not in sizes:
            return "inny"
        
        profile=str(profile).replace(".","")

        if profile=="7":
            return "w_700"
        else:
            return f"w_{profile}"



    def _description_generator(self, product):
        advert_description= product.advert_description
        advert_description_length=len(advert_description)
        if advert_description_length < 80:
            advert_description += ' ' + paragraphs(1)[0]
        
        return advert_description


    def get_advert_title(self,product):
        advert_title=product.advert_title
        title_length = len(advert_title)
        if title_length < 16:
            # Append Lorem Ipsum text to meet the minimum length
            advert_title += ' ' + paragraphs(1)[0][:16 - title_length]
        elif title_length > 70:
            # Trim the title to meet the maximum length
           advert_title = advert_title[:70]
        return advert_title

    def _prepare_advert_data(self, product:Product):
        try:
            price_atr = float(product.net_price) * 1.23 if product.net_price is not None else None
        except (ValueError, TypeError):
            price_atr = None
            
        if price_atr is None:
            return {"status": "error", "message": "Missing or invalid net price"}
        
        domain="tirgumpanel.pl"
        all_images =[{"url": domain+ item.image.url} for item in Image.objects.filter(product=product)[:8]]

        description = self._description_generator(product)

        advert = {
            "title": self.get_advert_title(product),
            "description": description if product.advert_description else product.advert_title,
            "category_id": 1383,
            "advertiser_type": "business",
            "contact": {
                "name": "Tirgum Mateusz Celej",
                "phone": "733-456-474",
            },
            "location": {"city_id": 17365, "latitude": 50.44613, "longitude": 18.85827},
            "images": all_images, #[{"url": "https://t4.ftcdn.net/jpg/00/51/96/31/360_F_51963161_ZIsqaaYu2lj7Tv7EU1cAKxdoHnAbMvBl.jpg"}], #all_images,
            "price": {
                "value": price_atr,
                "currency": "PLN",
                "negotiable": False,
                "trade": False,
            },
            "attributes": [
                {"code": "state", "value": "used"},
                {"code": "tiretype", "value": "inny"},
                {"code": "type", "value": "inny"},
                {"code": "producttype", "value": "caloroczne"},
                {"code": "size", "value": self._get_size(product.size.diameter)},
                {"code": "width", "value": self._get_width(product.size.width)},
                {"code": "profile", "value": self._get_profile(product.size.profile)},
            ],
            "courier": True,
        }
        return {"status": "success", "data": advert}

    def _status_checker(self, data):
        status = data["status"]
        is_olx = "error"
        olx_msg = "status error (can't pick status)"

        if status == "new":
            is_olx = "wait"
            olx_msg = "fresh advert before activation and moderation"

        elif status == "active":
            is_olx = "success"
            olx_msg = "visible on OLX"

        elif status == "limited":
            is_olx = "info"
            olx_msg = "advert exceeded limit of free adverts in selected category"

        elif status == "removed_by_user":
            is_olx = "no"
            olx_msg = "manually removed by user"

        elif status == "outdated":
            is_olx = "no"
            olx_msg = "advert reached expiration date"

        elif status == "unconfirmed":
            is_olx = "no"
            olx_msg = "waiting for confirmation"

        elif status == "unpaid":
            is_olx = "no"
            olx_msg = "waiting for confirmation"

        elif status == "moderated":
            is_olx = "no"
            olx_msg = "negative moderation result"

        elif status == "blocked":
            is_olx = "no"
            olx_msg = "blocked by moderation"

        elif status == "disabled":
            is_olx = "no"
            olx_msg = (
                "disabled by moderation, offer blocked and waiting for verification"
            )

        elif status == "removed_by_moderator":
            is_olx = "no"
            olx_msg = "removed by moderator"

        return [is_olx, olx_msg]


    def get_advert_info(self, id, access_token):
        response = requests.get(
            url=f"{self.url}/partner/adverts/{id}",
            headers={"Authorization": f"Bearer {access_token}", "Version": "2.0"},
        )
        return response

    def get_advert_list(self,access_token):
        r = requests.get(
            url=f"{self.url}/partner/adverts?limit=600",
            headers={"Authorization": f"Bearer {access_token}", "Version": "2.0"},
        )
        return r
    
    def get_advert(self,advert_id,access_token):
        url=f"{self.url}/partner/adverts/{advert_id}"
        r= requests.get(
            url, headers={"Authorization": f"Bearer {access_token}", "Version": "2.0"},
        )
        return r


    def verify_advert_status(self, advert_id, access_token):
        response = self.get_advert(advert_id, access_token)
        if response.status_code == 200:
            advert_data = response.json().get("data", {})
            advert_status = advert_data.get("status", "unknown")
            return advert_status == "active"
        logging.warning(f"Failed to verify advert status. Response: {response.text}")
        return False


    def add_advert_response_data_to_product(self, product, response, access_token):
        logger = logging.getLogger(__name__)
        
        try:
            json_response = response.json()
            logger.debug(f"add_advert_response: Status={response.status_code}, Response={response.text}")
            
            if response.status_code == 200:
                product.is_olx = True
                advert_data = json_response.get("data", {})
                product.olx_advert_id = advert_data.get("id")
                product.olx_response = "Successful"

                # Activate advert and update product status
                activate_advert_response = self.activate_advert(product.olx_advert_id, access_token)
                is_active = activate_advert_response.status_code == 400 or self.verify_advert_status(product.olx_advert_id, access_token)
                product.is_olx_active = is_active

                activate_response_data = activate_advert_response.json() if is_active else activate_advert_response.text

                logger.debug(f"Advert activation response: {activate_response_data}")
                product.olx_active_advert_response = "Successful" if is_active else activate_response_data

                product.advert_title = advert_data.get("title", "")
                product.advert_description = advert_data.get("description", "")
                product.product_listing_status = Product.ProductStatusChoice.LISTED.value
                product.save()

            else:
                product.is_olx = False
                product.olx_advert_id = None
                product.olx_response = json_response
                product.save()

            return product
        
        except Exception as e:
            logger.error(f"Error processing advert response: {e}")
            raise

    
    def activate_advert(self, advert_id, access_token):
        logger = logging.getLogger(__name__)
        url = f"{self.url}/partner/adverts/{advert_id}/commands"
        data = {
            "command": "activate"
        }
        data_json = json.dumps(data)
        response = requests.post(
                url=url,
                data=data_json,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Version": "2.0",
                    "Content-Type": "application/json",
                },
            )
        logger.debug(f"activate_advert : Status={response.status_code},{response}")
        return response


    
    def deactivate_advert(self,advert_id,access_token):
        url=f"{self.url}/partner/adverts/{advert_id}/commands"
        data={
            	"command": "deactivate",
                "is_success": True
        }
        data_json = json.dumps(data)
        response = requests.post(
            url=url,
            data=data_json,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Version": "2.0",
                "Content-Type": "application/json",
            },
        )
        return response

    def get_olx_advert(self, olx_advert_id, access_token):
        try:
            response = requests.get(
                url=f"{self.url}/partner/adverts/{olx_advert_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Version": "2.0",
                    "Content-Type": "application/json",
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OLX GET Error: {str(e)}")
        return None

    def add_advert(self, product, access_token):
        logger = logging.getLogger(__name__)
        logger.info(f"[OLX_ADD_ADVERT] Starting add for product ID={product.id}")

        try:
            adv_data = self._prepare_advert_data(product)
            data_json = json.dumps(adv_data["data"])
            logger.debug(f"[OLX_ADD_ADVERT] Prepared data for product ID={product.id}: {data_json}")

            response = requests.post(
                url=f"{self.url}/partner/adverts",
                data=data_json,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Version": "2.0",
                    "Content-Type": "application/json",
                },
            )

            logger.debug(
                f"[OLX_ADD_ADVERT_RESPONSE] Product ID={product.id}, "
                f"Status Code={response.status_code}, Response={response.text}"
            )

            self.add_advert_response_data_to_product(product, response, access_token)
            return response

        except Exception as e:
            logger.error(f"[OLX_ADD_ADVERT_ERROR] Failed to add product ID={product.id}, Error: {str(e)}")
            raise
        # return None


    def update_advert(self, product, access_token):
        logger = logging.getLogger(__name__)
        logger.info(f"[OLX_UPDATE_ADVERT] Starting update for product ID={product.id}, OLX Advert ID={product.olx_advert_id}")

        try:
            adv_data = self._prepare_advert_data(product)
            data_json = json.dumps(adv_data["data"])
            logger.debug(f"[OLX_UPDATE_ADVERT] Prepared data for product ID={product.id}: {data_json}")

            response = requests.put(
                url=f"{self.url}/partner/adverts/{product.olx_advert_id}",
                data=data_json,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Version": "2.0",
                    "Content-Type": "application/json",
                },
            )

            logger.debug(
                f"[OLX_UPDATE_ADVERT_RESPONSE] Product ID={product.id}, "
                f"Status Code={response.status_code}, Response={response.text}"
            )

            return response

        except Exception as e:
            logger.error(f"[OLX_UPDATE_ADVERT_ERROR] Failed to update product ID={product.id}, Error: {str(e)}")
            raise

    def remove_advert(self, product, access_token):
        print(product.olx_advert_id)
        response = requests.delete(
            url=f"{self.url}/partner/adverts/{product.olx_advert_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Version":"2.0"
            },
        )

        print(response)
        if response.status_code==204:
            product.olx_response= 'Successful'
            # product.olx_advert_id=None
            product.is_olx=False
            product.is_olx_active=False
            
        else:
            product.olx_response= response.json()
            product.is_olx=True
        product.save()
        return response
    

 #===========  OLX PAIR ADVERT FUNCTIONALITY ===========================
    
        
                
    def _pair_description_generator(self, pair):
        advert_description= pair.pair_description
        advert_description_length=len(advert_description)
        if advert_description_length < 80:
            advert_description += ' ' + paragraphs(1)[0]
        
        return advert_description
    def get_pair_advert_title(self,pair):
        advert_title=pair.pair_title
        title_length = len(advert_title)
        if title_length < 16:
           
            advert_title += ' ' + paragraphs(1)[0][:16 - title_length]
        elif title_length > 70:
            
           advert_title = advert_title[:70]
        return advert_title

    def _prepare_pair_advert_data(self, pair: Pair):
        # price_atr = float(pair.pair_price)
        price_atr = Decimal(pair.pair_price) * Decimal("1.23")
        domain = "tirgumpanel.pl"
        products = Product.objects.filter(pair=pair)
        rand_product = products.first()
        num_products = products.count()
       
        pair_image = PairImage.objects.filter(pair=pair).order_by('-id').first()
        all_images = []
        if pair_image:
            all_images.append({"url": domain + pair_image.image.url})
      
        product_images = []
        image_limit = 8 // num_products if num_products > 0 else 8
        for product in products:
            images = Image.objects.filter(product=product).order_by('-id')[:image_limit]
            product_images.extend([{"url": domain + item.image.url} for item in images])
        
        all_images.extend(product_images)
        
        if len(all_images) > 8:
            all_images = all_images[:8]  # Limit to exactly 8 images
        description = self._pair_description_generator(pair)
        advert = {
            "title": self.get_pair_advert_title(pair),
            "description": description if pair.pair_description else pair.pair_title,
            "category_id": 1383,
            "advertiser_type": "business",
            "contact": {
                "name": "Tirgum Mateusz Celej",
                "phone": "733-456-474",
            },
            "location": {"city_id": 17365, "latitude": 50.44613, "longitude": 18.85827},
            "images": all_images,
            "price": {
                "value": float(price_atr),
                "currency": "PLN",
                "negotiable": False,
                "trade": False,
            },
            "attributes": [
                {"code": "state", "value": "used"},
                {"code": "tiretype", "value": "inny"},
                {"code": "type", "value": "inny"},
                {"code": "pairtype", "value": "caloroczne"},
                {"code": "size", "value": self._get_size(rand_product.size.diameter)},
                {"code": "width", "value": self._get_width(rand_product.size.width)},
                {"code": "profile", "value": self._get_profile(rand_product.size.profile)},
            ],
            "courier": True,
        }
        return {"status": "success", "data": advert}

    def _status_checker(self, data):
        status = data["status"]
        is_olx = "error"
        olx_msg = "status error (can't pick status)"
        if status == "new":
            is_olx = "wait"
            olx_msg = "fresh advert before activation and moderation"
        elif status == "active":
            is_olx = "success"
            olx_msg = "visible on OLX"
        elif status == "limited":
            is_olx = "info"
            olx_msg = "advert exceeded limit of free adverts in selected category"
        elif status == "removed_by_user":
            is_olx = "no"
            olx_msg = "manually removed by user"
        elif status == "outdated":
            is_olx = "no"
            olx_msg = "advert reached expiration date"
        elif status == "unconfirmed":
            is_olx = "no"
            olx_msg = "waiting for confirmation"
        elif status == "unpaid":
            is_olx = "no"
            olx_msg = "waiting for confirmation"
        elif status == "moderated":
            is_olx = "no"
            olx_msg = "negative moderation result"
        elif status == "blocked":
            is_olx = "no"
            olx_msg = "blocked by moderation"
        elif status == "disabled":
            is_olx = "no"
            olx_msg = (
                "disabled by moderation, offer blocked and waiting for verification"
            )
        elif status == "removed_by_moderator":
            is_olx = "no"
            olx_msg = "removed by moderator"
        return [is_olx, olx_msg]
    def add_advert_response_data_to_pair(self, pair, response, access_token):
        logger = logging.getLogger(__name__)
        
        try:
            json_response = response.json()
            logger.debug(f"pair_add_advert_response: Status={response.status_code}, Response={response.text}")
            
            if response.status_code == 200:
                pair.pair_is_olx = True
                advert_data = json_response.get("data", {})
                pair.pair_olx_advert_id = advert_data.get("id")
                pair.pair_olx_response = "Successful"
                
                activate_advert_response = self.activate_pair_advert(pair.pair_olx_advert_id, access_token)
                is_active = activate_advert_response.status_code == 200
                pair.pair_is_olx_active = is_active
                activate_response_data = activate_advert_response.json() if is_active else activate_advert_response.text
                logger.debug(f"pair Advert activation response: {activate_response_data}")
                pair.olx_active_advert_response = "Successful" if is_active else activate_response_data
                pair.pair_title = advert_data.get("title", "")
                pair.pair_description = advert_data.get("description", "")
                pair.save()
            else:
                pair.pair_is_olx = False
                pair.pair_olx_advert_id = None
                pair.pair_olx_response = json_response
                pair.save()
            return pair
        
        except Exception as e:
            logger.error(f"Error processing advert response: {e}")
            raise
    def activate_pair_advert(self, advert_id, access_token):
        logger = logging.getLogger(__name__)
        url = f"{self.url}/partner/adverts/{advert_id}/commands"
        data = {
            "command": "activate"
        }
        data_json = json.dumps(data)
        response = requests.post(
                url=url,
                data=data_json,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Version": "2.0",
                    "Content-Type": "application/json",
                },
            )
        logger.debug(f"activate_pair_advert : Status={response.status_code},{response}")
        return response
    
    def add_pair_advert(self, pair,access_token):
        adv_data = self._prepare_pair_advert_data(pair)
        data_json = json.dumps(adv_data["data"])
        logger.debug(f"add_advert: Status={data_json}")
        response = requests.post(
            url=f"{self.url}/partner/adverts",
            data=data_json,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Version": "2.0",
                "Content-Type": "application/json",
            },
        )
        logger.debug(f"add_advert_response:{response}")
        self.add_advert_response_data_to_pair(pair,response,access_token)
        return response
    
    def update_pair_advert(self, pair, access_token):
        adv_data = self._prepare_pair_advert_data(pair)
        data_json = json.dumps(adv_data["data"])
        response = requests.put(
            url=f"{self.url}/partner/adverts/{pair.pair_olx_advert_id}",
            data=data_json,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Version": "2.0",
                "Content-Type": "application/json",
            },
        )
        logger.debug(f" Pair Advert update: {response.text}")
        return response
    def remove_pair_advert(self, pair, access_token):

        response = requests.delete(
            url=f"{self.url}/partner/adverts/{pair.pair_olx_advert_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Version":"2.0"
            },
        )
        print(response)
        if response.status_code==204:
            pair.pair_olx_response= 'Successful'
            pair.pair_olx_advert_id=None
            pair.pair_is_olx=False
            
        else:
            pair.pair_olx_response= response.json()
            pair.pair_is_olx=True
        pair.save()
        return response