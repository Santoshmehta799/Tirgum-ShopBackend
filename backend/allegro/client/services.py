from django.utils import timezone
from datetime import timedelta

from allegro.models import Allegroauthdata
from allegro.client.client import AllegroClientBase


from django.utils import timezone
from datetime import timedelta
from allegro.models import Allegroauthdata

class AllegroAuthService:

    @staticmethod
    def save_tokens(tokens):
        """
        Save or update Allegro access/refresh tokens in the DB.
        """
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in")

        if not access_token or not refresh_token or not expires_in:
            raise ValueError(f"Invalid token data: {tokens}")

        expires_at = timezone.now() + timedelta(seconds=expires_in)
        refresh_token_expiry = timezone.now() + timedelta(days=30)

        auth = Allegroauthdata.objects.first()
        if auth:
            # Update existing record
            auth.access_token = access_token
            auth.refresh_token = refresh_token
            auth.expires_at = expires_at
            auth.refresh_token_expired_time = refresh_token_expiry
            auth.save()
            created = False
        else:
            # First connection
            auth = Allegroauthdata.objects.create(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                refresh_token_expired_time=refresh_token_expiry
            )
            created = True

        print(f"Saved Allegro tokens, created={created}, id={auth.id}")
        return auth

    # @staticmethod
    # def get_valid_access_token():
    #     """
    #     Returns a valid access token. Refreshes if expired.
    #     """
    #     auth = Allegroauthdata.objects.first()

    #     if not auth:
    #         raise Exception("Allegro not connected")

    #     if auth.is_expired():
    #         client = AllegroClientBase()
    #         tokens = client.refresh_token(auth.refresh_token)
    #         auth = AllegroAuthService.save_tokens(tokens)

    #     return auth.access_token