from otomoto.client.single.otomoto_single_ad import OtomotoSingleAd
from otomoto.client.pair.otomoto_pair_ad import OtomotoPairAd
from .auth import OtomotoAuthMixin
# from .tokens import OtomotoTokenStorageMixin
from otomoto.client.auth import OtomotoAuthMixin


# from .api_brands import api_brands
from otomoto.api_brands import api_brands



class OtomotoClient(
    OtomotoAuthMixin,
    # OtomotoTokenStorageMixin,
    # OtomotoClientBase,
    # OtomotoSingleAd,
    # OtomotoPairAd
    
):
    pass
    # def ensure_authenticated(self):
    #     if not self.auth_data or self.auth_data.is_expired:
    #         self.refresh_access_token()
    # def ensure_authenticated(self):
    #     if not hasattr(self, 'auth_data') or not self.auth_data or self.auth_data.is_expired:
    #         self.refresh_access_token()




class AuthOtomotoClient(OtomotoAuthMixin):

    # def ensure_authenticated(self):
    #     if not self.auth_data:
    #         return self.authenticate_with_password()

    #     if self.auth_data.is_expired():
    #         return self.refresh_access_token()

    #     return self.auth_data.access_token

    # 🔥 REAL API CALL
    def get_my_adverts(self):
        access_token = self.ensure_authenticated()

        url = "https://www.otomoto.pl/api/open/account/adverts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = self.session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    