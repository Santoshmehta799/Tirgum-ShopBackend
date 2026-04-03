from django.contrib import admin
from olx.models import OLXAuthData
# Register your models here.

class OlxAuthDataAdmin(admin.ModelAdmin):
    list_display = ("id","access_token")
    search_fields = ('id',)


admin.site.register(OLXAuthData,OlxAuthDataAdmin)