from itertools import product
# from tkinter import Image
from rest_framework import serializers
from ..models import Product, Tread_Character, Image, Size, Brand, Tread, Pair, Pallete, TransportationCost, New_Tread_Depth, SelectedProductFilter
from django.utils.translation import gettext_lazy as _
from tyreadderapp.filters import ProductFilter
from tyreadderapp.api.processor import get_optimized_value
from datetime import datetime
from django.db.models import Count


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ["id", "size"]


class SelectedProductFilterSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    TRUE_NULL_CHOICES = [
        (True, 'Tak'),
        (None, 'Brak')
    ]

    is_tire_bead_damaged = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_front_heat_repair = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_side_repair = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_visible_cracks = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_braked = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_braked_repair = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_shoulder_repair = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_cosmetology = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_toothed_out = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_retreaded = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_ruts = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    is_circumventional_cut = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    issteer = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    isdrive = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)
    istrailer = serializers.ChoiceField(
        choices=TRUE_NULL_CHOICES, allow_null=True, required=False)

    class Meta:
        model = SelectedProductFilter
        fields = [
            'id',
            'name',
            'brand',
            'tread',
            'size',
            'is_tire_bead_damaged',
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
            'oldest_dot',
            'tread_depth_min',
            'issteer',
            'isdrive',
            'istrailer',
            'products',
        ]

    def get_products(self, obj):
        queryset = Product.objects.all()

        # Normal filters (brand, tread, size)
        if obj.brand:
            queryset = queryset.filter(brand=obj.brand)
        if obj.tread:
            queryset = queryset.filter(tread=obj.tread)
        if obj.size:
            queryset = queryset.filter(size=obj.size)
        if obj.oldest_dot:
            current_year = datetime.now().year
            age = current_year - int(obj.oldest_dot)
            queryset = queryset.filter(dot__gte=age)
        if obj.tread_depth_min:
            queryset = queryset.filter(
                tread_depth_min__gte=obj.tread_depth_min)
        if obj.issteer:
            queryset = queryset.filter(issteer=obj.issteer)
        if obj.isdrive:
            queryset = queryset.filter(isdrive=obj.isdrive)
        if obj.istrailer:
            queryset = queryset.filter(istrailer=obj.istrailer)

        # Boolean exclusion logic
        boolean_fields = [
            'is_tire_bead_damaged',
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
        ]

        for field in boolean_fields:
            value = getattr(obj, field)
            if value is True:
                queryset = queryset.exclude(**{field: True})

        return ProductSerializer(queryset, many=True, context=self.context).data


class TreadSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)

    class Meta:
        model = Tread
        fields = "__all__"


class TreadNameIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tread
        fields = ['id', 'name']


class SizeSerializer(serializers.ModelSerializer):
    real_profile_dim = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    pair_quantity = serializers.SerializerMethodField()
    count_of_brands = serializers.SerializerMethodField()
    count_of_brand_pairs = serializers.SerializerMethodField()

    class Meta:
        model = Size
        fields = "__all__"

    def get_real_profile_dim(self, obj):
        return obj.real_profile_dim()

    def get_quantity(self, obj):
        return Product.objects.filter(size=obj, status=Product.StatusChoices.ON_SALE).count()

    def get_pair_quantity(self, obj):
        return Pair.objects.filter(
            product__size=obj,
            product__status=Product.StatusChoices.ON_SALE
        ).distinct().count()

    def get_count_of_brands(self, obj):
        # Get product counts grouped by brand for this size
        brand_counts = (
            Product.objects
            .filter(size=obj, status=Product.StatusChoices.ON_SALE)
            # or 'brand__id' and 'brand__name' if you want IDs too
            .values('brand__name')
            .annotate(count=Count('id'))
            .order_by('-count')  # optional
        )
        # Return as list of dicts
        return [
            {"brand": item["brand__name"], "count": item["count"]}
            for item in brand_counts
        ]
        
    
    def get_count_of_brand_pairs(self, obj):
        brand_pair_counts = (
            Product.objects
            .filter(
                size=obj,
                status=Product.StatusChoices.ON_SALE,
                pair__isnull=False,
            )
            .values( 'brand__id','brand__name')  
            .annotate(count=Count('pair', distinct=True))
            .order_by('-count')
        )

        return [
            {
                "brand_id": item["brand__id"],
                "brand": item["brand__name"],                 
                "count": item["count"]
            }
            for item in brand_pair_counts
        ]

    


class BrandSerializer(serializers.ModelSerializer):
    brand_quantity = serializers.SerializerMethodField()
    brand_pair_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = "__all__"

    def get_brand_quantity(self, obj):
        size = self.context.get('size')
        qs = Product.objects.filter(
            brand=obj, status=Product.StatusChoices.ON_SALE)
        if size:
            qs = qs.filter(size=size)
        return qs.count()

    def get_brand_pair_quantity(self, obj):
        size = self.context.get('size')
        qs = Pair.objects.filter(
            product__brand=obj,
            product__status=Product.StatusChoices.ON_SALE,
        )
        if size:
            qs = qs.filter(product__size=size)
        return qs.distinct().count()


class PairSerializer(serializers.ModelSerializer):
    # LiteProductSerializer(source="product_set",many=True)
    products = serializers.SerializerMethodField()
    # pair_count = serializers.SerializerMethodField()

    def get_products(self, obj):
        request = self.context.get("request")
        # Filter out products with SOLD status
        queryset = obj.product_set.exclude(status=Product.StatusChoices.SOLD)
        products = ProductFilter(request.GET, queryset=queryset)
        return ProductSerializer(instance=products.qs, many=True, context={'request': request}).data
    
    
    
    

    def to_representation(self, instance):
        """
        Override to_representation to return None if there are no products in the pair
        Args:
            instance: Pair instance

        Returns:
            None if there are no products in the pair, otherwise the representation

        @see https://www.django-rest-framework.org/api-guide/serializers/#overriding-serialization-and-deserialization-behavior
        """
        representation = super().to_representation(instance)
        if not representation['products']:
            return None
        return representation

    class Meta:
        model = Pair
        fields = "__all__"


class SimilarProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="advert_title", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    tread_name = serializers.CharField(source="tread.name", read_only=True)
    size_text = serializers.CharField(source="size.size", read_only=True)
    size_description = serializers.CharField(
        source="size.description", read_only=True)
    image_urls = serializers.SerializerMethodField(read_only=True)

    def get_image_urls(self, obj):
        # Fetch images for the product and order them by ID
        images = Image.objects.filter(product=obj).order_by("id")

        # Build a list of URLs for images that have a valid image field
        urls = [image.image.url for image in images if image.image]

        # Get the request object from the context
        request = self.context.get('request')

        # Convert relative URLs to absolute URLs
        abs_urls = [request.build_absolute_uri(url) for url in urls if url]

        return abs_urls

    class Meta:
        model = Product
        fields = ['id', 'title', 'brand_name', 'tread_name',
                  'size_text', 'size_description', 'image_urls']


class ProductSerializer(serializers.ModelSerializer):
    # # len_name = serializers.SerializerMethodField()
    title = serializers.CharField(source="advert_title", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    tread_name = serializers.CharField(source="tread.name", read_only=True)
    size_text = serializers.CharField(source="size.size", read_only=True)
    size_description = serializers.CharField(
        source="size.description", read_only=True)
    pair_name = serializers.CharField(source="pair.name", read_only=True)
    description = serializers.SerializerMethodField(read_only=True)
    transportation_cost = serializers.SerializerMethodField(read_only=True)
    image_urls = serializers.SerializerMethodField(read_only=True)
    tread_details = serializers.SerializerMethodField(read_only=True)
    new_tread_depth = serializers.SerializerMethodField(read_only=True)
    tread_data = TreadSerializer(source="tread", read_only=True)
    # Adding tyre class to the response
    tyre_class = serializers.CharField(source="get_tyre_class", read_only=True)

    def get_image_urls(self, obj):
        # Fetch images for the product and order them by ID
        images = Image.objects.filter(product=obj).order_by("id")

        # Build a list of URLs for images that have a valid image field
        urls = [image.image.url for image in images if image.image]

        # Get the request object from the context
        request = self.context.get('request')

        # Convert relative URLs to absolute URLs
        abs_urls = [request.build_absolute_uri(url) for url in urls if url]

        return abs_urls

    def get_transportation_cost(self, ins):
        return ins.transportation_cost

    def get_description(self, instance):
        description = ""

        # Add lazy translated messages based on boolean fields
        description += (
            _("Tire bead is damaged.") if instance.is_tire_bead_damaged else ""
        )
        description += _("Tire is incised.") if instance.is_incised else ""
        description += _("Side repairs are present.") if instance.is_side_repair else ""
        description += (
            _("Visible cracks are present.") if instance.is_visible_cracks else ""
        )
        description += _("Brakes are present.") if instance.is_braked else ""
        description += _("Repairs after brake.") if instance.is_braked_repair else ""
        description += (
            _("Shoulder repair is present.") if instance.is_shoulder_repair else ""
        )
        description += _("Cosmetology is required.") if instance.is_cosmetology else ""
        description += _("Tire is toothed out.") if instance.is_toothed_out else ""
        description += _("Tire is retreaded.") if instance.is_retreaded else ""
        description += _("Ruts are present.") if instance.is_ruts else ""
        description += (
            _("Circumventional cut is present.")
            if instance.is_circumventional_cut
            else ""
        )

        return description

    def get_tread_details(self, obj):
        tread_char = Tread_Character.objects.annotate(
            optimized_brand=get_optimized_value('brand'),
            optimized_tread=get_optimized_value('tread')
        ).filter(
            optimized_brand=obj.optimized_brand,
            optimized_tread=obj.optimized_tread,
            size=obj.size
        ).values(
            "new_tire_price",
            # "new_tire_tread_depth",
            "tread_image",
        )
        return tread_char[0] if tread_char else None

    def get_new_tread_depth(self, obj):
        new_tread_depth = New_Tread_Depth.objects.annotate(
            optimized_brand=get_optimized_value('brand'),
            optimized_tread=get_optimized_value('tread')
        ).filter(
            optimized_brand=obj.optimized_brand,
            optimized_tread=obj.optimized_tread,
            size=obj.size
        ).values(
            "new_tire_tread_depth",

        )
        # return new_tread_depth[0] if new_tread_depth else None
        # Return just the float value instead of the full dict
        if new_tread_depth:
            return new_tread_depth[0]["new_tire_tread_depth"]
        return None

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("advert_title", "advert_description", "is_olx_active", "olx_advert_id", "olx_response",
                            "olx_active_advert_response", "is_olx")

    def get_title(self, object):
        return f"{object.brand.name} {object.tread.name} {object.width.name}/{object.profile} R{object.diameter} od {object.tread_depth_min} do {object.tread_depth_max}mm"

    def create(self, validated_data):
        obj = Product(**validated_data)

        obj.advert_title = obj.get_advert_title()
        obj.advert_description = obj.get_advert_description()
        obj.save()
        return obj


class TyreClassSerializer(serializers.ModelSerializer):
    tyre_class = serializers.CharField(source="get_tyre_class", read_only=True)

    class Meta:
        model = Product
        fields = ("id", "tyre_class")


class LiteProductSerializer(ProductSerializer):
    class Meta:
        model = Product
        fields = ("id", "title", "brand_name", "tread_name",
                  "size_text", "image_urls", "pair_name")


# class OLXAdvertSerializer(serializers.Serializer):
#     code = serializers.CharField(allow_null=True, required=False)
#     product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter())


# class OLXAdvertPairSerializer(serializers.Serializer):
#     code = serializers.CharField(allow_null=True, required=False)
#     pair = serializers.PrimaryKeyRelatedField(queryset=Pair.objects.filter())

class Tread_CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tread_Character
        fields = [
            "brand",
            "tread",
            "size",
            "new_tire_price",
            "optimized_brand",
            "optimized_tread",
        ]


class New_Tread_DepthSerializer(serializers.ModelSerializer):
    class Meta:
        model = New_Tread_Depth
        fields = [
            "brand",
            "tread",
            "size",
            "new_tire_tread_depth",
            "optimized_brand",
            "optimized_tread",
        ]


class PalletesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pallete
        fields = '__all__'


class ProductSearchSerailizer(serializers.ModelSerializer):
    tyre_class = serializers.CharField(source="get_tyre_class", read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductsSearchSerailizer(serializers.ModelSerializer):
    tyre_class = serializers.CharField(source="get_tyre_class", read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class AdvanceFilterProductSerializer(serializers.ModelSerializer):
    image_urls = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_image_urls(self, obj):
        # Get the request object from context
        request = self.context.get('request')

        # Fetch all images related to the product
        images = Image.objects.filter(product=obj).order_by("id")

        # Generate full absolute URLs
        image_urls = []
        for image in images:
            if image.image:
                url = image.image.url  # /media/...
                if request:
                    # http://tirgumpanel.pl/media/...
                    url = request.build_absolute_uri(url)
                else:
                    url = "http://tirgumpanel.pl" + url  # fallback
                image_urls.append(url)

        return image_urls


class TyreSizeListSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Size
        fields = ['size', 'slug', 'url']

    def get_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/api/tyreadderapp/sizes/{obj.slug}/tyres')
