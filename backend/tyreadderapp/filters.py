import django_filters

from .models import Product, Tread_Character, Brand


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class ProductFilter(django_filters.FilterSet):
    brands = NumberInFilter(field_name='brand_id', lookup_expr='in')
    ids = NumberInFilter(field_name='id', lookup_expr='in')
    brand__name = django_filters.CharFilter(field_name='brand__name', lookup_expr='istartswith')
    tread__name = django_filters.CharFilter(field_name='tread__name', lookup_expr='istartswith')
    front_repairs = django_filters.NumberFilter(field_name='front_repairs', lookup_expr='exact')
    is_side_repair = django_filters.BooleanFilter(field_name='is_side_repair', lookup_expr='exact')
    is_visible_cracks = django_filters.BooleanFilter(field_name='is_visible_cracks', lookup_expr='exact')
    is_braked = django_filters.BooleanFilter(field_name='is_braked', lookup_expr='exact')
    is_braked_repair = django_filters.BooleanFilter(field_name='is_braked_repair', lookup_expr='exact')
    is_shoulder_repair = django_filters.BooleanFilter(field_name='is_shoulder_repair', lookup_expr='exact')
    is_cosmetology = django_filters.BooleanFilter(field_name='is_cosmetology', lookup_expr='exact')
    is_toothed_out = django_filters.BooleanFilter(field_name='is_toothed_out', lookup_expr='exact')
    is_retreaded = django_filters.BooleanFilter(field_name='is_retreaded', lookup_expr='exact')
    is_ruts = django_filters.BooleanFilter(field_name='is_ruts', lookup_expr='exact')
    is_circumventional_cut = django_filters.BooleanFilter(field_name='is_circumventional_cut', lookup_expr='exact')
    tread_depth_min = django_filters.NumberFilter(field_name='tread_depth_min', lookup_expr='exact')
    tread_depth_min__lt = django_filters.NumberFilter(field_name='tread_depth_min', lookup_expr='lt')
    tread_depth_min__gt = django_filters.NumberFilter(field_name='tread_depth_min', lookup_expr='gt')
    tread_depth_max = django_filters.NumberFilter(field_name='tread_depth_max', lookup_expr='exact')
    tread_depth_max__lt = django_filters.NumberFilter(field_name='tread_depth_max', lookup_expr='lt')
    tread_depth_max__gt = django_filters.NumberFilter(field_name='tread_depth_max', lookup_expr='gt')
    dot = django_filters.NumberFilter(field_name='dot', lookup_expr='exact')
    net_price = django_filters.NumberFilter(field_name='net_price', lookup_expr='exact')
    net_price__lt = django_filters.NumberFilter(field_name='net_price', lookup_expr='lt')
    net_price__gt = django_filters.NumberFilter(field_name='net_price', lookup_expr='gt')
    supplier_price = django_filters.NumberFilter(field_name='supplier_price', lookup_expr='exact')
    
    status = django_filters.NumberFilter(field_name='status', lookup_expr='exact')
    is_label_printed = django_filters.BooleanFilter(field_name='is_label_printed', lookup_expr='exact')
    created = django_filters.DateTimeFilter(field_name='created', lookup_expr='exact')
    created__lt = django_filters.DateTimeFilter(field_name='created', lookup_expr='lt')
    created__gt = django_filters.DateTimeFilter(field_name='created', lookup_expr='gt')
    set_number = django_filters.NumberFilter(field_name='set_number', lookup_expr='exact')
    is_allegro = django_filters.BooleanFilter(field_name='is_allegro', lookup_expr='exact')
    is_otomoto = django_filters.BooleanFilter(field_name='is_otomoto', lookup_expr='exact')
    is_merchant_center = django_filters.BooleanFilter(field_name='is_merchant_center', lookup_expr='exact')
    size = django_filters.CharFilter(field_name='size__size', lookup_expr='exact')
    # Tread Filters to Product APIView
    is_steer = django_filters.BooleanFilter(field_name='tread__is_steer')
    is_drive = django_filters.BooleanFilter(field_name='tread__is_drive')
    is_trailer = django_filters.BooleanFilter(field_name='tread__is_trailer')
    is_3pmsf = django_filters.BooleanFilter(field_name='tread__is_3pmsf')
    is_incised = django_filters.BooleanFilter(field_name='is_incised')
    tyre_class = django_filters.NumberFilter(method='filter_by_tyre_class', label='Tyre Class')

    def get_products_by_brand_ids(self, queryset, name, value):
        return queryset.filter(brand__in=value)
    
    def filter_by_tyre_class(self, queryset, name, value):
        try:
            value = int(value)
        except ValueError:
            return queryset  # Return the original queryset if the value isn't an integer

        if value == 1:
            return queryset.filter(tread_depth_max__gte=11, tread_depth_min__gte=11)
        elif value == 2:
            return queryset.filter(tread_depth_max__lt=11, tread_depth_min__gte=7)
        elif value == 3:
            return queryset.filter(tread_depth_max__lt=7, tread_depth_min__lt=7)

        return queryset
    class Meta:
        model = Product
        fields = []


class TreadCharacterFilter(django_filters.FilterSet):
    class Meta:
        model = Tread_Character
        fields = ['brand', 'tread', 'size', 'new_tire_price']


class BrandFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Brand
        fields = "__all__"
