
import logging
import re
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
# from . models import Allegroauthdata
from datetime import timedelta
from django.utils import timezone
import requests
import json
from tyreadderapp.models import Product, Image
from django.http import JsonResponse
# from django.shortcuts import render, get_object_or_404
from django.contrib import messages
# import json
# import requests
# from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .client.client import AllegroClientBase


# Configure logger
logger = logging.getLogger(__name__)





def allegro_callback(request):
    # Extract the authorization code from the query parameters
    authorization_code = request.GET.get("code")
    if authorization_code:
        print(f"Authorization code received: {authorization_code}")
        tokens = Allegro.get_allegro_refresh_token(authorization_code)
        Allegro.allegro_token_generate(tokens)
        return redirect("tyreadderapp:main")
    else:
        return HttpResponse("Authorization failed or no code received.", status=400)

def updatetoken(request):
    authorization_redirect_url = f"{Allegro.AUTH_URL}?response_type=code&client_id={Allegro.CLIENT_ID}&redirect_uri={Allegro.REDIRECT_URI}"
    context = {
        "authorization_redirect_url" :authorization_redirect_url,
    }
    return render (request,"allegro/home.html",context)



class Allegro:
    CLIENT_ID = "819e6c3e67b74b59ae97913caaec41b8"
    CLIENT_SECRET = "ZP7CLmi62vOWgM9ydVnYg4GNFGxdmhCZ40yM7a7Hi2xPRiOVIX9HYLLUvoDEtSdN"
    REDIRECT_URI = "http://www.tirgumpanel.pl/allegro/callback"
    # REDIRECT_URI = "https://oauth.pstmn.io/v1/callback"
    AUTH_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/authorize"
    TOKEN_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/token"


    # def get_allegro_authorization_code():
    #     authorization_redirect_url = f"{Allegro.AUTH_URL}?response_type=code&client_id={Allegro.CLIENT_ID}&redirect_uri={Allegro.REDIRECT_URI}"
    #     print("Login to Allegro by pasting the following URL into your browser. After authorizing, enter the code:")
    #     authorization_code = input("Enter authorization code: ")
    #     return authorization_code

    def get_allegro_refresh_token(authorization_code):
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': Allegro.REDIRECT_URI
            }
            response = requests.post(
                Allegro.TOKEN_URL, 
                data=data, 
                auth=(Allegro.CLIENT_ID, Allegro.CLIENT_SECRET)
            )
            response.raise_for_status()  
            tokens = response.json()
            return tokens
        except requests.exceptions.RequestException as err:
            print(f"Error occurred: {err}")
            raise


    def get_valid_refresh_token():
        """
        Fetch a valid refresh token from the database. 
        If none exists or it has expired, redirect to the authorization page.
        """
        current_date_time = timezone.now()
        valid_refresh_token = Allegroauthdata.objects.filter(
            refresh_token_expired_time__gt=current_date_time
        ).first()
        
        if not valid_refresh_token:
            # Redirect to home.html with the authorization URL
            authorization_redirect_url = f"{Allegro.AUTH_URL}?response_type=code&client_id={Allegro.CLIENT_ID}&redirect_uri={Allegro.REDIRECT_URI}"
            context = {
                "authorization_redirect_url": authorization_redirect_url,
            }
            return render(None, "allegro/home.html", context)  # Return the rendered page
        
        return valid_refresh_token.refresh_token




    def get_allegro_access_from_refresh():
        """
        Use the refresh token to generate a new access token.
        If no valid refresh token exists, redirect to the authorization page.
        """
        logger.info("Starting token refresh process")
        
        refresh_token_response = Allegro.get_valid_refresh_token()
        
        if isinstance(refresh_token_response, HttpResponse):
            logger.warning("No valid refresh token found - redirecting to authorization page")
            return refresh_token_response
        
        refresh_token = refresh_token_response  # Token is valid; proceed normally
        logger.debug(f"Valid refresh token retrieved =::= {refresh_token}")
        
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'redirect_uri': Allegro.REDIRECT_URI,
            }
            
            logger.debug(f"Attempting to refresh token with redirect URI: {Allegro.REDIRECT_URI}")
            
            response = requests.post(
                Allegro.TOKEN_URL,
                data=data,
                auth=(Allegro.CLIENT_ID, Allegro.CLIENT_SECRET)
            )
            response.raise_for_status()  # Raise exception for HTTP errors
            
            tokens = response.json()
            logger.debug(f"===> Tokens response: {tokens} ")
            access_token = tokens.get('access_token')
            refresh_token = tokens.get('refresh_token')
            access_expiry = tokens.get('expires_in')
            
            if not all([access_token, refresh_token, access_expiry]):
                logger.error("Incomplete token data received from Allegro API")
                raise ValueError("Missing required token data in API response")
            
            logger.info("Successfully retrieved new tokens from Allegro API")
            logger.debug(f"Token expiry time: {access_expiry} seconds")
            
            # Update token expiry times
            current_time = timezone.now()
            # refresh_token_expiry_time = current_time + timedelta(seconds=access_expiry)
            access_token_expiry_time = current_time + timedelta(seconds=access_expiry)
            
            # Save tokens to database
            Allegroauthdata.objects.update_or_create(
                defaults={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "access_token_expired_time": access_token_expiry_time,
                }
            )
            
            logger.info("Successfully updated tokens in database")
            logger.debug(f"Access token will expire at: {access_token_expiry_time}")
            # logger.debug(f"Refresh token will expire at: {refresh_token_expiry_time}")
            
            return access_token
            
        except requests.exceptions.RequestException as err:
            logger.error(f"Request error during token refresh: {err}", exc_info=True)
            raise
        except ValueError as err:
            logger.error(f"Value error during token refresh: {err}", exc_info=True)
            raise
        except Exception as err:
            logger.error(f"Unexpected error during token refresh: {err}", exc_info=True)
            raise

    def get_allegro_access_token(self):
        current_date_time = timezone.now()
        valid_access_token = Allegroauthdata.objects.filter(access_token_expired_time__gt= current_date_time).first()
        if not valid_access_token:
            access_token = Allegro.get_allegro_access_from_refresh()
            return access_token
        return  valid_access_token.access_token


    def allegro_token_generate(tokens):
        refresh_token = tokens.get('refresh_token')
        access_token = tokens.get('access_token')
        refresh_expiry = tokens.get('expires_in')
        current_time = timezone.now()  
        refresh_token_expiry_time = current_time + timedelta(minutes=refresh_expiry) 
        access_token_expiry_time = current_time + timedelta(hours=24) 
        Allegroauthdata.objects.update_or_create(
            access_token= access_token,
            refresh_token = refresh_token,
            refresh_token_expired_time = refresh_token_expiry_time,
            access_token_expired_time = access_token_expiry_time
        )
        return refresh_token
    

    
        
    
    def get_return_policies(access_token):
        url = "https://api.allegro.pl.allegrosandbox.pl/after-sales-service-conditions/return-policies"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()  
                return JsonResponse(data, safe=False)
            except ValueError as e:
                return JsonResponse(
                    {"error": "Invalid JSON response", "details": str(e)},
                    status=500
                )
        else:
            return JsonResponse(
                {
                    "error": "Failed to fetch data",
                    "status_code": response.status_code,
                    "details": response.text
                },
                status=response.status_code
            )
        

    def get_implied_warranties(access_token):
        url = "https://api.allegro.pl.allegrosandbox.pl/after-sales-service-conditions/implied-warranties"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()  
                return JsonResponse(data, safe=False)
            except ValueError as e:
                return JsonResponse(
                    {"error": "Invalid JSON response", "details": str(e)},
                    status=500
                )
        else:
            return JsonResponse(
                {
                    "error": "Failed to fetch data",
                    "status_code": response.status_code,
                    "details": response.text
                },
                status=response.status_code
            )
        
    def get_warranties(access_token):
        url = "https://api.allegro.pl.allegrosandbox.pl/after-sales-service-conditions/warranties"
        headers = {
            "content-type": "application/vnd.allegro.public.v1+json",
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()  
                return JsonResponse(data, safe=False)
            except ValueError as e:
                return JsonResponse(
                    {"error": "Invalid JSON response", "details": str(e)},
                    status=500
                )
        else:
            return JsonResponse(
                {
                    "error": "Failed to fetch data",
                    "status_code": response.status_code,
                    "details": response.text
                },
                status=response.status_code
            )
        
    def advert_send_allegro(request,product_id):
        access_token = Allegro.get_allegro_access_token(request)
        alegro_advert(access_token,product_id)
        


def end_allegro_advert(access_token, advert_id):
    url = f"https://api.allegro.pl.allegrosandbox.pl//sale/product-offers/{advert_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "content-type": "application/vnd.allegro.public.v1+json"
    }
    body = { 
        "publication": {
            "status": "ENDED"
        }
    }
    try:
        response = requests.patch(url, headers=headers, json=body)
        response.raise_for_status()
        
        # Check for success status codes
        if response.status_code in [200, 202]:
            return {"success": True, "data": response.json(),"message": response.status_code}
        else:
            return {"success": False,"data": response.json(), "message": response.status_code}
        
    except requests.exceptions.HTTPError as http_err:
        return {"success": False, "message": f"HTTP error: {http_err}", "response": response.text}
    except requests.exceptions.RequestException as req_err:
        return {"success": False, "message": f"Request error: {req_err}"}
    except Exception as e:
        print("oiiioioioio")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}


def alegro_advert(access_token, product):
    logger.debug(f"product in advert  funct =::> {product}")
    try:  
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"
        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Content-Type': 'application/vnd.allegro.public.v1+json',
            'Accept-Language': 'pl-PL',
            'Authorization': 'Bearer ' + access_token
        }
        payload = _allegro_advert_data(product)
        json_payload = json.dumps(payload)
        logger.info("======will try to make post request====",json_payload)
        response = requests.post(url, headers=headers, data=json_payload)
        if response.status_code == 201 or response.status_code == 202:
            add_advert_response_to_product(product, response, access_token)
            return JsonResponse({'message': 'Offer created successfully!', 'data': response.json()})
        else:
            return JsonResponse({
                'error': 'Failed to create offer', 
                'details': response.json(),
                'status_code': response.status_code
            }, status=response.status_code)
            
    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while creating the offer',
            'details': str(e)
        }, status=500)

def add_advert_response_to_product(product, response, access_token):
    # try:
    #     product = Product.objects.get(id=product_id)
    # except ObjectDoesNotExist:
    #     return

    try:
        json_response = response.json()     
        if response.status_code in [201, 202]:
            product.is_allegro = True
            advert_id = json_response.get("id")
            if advert_id:
                product.allegro_advert_id = advert_id
                product.allegro_status = "Successful"
                product.is_allegro_active = True
                product.save()
            else:
                product.allegro_api_respose = response.text
                product.save()
        else:
            print("Response does not indicate success.")
    except Exception as e:
        print(f"Exception while processing response: {str(e)}")


def _allegro_advert_data(product):
    product_name = product.advert_title
    description = product.advert_description
    brand = product.brand.name
    category_id = "257701"
    width = product.size.width
    diameter = float(product.size.diameter)
    price = float(product.net_price)
    ean = product.ean
    stock = 1
    domain = "tirgumpanel.pl"
    
    # Get product images
    product_images = [
        domain + item.image.url 
        for item in Image.objects.filter(product=product)[:8]
    ]

    # Format description
    description = description.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = description.split("\n")
    formatted_description = "".join(
        f"<p>{line.strip()}</p>" 
        for line in paragraphs 
        if line.strip()
    )
    formatted_description = formatted_description.replace(
        "ID opony:", "<b>ID opony:</b>"
    )

    payload = {
        "productSet": [{
            "product": {
                "name": product_name,
                "category": {
                    "id": category_id
                },
                "parameters": [
                    {
                        "name": "EAN",
                        "values": [ean]
                    },
                    {
                        "id": "9300",
                        "name": "Marka", 
                        "values": [brand]
                    },
                    {
                        "id": "345",
                        "name": "Szerokość opony",
                        "values": [str(width)]  # Convert width to string
                    },
                    {
                        "id": "127088",
                        "name": "Średnica",
                        "values": [str(diameter)]  # Convert diameter to string
                    }
                ],
                "images": [product_images[0]]  # This should be a list
            }
        }],
        "parameters": [
            {
                "id": "11323",
                "name": "Stan",
                "valuesIds": ["11323_2"]
            },
            {
                "id": "128844",
                "name": "Liczba opon w ofercie",
                "values": ["1 szt."]
            }
        ],
        "images": product_images[1:],  # Additional images
        "afterSalesServices": {
            "impliedWarranty": {
                "id": "72def2ab-b35e-4ca8-bfc0-cf4bc39cfd56",
                "name": "domyślny"
            },
            "returnPolicy": {
                "id": "7aa7b5c7-4d48-4c50-ab49-f3f7b25aef9e",
                "name": "Warunki zwrotu"
            },
            "warranty": {
                "id": "d40a8bc8-7412-45ce-8c84-4badd12aaac5",
                "name": "check this is tril policy"
            }
        },
        "sellingMode": {
            "price": {
                "amount": str(price),  # Convert price to string
                "currency": "PLN"
            }
        },
        "stock": {
            "available": stock
        },
        "description": {
            "sections": [{
                "items": [{
                    "type": "TEXT",
                    "content": formatted_description
                }]
            }]
        }
    }
    return payload






def advert_end(request, product_id):
    try:
        access_token = Allegro.get_allegro_access_token(request)
        product = get_object_or_404(Product, id=product_id)
        if not product.allegro_advert_id:
            messages.error(request, "Product does not have an Allegro advert ID.")
            return render (request,"allegro/allegro_home.html")

        response = end_allegro_advert(access_token, product.allegro_advert_id)
        res = response.get("message")
        print(res)
        if res == 202 or res ==200:
            product.allegro_status = "ADVERT ENDED"
            product.is_allegro_active = False
            product.save()
        else:
            pass
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")

    return render (request,"allegro/allegro_home.html")





#  fill category id using this
    def get_allegro_category(request,access_token):
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/categories?parent.id=257687"
        headers = {
            "Authorization": f"bearer {access_token}",
            "Accept":"application/vnd.allegro.public.v1+json"
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()  
                return data
            except ValueError as e:
                return JsonResponse(
                    {"error": "Invalid JSON response", "details": str(e)},
                    status=500
                )
        else:
            return JsonResponse(
                {
                    "error": "Failed to fetch data",
                    "status_code": response.status_code,
                    "details": response.text
                },
                status=response.status_code
            )

    #  fill image using this
    def allegro_image(access_token,product):
        domain="tirgumpanel.pl"
        all_images =[{"url": domain+ item.image.url} for item in Image.objects.filter(product=product)[:8]]
        try:
            url = "https://upload.allegro.pl.allegrosandbox.pl/sale/images"
            headers = {
                "Authorization": f"bearer{access_token}",
                "Content-Type": "application/vnd.allegro.public.v1+json",
                "Accept": "application/vnd.allegro.public.v1+json"
            }
            payload= all_images
            response = requests.post(url,headers=headers,json=payload)
            if response.status_code == 201:
                response_data = response.json()
                # Extract URLs from the response data
                urls = []
                if 'links' in response_data:
                    urls = [link['href'] for link in response_data['links'] if 'href' in link]
                return JsonResponse({'message': 'Offer created successfully!', 'urls': urls})
            else:
                return JsonResponse({
                    'error': 'Failed to create offer', 
                    'details': response.json(),
                    'status_code': response.status_code
                }, status=response.status_code)
        except Exception as e:
            return JsonResponse({
                'error': 'An error occurred while creating the offer',
                'details': str(e)
            }, status=500)
        
    #  fill parameters using this
    def get_allegro_params(access_token, category_id):
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/categories/{category_id}/parameters"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()  
                return JsonResponse(data, safe=False)
            except ValueError as e:
                return JsonResponse(
                    {"error": "Invalid JSON response", "details": str(e)},
                    status=500
                )
        else:
            return JsonResponse(
                {
                    "error": "Failed to fetch data",
                    "status_code": response.status_code,
                    "details": response.text
                },
                status=response.status_code
            )
        
    #  fill Allegro_tyre_id using this
    def get_allegro_tyre_id(access_token,phrase):
        url ="https://api.allegro.pl.allegrosandbox.pl/sale/products"
        params ={
            "phrase": phrase
        }
        headers ={
            "Authorization":f"Bearer {access_token}",
            "Accept":"application/vnd.allegro.public.v1+json"
        }
        response = requests.get(url,params=params,headers=headers)
        if response.status_code ==200:
            try:
                data = response.json()
               
                return data
            except ValueError as e:
                return JsonResponse(
                    {"error":"invalid json response","details":str(e)}
                )
        else:
            return JsonResponse(
                {
                    "error":"failed to fwetch data",
                    "status_code": response.status_code,
                    "details":response.text
                },
                status = response.status_code
            )



