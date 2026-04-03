import requests
from django.conf import settings


class OtomotoClientBase():
    
    OTOMOTO_USERNAME = "warsztatboruszowice@gmail.com"
    OTOMOTO_PASSWORD = "Oponki1234@"
    #Sandbox"
    # OTOMOTO_USERNAME = "szymon1987st@gmail.com"
    # OTOMOTO_PASSWORD = "PCXvhWK5SRttC3!"
    CLIENT_ID = "1434"
    CLIENT_SECRET = "a2d0cc4f28df802ec62e0012bde78ba6"
    # client_id = "1434"
    # client_secret = "a2d0cc4f28df802ec62e0012bde78ba6"
    # sandbox
    # auth_url = "https://sandbox.api.otomoto.pl/api/open/oauth/token"
    # not sandbox
    base_url = "https://www.otomoto.pl/api/open"
    redirect_uri = "https://770b5b975075.ngrok-free.app/otomoto/callback/"
    TOKEN_URL = "https://www.otomoto.pl/api/open/oauth/token"
    scope = "read write"
    domain = "https://tirgumpanel.pl/"
    
    # auth_url = "https://www.otomoto.pl/api/open/oauth/token"
    # url = "https://www.otomoto.pl/"
    
    
    # sandbox
    # base_url = "https://sandbox.api.otomoto.pl"
    
#     -----------------------------
#     USERNAME = "szymon1987st@gmail.com"
#     PASSWORD = "PCXvhWK5SRttC3!"
    


    # not sandbox
    # base_url = "https://www.otomoto.pl"
    
    ###
    

  
    
    #Fajny kod pod sandbox
    # def __init__(self, sandbox=False):
    #     if sandbox:
    #         self.base_url = "https://sandbox.api.otomoto.pl"
    #     else:
    #         self.base_url = "https://www.otomoto.pl/api/open"


    def __init__(self, auth_data=None):
        self.auth_data = auth_data
        self.session = requests.Session()
        
    # def ensure_authenticated(self):
    #     if not self.auth_data or self.auth_data.is_expired:
    #         self.refresh_access_token()
        
    
    def deactivate_otomoto_advert(self, otomoto_advert_id: str, access_token: str):
        url = f"https://www.otomoto.pl/api/open/account/adverts/{otomoto_advert_id}/deactivate"
        headers = {
            "User-Agent": self.OTOMOTO_USERNAME,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        payload = {
            "reason": {
                "id": 13,
                "description": "false"
            }
        }
        # response = requests.post(url, headers=headers, json=payload)
        response = self.session.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()  # optional: raises exception on 4xx/5xx

        return response
        
    





