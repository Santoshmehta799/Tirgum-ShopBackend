# # from socket import fromshare
from django import forms
from django.forms import ModelForm
from .models import Brand, Tread, Product, Image, Tread_Character, Staff,PairImage, Warehouse, Rack, Row, Staple
from datetime import datetime
from django.utils import timezone
# from django.forms import TextInput, SelectMultiple,Select


class ProductForm(forms.ModelForm):
        
    is_tire_bead_damaged = forms.BooleanField(
        label="Uszkodzona stopka", required=False)
    is_incised = forms.BooleanField(
        label="Nacinana", required=False)
    is_side_repair = forms.BooleanField(
        label="Naprawy boczne", required=False)
    
    is_visible_cracks = forms.BooleanField(
        label="Pęknięcia", required=False)

    is_braked = forms.BooleanField(
        label="Hamulec", required=False)
    is_cosmetology = forms.BooleanField(
        label="Kosmetyka", required=False)
    is_toothed_out = forms.BooleanField(
        label="Wyząbkowana", required=False)
    is_retreaded = forms.BooleanField(
        label="Bieżnikowana", required=False)
    is_ruts = forms.BooleanField(
        label="Koleiny", required=False)
    is_circumventional_cut = forms.BooleanField(
        label="Wycięty rowek", required=False)
    is_label_rinted = forms.BooleanField(
        label="Etykieta wydrukowana", required=False)
    dot = forms.IntegerField(label="Dot",required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg mb-3 py-3'}))
    
    
    tread_depth_min = forms.IntegerField(label="Min. głębokość bieżnika", widget=forms.TextInput(attrs={'class': 'form-control form-control-lg mb-3 py-3'}))
    tread_depth_max = forms.IntegerField(label="Max. głębokość bieżnika", widget=forms.TextInput(attrs={'class': 'form-control form-control-lg mb-3 py-3'}))
    
    net_price = forms.DecimalField(label="Cena netto",widget=forms.TextInput(attrs={'class': 'price form-control form-control-lg mb-3 py-3'}))
    # name = forms.CharField(widget=forms.TextInput(attrs={'class': 'custom-input'}))
    # supplier_price = forms.DecimalField(label="Ile kosztowała")
    # description = forms.ModelMultipleChoiceField(label = "Defects", queryset=Description.objects.all(), widget = forms.CheckboxSelectMultiple())
    additional_text = forms.BooleanField(
        label="Opis", required=False)
    
    class Meta:

        

        model = Product
        fields = ['brand', 'tread','size', 'is_tire_bead_damaged', 'is_incised', 'front_repairs',
                  'is_side_repair', 'is_visible_cracks',
                  'is_braked','is_braked_repair','is_shoulder_repair', 'is_cosmetology', 'is_toothed_out', 'is_retreaded',
                  'is_ruts','is_circumventional_cut','tread_depth_min','tread_depth_max', 'dot', 'net_price','pair','is_label_printed','additional_text']
        

        widgets = {
            'front_repairs': forms.Select(attrs={'class': 'form-select form-select-lg py-3 mb-3'}),
            'size': forms.Select(attrs={'class': 'form-select form-select-lg py-3 mb-3'}),
            'pair': forms.Select(attrs={'class': 'form-select form-select-lg py-3 mb-3'}),

        }
        




# FORM TO BE ABLE TO EDIT ALL INPUTS OF A PRODUCT
class EditProductForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude=["olx_advert_id","olx_response","product_listing_status","profit"]


class ProductCreateForm(forms.ModelForm):

    class Meta:
        model = Product

        exclude = ['is_allegro','is_otomoto','is_merchant_center','set_number','is_olx','is_olx_active',
                   'olx_advert_id','olx_response','olx_active_advert_response','profit',
                    'is_label_printed','advert_title','advert_description','status', 'product_listing_status']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tread'].queryset = Tread.objects.none()

        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['tread'].queryset = Tread.objects.filter(brand_id=brand_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['tread'].queryset = self.instance.brand.tread_set.all().order_by('name')
        
        if 'warehouse' in self.data:
            try:
                warehouse_id = int(self.data.get('warehouse'))
                self.fields['rack'].queryset = Rack.objects.filter(warehouse_id=warehouse_id).order_by('code')
                self.fields['row'].queryset = Row.objects.filter(warehouse_id=warehouse_id).order_by('code')
                self.fields['staple'].queryset = Staple.objects.filter(warehouse_id=warehouse_id).order_by('code')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.warehouse:
            self.fields['rack'].queryset = self.instance.warehouse.racks.all().order_by('code')
            self.fields['row'].queryset = self.instance.warehouse.rows.all().order_by('code')
            self.fields['staple'].queryset = self.instance.warehouse.rows.all().order_by('code')


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude = ['is_allegro','is_otomoto','is_merchant_center','set_number','is_olx','is_olx_active',
                   'olx_advert_id','olx_response','olx_active_advert_response','advert_title','advert_description',
                    'is_label_printed','profit', 'product_listing_status']

class BrandForm(forms.ModelForm):

    brand = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'sel', 'select': 'select', 'label': 'label'})
    )

    class Meta:

        model = Brand
        fields = "__all__"


class TreadForm(forms.ModelForm):

    class Meta:

        model = Tread
        fields = "__all__"





class ImageForm(forms.ModelForm):
    image = forms. ImageField(
        # widget=forms.ClearableFileInput(attrs={"multiple": True}),
        # widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
        # image = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
        widget=forms.ClearableFileInput(attrs={"allow_multiple_selected": True}), required=False
    )

    class Meta:
        model = Image
        fields = ["image",]


class StaffLoginForm(forms.ModelForm):

    
    class Meta:

        model = Staff
        fields = ("__all__")


class Tread_CharacterForm(forms.ModelForm):
       

    class Meta:        

        model = Tread_Character
        fields = ['brand', 'tread','size',\
                  'new_tire_price']
        

FORMAT_CHOICES = (
    ('csv','csv'),
    ('json','json'),
    ('xml','xml'),

)
from django.apps import apps

MODEL_CHOICES = ((str(item),(str(item)).title()) for item  in apps.get_app_config("tyreadderapp").models)

class FormatForm(forms.Form):
    format = forms.ChoiceField(choices = FORMAT_CHOICES)
    model = forms.ChoiceField(choices = MODEL_CHOICES)

class ImportForm(FormatForm):
    file=forms.FileField()



class PairImageForm(forms.ModelForm):
    class Meta:
        model = PairImage
        fields = ['pair', 'image']
        
        



# class ProductLocationAssignmentForm(forms.Form):
#     product_ids = forms.CharField(
#         widget=forms.Textarea(attrs={'placeholder': 'e.g. 123, 456, 789'}),
#         help_text="Enter Product IDs separated by commas, spaces, or new lines."
#     )

#     warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), required=True)
#     row = forms.ModelChoiceField(queryset=Row.objects.all(), required=False)
#     rack = forms.ModelChoiceField(queryset=Rack.objects.all(), required=False)
#     staple = forms.ModelChoiceField(queryset=Staple.objects.all(), required=False)

#     def clean_product_ids(self):
#         raw_ids = self.cleaned_data['product_ids']
#         id_list = [int(i) for i in raw_ids.replace(',', ' ').split() if i.isdigit()]
#         if not id_list:
#             raise forms.ValidationError("Please provide at least one valid Product ID.")
#         return id_list

#     def save(self):
#         ids = self.cleaned_data['product_ids']
#         warehouse = self.cleaned_data['warehouse']
#         row = self.cleaned_data.get('row')
#         rack = self.cleaned_data.get('rack')
#         staple = self.cleaned_data.get('staple')

#         updated_products = Product.objects.filter(id__in=ids)

#         for product in updated_products:
#             product.warehouse = warehouse
#             product.row = row
#             product.rack = rack
#             product.staple = staple
#             product.save()

#         return updated_products

class ProductLocationAssignmentForm(forms.Form):
    product_ids = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'e.g. 123, 456, 789'}),
        help_text="Enter Product IDs separated by commas, spaces, or new lines."
    )

    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), required=True)
    row = forms.ModelChoiceField(queryset=Row.objects.none(), required=False)
    rack = forms.ModelChoiceField(queryset=Rack.objects.none(), required=False)
    staple = forms.ModelChoiceField(queryset=Staple.objects.none(), required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        warehouse_id = None

        if 'warehouse' in self.data:
            try:
                warehouse_id = int(self.data.get('warehouse'))
            except (ValueError, TypeError):
                pass
        elif self.initial.get('warehouse'):
            warehouse_id = self.initial.get('warehouse').id

        if warehouse_id:
            self.fields['row'].queryset = Row.objects.filter(warehouse_id=warehouse_id)
            self.fields['rack'].queryset = Rack.objects.filter(warehouse_id=warehouse_id)
            self.fields['staple'].queryset = Staple.objects.filter(warehouse_id=warehouse_id)



    def clean_product_ids(self):
        raw_ids = self.cleaned_data['product_ids']
        id_list = [int(i) for i in raw_ids.replace(',', ' ').split() if i.isdigit()]
        if not id_list:
            raise forms.ValidationError("Please provide at least one valid Product ID.")
        return id_list

    def save(self):
        ids = self.cleaned_data['product_ids']
        warehouse = self.cleaned_data['warehouse']
        row = self.cleaned_data.get('row')
        rack = self.cleaned_data.get('rack')
        staple = self.cleaned_data.get('staple')

        queryset = Product.objects.filter(id__in=ids)

        # Efficient bulk update (single SQL query)
        queryset.update(
            warehouse=warehouse,
            row=row,
            rack=rack,
            staple=staple
        )

        # Return updated queryset (for display in template)
        return queryset

    


class StapleForm(forms.ModelForm):
    class Meta:
        model = Staple
        fields = ['warehouse', 'code', 'description']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            # 'description': forms.Textarea(attrs={'rows': 3}),
            # 'code': forms.Select(attrs={'class': 'form-select'}),
        }




from django import forms
from .models import Product, Pair


class ProductStatusForm(forms.Form):
    product_ids = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g. 123, 456, 789',
            'rows': 4
        }),
        help_text="Enter Product IDs separated by commas, spaces, or new lines."
    )

    pair_name = forms.CharField(
        required=False,
        help_text="Enter Pair name to update all products in that pair."
    )
    
    status = forms.ChoiceField(
        choices=Product.StatusChoices.choices,
        required=True,
        initial=Product.StatusChoices.SOLD
    )

    def clean_product_ids(self):
        raw_ids = self.cleaned_data.get('product_ids', '')
        if not raw_ids:
            return []
        
        return [int(i) for i in raw_ids.replace(',', ' ').split() if i.isdigit()]

    def clean(self):
        cleaned_data = super().clean()
        
        product_ids = cleaned_data.get('product_ids', [])
        pair_name = cleaned_data.get('pair_name')
        
        

        if not product_ids and not pair_name:
            raise forms.ValidationError(
                "You must provide either Product IDs or a Pair name."
            )

        if pair_name:
            pair_name = pair_name.strip().replace("\n", "").replace("\r", "")            
            
            try:
                cleaned_data['pair'] = Pair.objects.get(name__iexact=pair_name)
                # get_pair_name = cleaned_data['pair'].name
                # print(f"***********Pair found: {cleaned_data['pair'].name}")
            except Pair.DoesNotExist:
                 self.add_error('pair_name', "Pair with this name does not exist.")
                 
        
        else:
            cleaned_data["pair"] = None

        # print("***********Cleaned data:", cleaned_data)
        return cleaned_data
        


    def save(self):
        product_ids = self.cleaned_data.get('product_ids',[])
        pair = self.cleaned_data.get('pair') # 👈 use the Pair instance
        print(f"########## Pair in save(): {pair}")
        status = self.cleaned_data['status']

        qs = Product.objects.all()

        if product_ids:
            qs = qs.filter(id__in=product_ids)
            # print(f"########## Product IDs: {product_ids}")

        if pair:
            # print(f"Filtering products for pair: {pair}")
            qs = qs.filter(pair=pair)
            # print(f"&&&&&&&&&&&& '{qs}'")

        for product in qs:
            print(f"********************{product.id}")
            product.status = Product.StatusChoices.SOLD
            product.sold_at = timezone.now()  
            # Product.StatusChoices.SOLD
            # product.status = status
            product.save()
        # qs.update(
        #         status=Product.StatusChoices.SOLD,
        #         sold_at=timezone.now()
        #     )

        return qs

    
    
# class ProductSearchForm(forms.Form):
#     product_id = forms.IntegerField(required=False, label="ID")
#     brand = forms.CharField(required=False)
#     tread = forms.CharField(required=False)
#     size = forms.CharField(required=False)
    
    


class ProductSearchForm(forms.Form):
    product_id = forms.CharField(
        required=False,
        label="ID",
        widget=forms.TextInput(attrs={
            "class": "tyre-search-form-control",
            "placeholder": "Product ID"
        })
    )
    brand = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "tyre-search-form-control",
            "placeholder": "Marka"
        })
    )
    tread = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "tyre-search-form-control",
            "placeholder": "Bieżnik"
        })
    )
    size = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "tyre-search-form-control",
            "placeholder": "Rozmiar"
        })
    )
    pair_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "tyre-search-form-control",
            "placeholder": "Nawa Pary"
        }) 
    )
    # new filters for tread type
    is_steer = forms.BooleanField(required=False, label="Steer")
    is_drive = forms.BooleanField(required=False, label="Drive")
    is_trailer = forms.BooleanField(required=False, label="Trailer")
    
    only_pairs = forms.BooleanField(required=False, label="Pary")
    no_side_repairs = forms.BooleanField(required=False, label="Bez napraw bocznych")
    no_incised = forms.BooleanField(required=False, label="Bez nacinanych")
    no_retreaded = forms.BooleanField(required=False, label="Bez bieżnikowanych")
    is_brand_new_price = forms.BooleanField(required=False, label="Brand New Price")
    is_brand_new_tread = forms.BooleanField(required=False, label="Brand New Tread")
    only_retreaded = forms.BooleanField(required=False, label="Retreaded")
     # 🔹 Filters for remaining tread percent
    tread_remaining_min = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            "class": "tyre-search-form-control",
            "placeholder": "Min % bieżnika"
        }),
        label="Minimalny % bieżnika"
    )

    tread_remaining_max = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            "class": "tyre-search-form-control",
            "placeholder": "Max % bieżnika"
        }),
        label="Maksymalny % bieżnika"
    )
    
    





