from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from tyreadderapp.models import Product, Pair

# from datetime import timezone
# from django.db import models
# from datetime import timedelta
# from django.core.exceptions import ObjectDoesNotExist

# Create your models here.
class Allegroauthdata(models.Model):
    access_token = models.TextField(null=True, blank=True)
    refresh_token= models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    refresh_token_expired_time=models.DateTimeField(null=True,blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def is_expired(self):
        #will_expire_soon
        return timezone.now() >= self.expires_at - timedelta(seconds=30)
    
    def __str__(self):
        return "Allegro Auth Token"
    
    
#################################################################

class AllegroAdvertData(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='allegro_single_advert_data',
        # blank=True,
        # null=True,
    )
    allegro_advert_id = models.BigIntegerField(blank=True, null=True)
     # timestamps from API
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, db_index=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)
    # valid_to = models.DateTimeField(blank=True, null=True)
    # allegro_advert_status = models.CharField(null=True, blank=True)
    # # otomoto_advert_description = models.TextField(
    # #     max_length=9000, null=True, blank=True)
    # is_autorefresh = models.BooleanField(default=False)
    # is_exported_to_olx = models.BooleanField(default=False)

    # # Aggregated stats
    # ad_views_total = models.PositiveIntegerField(default=0)
    # ad_visits_total = models.PositiveIntegerField(default=0)
    # phone_views_total = models.PositiveIntegerField(default=0)
    # phone_calls_total = models.PositiveIntegerField(default=0)
    # messages_total = models.PositiveIntegerField(default=0)
    # last_synced_at = models.DateTimeField(auto_now=True)


