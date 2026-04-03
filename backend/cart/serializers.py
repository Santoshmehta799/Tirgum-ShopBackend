import importlib
from itertools import product
from rest_framework import serializers
from .models import Cart, CartItem
from django.db import transaction
from decimal import Decimal
from . import utils as cart_utils
from rest_framework.renderers import JSONRenderer
import time
from django.contrib.auth import get_user_model

from django.db.models import Min
from tyreadderapp.api.serializers import ProductSerializer, SizeSerializer
from tyreadderapp.models import Image, Product, Size, Pallete, TransportationCost
import logging
logger = logging.getLogger(__name__)

User = get_user_model()

class LiteProductSerializer(ProductSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    def get_image_url(self, obj):
        request = self.context.get('request')
        image = Image.objects.filter(product=obj).first()
        return request.build_absolute_uri(image.image.url) if image else None

    class Meta:
        model = Product
        fields = ("id", "brand_name", "tread_name", "size_text", "net_price", "image_url")


class CartItemSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    product = LiteProductSerializer()

    class Meta:
        model = CartItem
        fields = "__all__"


class CartsItemSerializer(serializers.ModelSerializer):
    size = serializers.CharField(source="product.size.size", read_only=True)
    width = serializers.CharField(source="product.size.width", read_only=True)
    id = serializers.IntegerField(source="product.id", read_only=True)
    brand_name = serializers.CharField(source="product.brand.name", read_only=True)
    tread_name = serializers.CharField(source="product.tread.name", read_only=True)
    net_price = serializers.DecimalField(source="product.net_price", max_digits=8, decimal_places=2, read_only=True)
    OFD = serializers.CharField(source="product.size.OFD", read_only=True)
    weights = serializers.CharField(source="product.weight", read_only=True)
    image_url = serializers.SerializerMethodField()
    cart_item_id = serializers.IntegerField(source='id', read_only=True)

    def get_image_url(self, obj):
        """
        Fetches the first image URL associated with the product.
        If no image exists, returns None.
        """
        first_image = obj.product.images.first() 
        base_url = "http://tirgumpanel.pl"
        if first_image and first_image.image:
            return f"{base_url}{first_image.image.url}"   
        return None

    class Meta:
        model = CartItem
        fields = ["cart_item_id", "id", "size", "width",  "brand_name", "tread_name", "net_price", "OFD", "weights", "image_url"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']


class CartSerializers(serializers.ModelSerializer):
    items = CartsItemSerializer(many=True, read_only=True)
    pallets = serializers.SerializerMethodField()
    summary_of_order = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Cart
        fields = ["id", "cart_id", "user", "items", "pallets", "summary_of_order"]

    def get_items(self, obj):
        items = obj.items.all()
        sorted_items = sorted(items, key=lambda x: float(x.product.size.OFD) if x.product.size.OFD else 0)
        return CartsItemSerializer(sorted_items, many=True).data
   
    def get_pallets(self, obj):
        items = obj.items.all()
        size_groups = {}
        for item in items:
            size = item.product.size.size
            if size not in size_groups:
                size_groups[size] = []
            size_groups[size].append(item)

        for size in size_groups:
            size_groups[size] = sorted(
                size_groups[size],
                key=lambda x: float(x.product.size.OFD) if x.product.size.OFD else 0,
                reverse=True
            )

        sorted_sizes = sorted(
            size_groups.keys(),
            key=lambda s: max([float(item.product.size.OFD) for item in size_groups[s]]) if size_groups[s] else 0,
            reverse=True
        )

        sorted_items = []
        for size in sorted_sizes:
            sorted_items.extend(size_groups[size])
        
        pallets = []
        current_pallet = []
        current_width = 0
        max_width_difference = 20  # Maximum allowed OFD difference in mm
        
        for item in sorted_items:
            width = int(item.product.size.width)
            current_ofd = float(item.product.size.OFD)
            
            if not current_pallet:
                current_pallet.append(item)
                current_width += width
                continue
                
            first_item_ofd = float(current_pallet[0].product.size.OFD)
           
            if (current_width + width <= 1960 and
                abs(current_ofd - first_item_ofd) <= max_width_difference):
                current_pallet.append(item)
                current_width += width
            else:
                pallets.append(current_pallet)
                current_pallet = [item]
                current_width = width
                
        if current_pallet:
            pallets.append(current_pallet)

        formatted_pallets = []
        for i, pallet in enumerate(pallets):
            size_counts = {}
            biggest_item = max(pallet, key=lambda item: float(item.product.size.OFD))
            biggest_ofd = float(biggest_item.product.size.OFD)
            biggest_ofd_size = biggest_item.product.size.size

            try:
                matching_size = Size.objects.get(size=biggest_ofd_size)
            except Size.DoesNotExist:
                matching_size = None

            
            for item in pallet:
                size = item.product.size.size
                ofd = item.product.size.OFD
                size_counts[size] = size_counts.get(size, 0) + 1
                
            
            # Check if there are multiple different sizes on the pallet
            has_different_sizes = len(size_counts) > 1
            
            max_same_size = max(size_counts.values()) if size_counts else 0
            

            if has_different_sizes:
                position = "stack"
            else:
                if max_same_size <= 2:
                    position = "tread_to_y"
                elif 2 < max_same_size <= 3:
                    position = "tread_to_x"
                elif max_same_size >= 4:
                    position = "stack"

            # pal_type = matching_size.tread_to_x_winner
            if position == "tread_to_y":
                pal_type = matching_size.tread_to_y_winner
            elif position == "tread_to_x":
                pal_type = matching_size.tread_to_x_winner 
            elif position == "stack":
                pal_type = matching_size.stack_winner 

            # try:
            #     formatted_pal_type = pal_type.replace("_", " ").upper()
            #     pallete_mht = Pallete.objects.get(name=formatted_pal_type)
            # except Pallete.DoesNotExist:
            #     matching_size = None

            try:
                # Check if pal_type is not None before attempting to replace
                if pal_type is not None:
                    formatted_pal_type = pal_type.replace("_", " ").upper()
                    pallete_mht = Pallete.objects.get(name=formatted_pal_type)
                else:
                    # If pal_type is None, set pallete_mht to None
                    pallete_mht = None
                    print("Pallet type is None")
            except Pallete.DoesNotExist:
                pallete_mht = None
                print(f"No Pallete found for type: {formatted_pal_type}")

            weights = sum(
                    Decimal(item.product.weight) if item.product.weight is not None else Decimal(0)
                    for item in pallet
                )
            empty_pallet_weight = weights + pallete_mht.empty_pal_weight if pallete_mht else weights
  
            if pallete_mht:
                # Find the closest higher `kg` value
                closest_kg = (
                    TransportationCost.objects.filter(kg__gte=empty_pallet_weight)
                    .aggregate(Min("kg"))["kg__min"]
                )

                courier_company = TransportationCost.objects.filter(
                    pallet=pallete_mht, kg=closest_kg).order_by("price").first()
                
            else:
                courier_company = None

            # ✅ Add null check for courier_company
            if courier_company:
                courier_company_name = courier_company.company.company_name
                courier_transportation_cost = courier_company.price
                pal_discounted_price = courier_company.pal_discounted_price
            else:
                courier_company_name = "Unknown"
                courier_transportation_cost = 0
                pal_discounted_price = 0

            if position != "stack":
                tyres_standing_height = biggest_ofd
            else:
                tyres_standing_height = None

            pallet_total_quantity = sum(size_counts.values())
            
            # ✅ Add null check for pallete_mht
            if pallete_mht:
                mht = pallete_mht.mht
                mht = mht * 10
            else:
                mht = 0  # or set a default value
                print("Warning: pallete_mht is None, cannot calculate MHT")
            
            tyres_stack_height = sum(int(item.product.size.width) for item in pallet)
            
            # ✅ Handle None values in net_price
            tyres_net_price = sum(
                Decimal(item.product.net_price) if item.product.net_price is not None else Decimal(0)
                for item in pallet
            )

            stack_space = mht - tyres_stack_height if mht else 0
            is_pal_full = (mht - 300 <= tyres_stack_height <= mht) if mht else False

            # ✅ Updated condition with null check
            if is_pal_full and courier_company:
                final_net_transportation_cost = courier_company.pal_discounted_price
            else:
                final_net_transportation_cost = courier_transportation_cost

            final_gross_transportation_cost = final_net_transportation_cost * Decimal("1.23")
            transport_and_tyres_final_net_price = final_net_transportation_cost + tyres_net_price
            transport_and_tyres_final_gross_price = transport_and_tyres_final_net_price * Decimal("1.23")           
            qunatity = {size: count for size, count in size_counts.items()}
            list_of_tyre = [295, 315, 355, 385, 425, 435]
            sizes_to_add = {size: stack_space // size for size in list_of_tyre} if stack_space else {}

            max_size = max(qunatity, key=qunatity.get)
            tyres_to_add = {max_size: qunatity[max_size]} if qunatity else None

            formatted_pallet = {
                "pallet_number": i + 1,
                "tyres_net_price": float(tyres_net_price),
                'total_weight': empty_pallet_weight,
                "items": CartsItemSerializer(pallet, many=True).data,
                
                "ofd_range": {
                    "min": min(float(item.product.size.OFD) for item in pallet),
                    "max": max(float(item.product.size.OFD) for item in pallet)
                },
                "qunatity": qunatity,
                "pal_type": pal_type,
                "position": position,
                "mht": mht,
                "tyres_stack_height": tyres_stack_height,
                "tyres_standing_height": tyres_standing_height,
                "stack_free_space": stack_space,
                "items_quantity": pallet_total_quantity,
                "courier": courier_company_name,
                "net_pallete_transportation_cost": courier_transportation_cost,
                "is_pal_full": is_pal_full,
                "final_net_transportation_cost": final_net_transportation_cost,
                "final_gross_transportation_cost": final_gross_transportation_cost,
                "transport_and_tyres_final_net_price": transport_and_tyres_final_net_price,
                "transport_and_tyres_final_gross_price": transport_and_tyres_final_gross_price,
                "pal_discounted_price": pal_discounted_price,
                "sizes_to_add": sizes_to_add,
                "tyres_to_add": tyres_to_add,
                "cargo_height": tyres_stack_height if tyres_standing_height is None else tyres_standing_height
            }
            formatted_pallets.append(formatted_pallet)
            
        return formatted_pallets
    
    def get_summary_of_order(self, obj):
        pallets = self.get_pallets(obj)
        first_name = ""
        last_name = ""
        total_tyres = sum(item.quantity for item in obj.items.all())

        # ✅ Handle None values in net_price
        tyres_net_value = sum(
            float(item.product.net_price) if item.product.net_price is not None else 0
            for item in obj.items.all()
        )
        tyres_gross_value = tyres_net_value * 1.23

        final_shipping_net_value = sum(
            float(pallet.get('final_net_transportation_cost', 0))
            for pallet in pallets
        )
        net_pallete_transportation_cost = sum(
            float(pallet.get('net_pallete_transportation_cost', 0))
            for pallet in pallets
        )

        # ✅ NEW: Include aggregated final_gross_transportation_cost
        final_gross_transportation_cost = sum(
            float(pallet.get('final_gross_transportation_cost', 0))
            for pallet in pallets
        )

        final_shipping_gross_value = final_shipping_net_value * 1.23
        tyres_and_transport_net_value = tyres_net_value + final_shipping_net_value
        tyres_and_transport_gross_value = tyres_and_transport_net_value * 1.23

        fields_to_update = []

        if obj.tyres_and_transport_gross_value != tyres_and_transport_gross_value:
            obj.tyres_and_transport_gross_value = tyres_and_transport_gross_value
            fields_to_update.append("tyres_and_transport_gross_value")
        
        # ✅ Save total gross transportation cost
        if obj.final_gross_transportation_cost != final_gross_transportation_cost:
            obj.final_gross_transportation_cost = final_gross_transportation_cost
            fields_to_update.append("final_gross_transportation_cost")

        if obj.total_tyres_net_value != tyres_net_value:
            obj.total_tyres_net_value = tyres_net_value
            fields_to_update.append("total_tyres_net_value")

        if obj.tyres_gross_value != tyres_gross_value:
            obj.tyres_gross_value = tyres_gross_value
            fields_to_update.append("tyres_gross_value")
            
        if fields_to_update:
            obj.save(update_fields=fields_to_update)
            # obj.save(update_fields=["total_tyres_net_value"])

        

        saved_on_shipping_net_value = net_pallete_transportation_cost - final_shipping_net_value

        Tyres_tax_fee = tyres_gross_value - tyres_net_value
        tyres_gross_value = tyres_net_value * 1.23
        self_pickup = obj.self_pickup
        payu_total = tyres_and_transport_gross_value if not self_pickup else tyres_gross_value

        user_data = {}
        if obj.user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                # Fetch the complete user object from database
                user = User.objects.get(id=obj.user.id)
                user_data = {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "nip": user.nip,
                    "company_name": user.company_name,
                    "company_street": user.company_street,
                    "company_building": user.company_building,
                    "company_apartment": user.company_apartment,
                    "company_zip_code": user.company_zip_code,
                    "company_city": user.company_city,
                    
                    "delivery_street": user.delivery_street,
                    "delivery_bulding": user.delivery_building,
                    "delivery_apartment": user.delivery_apartment,
                    "delivery_zip_code": user.delivery_zip_code,
                    "delivery_city": user.delivery_city,
                    
                }
            except User.DoesNotExist:
                pass

        if obj.full_name:
            name_parts = obj.full_name.split(maxsplit=1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

        result = {
            "user": obj.user.id if obj.user else None,
            "session_id": obj.session_id if obj.session_id else "",
            "cart_id": obj.cart_id,
            "date": obj.date,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": obj.full_name,
            "email": obj.email,
            "mobile": int(obj.mobile) if obj.mobile and str(obj.mobile).isdigit() else None,
            "self_pickup": obj.self_pickup,
            "nip": obj.nip,
            
            "company_name": obj.company_name,
            "company_street": obj.company_street,
            "company_apartment": obj.company_apartment,
            "company_zip_code": obj.company_zip_code,
            "company_city": obj.company_city,
            
            "delivery_street": obj.delivery_street,
            "delivery_bulding": obj.delivery_building,            
            "delivery_apartment": obj.delivery_apartment,
            "delivery_zip_code": obj.delivery_zip_code,
            "delivery_city": obj.delivery_city,           
            
            "company_building": obj.company_building,
            "tyres_qty": total_tyres,
            "tyres_net_value": tyres_net_value,
            "tyres_gross_value": tyres_gross_value,
            "final_shipping_net_value": final_shipping_net_value,
            "final_shipping_gross_value": final_shipping_gross_value,
            "final_gross_transportation_cost": final_gross_transportation_cost,  # ✅ NEW FIELD
            "saved_on_shipping_net_value": saved_on_shipping_net_value,
            "tyres_and_transport_net_value": tyres_and_transport_net_value,
            "tyres_and_transport_gross_value": tyres_and_transport_gross_value,
            "Tyres_tax_fee": Tyres_tax_fee,
            "payu_total": payu_total
        }

        if user_data:
            result.update(user_data)
        return result

        


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    aggregated_sizes = serializers.SerializerMethodField()
    merged_pallets = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    net_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    gross_price = serializers.SerializerMethodField(read_only=True)
    ultimate_net_price = serializers.SerializerMethodField(read_only=True)
    ultimate_transportation_costs = serializers.SerializerMethodField(read_only=True)
    net_price_after_qty_discount = serializers.SerializerMethodField()
    shipping_amount = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    tax_fee = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    ultimate_transportation_costs_gross = serializers.SerializerMethodField(read_only=True)
    total_quantity = serializers.SerializerMethodField()
    pallets = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = (
            "user", "total_price", "net_price", "gross_price", "date", "cart_id", "shipping_amount", "tax_fee")

    def create_cart(self, validated_data, items):
        user = self.context["request"].user
        cart = Cart.objects.create(
            **validated_data,
            user=user if user.is_authenticated else None
        )
        return cart

    def create_cart_items(self, cart, items):
        objs = [
            CartItem(
                product=item.get("product"),
                quantity=item.get("quantity"),
                cart=cart
            ) for item in items
        ]
        CartItem.objects.bulk_create(objs)

    def create(self, validated_data):
        items = validated_data.pop("items")

        with transaction.atomic():
            cart = self.create_cart(validated_data, items)
            self.create_cart_items(cart, items)
        return cart

    def aggregated_sizes_data(self, obj):
        serialized_aggregated_sizes = {}

        # Prepare data for each item in the cart
        all_items = list(obj.items.all())  # Get all items once for later use
        item_data_map = {item.id: {'id': item.id, 'product_id': item.product.id, 'net_price': item.product.net_price,
                                   "size": item.product.size.size, "brand": item.product.brand.name,
                                   "tread": item.product.tread.name, 'weight': item.product.weight,
                                   "OFD": item.product.size.OFD, "width": item.product.size.width,
                                   "diameter": item.product.size.diameter
                                   } for item in all_items}
        vat = 1.23
        fuel_charge = 1.29
        non_standard_fee = 87.70
        percentage_discount = 2  # Represents 2%
        quantity_updated = 1
        rem_transportation_cost = 0
        transportation_costs = 0
        stack_free_space = 0
        for item in all_items:
            size_obj = item.product.size
            size = size_obj.size
            quantity = item.quantity if item.quantity is not None else 0
            tyre_data = item_data_map[item.id]
            if size not in serialized_aggregated_sizes:
                width_str = size_obj.width
                profile_str = size_obj.profile
                quantity_updated = quantity
                tread_to_y_quantity = size_obj.tread_to_y_quantity
                tread_to_x_quantity = size_obj.tread_to_x_quantity
                stack_quantity = size_obj.stack_quantity
                final_profile_size = (width_str * (profile_str / 100) * 0.1) if profile_str else (
                        width_str * 0.8 * 2.54)
                final_profile_size = round(final_profile_size, 2)

                # transportation_cost = size_obj.pallete.transportation_cost if size_obj.pallete else 0
                # pallet_cost = size_obj.pallete.pallet_cost if size_obj.pallete else 0
                pallet_cost = 10

                serialized_aggregated_sizes[size] = {
                    'size': size,
                    'quantity': quantity,
                    'real_profile_dim': final_profile_size,
                    'details': {
                        "tread_to_y_winner": size_obj.tread_to_y_winner,
                        "tread_to_x_winner": size_obj.tread_to_x_winner,
                        "stack_winner": size_obj.stack_winner,
                        "tread_to_y_quantity": tread_to_y_quantity,
                        "tread_to_x_quantity": tread_to_x_quantity,
                        "stack_quantity": stack_quantity,
                        "OFD": size_obj.OFD,
                        "FW": size_obj.FW,
                        "diameter": size_obj.diameter,
                    },

                    'full_pal': []
                }
            else:
                serialized_aggregated_sizes[size]['quantity'] += quantity
                quantity_updated += quantity
            remaining_tyre = (
                    quantity_updated % stack_quantity) if stack_quantity <= quantity_updated else quantity_updated

            # serialized_aggregated_sizes[size]['stack_free_space'] = 1960 - (remaining_tyre * width_str) old
            # serialized_aggregated_sizes[size]["same_size_stack_additional_qty"] = stack_quantity - remaining_tyre old

            serialized_aggregated_sizes[size]['full_pal'].extend([tyre_data] * item.quantity)
        # Determine suggested packing for each size
        for size, data in serialized_aggregated_sizes.items():
            # remaining_tyre = data['remaining_tyre']
            details = data['details']

            # Calculate full and remaining pallet details
            tyres = data['full_pal']
            full_stack_tyres_qty = details['stack_quantity']
            total_tyres = len(tyres)
            if total_tyres < full_stack_tyres_qty:
                # If the total tyres are less than 5, force them into full_pal
                pal_qty = 1
                remaining_tyre = total_tyres  # No remaining tyres
            else:
                pal_qty = total_tyres // full_stack_tyres_qty
                remaining_tyre = total_tyres % full_stack_tyres_qty
            total_net_price = sum(tyre['net_price'] for tyre in tyres[:pal_qty * full_stack_tyres_qty])
            total_net_price = Decimal(total_net_price)
            ultimate_net_price = total_net_price - (total_net_price * (Decimal(percentage_discount) / Decimal(100)))
            pal_name = details['stack_winner']
            # print('size ===>',size)
            if '/' in size:
                width_str = int(size.split('/')[0])
            else:
                # Handle the case where '/' is not present
                width_str = int(float(size.split(' ')[0]))
            # print('width_str ===>',size.split('/'[0]))

            # width_str = int(size.split('/')[0])
            stack_quantity = details['stack_quantity']

            if total_tyres >= stack_quantity:
                full_pall_space = total_tyres - remaining_tyre
                full_pall_stack_free_space = 1960 - (stack_quantity * width_str)
                # serialized_aggregated_sizes[size]['remaining_tyre'] = remaining_tyre
                full_pal = {
                    "pal_qty": pal_qty,
                    "pal_name": pal_name,
                    "position": "stack",
                    "tyres_qty": total_tyres if total_tyres < stack_quantity else pal_qty * full_stack_tyres_qty,
                    'stack_free_space': full_pall_stack_free_space,
                    'same_size_stack_additional_qty': stack_quantity - total_tyres if total_tyres < stack_quantity else 0,
                    "ultimate_transportation_costs": 0,
                    # 'suggested_packing': pal_name,
                }
                full_pal['tyres_net_price'] = total_net_price
                full_pal['ultimate_net_price'] = ultimate_net_price
                full_pal['ultimate_gross_price'] = float(ultimate_net_price) * vat
                updated_pal_cost = pal_qty * pallet_cost
                if pal_name == 'half':
                    transportation_costs = cart_utils.half_pal_ultimate_transport_net_price(full_pal['tyres_qty'],
                                                                                            updated_pal_cost,
                                                                                            fuel_charge)
                elif pal_name == 'euro':
                    transportation_costs = cart_utils.euro_pal_ultimate_transport_net_price(full_pal['tyres_qty'],
                                                                                            updated_pal_cost,
                                                                                            fuel_charge)
                elif pal_name == 'industrial_m':
                    transportation_costs = cart_utils.industrial_m_ultimate_transport_net_price(fuel_charge,
                                                                                                non_standard_fee)
                elif pal_name == 'industrial_d':
                    transportation_costs = cart_utils.industrial_d_ultimate_transport_net_price(fuel_charge,
                                                                                                non_standard_fee)
                else:
                    transportation_costs = 0

                merge_weight_full = 0
                for i in range(pal_qty):
                    full_pal[f"full_pal_{i + 1}"] = tyres[i * full_stack_tyres_qty:(i + 1) * full_stack_tyres_qty]
                    start_index = i * full_stack_tyres_qty
                    end_index = (i + 1) * full_stack_tyres_qty
                    pallet_tyres = tyres[start_index:end_index]
                    for tyre in pallet_tyres:
                        if tyre['weight'] is not None:
                            merge_weight_full += tyre['weight']
                        else:
                            merge_weight_full += 0
                transportation_cost, company_name = cart_utils.get_transportation_cost(pal_name, merge_weight_full)
                transportation_costs = transportation_cost
                full_pal_tyres_no_discount_net_price = total_net_price + Decimal(transportation_costs)
                your_savings = full_pal_tyres_no_discount_net_price - ultimate_net_price
                full_pal['full_pal_tyres_no_discount_net_price'] = full_pal_tyres_no_discount_net_price
                full_pal['your_savings'] = round(your_savings, 2)
                full_pal['transportation_costs'] = transportation_costs
                full_pal['courier'] = company_name
                data['full_pal'] = full_pal
            else:
                data['full_pal'] = {}
            data['remaining_pal'] = {}
            suggested_packing = ''
            rem_pallete = ''
            # Calculate remaining pallet details
            if remaining_tyre > 0:
                stack_free_space = 1960 - (remaining_tyre * width_str)
                suggested_packing = cart_utils.determine_packing(remaining_tyre, details['tread_to_y_quantity'],
                                                      details['tread_to_x_quantity'], details['stack_quantity'])
                rem_pallete = details[f"{suggested_packing}_winner"]
                if rem_pallete == 'half':
                    rem_transportation_costs = cart_utils.half_pal_ultimate_transport_net_price(remaining_tyre,
                                                                                                10,
                                                                                                fuel_charge)
                elif rem_pallete == 'euro':
                    rem_transportation_costs = cart_utils.euro_pal_ultimate_transport_net_price(remaining_tyre,
                                                                                                10,
                                                                                                fuel_charge)
                elif rem_pallete == 'industrial_m':
                    rem_transportation_costs = cart_utils.industrial_m_ultimate_transport_net_price(fuel_charge,
                                                                                                    non_standard_fee)
                elif rem_pallete == 'industrial_d':
                    rem_transportation_costs = cart_utils.industrial_d_ultimate_transport_net_price(fuel_charge,
                                                                                                    non_standard_fee)
                else:
                    rem_transportation_costs = 0
                rem_tyres = tyres[-remaining_tyre:]
                merge_weight_rem = 0
                for tyre in rem_tyres:
                    weight = tyre.get("weight")
                    if weight is not None:
                        merge_weight_rem += weight
                    else:
                        merge_weight_rem += 0
                transportation_cost, company_name = cart_utils.get_transportation_cost(rem_pallete, merge_weight_rem)
                rem_transportation_cost = transportation_cost
                full_pal_tyres_no_discount_net_price = total_net_price + Decimal(rem_transportation_cost)
                your_savings = round((full_pal_tyres_no_discount_net_price - ultimate_net_price), 2)
                remaining_net_price = sum(tyre['net_price'] for tyre in rem_tyres)
                # remaining_ultimate_net_price = remaining_net_price - (remaining_net_price * 0)
                remaining_gross_price = float(remaining_net_price) * vat
                remaining_pal = {
                    "pal_qty": 1,
                    "tyres_qty": remaining_tyre,
                    "name": rem_pallete,
                    "position": suggested_packing,
                    'tyres_net_price': remaining_net_price,
                    'ultimate_net_price': remaining_net_price,
                    'ultimate_gross_price': remaining_gross_price,
                    'stack_free_space': stack_free_space,
                    'same_size_stack_additional_qty': stack_quantity - remaining_tyre,
                    'transportation_costs': rem_transportation_cost,
                    'ultimate_transportation_cost': rem_transportation_cost,
                    'courier': company_name,
                    'your_savings': 0,
                    "rem_pal_1": rem_tyres,
                }

                data['remaining_pal'] = remaining_pal
            size_net_total = data['remaining_pal'].get('ultimate_net_price', 0)
            gross_price = data['remaining_pal'].get('ultimate_gross_price', 0)
            # Calculate size summary
            size_summary = {
                "size": size,
                "size_net_total": size_net_total,
                "gross_price": gross_price,
                'ultimate_transportation_costs': rem_transportation_cost if remaining_tyre > 0 else 0,
                'ful_pal': pal_qty if total_tyres >= stack_quantity else 0,
                'remainig_pal': 1 if remaining_tyre > 0 else 0,
                'remainig_pal_positions': suggested_packing
            }
            data['size_summary'] = size_summary

        aggregated_sizes_list = list(serialized_aggregated_sizes.values())

        def sorting_key(item):
            size = item['size']
            r_index = size.index('R')
            r_value_str = size[r_index + 1:].split('/')[0]
            try:
                r_value = float(r_value_str)
            except ValueError:
                r_value = 0

            return (r_value, item['real_profile_dim'])

        # Sort the list using the custom sorting key
        sorted_aggregated_sizes = sorted(aggregated_sizes_list, key=sorting_key)

        for item in sorted_aggregated_sizes:
            if item.get('full_stack_pal'):
                item['full_stack_pal'] = item.pop('full_stack_pal')
            if item.get('full_stack_tyres_qty'):
                item['full_stack_tyres_qty'] = item.pop('full_stack_tyres_qty')
            if item.get('full_stack_name'):
                item['full_stack_name'] = item.pop('full_stack_name')
            if item.get('remaining_tyre'):
                item['remaining_tyre'] = item.pop('remaining_tyre')
            if item.get('pallete'):
                item['pallete'] = item.pop('pallete')
            if item.get('suggested_packing'):
                item['suggested_packing'] = item.pop('suggested_packing')
            if item.get('same_size_stack_additional_qty'):
                item['same_size_stack_additional_qty'] = item.pop('same_size_stack_additional_qty')
            if item.get('stack_free_space'):
                item['stack_free_space'] = item.pop('stack_free_space')

        return sorted_aggregated_sizes

    # def get_merged_pallets(self, obj):
    #     aggregated_sizes = self.aggregated_sizes_data(obj)
    #     vat = 1.23
    #     fuel_charge = 1.29
    #     non_standard_fee = 87.70
    #     size_info = []

    #     # Collect merge pallets only if there are more than 1 remaining different size pallets
    #     no_of_remaining = 0
    #     for size_data in aggregated_sizes:
    #         if size_data["remaining_pal"]:
    #             no_of_remaining += 1
    #     if no_of_remaining < 2:
    #         return []

    #     # Collecting information only from remaining pallets (remaining_pal)
    #     for size_data in aggregated_sizes:
    #         if "remaining_pal" in size_data and size_data["remaining_pal"]:
    #             size = size_data["size"]
    #             tyres_qty = size_data["remaining_pal"]["tyres_qty"]  # Use qty from remaining_pal
    #             tyres_width = int(
    #                 size_data["details"]["FW"] * 10) * tyres_qty  # Convert width to mm and calculate total width

    #             size_info.append({
    #                 "size": size,
    #                 "tyres_qty": tyres_qty,
    #                 "tyres_width": tyres_width,
    #                 "stack_winner": size_data["details"]["stack_winner"],
    #                 "tread_to_y_quantity": size_data["details"]["tread_to_y_quantity"],
    #                 "tread_to_x_quantity": size_data["details"]["tread_to_x_quantity"],
    #                 "stack_quantity": size_data["details"]["stack_quantity"],
    #                 "FW": size_data["details"]["FW"] * 10,  # width in mm
    #                 "remaining_pal": size_data["remaining_pal"],
    #                 "OFD": size_data["details"]["OFD"],
    #                 "diameter": size_data["details"]["diameter"]
    #             })
    #     # Sort the sizes by tyre diameter & OFD in descending order
    #     size_info.sort(key=lambda x: (x["diameter"], x["OFD"]), reverse=True)
    #     # Step 2: Organize pallets
    #     pallets = []
    #     current_pallet = {
    #         "total_width": 0,
    #         'stack_winner': '',
    #         'suggested_packing': '',
    #         'mht': 0,
    #         'ultimate_net_price': 0,
    #         'ultimate_gross_price': 0,
    #         'transportation_costs': 0,
    #         'ultimate_transportation_cost': 0,
    #         'stack_free_space': 0,
    #         'tyres_qty': 0,
    #         'tyres_height': 0,
    #         'tyres': [],
    #     }
    #     max_height = 1960  # 196 cm in mm

    #     for size in size_info:
    #         qty_to_add = size["tyres_qty"]
    #         while qty_to_add > 0:
    #             tyre_width = size["FW"]
    #             if not current_pallet['stack_winner']:
    #                 current_pallet['stack_winner'] = size['stack_winner']
    #                 # get MHT key from winner pallete model objects
    #                 pallet_name = current_pallet['stack_winner'].replace('_', ' ').swapcase()
    #                 pallet_mht = Pallete.objects.filter(name=pallet_name).last()
    #                 current_pallet['mht'] = pallet_mht.mht if pallet_mht else 0
    #             remaining_width = current_pallet['mht'] * 10 - current_pallet["total_width"]
    #             if tyre_width <= remaining_width and (current_pallet['tyres_height'] + tyre_width) <= max_height:
    #                 qty_to_add -= 1
    #                 current_pallet["tyres"].append(
    #                     size['remaining_pal']['rem_pal_1'][qty_to_add]
    #                 )
    #                 total_width = tyre_width / 10
    #                 current_pallet["total_width"] += total_width
    #                 current_pallet['tyres_height'] += tyre_width
    #                 current_pallet["tyres_qty"] += 1
    #                 remaining_width -= tyre_width
    #             else:
    #                 # Save the current pallet and start a new one
    #                 pallets.append(current_pallet)
    #                 current_pallet = {
    #                     "total_width": 0,
    #                     'stack_winner': '',
    #                     'suggested_packing': '',
    #                     'mht': 0,
    #                     'ultimate_net_price': 0,
    #                     'ultimate_gross_price': 0,
    #                     'transportation_costs': 0,
    #                     'ultimate_transportation_cost': 0,
    #                     'stack_free_space': 0,
    #                     'tyres_qty': 0,
    #                     'tyres_height': 0,
    #                     "tyres": [],
    #                 }
    #             # Position will always be stack in merged palettes
    #         current_pallet['suggested_packing'] = f"stack"

    #         current_pallet["stack_free_space"] = current_pallet['mht'] * 10 - current_pallet["tyres_height"]

    #     # Add the last pallet if its total width is above the threshold
    #     if current_pallet["tyres"]:
    #         pallets.append(current_pallet)

    #     # Iterate through the pallets and size_info to append id, brand, and tread
    #     for pallet in pallets:

    #         # calculate and add Transportation cost & ultimate transportation cost.
    #         if pallet['stack_winner'] == 'half':
    #             merged_transportation_costs = cart_utils.half_pal_ultimate_transport_net_price(len(pallet["tyres"]),
    #                                                                                         10,
    #                                                                                         fuel_charge)
    #         elif pallet['stack_winner'] == 'euro':
    #             merged_transportation_costs = cart_utils.euro_pal_ultimate_transport_net_price(len(pallet["tyres"]),
    #                                                                                         10,
    #                                                                                         fuel_charge)
    #         elif pallet['stack_winner'] == 'industrial_m':
    #             merged_transportation_costs = cart_utils.industrial_m_ultimate_transport_net_price(fuel_charge,
    #                                                                                             non_standard_fee)
    #         elif pallet['stack_winner'] == 'industrial_d':
    #             merged_transportation_costs = cart_utils.industrial_d_ultimate_transport_net_price(fuel_charge,
    #                                                                                             non_standard_fee)
    #         else:
    #             merged_transportation_costs = 0
    #         transportation_cost = 0
    #         stack_winner_merge = None
    #         merge_weight = 0
    #         for tyre in pallet["tyres"]:
    #             weight = tyre.get("weight")
    #             if stack_winner_merge is None:
    #                 stack_winner_merge = pallet["stack_winner"]
    #             if weight is not None:
    #                 merge_weight += weight
    #             else:
    #                 merge_weight += 0

    #         # pallet['transportation_costs'] = round((1 * (10 + merged_transportation_costs)), 2)
    #         # ultimate_transportation_cost = round((1 * (10 + merged_transportation_costs)), 2)
    #         transportation_cost, company_name = cart_utils.get_transportation_cost(stack_winner_merge, merge_weight)
    #         pallet['transportation_costs'] = transportation_cost
    #         pallet['courier'] = company_name
    #         ultimate_transportation_cost = transportation_cost
    #         if (current_pallet["mht"] - current_pallet['total_width']) < 30:
    #             ultimate_transportation_cost = 0
    #         pallet['ultimate_transportation_cost'] = ultimate_transportation_cost

    #         # Add net and gross prices of merged palettes.
    #         pallet['ultimate_net_price'] = sum(tyre['net_price'] for tyre in pallet["tyres"])
    #         pallet['ultimate_gross_price'] = float(pallet['ultimate_net_price']) * vat
    #     # Step 3: Return organized pallets
    #     return pallets


    def get_merged_pallets(self, obj):
        aggregated_sizes = self.aggregated_sizes_data(obj)
        vat = Decimal("1.23")  # Ensure vat is a Decimal
        fuel_charge = Decimal("1.29")
        non_standard_fee = Decimal("87.70")
        size_info = []

        # Collect merge pallets only if there are more than 1 remaining different size pallets
        no_of_remaining = 0
        for size_data in aggregated_sizes:
            if size_data["remaining_pal"]:
                no_of_remaining += 1
        if no_of_remaining < 2:
            return []

        # Collecting information only from remaining pallets (remaining_pal)
        for size_data in aggregated_sizes:
            if "remaining_pal" in size_data and size_data["remaining_pal"]:
                size = size_data["size"]
                tyres_qty = size_data["remaining_pal"]["tyres_qty"]  # Use qty from remaining_pal
                tyres_width = int(
                    size_data["details"]["FW"] * 10) * tyres_qty  # Convert width to mm and calculate total width

                size_info.append({
                    "size": size,
                    "tyres_qty": tyres_qty,
                    "tyres_width": tyres_width,
                    "stack_winner": size_data["details"]["stack_winner"],
                    "tread_to_y_quantity": size_data["details"]["tread_to_y_quantity"],
                    "tread_to_x_quantity": size_data["details"]["tread_to_x_quantity"],
                    "stack_quantity": size_data["details"]["stack_quantity"],
                    "FW": size_data["details"]["FW"] * 10,  # width in mm
                    "remaining_pal": size_data["remaining_pal"],
                    "OFD": size_data["details"]["OFD"],
                    "diameter": size_data["details"]["diameter"]
                })
        # Sort the sizes by tyre diameter & OFD in descending order
        size_info.sort(key=lambda x: (x["size"], x["OFD"]), reverse=True)
        # Step 2: Organize pallets
        pallets = []
        current_pallet = {
            "total_width": 0,
            'stack_winner': '',
            'suggested_packing': '',
            'mht': 0,
            'ultimate_net_price': 0,
            'ultimate_gross_price': 0,
            'transportation_costs': 0,
            'ultimate_transportation_cost': 0,
            'stack_free_space': 0,
            'tyres_qty': 0,
            'tyres_height': 0,
            'tyres': [],
        }
        max_height = 1960  # 196 cm in mm

        for size in size_info:
            qty_to_add = size["tyres_qty"]
            while qty_to_add > 0:
                tyre_width = size["FW"]
                if not current_pallet['stack_winner']:
                    current_pallet['stack_winner'] = size['stack_winner']
                    # get MHT key from winner pallete model objects
                    pallet_name = current_pallet['stack_winner'].replace('_', ' ').swapcase()
                    pallet_mht = Pallete.objects.filter(name=pallet_name).last()
                    current_pallet['mht'] = pallet_mht.mht if pallet_mht else 0
                remaining_width = current_pallet['mht'] * 10 - current_pallet["total_width"]
                if tyre_width <= remaining_width and (current_pallet['tyres_height'] + tyre_width) <= max_height:
                    qty_to_add -= 1
                    current_pallet["tyres"].append(
                        size['remaining_pal']['rem_pal_1'][qty_to_add]
                    )
                    total_width = tyre_width / 10
                    current_pallet["total_width"] += total_width
                    current_pallet['tyres_height'] += tyre_width
                    current_pallet["tyres_qty"] += 1
                    remaining_width -= tyre_width
                else:
                    # Save the current pallet and start a new one
                    pallets.append(current_pallet)
                    current_pallet = {
                        "total_width": 0,
                        'stack_winner': '',
                        'suggested_packing': '',
                        'mht': 0,
                        'ultimate_net_price': 0,
                        'ultimate_gross_price': 0,
                        'transportation_costs': 0,
                        'ultimate_transportation_cost': 0,
                        'stack_free_space': 0,
                        'tyres_qty': 0,
                        'tyres_height': 0,
                        "tyres": [],
                    }
                # Position will always be stack in merged palettes
            current_pallet['suggested_packing'] = f"stack"

            current_pallet["stack_free_space"] = current_pallet['mht'] * 10 - current_pallet["tyres_height"]

        # Add the last pallet if its total width is above the threshold
        if current_pallet["tyres"]:
            pallets.append(current_pallet)

        # Iterate through the pallets and size_info to append id, brand, and tread
        for pallet in pallets:
            pallet_mht_weight = Pallete.objects.filter(name=pallet["stack_winner"].replace('_', ' ').swapcase()).last()
            empty_pallet_weight = getattr(pallet_mht_weight, 'mht', 0)  # Fix: use 'mht' attribute
            transportation_cost, company_name = cart_utils.get_transportation_cost(pallet["stack_winner"], sum(tyre.get("weight", 0) for tyre in pallet["tyres"]))
            pallet['transportation_costs'] = transportation_cost
            pallet['courier'] = company_name
            pallet['total_weight'] = sum(tyre.get("weight", 0) for tyre in pallet["tyres"]) + empty_pallet_weight  # Updated field
            pallet['net_pallete_transportation_cost'] = transportation_cost
            pallet['gross_pallete_transportation_cost'] = transportation_cost * vat  # Fixed Decimal multiplication

            # Add net and gross prices of merged palettes.
            pallet['ultimate_net_price'] = sum(tyre['net_price'] for tyre in pallet["tyres"])
            pallet['ultimate_gross_price'] = Decimal(pallet['ultimate_net_price']) * vat
        # Step 3: Return organized pallets
        return pallets


    def get_pallets(self, obj):
        # pallets = cart_utils.get_palletes(pal_qty, pal_name, remaining_tyre, rem_pallete)
        # return data
        return {
            "half": 0,
            "euro": 0,
            "industrial_m": 0,
            "industrial_d": 0
        }

    def get_net_price_after_qty_discount(self, obj):
        return round((float(obj.net_price)/1.18), 2)

    def get_ultimate_net_price(self, obj):
        merged_pallets = self.get_merged_pallets(obj)

        if merged_pallets:
            # Sum up the ultimate_net_price of all merged pallets
            total_net_price = sum(pallet['ultimate_net_price'] for pallet in merged_pallets)
            return total_net_price
        else:
            aggregated_sizes = self.aggregated_sizes_data(obj)
            # Initialize a variable to hold the total remaining pallet ultimate net price
            total_remaining_pal_ultimate_net_price = 0

            # Iterate through each size data and sum up the ultimate_net_price for remaining pallets
            for size_data in aggregated_sizes:
                if "remaining_pal" in size_data and size_data["remaining_pal"]:
                    remaining_pal = size_data["remaining_pal"]
                    if "ultimate_net_price" in remaining_pal:
                        total_remaining_pal_ultimate_net_price += remaining_pal["ultimate_net_price"]
            return total_remaining_pal_ultimate_net_price

    def get_ultimate_transportation_costs(self, obj):
        merged_pallets = self.get_merged_pallets(obj)

        if merged_pallets:
            # Sum up the ultimate_net_price of all merged pallets
            total_net_price = sum(pallet['ultimate_transportation_cost'] for pallet in merged_pallets)
            return total_net_price
        else:
            aggregated_sizes = self.aggregated_sizes_data(obj)
            # Initialize a variable to hold the total remaining pallet ultimate net price
            total_remaining_pal_ultimate_net_price = 0

            # Iterate through each size data and sum up the ultimate_net_price for remaining pallets
            for size_data in aggregated_sizes:
                if "remaining_pal" in size_data and size_data["remaining_pal"]:
                    remaining_pal = size_data["remaining_pal"]
                    if "ultimate_transportation_cost" in remaining_pal:
                        total_remaining_pal_ultimate_net_price += remaining_pal["ultimate_transportation_cost"]
            return total_remaining_pal_ultimate_net_price

    def get_aggregated_sizes(self, obj):
        merged_pallets = self.get_merged_pallets(obj)
        serialized_aggregated_sizes = self.aggregated_sizes_data(obj)
        if merged_pallets:
            for size_data in serialized_aggregated_sizes:
                if "remaining_pal" in size_data:
                    size_data['remaining_pal'] = {}
                    size_data['size_summary']['remainig_pal'] = 0
                    size_data['size_summary']['remainig_pal_positions'] = ''
        return serialized_aggregated_sizes

    def get_gross_price(self, obj):
        return float(obj.net_price) * 1.23


    def get_ultimate_transportation_costs_gross(self, obj):
        transportation_costs = self.get_ultimate_transportation_costs(obj)
        # Use Decimal for the constant multiplier
        return transportation_costs * Decimal('1.23') if transportation_costs else None


    def get_total_quantity(self, obj):
        """
        Calculates the total quantity of all items in the cart.
        """
        return sum(item.quantity for item in obj.items.all())
    # def get_shipping_amount(self, obj):
    #     return obj.get_shipping_amount()

    # def get_total_price(self, obj):
    #     return obj.total_price

class CartItemSaveSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    def validate(self, data):
        if 'product_id' in data and data['product_id']:
            try:
                product = Product.objects.get(id=data['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError(
                    {'product_id': f'Product {data["product_id"]} does not exist!'})
        
        # Validate quantity
        quantity = data.get('quantity', 1)
        if quantity < 1:
            raise serializers.ValidationError(
                {'quantity': 'Quantity must be at least 1'})
        
        return data

    class Meta:
        model = CartItem
        fields = ["product_id", "quantity"]

class CreateCartSerializer(serializers.ModelSerializer):
    items = CartItemSaveSerializer(many=True, required=False)

    class Meta:
        model = Cart
        fields = "__all__"
        extra_kwargs = {
            'user': {'required': False},
            'session_id': {'required': False}
        }

    def validate(self, data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        session_id = data.get("session_id")

        if not user and not session_id:
            raise serializers.ValidationError("Either an authenticated user or a session_id must be provided.")

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        session_id = validated_data.get("session_id")

        # Remove items from validated_data
        items = validated_data.pop('items', [])

        # Determine filter criteria based on user or session_id
        cart_filter = {}
        if user:
            cart_filter["user"] = user
        elif session_id:
            cart_filter["session_id"] = session_id

        # Get or create the cart
        cart, created = Cart.objects.get_or_create(defaults=validated_data, **cart_filter)

        # Create cart items (if not already present)
        for item_data in items:
            product_id = item_data.get("product_id")
            if not CartItem.objects.filter(cart=cart, product_id=product_id).exists():
                CartItem.objects.create(cart=cart, **item_data)
        return cart


    def update(self, instance, validated_data):
        items = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items is not None:
            for item_data in items:
                product_id = item_data.get('product_id')
                if CartItem.objects.filter(cart=instance, product_id=product_id).exists():
                    continue
                CartItem.objects.create(cart=instance, **item_data)
        return instance