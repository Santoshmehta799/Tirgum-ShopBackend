import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from allegro.models import Allegroauthdata
import base64




import requests
import base64
from django.utils import timezone
from datetime import timedelta

class AllegroClientBase:
    
    CLIENT_ID = "1c952b8d6b3f416598de1d91c0bcb63b"

    # CLIENT_ID = "819e6c3e67b74b59ae97913caaec41b8" sandbox
    CLIENT_SECRET = "jx9YllUhbyuknGYx9VlTf7s5YojA6eqBU9hzjh6IMRO4WuGFW3NCf1opm1IKtdzr"
    # CLIENT_SECRET = "ZP7CLmi62vOWgM9ydVnYg4GNFGxdmhCZ40yM7a7Hi2xPRiOVIX9HYLLUvoDEtSdN"sandbox
    # TOKEN_URL = "https://allegro.pl/allegrosandbox.pl/auth/oauth/token"
    # TOKEN_URL = "https://allegro.pl/auth/oauth/token"
    # REDIRECT_URI = "http://www.tirgumpanel.pl/allegro/callback"
    
    
    # REDIRECT_URI = "http://localhost:8000/allegro/callback/"
    # REDIRECT_URI = "http://localhost:8000/allegro/callback/"
    REDIRECT_URI = "https://www.tirgumpanel.pl/allegro/callback/"
    # AUTH_URL = "https://allegro.pl/allegrosandbox.pl/auth/oauth/authorize"
    
    AUTH_URL = "https://allegro.pl/auth/oauth/authorize"
    
    # AUTH_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/authorize"
    TOKEN_URL = "https://allegro.pl/auth/oauth/token"
    # TOKEN_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/token"

    def __init__(self):
        self.session = requests.Session()

    def _get_oauth_headers(self):
        credentials = f"{self.CLIENT_ID}:{self.CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def refresh_token(self, refresh_token):
        """
        Uses the Allegro refresh token to get a new access token.
        Returns the token dict, ready to pass to save_tokens().
        """
        headers = self._get_oauth_headers()
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        response = self.session.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()  # raise error if request fails
        tokens = response.json()
        return tokens
    


from django.utils import timezone
from datetime import timedelta
from allegro.models import Allegroauthdata

class AllegroClient(AllegroClientBase):
    TOKEN_EXPIRY_MARGIN = 30  # seconds before expiry to refresh

    def __init__(self, auth_data: Allegroauthdata):
        super().__init__()
        self.auth_data = auth_data
        self.access_token = auth_data.access_token

    def is_token_expired(self):
        # checks if token is expired or about to expire
        return timezone.now() >= self.auth_data.expires_at - timedelta(seconds=self.TOKEN_EXPIRY_MARGIN)

    def ensure_authenticated(self):
        if self.is_token_expired():
            self.refresh_and_save_token()

    def refresh_and_save_token(self):
        if not self.auth_data.refresh_token:
            raise Exception("No refresh token available to refresh Allegro access token")

        tokens = self.refresh_token(self.auth_data.refresh_token)
        self.access_token = tokens["access_token"]
        self.auth_data.access_token = tokens["access_token"]
        self.auth_data.refresh_token = tokens.get("refresh_token", self.auth_data.refresh_token)
        self.auth_data.expires_at = timezone.now() + timedelta(seconds=tokens["expires_in"])
        self.auth_data.save()
    
    def get_valid_access_token(self):
        """
        Returns a valid access token. Refreshes it if expired or about to expire.
        """
        if self.auth_data.is_expired():
            self.refresh_and_save_token()
        return self.access_token
    
    
    def get_active_offer_ids(self):
        access_token = self.get_valid_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json",
        }

        active_ids = []
        url = "https://api.allegro.pl/sale/offers?publication.status=ACTIVE&limit=100"
        while url:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            active_ids.extend(offer["id"] for offer in data.get("offers", []))
            url = data.get("next")  # if Allegro API returns pagination links
        return active_ids