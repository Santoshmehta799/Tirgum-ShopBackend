# from import_export.admin import ImportExportModelAdmin
import logging
logger = logging.getLogger(__name__)

from import_export.admin import ExportMixin
from .models import (Brand, SelectedProductFilter, SimilarTread,Tyre_Ean, Tread, Product, Image, Tread_Character, New_Tread_Depth, Tread_Image, Staff, Size, Pair, Pallete,
                    PairImage, TransportationCost, Company, Warehouse, Rack,StockItem, Row, Staple )


from django.contrib import admin
from import_export import resources, fields
from . import models as tyreadderapp_models, resources as tyre_resources
from import_export.widgets import ForeignKeyWidget
from .resources import ProductResource,NewTreadDepthResource, TreadResource
from import_export.formats.base_formats import CSV
from import_export.admin import ImportExportModelAdmin
from .resources import TreadCharacterResource 




# Register your models here.




class ProductAdmin(ExportMixin,admin.ModelAdmin):
   resource_class = ProductResource  # dodane
   list_filter = ("brand", "tread", "is_tire_bead_damaged", "is_incised", "size",
                  "front_repairs", "is_side_repair", "is_visible_cracks", "is_braked", "is_braked_repair",
                  "is_shoulder_repair", "is_cosmetology", "is_toothed_out", "is_retreaded", "is_ruts",
                  "tread_depth_min", "tread_depth_max")


   list_display = ("id", "brand", "tread","size", "pair", 'status','olx_advert_id','olx_advert_status', "is_tire_bead_damaged", 'is_olx', 'is_olx_active', 'product_listing_status',"is_incised",
                   "front_repairs", "is_side_repair", "is_visible_cracks", "is_braked", "is_braked_repair",
                   "is_shoulder_repair", "is_cosmetology", "is_toothed_out", "is_retreaded", "is_ruts",
                   "tread_depth_min", "tread_depth_max","optimized_brand","optimized_tread","weight","tread_id")
   search_fields = ("olx_advert_id","id",)



class BrandAdmin(admin.ModelAdmin):
   list_display = ("id", "name", "country_of_origin", "allegro_brand_id")
   search_fields = ("id","name","country_of_origin","allegro_brand_id",)



class TransportAdmin(admin.ModelAdmin):
   list_display = ("id", "pallet", "company", "kg", "price", "pal_discounted_price")


class SizeAdmin(admin.ModelAdmin):
   list_display = ("id", "size", "slug", "description")
   search_fields = ("id","size","slug",)


class SimilarTreadAdmin(admin.ModelAdmin):
   list_display = ('id', 'brand', 'tread', 'similar_trade_combinations',)


   def similar_trade_combinations(self, obj):
       return ", ".join([
           f"{st.brand.name} - {st.tread.name}"
           for st in obj.similar_tread_combinations.all()
       ])


class SelectedProductFilterAdmin(admin.ModelAdmin):
   list_display = ('id', 'name', "brand",'tread','size')




admin.site.register(SimilarTread, SimilarTreadAdmin)
admin.site.register(Brand)
# admin.site.register(Tread, TreadAdmin)
admin.site.register(Product, ProductAdmin)
# admin.site.register(Image)

admin.site.register(Tread_Image)
admin.site.register(Staff)
admin.site.register(Size, SizeAdmin)
#admin.site.register(Pair)
admin.site.register(TransportationCost, TransportAdmin)
admin.site.register(Company)
admin.site.register(Warehouse)
admin.site.register(Rack)
admin.site.register(Row)
admin.site.register(Staple)
admin.site.register(StockItem)
admin.site.register(SelectedProductFilter, SelectedProductFilterAdmin)


# admin.site.register(PairImage)
@admin.register(Tyre_Ean)
class EanAdmin(admin.ModelAdmin):
   list_display = ('ean','ean_brand', 'ean_tread', 'ean_size', 'ean_li', 'ean_si')
   list_filter = ('ean_brand',)
   search_fields = ('ean_size',)


@admin.register(Pallete)
class PalleteAdmin(ImportExportModelAdmin):
   resource_class = tyre_resources.PalleteResource
   list_display = ('name', 'net_price', 'mht', "X", "Y", "empty_pal_weight")
   search_fields = ('name', 'mht')






@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
   list_display = ('product_id', 'image',)
   search_fields = ('product__id','image')




@admin.register(Pair)
class pair(admin.ModelAdmin):
  list_display = ("id","name","pair_title","blocked_pair",'pair_listing_status', "pair_is_olx","pair_is_olx_active","pair_olx_advert_id","pair_olx_response","pair_olx_active_advert_response","blocked_pair")
  search_fields = ('id',)




@admin.register(PairImage)
class PairImageAdmin(admin.ModelAdmin):
   list_display = ('pair_id','pair','image','pair_name')
   search_fields = ('pair__id',)
   
   def pair_name(self, obj):
        return (f"{obj.pair.name}|")
   
   # pair_name.short_description = "Pair name"



# @admin.register(New_Tread_Depth)
# class NewTreadDepthAdmin(ImportExportModelAdmin):
#     resource_class = NewTreadDepthResource
#     list_display = ('brand', 'tread', 'size', 'new_tire_tread_depth')
#     search_fields = ('brand', 'tread', 'size')

from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import New_Tread_Depth, Product
from .resources import NewTreadDepthResource

@admin.register(New_Tread_Depth)
class NewTreadDepthAdmin(ImportExportModelAdmin):
    resource_class = NewTreadDepthResource
    list_display = ('brand', 'tread', 'size', 'new_tire_tread_depth')
    search_fields = ('brand', 'tread', 'size')

    # Button in top admin bar
    change_list_template = "admin/tyreadderapp/new_tread_depth/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'refresh-all/',
                self.admin_site.admin_view(self.refresh_all),
                name='refresh_new_tread_depth_all'
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['refresh_all_url'] = reverse('admin:refresh_new_tread_depth_all')
        return super().changelist_view(request, extra_context=extra_context)

    def refresh_all(self, request):
        updated_count = 0
        for depth_entry in New_Tread_Depth.objects.all():
            products = Product.objects.filter(optimized_tyre_name=depth_entry.optimized_tyre_name)
            for product in products:
                old_depth = product.new_tire_tread_depth
                if depth_entry.new_tire_tread_depth is not None and depth_entry.new_tire_tread_depth != old_depth:
                    product.new_tire_tread_depth = depth_entry.new_tire_tread_depth
                    product.save(update_fields=['new_tire_tread_depth'])
                    updated_count += 1

        self.message_user(request, f"Refreshed new_tire_tread_depth for {updated_count} products!")
        return redirect(request.META.get('HTTP_REFERER', '/'))


    

@admin.register(Tread)
class TreadAdmin(ImportExportModelAdmin):
    resource_class = TreadResource
    list_display = ('id','name', 'brand', 'has_image','product_count')
    search_fields = ('name',)


# @admin.register(Tread_Character)
# class TreadCharacterAdmin(ImportExportModelAdmin):
#    list_display = ('brand', 'tread','size','optimized_tyre_name')
#    resource_class = TreadCharacterResource
#    search_fields = ('optimized_tyre_name',)

from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Tread_Character, Product
from .resources import TreadCharacterResource


from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from import_export.admin import ImportExportModelAdmin
from .models import Tread_Character, Product
from .resources import TreadCharacterResource




# def refresh_all(self, request):
#     try:
#         logger.info("Refresh started")
#         updated_count = 0

#         for tread_char in Tread_Character.objects.all():
#             logger.info(f"Processing {tread_char.id}")
#             products = Product.objects.filter(
#                 optimized_tyre_name=tread_char.optimized_tyre_name
#             )

#             for product in products:
#                 if (
#                     tread_char.new_tire_price is not None and
#                     tread_char.new_tire_price != product.new_tire_price
#                 ):
#                     product.new_tire_price = tread_char.new_tire_price
#                     product.save(update_fields=['new_tire_price'])
#                     updated_count += 1

#         logger.info(f"Updated {updated_count} products")
#         self.message_user(request, f"Updated {updated_count} products")

#     except Exception as e:
#         logger.exception("Refresh all crashed")

#     return redirect(request.META.get('HTTP_REFERER', '/'))



@admin.register(Tread_Character)
class TreadCharacterAdmin(ImportExportModelAdmin):
    resource_class = TreadCharacterResource
    list_display = ('brand', 'tread', 'size', 'optimized_tyre_name')
    search_fields = ('optimized_tyre_name',)

    # Add a button in the top "object tools" bar
    change_list_template = "admin/tyreadderapp/tread_character/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'refresh-all/',
                self.admin_site.admin_view(self.refresh_all),
                name='refresh_tread_character_all'
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add a 'Refresh All Products' button in the top admin bar"""
        if extra_context is None:
            extra_context = {}
        extra_context['refresh_all_url'] = reverse('admin:refresh_tread_character_all')
        return super().changelist_view(request, extra_context=extra_context)

    # def refresh_all(self, request):
    #     """Refresh all products, but only if data has changed"""
    #     updated_count = 0
    #     for tread_char in Tread_Character.objects.all():
    #         products = Product.objects.filter(optimized_tyre_name=tread_char.optimized_tyre_name)
    #         for product in products:
    #             old_price = product.new_tire_price
    #             if tread_char.new_tire_price is not None and tread_char.new_tire_price != old_price:
    #                 product.new_tire_price = tread_char.new_tire_price
    #                 product.save(update_fields=['new_tire_price'])
    #                 updated_count += 1

    #     self.message_user(request, f"Refreshed new_tire_price for {updated_count} products!")
    #     return redirect(request.META.get('HTTP_REFERER', '/'))
    
    def refresh_all(self, request):
        try:
            logger.info("Refresh started")
            updated_count = 0

            for tread_char in Tread_Character.objects.all():
                logger.info(f"Processing {tread_char.id}")
                products = Product.objects.filter(
                    optimized_tyre_name=tread_char.optimized_tyre_name
                )

                for product in products:
                    old_price = product.new_tire_price
                    if tread_char.new_tire_price is not None and tread_char.new_tire_price != old_price:
                        Product.objects.filter(id=product.id).update(new_tire_price=tread_char.new_tire_price)
                        updated_count += 1

            logger.info(f"Updated {updated_count} products")
            self.message_user(request, f"Updated {updated_count} products")

        except Exception as e:
            logger.exception("Refresh all crashed")

        return redirect(request.META.get('HTTP_REFERER', '/'))




   


# @admin.action(description="Refresh new tire data from reference models")
# def refresh_new_tire_data(modeladmin, request, queryset):
#     updated_count = 0
#     for product in queryset:
#         old_price = product.new_tire_price
#         old_depth = product.new_tire_tread_depth
#         product.refresh_new_tire_data()
#         if product.new_tire_price != old_price or product.new_tire_tread_depth != old_depth:
#             updated_count += 1
#     modeladmin.message_user(request, f"Refreshed new tire data for {updated_count} products!")


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['id', 'optimized_tyre_name', 'new_tire_price', 'new_tire_tread_depth']
#     actions = [refresh_new_tire_data]
