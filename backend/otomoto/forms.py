from django import forms

class AdvertForm(forms.Form):
    # Basic info
    id = forms.CharField(max_length=255, required=False)
    user_id = forms.CharField(max_length=255, required=False)
    status = forms.CharField(max_length=255, required=False)
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)
    
    # URL / title parts
    url = forms.CharField(max_length=255, required=False)
    title_parts = forms.CharField(max_length=255, required=False)
    
    # Price
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Price in PLN"
    )
    
    # Location info
    category_id = forms.IntegerField(required=False)
    region_id = forms.IntegerField(required=False)
    city_id = forms.IntegerField(required=False)
    district_id = forms.IntegerField(required=False)
    
    # Coordinates
    latitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False)
    
    # Contact info
    contact_person = forms.CharField(max_length=255, required=False)
    
    # Advert details
    advertiser_type = forms.CharField(max_length=50, required=False)
    new_used = forms.CharField(max_length=50, required=False)
    brand_program_id = forms.CharField(max_length=50, required=False)
    image_collection_id = forms.IntegerField(required=False)


    
