from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
import os
from django.utils import timezone


# from django.utils.translation import gettext_lazy as _


def get_profile_image_name(instance, filename):
    upload_to = "images/profile_pictures"
    ext = filename.split('.')[-1]
    filename = f"{instance.username}.{ext}"
    return os.path.join(upload_to, filename)


class User(AbstractUser):
    class UserType(models.TextChoices):
        SUPER_ADMIN = 'super_admin', ('super_admin')
        ADMIN = 'admin', ('admin')
        TEAM_LEADER = 'team_leader', ('team_leader')
        MANAGER = 'manager', ('manager')
        CUSTOMER = 'customer', ('customer')

    name = models.CharField(max_length=50, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    # address = models.TextField(null=True,blank=True)
    user_type = models.CharField(max_length=12, choices=UserType.choices, default=UserType.CUSTOMER)
    phone = models.CharField(max_length=14, null=True, blank=True)
    email = models.EmailField(('email address'), unique=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # profile_picture = models.ImageField(null=True, blank=True, upload_to=get_profile_image_name) ok
    # city = models.CharField(max_length=30, null=True, blank=True) ok
    # street = models.CharField(max_length=30, null=True, blank=True) ok
    # street_number = models.CharField(max_length=30, null=True, blank=True) ok
    # post_code = models.CharField(max_length=30, null=True, blank=True) ok
    # apartment_number = models.CharField(max_length=30, null=True, blank=True) ok
    # registry_number = models.CharField(max_length=30, null=True, blank=True)  ok

    company_name = models.CharField(max_length=30, null=True, blank=True)
    nip = models.CharField(max_length=10, null=True, blank=True)
    username = models.CharField(max_length=30, null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    
    company_street = models.CharField(max_length=555, null=True, blank=True)
    company_building = models.CharField(max_length=555, null=True, blank=True)
    company_apartment = models.CharField(max_length=555, null=True, blank=True)
    company_zip_code  = models.CharField(max_length=555, null=True, blank=True)
    company_city = models.CharField(max_length=555, null=True, blank=True)
    # company_address = models.CharField(max_length=555, null=True, blank=True)
    
    # company_delivery = models.CharField(max_length=555, null=True, blank=True)
    delivery_street = models.CharField(max_length=555, null=True, blank=True)
    delivery_building = models.CharField(max_length=555, null=True, blank=True)
    delivery_apartment = models.CharField(max_length=555, null=True, blank=True)
    delivery_zip_code = models.CharField(max_length=555, null=True, blank=True)
    delivery_city = models.CharField(max_length=555, null=True, blank=True)
    
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-id']

    def __str__(self):
        return f" {self.pk} - {self.email}"



class ContactUs(models.Model):
    name = models.CharField(max_length=225)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"