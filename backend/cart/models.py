from decimal import Decimal

from django.db import models
from tyreadderapp.models import Product, Size, Pallete
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.TextField(null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)
    cart_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Buyer data
    full_name = models.CharField(max_length=555, null=True, blank=True)
    email = models.CharField(max_length=555, null=True, blank=True)
    mobile = models.CharField(max_length=100, null=True, blank=True)
    # Shipping address
    address = models.TextField(null=True, blank=True)
    # city = models.CharField(max_length=555, null=True, blank=True)
    self_pickup = models.BooleanField(default=True, null=True, blank=True)
    first_name = models.CharField(max_length=555, null=True, blank=True)
    last_name = models.CharField(max_length=555, null=True, blank=True)
    nip = models.CharField(max_length=10, null=True, blank=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)    
    
    company_street = models.CharField(max_length=555, null=True, blank=True)
    company_building = models.CharField(max_length=555, null=True, blank=True)
    company_apartment = models.CharField(max_length=555, null=True, blank=True)
    company_zip_code  = models.CharField(max_length=555, null=True, blank=True)
    company_city = models.CharField(max_length=555, null=True, blank=True)
    
    delivery_street = models.CharField(max_length=555, null=True, blank=True)
    delivery_building = models.CharField(max_length=555, null=True, blank=True)
    delivery_apartment = models.CharField(max_length=555, null=True, blank=True)
    delivery_zip_code = models.CharField(max_length=555, null=True, blank=True)
    delivery_city = models.CharField(max_length=555, null=True, blank=True)
    delivery_phone = models.CharField(max_length=14, null=True, blank=True)
    tyres_and_transport_gross_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    tyres_gross_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    final_gross_transportation_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    total_tyres_net_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    delivery_phone = models.CharField(max_length=15, null=True, blank=True)
    
    # company_address = models.CharField(max_length=555, null=True, blank=True)
    # company_delivery = models.CharField(max_length=555, null=True, blank=True)

    def __str__(self):
        return f"{self.cart_id}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=~models.Q(user=None),
                name="unique_user_cart"
            ),
            models.UniqueConstraint(
                fields=["session_id"],
                condition=~models.Q(session_id=None),
                name="unique_session_cart"
            ),
        ]
    @property
    def tax_fee(self):
        amount = float(self.net_price or 0) + float(self.shipping_amount or 0)
        vat = 1.23 * amount / 100
        return vat

    @property
    def total_price(self):
        total = Decimal(self.net_price) + Decimal(self.shipping_amount) + Decimal(self.tax_fee)
        return total

    @property
    # def net_price(self):
    #     items_total = sum(item.net_price for item in self.items.all())
    #     total = Decimal(items_total)
    #     return total
    def net_price(self):
        items_total = sum(Decimal(item.net_price or 0) for item in self.items.all())
        return items_total

    def get_aggregated_sizes(self):
        size_counts = {}
        for item in self.items.all():
            size_str = item.product.size.size
            width_str = item.product.size.width
            profile_str = item.product.size.profile

            tread_to_x_quantity_value = item.product.size.tread_to_x_quantity
            tread_to_y_quantity_value = item.product.size.tread_to_y_quantity
            stack_quantity_value = item.product.size.stack_quantity
            if profile_str is None:
                final_profile_size = width_str * 0.8 * 2.54
                final_profile_size =  round(final_profile_size, 2)
            else:
                profile_size = width_str * (profile_str / 100)
                final_profile_size = profile_size * 0.1
                final_profile_size= round(final_profile_size, 2)

            final_profile_size = round(final_profile_size, 2)

            if size_str in size_counts:
                size_counts[size_str]["quantity"] += item.quantity
            else:
                size_counts[size_str] = {
                    "quantity": item.quantity,
                    "size": item.product.size,
                    "real_profile_dim": final_profile_size
                }

            

            if width_str in size_counts:
                size_counts[width_str]["width"] += item.quantity
            else:
                size_counts[width_str] = {"width": item.quantity, "size": item.product.size}

        aggregated_sizes = [
            {
                'size': key,
                'quantity': item.get("quantity", 0),
                'details': item.get("size", {}),
                "stack_free_space": 1960 - (item.get('quantity', 0) * item.get('size').width),
                "same_size_stack_additional_qty": item.get("size").stack_quantity - item.get('quantity', 0),
                'real_profile_dim': item.get("real_profile_dim", None)

            } for key, item in
            size_counts.items()]
        return aggregated_sizes

    def get_pallets(self):
        pallets = {
            "half": 0,
            "euro": 0,
            "industrial_m": 0,
            "industrial_d": 0
        }

        for size in self.get_aggregated_sizes():
            details = size['details']
            stack_winner = None
            tread_to_y_winner = None
            if details.tread_to_y_winner:
                tread_to_y_winner = details.tread_to_y_winner.lower().replace(' ', '_').lower()
            if details.stack_winner:
                stack_winner = details.stack_winner.lower().replace(' ', '_').lower()
            if size['quantity'] <= details.tread_to_y_quantity:
                if tread_to_y_winner in pallets:
                    pallets[tread_to_y_winner] += details.tread_to_y_quantity
                else:
                    pallets[tread_to_y_winner] = details.tread_to_y_quantity
            else:
                quantity = size['quantity'] - details.tread_to_y_quantity
                if stack_winner in pallets:
                    pallets[stack_winner] += quantity
                else:
                    pallets[stack_winner] = quantity
        return pallets

    @property
    def shipping_amount(self):
        pallets = self.get_pallets()
        pallets_from_db = Pallete.objects.all()
        amount = 0
        for name, quantity in pallets.items():
            if name:
                name = name.replace("_", " ")
                pallet = pallets_from_db.filter(name__iexact=name).first()
                amount += (pallet.net_price or 0) * quantity if pallet else 0  # Ensure net_price is not None
        return amount


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)

    @property
    def net_price(self):
        return self.product.net_price

    @property
    def total_price(self):
        return self.net_price * self.quantity

    @property
    def vat(self):
        return self.product.get_vat * self.quantity

    def __str__(self):
        return f"{self.product} ({self.quantity})"
