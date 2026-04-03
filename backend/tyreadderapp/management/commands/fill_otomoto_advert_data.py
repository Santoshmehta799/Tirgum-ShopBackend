import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from otomoto.models import PairOtoMotoAdvertData
import requests
from otomoto.client.base import OtomotoClientBase
from otomoto.client.auth import OtomotoAuthMixin
from django.conf import settings


class Command(BaseCommand):
    help = "Fill missing Otomoto advert data (status, created_at, valid_to) for existing adverts."

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # You will need a valid session with your access token
        session = requests.Session()
        # Example: replace this with your actual token retrieval
        # access_token = "YOUR_ACCESS_TOKEN_HERE"
        # --- Temporary client to get a valid access token ---
        class TempClient(OtomotoAuthMixin, OtomotoClientBase):
            TOKEN_URL = "https://www.otomoto.pl/api/open/oauth/token",
            CLIENT_ID = "1434"
            CLIENT_SECRET = "a2d0cc4f28df802ec62e0012bde78ba6",
            
            OTOMOTO_USERNAME = "warsztatboruszowice@gmail.com"
            OTOMOTO_PASSWORD = "Oponki1234@"
        
        client = TempClient()
        access_token = client.get_valid_access_token()
        
        session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        })

        def make_aware_if_needed(dt):
            if dt and timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return dt

        updated_count = 0
        qs = PairOtoMotoAdvertData.objects.filter(otomoto_advert_id__isnull=False)
        for advert in qs:
            advert_id = advert.otomoto_advert_id
            url = f"https://www.otomoto.pl/api/open/account/adverts/{advert_id}"
            try:
                response = session.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch advert {advert_id}: {e}")
                continue

            # Parse API response
            status = data.get("status")
            created_at = make_aware_if_needed(parse_datetime(data.get("created_at")))
            valid_to = make_aware_if_needed(parse_datetime(data.get("valid_to")))

            # Update only if something is missing
            updated = False
            if advert.otomoto_advert_status != status:
                advert.otomoto_advert_status = status
                updated = True
            if advert.created_at != created_at:
                advert.created_at = created_at
                updated = True
            if advert.valid_to != valid_to:
                advert.valid_to = valid_to
                updated = True

            if updated:
                advert.save(update_fields=["otomoto_advert_status", "created_at", "valid_to"])
                updated_count += 1
                logger.info(f"Updated advert {advert_id}")

        self.stdout.write(self.style.SUCCESS(f"Total adverts updated: {updated_count}"))