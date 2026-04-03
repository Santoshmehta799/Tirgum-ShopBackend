# utils.py (or anywhere suitable)
import requests
from datetime import date
from .models import OtoMotoAdvertData
from .client import OtomotoClient
from urllib.parse import urlencode
from tyreadderapp.models import Product
from django.utils.translation import gettext_lazy as _

def update_otomoto_stats(otomoto_data, access_token):
    if not otomoto_data.created_at:
        return
    
    # If advert_id is missing → show blank and stop
    if not otomoto_data.otomoto_advert_id:
        print(" ")   # or return " "
        return

    if not otomoto_data.created_at:
        return

    start = otomoto_data.created_at.strftime('%Y-%m-%d')
    end = date.today().strftime('%Y-%m-%d')
    params = urlencode({"start": start, "end": end})
    url = f"{OtomotoClient.main_url}/account/adverts/{otomoto_data.otomoto_advert_id}/stats/details?start={start}&end={end}"
    print(url)
    headers = {
        "User-Agent": "YOUR_EMAIL",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        totals = {
            "ad_views_total": sum(int(d.get("adViews", 0)) for d in data),
            "ad_visits_total": sum(int(d.get("adVisits", 0)) for d in data),
            "phone_views_total": sum(int(d.get("phoneViews", 0)) for d in data),
            "phone_calls_total": sum(int(d.get("phoneCalls", 0)) for d in data),
            "messages_total": sum(int(d.get("messages", 0)) for d in data),
        }

        for field, value in totals.items():
            setattr(otomoto_data, field, value)
        
        otomoto_data.save()
    except requests.RequestException as e:
        print(f"Error fetching Otomoto stats for {otomoto_data.product}: {e}")




# utils.py or services.py
from django.db import transaction
from .models import Pair


# def create_otomoto_pair_advert(pair_instance):
#     if pair_instance.is_otomoto_pair_advert_created:
#         return False  # Already created

#     def create_advert():
#         otomoto_client = OtomotoClient()
#         success = otomoto_client.create_and_save_pair_advert(pair_instance)

#         if success:
#             Pair.objects.filter(pk=pair_instance.pk).update(
#                 is_otomoto_pair_advert_created=True
#             )
#             print("Otomoto pair advert created successfully.")
#         else:
#             print("Failed to create Otomoto pair advert.")

#     transaction.on_commit(create_advert)
#     return True
