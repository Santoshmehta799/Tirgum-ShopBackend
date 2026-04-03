from django.db import models


class PayUAuth(models.Model):
    access_token = models.CharField(max_length=255,null=True, blank=True)
    token_type = models.CharField(max_length=255, default='Bearer', null=True, blank=True)
    # expires_in = models.IntegerField(null=True, blank=True,default=0)
    expires_in = models.DateTimeField(null=True, blank=True)
    grant_type = models.CharField(max_length=255, default='client_credentials', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

