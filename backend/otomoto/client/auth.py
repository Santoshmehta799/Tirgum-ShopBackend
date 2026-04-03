import requests
from urllib.parse import urlencode
from django.utils import timezone
from datetime import timedelta
from otomoto.models import OtomotoAuthData
from otomoto.client.base import OtomotoClientBase



class OtomotoNotAuthenticated(Exception):
    pass

class OtomotoAuthMixin(OtomotoClientBase):
    
    def get_valid_access_token(self):
        """
        Retrieve a valid access token.
        
        - If `auth_data` is not loaded, fetch the latest token from the database.
        - If no token exists or it is expired, refresh or re-authenticate using password.
        
        Returns:
            str: A valid access token.
        """
        # Try to get the latest token from the DB if not already in memory
        if not hasattr(self, "auth_data") or self.auth_data is None:
            self.auth_data = OtomotoAuthData.objects.last()

        # If no token exists in DB or it's expired → refresh or re-authenticate
        if not self.auth_data or self.auth_data.is_expired():
            return self.refresh_access_token()

        return self.auth_data.access_token
    
    
    def ensure_authenticated(self):
        """
        Ensure that the current session has a valid access token.
        If the token is expired or missing, refresh it.
        
        Returns:
            str: A valid access token.
        """
        if not self.auth_data or self.auth_data.is_expired():
            self.refresh_access_token()    

        return self.auth_data.access_token
    
    

    def authenticate_with_password(self):
        """
        Authenticate with the Otomoto API using username and password.
        Saves the access and refresh tokens in the database.
        
        Returns:
            str: The new access token.
        
        Raises:
            requests.HTTPError: If the login request fails.
        """
        payload = {
            "grant_type": "password",
            "username": self.OTOMOTO_USERNAME,
            "password": self.OTOMOTO_PASSWORD,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
        }

        response = self.session.post(self.TOKEN_URL, data=payload)
        response.raise_for_status()

        self._save_tokens(response.json())
        return self.auth_data.access_token
    

    def refresh_access_token(self):
        """
        Refresh the access token using the refresh token.
        If refreshing fails, falls back to password authentication.
        
        Returns:
            str: A valid access token.
        """
        if not self.auth_data:
            return self.authenticate_with_password()
    
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.auth_data.refresh_token,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
        }

        response = self.session.post(self.TOKEN_URL, data=payload)

        if response.status_code != 200:
            # refresh fail → password login again
            return self.authenticate_with_password()

        self._save_tokens(response.json())
        return self.auth_data.access_token
       
    
    def _save_tokens(self, data):
        """
        Save access and refresh tokens to the database.
        Updates the latest `OtomotoAuthData` record if it exists, otherwise creates a new one.
        
        Args:
            data (dict): Dictionary containing 'access_token', 'refresh_token', and 'expires_in' fields.
        """
        expires_at = timezone.now() + timedelta(seconds=data["expires_in"])

        # Update latest token if exists, otherwise create
        auth_data = OtomotoAuthData.objects.last()
        if auth_data:
            auth_data.access_token = data["access_token"]
            auth_data.refresh_token = data["refresh_token"]
            auth_data.expires_at = expires_at
            auth_data.save()
        else:
            auth_data = OtomotoAuthData.objects.create(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_at=expires_at
            )
        self.auth_data = auth_data
    
    


