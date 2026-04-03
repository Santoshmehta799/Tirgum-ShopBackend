from django.db import models
from django.utils import timezone

# Create your models here.
class OLXAuthData(models.Model):
    access_token=models.CharField(max_length=50)
    refresh_token=models.CharField(max_length=50)
    access_token_expired_time=models.DateTimeField()
    refresh_token_expired_time=models.DateTimeField()
    olx_code=models.CharField(max_length=50,null=True,blank=True)


    def is_access_token_expired(self):
        current_date_time=timezone.now()
        return not self.access_token_expired_time >= current_date_time

    def is_refresh_token_expired(self):
        current_date_time=timezone.now()
        return not self.refresh_token_expired_time >= current_date_time
    
