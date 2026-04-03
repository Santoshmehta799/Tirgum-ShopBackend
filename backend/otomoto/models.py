from django.db import models
from django.utils import timezone
from datetime import date, datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist


import requests
from tyreadderapp.models import Product,Pair
from django.utils.translation import gettext_lazy as _


class OtomotoAuthData(models.Model):
    # increased length in case OLX tokens are long
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    
   
    def is_expired(self):
        #will_expire_soon
        return timezone.now() >= self.expires_at - timedelta(seconds=30)
    
    # def __str__(self):
    #     return "Otomoto OAuth credentials"
    

class OtoMotoAdvertData(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='otomoto_data',
        # blank=True,
        # null=True,
    )
    otomoto_advert_id = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    otomoto_advert_status = models.CharField(null=True, blank=True, max_length=255)
    # otomoto_advert_description = models.TextField(
    #     max_length=9000, null=True, blank=True)
    is_autorefresh = models.BooleanField(default=False)
    is_exported_to_olx = models.BooleanField(default=False)

    # Aggregated stats
    ad_views_total = models.PositiveIntegerField(default=0)
    ad_visits_total = models.PositiveIntegerField(default=0)
    phone_views_total = models.PositiveIntegerField(default=0)
    phone_calls_total = models.PositiveIntegerField(default=0)
    messages_total = models.PositiveIntegerField(default=0)
    last_synced_at = models.DateTimeField(auto_now=True)
    
    def refresh_ad(self):
        from .client import OtomotoClient

        """
        Activate advert only if:
        1) product exists and is_otomoto_advert_activated is True
        2) advert is not unpaid
        3) valid_to exists
        4) valid_to has passed
        """

        # 🔒 Autorefresh disabled → do nothing
        if not self.is_autorefresh:
            return None

        try:
            if not self.product.is_otomoto_advert_activated:
                return None
        except ObjectDoesNotExist:
            return None

        if self.otomoto_advert_status == "unpaid" or not self.valid_to:
            return None

        now = timezone.now()

        # Activate advert only if it expired
        if self.valid_to <= now:
            print("Advert expired. Activating Otomoto advert...")

            auth_data = OtomotoAuthData.objects.last()
            access_token = auth_data.access_token
            otomoto_advert_id = self.otomoto_advert_id

            OtomotoClient.activate_advert(self, otomoto_advert_id, access_token)

            return {"days": 0, "hours": 0}

        # If still active, return remaining time
        delta = self.valid_to - now
        remaining = {
            "days": delta.days,
            "hours": delta.seconds // 3600,
        }

        return remaining

       


    def save(self, *args, **kwargs):
        """
        Auto-update otomoto_advert_description every time the model is saved.
        """
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f" ID produktu: {self.product.pk}"





class PairOtoMotoAdvertData(models.Model):
    id = models.BigAutoField(primary_key=True)
    pair = models.OneToOneField(Pair, on_delete=models.CASCADE, related_name="otomoto_advert",blank=True, null=True)
    
    otomoto_advert_id = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    otomoto_advert_status = models.CharField(null=True, blank=True, max_length=255)
    # # otomoto_advert_description = models.TextField(
    # #     max_length=9000, null=True, blank=True)
    is_autorefresh = models.BooleanField(default=False)
    # is_exported_to_olx = models.BooleanField(default=False)

    # Aggregated stats
    ad_views_total = models.PositiveIntegerField(default=0)
    ad_visits_total = models.PositiveIntegerField(default=0)
    phone_views_total = models.PositiveIntegerField(default=0)
    phone_calls_total = models.PositiveIntegerField(default=0)
    messages_total = models.PositiveIntegerField(default=0)
    last_synced_at = models.DateTimeField(auto_now=True)