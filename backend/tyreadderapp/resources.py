from import_export import resources,fields
from import_export.widgets import ForeignKeyWidget,NumberWidget, CharWidget, FloatWidget
from import_export.formats.base_formats import CSV
from import_export.admin import ExportMixin
from import_export.admin import ImportExportModelAdmin


from .models import Brand, Tread, Product, Image, Tread_Character, New_Tread_Depth, Tread_Image, Staff,Size,Pair, Pallete
from django.contrib import admin




class SizeResource(resources.ModelResource):
   class Meta:
       model = Size


class BrandResource(resources.ModelResource):
   class Meta:
       model = Brand




class TreadResource(resources.ModelResource):


   brand = fields.Field(
       column_name='brand',
       attribute='brand',
       widget=ForeignKeyWidget(Brand, field='name'))
  
   class Meta:
       model = Tread
       export_order=("id","name","brand")






class BaseResource(resources.ModelResource):
   id=fields.Field(attribute='id', column_name='id',
       widget=NumberWidget())


   brand = fields.Field(
       column_name='brand',
       attribute='brand',
       widget=ForeignKeyWidget(Brand, field='name'))


   tread = fields.Field(
       column_name='tread',
       attribute='tread',
       widget=ForeignKeyWidget(Tread, field='name'))


   size = fields.Field(
       column_name='size',
       attribute='size',
       widget=ForeignKeyWidget(Size, field='size'))






class ProductResource(resources.ModelResource):
   class Meta:
       model = Product
       fields = (
           'brand__name',
           'tread__name',
           'size__size',
           'is_tire_bead_damaged',
           'is_incised',
           'front_repairs',
           'is_front_heat_repair',
           'is_side_repair',
           'is_visible_cracks',
           'is_braked',
           'is_braked_repair',
           'is_shoulder_repair',
           'is_cosmetology',
           'is_toothed_out',
           'is_retreaded',
           'is_ruts',
           'is_circumventional_cut',
           'tread_depth_min',
           'tread_depth_max',
           'dot',
           'net_price',
       )
   def get_export_formats(self):
       return [CSV()]  




# class Tread_CharacterResource(BaseResource):
#    class Meta:
#        model = Tread_Character
       

from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Tread_Character


class TreadCharacterResource(resources.ModelResource):
    class Meta:
        model = Tread_Character
        import_id_fields = ('brand', 'tread', 'size')  # prevent duplicates
        fields = (
            'brand',
            'tread',
            'size',
            'new_tire_price',
            'shop_url',
        )
        skip_unchanged = True
        report_skipped = True



class TreadCharacterAdmin(ImportExportModelAdmin):
    resource_class = TreadCharacterResource



class New_Tread_DepthResource(resources.ModelResource):
   class Meta:
       model = New_Tread_Depth
       # fields = ('brand__name', 'tread__name', 'width__name', 'profile__profile', 'diameter__diameter',
       #           'axis', 'direction', 'sips_quantity', 'new_tire_price', 'new_tire_tread_depth', 'recommended_pressure')


       # export_order = ('brand__name', 'tread__name', 'width__name', 'profile__profile', 'diameter__diameter',
       #                 'axis', 'direction', 'sips_quantity', 'new_tire_price', 'new_tire_tread_depth', 'recommended_pressure')






# class BaseResource(resources.ModelResource):
#     class Meta:
#         fields="__all__"


# def get_resource(model):
#     model=getattr(tyreadderapp_models,model.title())
#     BaseResource._meta.model=model
#     BaseResource.Meta.model=model
#     return BaseResource()
      




class PalleteResource(resources.ModelResource):
   class Meta:
       model = Pallete
       import_id_fields = ('id',)
       fields = ('id', 'name', 'net_price', 'mht', 'X', 'Y')
       export_order = ('id', 'name', 'net_price', 'mht', 'X', 'Y')


class NewTreadDepthResource(resources.ModelResource):
    
    # optimized_brand = fields.Field(attribute='optimized_brand', readonly=True)
    # optimized_tread = fields.Field(attribute='optimized_tread', readonly=True)
    
    class Meta:
        model = New_Tread_Depth
        fields = (
            'id',
            'brand',
            'tread',
            'size',
            'new_tire_tread_depth',
        )
        export_order = fields
    
    def get_instance(self, instance_loader, row):
        # Prevent duplicates based on brand, tread, size
        return New_Tread_Depth.objects.filter(
            brand=row.get('brand'),
            tread=row.get('tread'),
            size=row.get('size')
        ).first()
    
    # def skip_row(self, instance, original, row, import_validation_errors):
    #     return instance is not None
    
    def before_import_row(self, row, **kwargs):
        try:
            # Validate float type
            float(row.get('new_tire_tread_depth'))
        except (ValueError, TypeError):
            raise Exception(f"Invalid depth value: {row.get('new_tire_tread_depth')}")
        

class TreadResource(resources.ModelResource):
    brand = fields.Field(
        column_name='brand',
        attribute='brand',
        widget=ForeignKeyWidget(Brand, field='name')  # Make sure 'name' is unique or switch to 'id'
    )

    class Meta:
        model = Tread
        import_id_fields = ['id']
        fields = (
            'id',
            'name',
            'brand',
            'is_steer',
            'is_drive',
            'is_trailer',
            'is_m_s',
            'is_3pmsf',
            'has_image',
        )
        export_order = fields
