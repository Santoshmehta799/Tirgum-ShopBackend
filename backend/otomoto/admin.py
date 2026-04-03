from django.contrib import admin


from otomoto.models import OtomotoAuthData,OtoMotoAdvertData, PairOtoMotoAdvertData
# Register your models here.

class OtoMotoAuthDataAdmin(admin.ModelAdmin):
    list_display = ("id","access_token")
    search_fields = ('id',)
    

# @admin.register(OtoMotoAdvertData)
# class OtoMotoAdvertDataAdmin(admin.ModelAdmin):
#     list_display = ("product", "created_at", "valid_to")


class OtoMotoAdvertDataAdmin(admin.ModelAdmin):
    list_display = ('product_pk', 'otomoto_advert_id', 'created_at', 'valid_to', 'ad_views_total')

    # Custom method to display only the product PK
    def product_pk(self, obj):
        return obj.product.pk
    
    def otomoto_advert_id(self, obj):
        return obj.otomoto_advert_id
    # product_pk.short_description = 'Product ID'  # optional column name
    

class PairOtoMotoAdvertDataAdmin(admin.ModelAdmin):
    list_display = ('product_pk', 'otomoto_advert_id','product_name')

    # Custom method to display only the product PK
    def product_pk(self, obj):
        return obj.pair.pk
    
    def otomoto_advert_id(self, obj):
        return obj.otomoto_advert_id
    
    def product_name(self, obj):
        return obj.pair.name
    # product_pk.short_description = 'Product ID'  # optional column name

admin.site.register(OtomotoAuthData,OtoMotoAuthDataAdmin)
admin.site.register(OtoMotoAdvertData,OtoMotoAdvertDataAdmin)
admin.site.register(PairOtoMotoAdvertData,PairOtoMotoAdvertDataAdmin)

