from tyreadderapp.generate_filename import OverwriteStorage
import io
import os
import requests
import numpy as np
from decimal import Decimal
from PIL import Image as PImage
from django.conf import settings
from django.utils import timezone
from xmlrpc.client import Boolean
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import InMemoryUploadedFile
from .predictor import predict_net_price
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.apps import apps
from django.db.models import Min
from PIL import Image as PILImage
from io import BytesIO
from .helpers import optimize_value
from django.contrib.auth import get_user_model
from .helpers import optimize_value

User = get_user_model()


class Staff(models.Model):
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    login = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    def __str__(self):
        return (
            f"{self.first_name} - {self.last_name} - {self.login} - {self.password}"
        )


class Brand(models.Model):
    name = models.CharField(("Marka"), max_length=50, blank=True, unique=True)
    country_of_origin = models.CharField(max_length=50, blank=True)
    allegro_brand_id = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]
        ordering = ["name"]

    def __str__(self):
        return (
            f"{self.pk} - {self.name} {self.country_of_origin} - {self.allegro_brand_id}"
        )


class Tread(models.Model):
    name = models.CharField(max_length=50, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    is_steer = models.BooleanField(default=False)
    is_drive = models.BooleanField(default=False)
    is_trailer = models.BooleanField(default=False)
    is_m_s = models.BooleanField(default=False)
    is_3pmsf = models.BooleanField(default=False)
    image = models.ImageField(upload_to='tread_images/', blank=True, null=True)
    has_image = models.BooleanField(default=False)
    

    def save(self, *args, **kwargs):
        self.has_image = bool(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    def product_count(self):
        return self.product_set.count()
    product_count.short_description = "Liczba produktów"

    class Meta:
        ordering = ['name']


# class StatusClassChoices(models.IntegerChoices):
#     TO_ADD = 0, "Do dodania"
#     ON_SALE = 1, "W sprzedaży"
#     SOLD = 2, "Sprzedane"


class FrontRepairClassChoices(models.IntegerChoices):
    ZERO = 0, "0"
    ONE = 1, "1"
    TWO = 2, "2"
    THREE = 3, "3"


class Pallete(models.Model):
    name = models.CharField(max_length=256)
    net_price = models.DecimalField(max_digits=10, decimal_places=2)
    # gross_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mht = models.PositiveIntegerField()
    pallet_cost = models.PositiveIntegerField(default=0)
    transportation_cost = models.PositiveIntegerField(default=0)
    X = models.DecimalField(max_digits=10, decimal_places=2)
    Y = models.DecimalField(max_digits=10, decimal_places=2)
    empty_pal_weight = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    # def save(self, *args, **kwargs):
    #     if not self.gross_price:
    #         self.gross_price = float(self.net_price) * self.VAT_Rate
    #     super().save(*args, **kwargs)
    @property
    def gross_price(self):
        return float(self.net_price) + (float(self.net_price) * 1.23) / 100

    class Meta:
        verbose_name = "Pallete"
        verbose_name_plural = "Palletes"


def custom_slugify(value):
    value = value.replace('.', '-')  # dot ko hyphen me
    value = value.replace('/', '-')  # slash ko bhi safe bana le
    return slugify(value)


class Size(models.Model):
    class WinnerChoices(models.TextChoices):
        HALF = "half"
        EURO = "euro"
        INDUSTRIAL_M = "industrial_m"
        INDUSTRIAL_D = "industrial_d"
        ODBIÓR_OSOBISTY = "odbiór_osobisty"

    pallete = models.ForeignKey(Pallete, related_name='pallete_size', on_delete=models.CASCADE,
                                null=True, blank=True)
    size = models.CharField(max_length=30, unique=True)
    width = models.PositiveSmallIntegerField()
    weight = models.DecimalField(
        ("Waga"), max_digits=8, decimal_places=2, blank=True, null=True)
    profile = models.PositiveSmallIntegerField(null=True, blank=True)
    diameter = models.DecimalField(max_digits=5, decimal_places=2)
    OFD = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    FW = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    tread_to_x_winner = models.CharField(
        max_length=30, null=True, blank=True, choices=WinnerChoices.choices)
    tread_to_y_winner = models.CharField(
        max_length=30, null=True, blank=True, choices=WinnerChoices.choices)
    stack_winner = models.CharField(
        max_length=30, null=True, blank=True, choices=WinnerChoices.choices)
    tread_to_x_quantity = models.PositiveSmallIntegerField(default=0)
    tread_to_y_quantity = models.PositiveSmallIntegerField(default=0)
    stack_quantity = models.PositiveSmallIntegerField(default=0)
    stack_rem_space_height = models.DecimalField(
        decimal_places=2, max_digits=8, default=0)
    weight = models.DecimalField(
        decimal_places=2, max_digits=5, null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = custom_slugify(self.size)
            slug = base_slug
            count = 1
            while Size.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('size-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.size

    def real_profile_dim(self):
        if self.profile is None:
            final_profile_size = self.width * 0.8 * 2.54
            final_profile_size = round(final_profile_size, 2)
        else:
            profile_size = self.width * (self.profile / 100)
            final_profile_size = profile_size * 0.1
            final_profile_size = round(final_profile_size, 2)

        return final_profile_size

    class Meta:
        ordering = ["size"]


class Pair(models.Model):
    class PairStatusChoice(models.TextChoices):
        NEW = "new"
        LISTED = "listed"

    name = models.CharField(max_length=50, unique=True)
    pair_title = models.CharField(max_length=70, null=True, blank=True)
    pair_description = models.TextField(null=True, blank=True)
    pair_price = models.DecimalField(
        decimal_places=2, max_digits=8, null=True, blank=True)
    pair_is_olx = models.BooleanField(("Olx"), default=False)
    pair_is_olx_active = models.BooleanField(
        ("Olx_Advert_Active"), default=False)
    pair_olx_advert_id = models.PositiveIntegerField(null=True, blank=True)
    pair_olx_response = models.TextField(null=True, blank=True)
    pair_olx_active_advert_response = models.TextField(null=True, blank=True)
    blocked_pair = models.BooleanField(default=False)
    pair_listing_status = models.CharField(
        max_length=20, choices=PairStatusChoice.choices, default=PairStatusChoice.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    is_otomoto_pair_advert_created = models.BooleanField(default=False)
    is_otomoto_pair_advert_activated = models.BooleanField(default=False)
        
    def on_product_sold(self, product):
        """
        Called AFTER a related product changes status to SOLD
        """
        remaining = self.products.exclude(status=Product.SOLD).count()

        # Transition: >1 → 1
        if remaining == 1:
            self.delete()

    def process_and_save_pair_image(self):
        processor = PairAdvertImageProcessor(self)
        return processor
    
    
    def get_pair_name(self):
        return self.name
    
    
    
    
    def get_pair_best_pallete_option(self):
        # ---- 1. Get products in the pair ----
        products = Product.objects.filter(pair=self).exclude(
            status=Product.StatusChoices.SOLD
        )

        if not products.exists():
            return None

        qty = products.count()

        # ---- 2. Sum weights (default 50 kg if missing) ----
        total_weight = sum(
            (p.weight if p.weight is not None else 50)
            for p in products
        )

        product = products.first()
        size = product.size

        if not size:
            return None

        # ---- 3. Determine valid pallet options based on quantity ----
        options = {
            "tread_to_x": {
                "capacity": size.tread_to_x_quantity,
                "winner": size.tread_to_x_winner,
            },
            "tread_to_y": {
                "capacity": size.tread_to_y_quantity,
                "winner": size.tread_to_y_winner,
            },
            "stack": {
                "capacity": size.stack_quantity,
                "winner": size.stack_winner,
            },
        }

        valid_options = {
            k: v for k, v in options.items()
            if v["capacity"] and qty <= v["capacity"]
        }

        if not valid_options:
            return None

        # ---- 4. Pick the tightest fit (smallest capacity) ----
        best_layout = min(
            valid_options,
            key=lambda k: valid_options[k]["capacity"]
        )

        pallet_winner = valid_options[best_layout]["winner"]
        if not pallet_winner:
            return None

        normalized_pallet_name = pallet_winner.replace('_', ' ').upper()

        # ---- 5. Map Winner choice string to actual Pallete object ----
        try:
            pallet_obj = Pallete.objects.get(name=normalized_pallet_name)
        except Pallete.DoesNotExist:
            return None

        # ---- 6. Get the lowest transport price for the pallet + total weight ----
        best_cost = (
            TransportationCost.objects
            .filter(
                pallet=pallet_obj,
                kg__gte=total_weight
            )
            .order_by('price')
            .values('company', 'price', 'kg')
            .first()
        )

        if not best_cost:
            return None

        # ---- 7. Return all relevant info ----
        return {
            "layout": best_layout,
            "pallet": pallet_winner,
            "qty": qty,
            "total_weight": total_weight,
            "carrier": best_cost["company"],
            "price": best_cost["price"],
            "weight_limit": best_cost["kg"],
        }         
    
    
    
    def get_first_tire_size(self):
        """
        Returns Size instance of the first Product in this pair,
        or None if no products or size is missing.
        """
        product = self.products.select_related("size").order_by("id").first()
        return product.size if product and product.size else None
    
    def get_first_tire_width(self):
        """
        Returns width of the first Product in this pair,
        or None if no products or size is missing.
        """
        product = self.products.select_related("size").order_by("id").first()
        return product.size.width if product and product.size else None
    
    def get_first_tire_aspect_ratio(self):
        """
        Returns profile of the first Product in this pair,
        or None if no products or size is missing.
        """
        product = self.products.select_related("size").order_by("id").first()
        return product.size.profile if product and product.size else None
    

    def get_pair_advert_title(self):
        products = Product.objects.filter(pair=self).exclude(
            status=Product.StatusChoices.SOLD)
        quantity = products.count()

        if products.exists():
            product = products.first()
            product_size = product.size
            product_brand = product.brand
            product_tread = product.tread

            # Determine the correct plural form for 'sztuka'
            quantity_text = "sztuka" if quantity == 1 else "sztuki"

            title_pair = (
                f"Komplet opon - {quantity} x {product_size} {product_brand} {product_tread}"
            )
        else:
            title_pair = "-"
        return title_pair

    def get_pair_advert_price(self):
        products = Product.objects.filter(pair=self).exclude(
            status=Product.StatusChoices.SOLD)
        total_net_price = Decimal(0)
        for product in products:
            total_net_price += product.net_price

        return total_net_price
    
    def get_pair_brand(self):
        products = Product.objects.filter(pair=self).exclude(
            status=Product.StatusChoices.SOLD)
        if products.exists():
            first_product = products.first()
            return first_product.brand
        return None

    # def check_and_destroy_if_single_product(self):
    #     """
    #     Checks the number of products associated with this pair. If there is exactly one product,
    #     the pair is automatically deleted to ensure data consistency, as valid pairs must contain
    #     2, 3, or 4 products.

    #     This method should be called after any operation that might reduce the number of products
    #     in the pair (e.g., deleting a product or updating its `pair` field).

    #     Returns:
    #         bool: True if the pair was deleted, False otherwise.
    #     """
    #     product_count = self.product_set.count()
    #     if product_count == 1:
    #         self.delete()
    #         return True
    #     return False

    def get_pair_advert_description(self):
        products = Product.objects.filter(pair=self).exclude(
            status=Product.StatusChoices.SOLD)
        quantity = products.count()

        if not products.exists():
            return ""
        # Assuming brand and tread of the first product
        first_product = products.first()
        product_brand = first_product.brand.name if first_product.brand else "Unknown brand"
        product_tread = first_product.tread.name if first_product.tread else "Unknown tread"
        product_size = first_product.size if first_product.size else "Unknown tread"
        # Main header for the advert
        combined_description = f"Mam do sprzedania komplet opon ({quantity} sztuki) x {product_size} {product_brand} {product_tread}:\n\n"

        total_net_price = Decimal(0)
        for index, product in enumerate(products, start=1):
            lines = []
            if product.id:
                lines.append(f"Opona id: {product.id}")
            if product.brand:
                lines.append(f"Marka: {product.brand.name}")
            if product.tread:
                lines.append(f"Model: {product.tread.name}")
            if product.size:
                lines.append(f"Rozmiar: {product.size}")
            if product.is_tire_bead_damaged:
                lines.append("Stopka opony posiada niewielki uszczerbek gumy, powstały podczas montażu opony na felgę. Jest to kosmetyczny ubytek, który w zaden sposób nie wpływa na bezpieczeństwo jazdy czy dalszą eksploatację opony.")
            if product.is_incised:
                lines.append(
                    "Bieżnik opony został profesjonalnie pogłębiony, według zaleceń producenta opon.")
            if product.front_repairs:
                lines.append(f"naprawy gwozdziowe: {product.front_repairs}")
            # if not product.is_side_repair:
            #     lines.append("Opona bez napraw ścian bocznych.")
            if product.is_visible_cracks:
                lines.append("Guma opony jest w niewielkim stopniu sparciała. Takie oznaki eksploatacji są widoczne czasem nawet po 1 roku użytkowania opony i nie wpływają na jej dalszą eksploatację. Przyczyną zazwyczaj są czynniki zewnętrzne takie jak np. Promienie słoneczne, NIE jest to opona uszkodzona.")
            if product.is_braked:
                lines.append(
                    "Opona posiada delikatny ślad po hamowaniu, widoczny w części bieżnika. Jest to nieduży defekt, który nie ma wpływu na dalszą eksploatację.")
            if product.is_braked_repair:
                lines.append("Opona została profesjonalnie naprawiona po “przyhamowaniu”. Widoczny ślad po hamowaniu bądź po zablokowanym hamulcu w naczepie, zostaje nadlany nową gumą oraz zwulkanizowany w autoklawie. Taka metoda naprawy pozwala na dalsze, bezpieczne użytkowanie opony.")
            if product.is_shoulder_repair:
                lines.append(
                    "Opona posiada profesjonalnie wykonaną naprawę w części barku.")
            if product.is_cosmetology:
                lines.append("Opona posiada niewielkie “poprawki” kosmetyczne. Nie nazywamy tego naprawą, ponieważ opona nie była uszkodzona. Opona używana czasami ma drobne pęknięcie lub uszczerbek gumy, np. Od kręcenia kołami w miejscu. Tego typu kosmetykę wykonujemy aby klient dostał oponę w 100 sprawną, gotową do montażu.")
            if product.is_toothed_out:
                lines.append(
                    "Opona jest delikatnie wyząbkowana. Ze względu na to, że jest to wyząbkowanie w niewielkim stopniu, może ona być dalej eksploatowana na osiach napędowych bądź wleczonych.")
            if product.is_retreaded:
                lines.append("Opona bieżnikowana")
            if product.is_ruts:
                lines.append(
                    "Widoczne są koleiny na krawędziach. Nierówności są małe, dlatego opony w pełni nadają się do dalszej jazdy.")
            if product.is_circumventional_cut:
                lines.append(
                    "Opona posiada dodatkowy rowek, który został wyżłobiony w bieżniku od ostrego przedmiotu.")
            if product.tread_depth_min is not None and product.tread_depth_max is not None:
                lines.append(
                    f"minimalna glebokosc bieznika: {product.tread_depth_min} mm")
                lines.append(
                    f"maksymalna glebokosc bieznika: {product.tread_depth_max} mm")
            if product.dot:
                lines.append(f"rok produkcji (DOT): {product.dot} r")
            if product.net_price is not None:
                total_net_price += Decimal(product.net_price)
            # if product.net_price:
                # lines.append(f"Cena netto: {product.net_price} PLN")
                # total_net_price += product.net_price
            # if product.gross_price:
            #     lines.append(f"Cena brutto: {product.gross_price} PLN")
            description = "\n".join(lines)
            if description:  # Only add to combined description if not empty
                combined_description += f"Opona {index}\n{description}\n\n"
        # Add total net and gross prices at the end of the description
        total_gross_price = round(total_net_price * Decimal('1.23'), 2)
        # combined_description += f"Cena netto razem: {total_net_price} PLN\n"
        combined_description += f"Cena brutto razem: {total_gross_price} PLN\n Wystawiam FV 23%\n"
        return combined_description
    
    @classmethod
    def get_missing_pair_numbers(cls):
        """
        Returns the first 5 missing pair numbers (as ints),
        starting from 1 up to max(existing) + 20.
        """
        numbers = set(
            int(name)
            for name in cls.objects.values_list("name", flat=True)
            if name is not None and str(name).isdigit()
        )

        if not numbers:
            missing_numbers = list(range(1, 6))
            return missing_numbers

        upper_limit = max(numbers) + 20

        missing_numbers = sorted(
            set(range(1, upper_limit + 1)) - numbers
        )

        return missing_numbers[:5]
    
    def get_tread_remaining_percent_per_product_for_pair(self):
        """
        Returns a dictionary mapping each product ID to its 
        `calculate_tread_remaining_percent` if available.
        Only considers products that are not sold.
        """
        result = {}
        products = self.products.exclude(status=Product.StatusChoices.SOLD)
        for product in products:
            percent = product.calculate_tread_remaining_percent
            if percent is not None:
                result[product.id] = percent
        return result


class PairAdvertImageProcessor:
        def __init__(self, pair, target_height=900):
            
            self.pair = pair
            self.target_height = target_height            
            product_count = pair.products.count()
            
            if product_count not in (2, 4, 8):
                pass
            # if auto_generate:
            #     self.generate_main_pair_image()
        
        def get_overlap_for_count(self, product_count):
            """
            Returns overlap in pixels.
            Positive number = overlap amount.
            """
            if product_count == 2:
                return 10   # minimal overlap
            elif product_count == 4:
                return 50    # mild overlap
            elif product_count == 8:
                return 10    # almost none
            return 0
        
        def generate_main_pair_image(self):
            products = Product.objects.filter(pair=self.pair).order_by("id")

            main_images = []

            for product in products:
                first_image = Image.objects.filter(
                    product=product,
                    image__endswith="1.jpg"
                ).first()

                if first_image and first_image.image:
                    main_images.append(first_image.image.path)

            if len(main_images) < 2:
                raise ValueError("Not enough images to generate pair image")

            pil_images = []

            for path in main_images:
                if not os.path.exists(path):
                    raise FileNotFoundError(path)

                img = PILImage.open(path).convert("RGBA")
                img = self.remove_background(img)
                img = self.smart_crop(img)
                pil_images.append(img)

            if len(pil_images) < 2:
                raise ValueError("Required image files missing on disk")

            # Resize to same height
            resized_images = []
            for img in pil_images:
                w, h = img.size
                new_width = int(self.target_height * w / h)
                resized_images.append(
                    img.resize((new_width, self.target_height), PILImage.Resampling.LANCZOS)
                )

            overlap = self.get_overlap_for_count(len(resized_images))

            total_width = sum(img.width for img in resized_images) + overlap * (len(resized_images) - 1)

            merged_img = PILImage.new(
                "RGBA",
                (total_width, self.target_height),
                (255, 255, 255, 0)
            )

            x_offset = 0
            for img in resized_images:
                merged_img.paste(img, (x_offset, 0), img)
                x_offset += img.width + overlap

            self.save_pair_image(merged_img)
        
        def remove_background(self, image, max_color_diff=50):
            img_array = np.array(image)

            if img_array.shape[2] == 3:
                alpha = np.full(img_array.shape[:2], 255, dtype=np.uint8)
                img_array = np.dstack((img_array, alpha))

            bg_color = np.array([255, 255, 255])
            color_diff = np.linalg.norm(img_array[:, :, :3] - bg_color, axis=2)
            mask = color_diff < max_color_diff
            img_array[mask, 3] = 0

            return PILImage.fromarray(img_array)
        


        def smart_crop(self, image, margin=20):
            img_array = np.array(image)
            alpha = img_array[:, :, 3]
            non_zero = np.argwhere(alpha > 0)

            if non_zero.size == 0:
                return image

            (min_y, min_x), (max_y, max_x) = non_zero.min(axis=0), non_zero.max(axis=0)

            min_x = max(0, min_x - margin)
            min_y = max(0, min_y - margin)
            max_x = min(image.width, max_x + margin)
            max_y = min(image.height, max_y + margin)

            return image.crop((min_x, min_y, max_x, max_y))


        def save_pair_image(self, image):
            buffer = BytesIO()
            image.convert("RGB").save(buffer, format="JPEG", quality=90)
            buffer.seek(0)

            filename = f"pair_{self.pair.id}_combined.jpg"

            pair_image, _ = PairImage.objects.get_or_create(pair=self.pair)

            if pair_image.image:
                pair_image.image.delete(save=False)

            pair_image.image.save(
                filename,
                InMemoryUploadedFile(
                    buffer,
                    None,
                    filename,
                    "image/jpeg",
                    buffer.getbuffer().nbytes,
                    None
                ),
                save=True
            )

            return pair_image


        
        # def save_pair_image(self, image):
        #     print("Saving the combined image...")
        #     buffer = io.BytesIO()
        #     image.save(buffer, format='JPEG')
        #     image_file = ContentFile(buffer.getvalue())
        #     try:
        #         # Try to fetch the first existing PairImage
        #         pair_image = PairImage.objects.filter(pair=self.pair).first()
        #         if not pair_image:
        #             # Create a new PairImage if none exists
        #             pair_image = PairImage.objects.create(pair=self.pair)
        #         pair_image.image.save(f'pair_image_{self.pair.id}.jpg', image_file, save=True)
        #     except Exception as e:
        #         print(f"Error saving pair image: {e}")

    # for use serializer multiple pair
    # def get_detailed_display(self):
    #     products = self.product_set.all()
    #     if products:
    #         product_strings = []
    #         for index, product in enumerate(products):
    #             if index == 0:
    #                 product_strings.append(f"{self.name}| {product.size} |{index + 1}: {product.brand}, {product.tread}")
    #             else:
    #                 product_strings.append(f"    |{index + 1}: {product.brand}, {product.tread}")
    #         return "\n".join(product_strings)
    #     return self.name

    # def get_product_details(self):
    #     return self.product_set.all()

    # for use serializer single pair
    # def get_detailed_display(self):
    #     products = self.product_set.all()
    #     if products:
    #         product = products.first()
    #         return f"{self.name}| {product.size} |1: {product.brand}, {product.tread}"
    #     return self.name

    # showing 1 pair

def __str__(self):
        products = self.products.all()
        if products:
            product = products.first()
            return f"{self.name}| {product.size} |1: {product.brand}, {product.tread}"
        return self.name    

    


class PairImage(models.Model):
    pair = models.ForeignKey(
        Pair, related_name='pairimages', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='pair_images/')


class SimilarTread(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    tread = models.ForeignKey(Tread, on_delete=models.CASCADE)
    similar_tread_combinations = models.ManyToManyField(
        'self', symmetrical=False, blank=True)

    def __str__(self):
        return f"{self.brand.name} - {self.tread.name}"


class SelectedProductFilter(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='selected_product_filter')
    name = models.CharField(max_length=100, default="Mój filtr")
    brand = models.ForeignKey(
        'Brand', on_delete=models.SET_NULL, null=True, blank=True)
    tread = models.ForeignKey(
        'Tread', on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(
        'Size', on_delete=models.SET_NULL, null=True, blank=True)
    is_tire_bead_damaged = models.BooleanField(
        ("Uszkodzona stopka"), null=True, blank=True, default=None)
    is_front_heat_repair = models.BooleanField(
        ("Naprawa czoła na gorąco"), null=True, blank=True, default=None)
    is_side_repair = models.BooleanField(
        ("Naprawy boczne"), null=True, blank=True, default=None)
    is_visible_cracks = models.BooleanField(
        ("Widoczne pęknięcia"), null=True, blank=True, default=None)
    is_braked = models.BooleanField(
        ("Hamulec"), null=True, blank=True, default=None)
    is_braked_repair = models.BooleanField(
        ("Nap. po hamulcu"), null=True, blank=True, default=None)
    is_shoulder_repair = models.BooleanField(
        ("Naprawa barku"), null=True, blank=True, default=None)
    is_cosmetology = models.BooleanField(
        ("Kosmetyka"), null=True, blank=True, default=None)
    # wyząbkowana
    is_toothed_out = models.BooleanField(
        ("Wyząbkowana"), null=True, blank=True, default=None)
    is_retreaded = models.BooleanField(
        ("Bieżnikowana"), null=True, blank=True, default=None)
    is_ruts = models.BooleanField(
        ("Koleiny"), null=True, blank=True, default=None)
    is_circumventional_cut = models.BooleanField(
        ("Wycięty rowek"), null=True, blank=True, default=None)
    oldest_dot = models.IntegerField(
        ("Najstarszy dot"),   default=0, null=True, blank=True)
    tread_depth_min = models.IntegerField(
        "Minimalny bieżnik", default=0, null=True, blank=True, validators=[MinValueValidator(4)])

    issteer = models.BooleanField(
        ("Oś sterująca"), null=True, blank=True, default=None)
    isdrive = models.BooleanField(
        ("Oś napędowa"), null=True, blank=True, default=None)
    istrailer = models.BooleanField(
        ("Oś naczepowa"), null=True, blank=True, default=None)

    # slug = models.SlugField(max_length=255, unique=True, blank=True)

    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"Filtr użytkownika {self.user.username}"


class Warehouse(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class Row(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name='rows')
    code = models.CharField(max_length=20)  # e.g., "Row 1", "A", etc.
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Rząd {self.code}"


class Rack(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name='racks')
    code = models.CharField(max_length=20)  # e.g., "R1", "A2"
    description = models.TextField(blank=True)
    row = models.ForeignKey(Row, on_delete=models.SET_NULL,
                            related_name='racks', null=True, blank=True)

    def __str__(self):
        return f"Stelaż {self.code}"


class Staple(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name='staples')
    code = models.CharField(max_length=20)  # e.g., "Row 1", "A", etc.
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Staple {self.code}"

from django.db import transaction
class Product(models.Model):
    class ProductStatusChoice(models.TextChoices):
        NEW = "new"
        LISTED = "listed"

    class StatusChoices(models.TextChoices):
        TO_ADD = "Do dodania"
        ON_SALE = "W sprzedaży"
        SOLD = "Sprzedane"
    

    # uuid = models.UUIDField(editable=False, unique=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    tread = models.ForeignKey(Tread, on_delete=models.PROTECT)
    size = models.ForeignKey(
        Size, on_delete=models.CASCADE, null=True, blank=True)
    pair = models.ForeignKey(
        Pair, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'  )
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.TO_ADD)

    is_tire_bead_damaged = models.BooleanField(
        ("Uszkodzona stopka"), default=False)
    is_incised = models.BooleanField(("Nacinana"), default=False)
    front_repairs = models.PositiveSmallIntegerField(("Naprawy gwoździowe"),
                                                     choices=FrontRepairClassChoices.choices,
                                                     default=FrontRepairClassChoices.ZERO
                                                     )
    is_front_heat_repair = models.BooleanField(
        ("Naprawa czoła na gorąco"), default=False)
    is_side_repair = models.BooleanField(("Naprawy boczne"), default=False)
    is_visible_cracks = models.BooleanField(
        ("Widoczne pęknięcia"), default=False)
    is_braked = models.BooleanField(("Hamulec"), default=False)
    is_braked_repair = models.BooleanField(
        ("Nap. po hamulcu"), default=False)
    is_shoulder_repair = models.BooleanField(("Naprawa barku"), default=False)
    is_cosmetology = models.BooleanField(("Kosmetyka"), default=False)
    # wyząbkowana
    is_toothed_out = models.BooleanField(("Wyząbkowana"), default=False)
    is_retreaded = models.BooleanField(("Bieżnikowana"), default=False)
    is_ruts = models.BooleanField(("Koleiny"), default=False)
    is_circumventional_cut = models.BooleanField(
        ("Wycięty rowek"), default=False)
    tread_depth_min = models.IntegerField(("Bieżnik MIN"))
    # tread_depth_min = models.PositiveIntegerField(validators=[MinValueValidator(5), MaxValueValidator(20)]( "Bieżnik MIN"))
    tread_depth_max = models.IntegerField(("Bieżnik MAX"))
    dot = models.IntegerField(null=True, blank=True)
    net_price = models.DecimalField(
        ("Cena netto"), max_digits=8, decimal_places=2, blank=True, null=True)
    supplier_price = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    weight = models.DecimalField(
        ("Waga"), max_digits=8, decimal_places=2, blank=True, null=True)

    is_label_printed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, auto_created=True)
    set_number = models.IntegerField(null=True, blank=True)
    product_description = models.TextField(blank=True, null=True)
    # all_apis
    ean = models.CharField(null=True, blank=True,
                           max_length=255, verbose_name="ean_number")
    advert_title = models.CharField(max_length=200)
    advert_description = models.TextField()
    
    # new_tire_tread_depth = models.FloatField(null=True, blank=True)
    # new_tire_price = models.FloatField(null=True, blank=True)
    optimized_tyre_name = models.CharField(max_length=200,blank=True, null=True)

    # otomoto
    is_otomoto_advert_created = models.BooleanField(
        ("Otomoto_advert_created"), default=False)
    is_otomoto_advert_activated = models.BooleanField(
        ("Otomoto_advert_activated"), default=False)
    

    # olx
    is_olx = models.BooleanField(("Olx"), default=False)
    is_olx_active = models.BooleanField(("Olx_Advert_Active"), default=False)
    olx_advert_id = models.PositiveIntegerField(null=True, blank=True)
    olx_response = models.TextField(null=True, blank=True)
    olx_active_advert_response = models.TextField(null=True, blank=True)
    additional_text = models.TextField(max_length=255, null=True, blank=True)
    olx_advert_status = models.CharField(max_length=50, null=True, blank=True)
    
    
    # allegro
    is_allegro = models.BooleanField(("Allegro"), default=False)
    is_allegro_active = models.BooleanField(
        ("Allegro_Advert_Active"), default=False)
    allegro_advert_id = models.CharField(max_length=255, null=True, blank=True)
    allegro_status = models.CharField(
        max_length=800, null=True, blank=True, verbose_name="Allegro response")
    allegro_api_respose = models.TextField(
        max_length=1000, null=True, blank=True)
    
    
    
    product_listing_status = models.CharField(
        max_length=20, choices=ProductStatusChoice.choices, default=ProductStatusChoice.NEW)
    # merchant center
    is_merchant_center = models.BooleanField(
        ("Google Merchant"), default=False)
    image_update_status = models.BooleanField(default=False)
    # warehouse
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    rack = models.ForeignKey(
        Rack, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    row = models.ForeignKey(Row, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='products')
    staple = models.ForeignKey(
        Staple, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    sold_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Date Sold"
    )
    on_sale_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Date On Sale"
    )
    new_tire_price = models.FloatField(
        ("New Tire Price"), null=True, blank=True)
    new_tire_tread_depth = models.FloatField(
        ("New Tire Tread Depth"), null=True, blank=True)
    
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # True if the product is being created

        if is_new:
            # Set optimized tyre name
            if self.brand and self.tread and self.size:
                combined = f"{self.brand.name}{self.tread.name}{self.size.size}"
                self.optimized_tyre_name = optimize_value(combined)

            # Fetch new_tire_price from Tread_Character
            try:
                tread_char = Tread_Character.objects.get(
                    optimized_tyre_name=self.optimized_tyre_name
                )
                if tread_char.new_tire_price is not None:
                    self.new_tire_price = tread_char.new_tire_price
            except Tread_Character.DoesNotExist:
                pass

            # Fetch new_tire_tread_depth from New_Tread_Depth
            try:
                new_depth = New_Tread_Depth.objects.get(
                    optimized_tyre_name=self.optimized_tyre_name
                )
                if new_depth.new_tire_tread_depth is not None:
                    self.new_tire_tread_depth = new_depth.new_tire_tread_depth
            except New_Tread_Depth.DoesNotExist:
                pass
        
         # fetch old value from DB if it exists
        old_status = None
        if self.pk:
            old_status = Product.objects.get(pk=self.pk).status   
                                

        super().save(*args, **kwargs)
        if old_status != self.status:
            print(f"ZMIANA STATUSU Z {old_status} NA {self.status} DLA PRODUKTU {self.id}")
            # if self.status == self.StatusChoices.SOLD:
            if self.status == "Sprzedane":
                
                try:
                    self.post_sold_actions(
                        old_status=old_status,
                        new_status=self.status,
                    )
                except Exception as e:
                    # Log the error, but do not raise
                    print(f"Failed to trigger post_sold_actions in save(): {e}")
    
    
    
    
    
    def change_status(self, new_status, *, user=None):
        
        old_status = self.status        
        self.status = new_status
        
        update_fields = ["status"]

        if new_status == self.StatusChoices.ON_SALE and not self.on_sale_at:
            self.on_sale_at = timezone.now()
            update_fields.append("on_sale_at")

        if new_status == self.StatusChoices.SOLD and not self.sold_at:
            self.sold_at = timezone.now()
            update_fields.append("sold_at")
            print(f"-------------Setting sold_at for product {self.id} to {self.sold_at}")

        self.save(update_fields=update_fields)
        
                   
    
    def post_sold_actions(self,old_status, new_status, user=None):
        #Should be named post_sold_actions
        print(f"---------------Post_Sold_actions_triggered--------------")
        

                
        from otomoto.client.otomoto_client import OtomotoClient
        from otomoto.models import OtoMotoAdvertData
        from otomoto.models import OtomotoAuthData
        
        if not self.pair:
            if  self.is_otomoto_advert_activated:
                try:
                    otomoto_data = self.otomoto_data
                except OtoMotoAdvertData.DoesNotExist:
                    # No external ad exists → nothing to deactivate
                    return
                                
                print(f"---------------Access token obtained--------------")

                client = OtomotoClient()
                client.ensure_authenticated()
                token = client.get_valid_access_token()
                response = client.deactivate_otomoto_advert(
                    otomoto_advert_id=otomoto_data.otomoto_advert_id,
                    access_token=token)
                print(f"---------------Otomoto advert deactivation response status: {response.status_code}--------------")
                
                if response.status_code // 100 == 2:                    
                    
                    with transaction.atomic():
                        obj = Product.objects.select_for_update().get(pk=self.pk)
                        obj.is_otomoto_advert_activated = False
                        obj.save(update_fields=["is_otomoto_advert_activated"])
                        # optional: refresh self
                        self.refresh_from_db(fields=["is_otomoto_advert_activated"])
            else:
                print(f"---------------Otomoto advert was not activated, skipping deactivation--------------")
        
        else:
            pair = self.pair
            print(f"Product belongs to pair ID: {pair.id}")

            # Attempt to deactivate the Otomoto advert linked to the pair
            try:
                otomoto_data = pair.otomoto_advert  # assumes pair has a OneToOne/ForeignKey to OtoMotoAdvertData
                print(f"Found Otomoto advert ID {otomoto_data.otomoto_advert_id} linked to pair {pair.id}")

                client = OtomotoClient()
                client.ensure_authenticated()
                token = client.get_valid_access_token()
                response = client.deactivate_otomoto_advert(
                    otomoto_advert_id=otomoto_data.otomoto_advert_id,
                    access_token=token
                )
                print(f"Otomoto deactivation response status: {response.status_code}")

                if response.status_code // 100 == 2:
                    with transaction.atomic():
                        pair.is_otomoto_pair_advert_activated = False  # update pair advert status
                        pair.save(update_fields=["is_otomoto_pair_advert_activated"])
                        print(f"Otomoto advert for pair {pair.id} deactivated successfully.")
                else:
                    print("Failed to deactivate Otomoto advert for pair.")

            except Exception as e:
                # Catch all exceptions, so deactivation failures do not prevent pair deletion
                print(f"Error during Otomoto deactivation: {e}")

            # Delete the pair regardless of what happened with the ad
            try:
                print(f"Deleting pair ID: {pair.id} ({pair.name})")
                pair.delete()
                print(f"Pair {pair.id} deleted successfully.")
            except Exception as e:
                print(f"Failed to delete pair {pair.id}: {e}")
    
    
    def refresh_new_tire_data(self):
        """Refresh new_tire_price and new_tire_tread_depth from related models."""
        if not self.optimized_tyre_name:
            return  # nothing to fetch

        # Update price
        try:
            tread_char = Tread_Character.objects.get(
                optimized_tyre_name=self.optimized_tyre_name
            )
            if tread_char.new_tire_price is not None:
                self.new_tire_price = tread_char.new_tire_price
        except Tread_Character.DoesNotExist:
            self.new_tire_price = None

        # Update tread depth
        try:
            new_depth = New_Tread_Depth.objects.get(
                optimized_tyre_name=self.optimized_tyre_name
            )
            if new_depth.new_tire_tread_depth is not None:
                self.new_tire_tread_depth = new_depth.new_tire_tread_depth
        except New_Tread_Depth.DoesNotExist:
            self.new_tire_tread_depth = None

        # Save changes to DB
        self.save(update_fields=['new_tire_price', 'new_tire_tread_depth'])
        
    
    @property
    def calculate_percent_of_new_tyre_price(self):
        """
        Returns percent price of a new tyre
        """
        if (
        not self.new_tire_price
        or not self.net_price
        ):
            return None
        
        percent = (self.net_price / Decimal(str(self.new_tire_price))) * Decimal("100")
        return round(percent, 0)
        
    @property
    def calculate_tread_remaining_percent(self):
        """
        Returns how much of a new tyre tread remains (in percent).
        Example: 8mm from 10mm = 80
        """
        if (
            self.new_tire_tread_depth is None
            or self.new_tire_tread_depth == 0
            or self.tread_depth_min is None
        ):
            return None

        percent = (
            self.tread_depth_min / self.new_tire_tread_depth
        ) * 100

        # Optional safety clamp (protect against bad data)
        percent = max(0, min(percent, 100))

        return int(round(percent))
    
    
    @property
    def assessed_potential_mileage(self):
        premium_brands = ["michelin", "hankook","pirelli","bridgestone","continental"]
        brand_name = self.brand.name.lower()
        current_tread_depth = self.tread_depth_min
        tread_to_wear = max(current_tread_depth - 2, 0)  # avoid negative mileage

        # Base mileage ranges per 1 mm of tread
        steer_mileage = (8000, 10000)
        drive_mileage = (4000, 6000)
        trailer_mileage = (6000, 8000)
        
        mileage = {}

        # Steer
        if self.tread.is_steer:
            m = (tread_to_wear * steer_mileage[0], tread_to_wear * steer_mileage[1])
            if brand_name in premium_brands:
                m = (m[0] + 10000, m[1] + 10000)
            mileage['s'] = m

        # Drive
        if self.tread.is_drive:
            m = (tread_to_wear * drive_mileage[0], tread_to_wear * drive_mileage[1])
            if brand_name in premium_brands:
                m = (m[0] + 10000, m[1] + 10000)
            mileage['d'] = m

        # Trailer
        if self.tread.is_trailer:
            m = (tread_to_wear * trailer_mileage[0], tread_to_wear * trailer_mileage[1])
            if brand_name in premium_brands:
                m = (m[0] + 10000, m[1] + 10000)
            mileage['t'] = m

        if not mileage:
            mileage['unknown'] = (0, 0)

        return mileage
            

    
    
                     
    @property
    def preferred_image(self):
        # Try to find image ending with -1.jpg
        img = self.images.filter(image__endswith='-1.jpg').first()
        if img:
            return img

        # Fallback to first image
        return self.images.first()
          
      
      
    @property
    def get_tyre_class(self):

        tread_average = (self.tread_depth_max + self.tread_depth_min) / 2
        tyre_class = ""
        if tread_average < 7:
            tyre_class = 3
        elif tread_average < 11:
            tyre_class = 2
        else:
            tyre_class = 1
        return tyre_class
    
    @property
    def tread_character_price(self):
        """
        Returns the new_tire_price from Tread_Character matching this product's optimized_tyre_name.
        """
        if not self.optimized_tyre_name:
            return None
        tc = Tread_Character.objects.filter(
            optimized_tyre_name=self.optimized_tyre_name
        ).first()
        return tc.new_tire_price if tc else None
    
    @property
    def images_uploaded_to_allegro(self):
        # Returns True if any images have allegro_image_url
        return self.images.filter(allegro_image_url__isnull=False).exists()
    
    
  
   
    
    @property
    def new_tread_depth(self):
        """
        Returns the new_tire_price from Tread_Character matching this product's optimized_tyre_name.
        """
        if not self.optimized_tyre_name:
            return None
        tc = New_Tread_Depth.objects.filter(
            optimized_tyre_name=self.optimized_tyre_name
        ).first()
        return tc.new_tire_tread_depth if tc else None

    # # --- main method ---
    # def assign_new_tire_tread_depth(self, save=True):
    #     """
    #     Assigns new_tire_tread_depth based on brand, tread and size.
    #     Returns assigned value or None.
    #     """
    #     if not self.size:
    #         self.new_tire_tread_depth = None
    #         if save:
    #             self.save(update_fields=["new_tire_tread_depth"])
    #         return None

    #     optimized_brand = self._optimize(self.brand.name)
    #     optimized_tread = self._optimize(self.tread.name)
    #     size_name = str(self.size.size)

    #     nt = New_Tread_Depth.objects.filter(
    #         brand__isnull=False,
    #         tread__isnull=False,
    #         size=size_name,
    #     ).first()

    #     # safer match using optimized fields
    #     nt = New_Tread_Depth.objects.filter(
    #         size=size_name
    #     ).annotate(
    #         ob=models.functions.Lower(
    #             models.functions.Replace(
    #                 models.functions.Replace("brand", models.Value(" "), models.Value("")),
    #                 models.Value("-"), models.Value("")
    #             )
    #         ),
    #         ot=models.functions.Lower(
    #             models.functions.Replace(
    #                 models.functions.Replace("tread", models.Value(" "), models.Value("")),
    #                 models.Value("-"), models.Value("")
    #             )
    #         ),
    #     ).filter(
    #         ob=optimized_brand,
    #         ot=optimized_tread,
    #     ).first()

    #     self.new_tire_tread_depth = nt.new_tire_tread_depth if nt else None

    #     if save:
    #         self.save(update_fields=["new_tire_tread_depth"])

    #     return self.new_tire_tread_depth
    
    
    
    def get_best_pallete_option(self):
        if not self.size or not hasattr(self.size, 'tread_to_y_winner'):
            return None

        tread_to_y_value = self.size.tread_to_y_winner
        if not tread_to_y_value:
            return None

        lowest_prices_dict = TransportationCost.lowest_price_per_pallet()

        # Normalize winner: replace underscores, uppercase, strip spaces
        normalized_winner = ' '.join(self.size.tread_to_y_winner.replace('_', ' ').upper().split())

        # Normalize dictionary keys
        normalized_dict = {' '.join(k.upper().split()): v for k, v in lowest_prices_dict.items()}

        lowest_transport_price = normalized_dict.get(normalized_winner)

        return {
            "winner": tread_to_y_value,
            "transport_price": lowest_transport_price,
        }
    
    
    
    

    def get_advert_title(self):
        advert_title = f"{self.size} {self.brand} {self.tread} "
        return advert_title

    def get_product_description(self):

        instance = self
        description = ""
        description += f"Id opony:{instance.id}\n\n"

        description += f"Na sprzedaż opona {instance.brand} {instance.tread} w rozmiarze {instance.size} \n\n"

        description += f"Rozmiar: {instance.size} \n\n"
        # description += f"Data produkcji opony:{instance.dot}r \n\n"

        if instance.dot == None or instance.dot == 0:
            description += f""
        else:
            description += f"Data produkcji to: {instance.dot}r \n\n"

        description += f"Głębokość bieżnika w najpłytszym miejscu: {instance.tread_depth_min} mm\n\n"
        description += f"Głębokość bieżnika w najgłębszym miejscu: {instance.tread_depth_max} mm \n\n"
        description += _(
            "Stopka opony posiada niewielki uszczerbek gumy, powstały podczas montażu opony na felgę. Jest to kosmetyczny ubytek, który w zaden sposób nie wpływa na bezpieczeństwo jazdy czy dalszą eksploatację opony.\n\n") if instance.is_tire_bead_damaged else ""
        description += _(
            "Bieżnik opony został profesjonalnie pogłębiony, według zaleceń producenta opon.\n\n") if instance.is_incised else ""
        description += _("Opona posiada profesjonalnie wykonaną naprawę na ścianie bocznej. \
                        Tego typu naprawy, wykonujemy jedynie jeśli uszkodzenie było nieduże i \
                        technologicznie możliwe do naprawy. Dostosowujemy się do zaleceń \
                        producentów wkładów naprawczych, które jasno określają, jakiego \n\n") \
            if instance.is_side_repair else "Opona bez napraw ścian bocznych.\n\n"
        description += (
            _("Guma opony jest w niewielkim stopniu sparciała. Takie oznaki eksploatacji są widoczne czasem nawet po 1 roku użytkowania opony i nie wpływają na jej dalszą eksploatację. Przyczyną zazwyczaj są czynniki zewnętrzne takie jak np. Promienie słoneczne, NIE jest to opona uszkodzona.\n\n") if instance.is_visible_cracks else ""
        )
        description += _(
            "Opona posiada delikatny ślad po hamowaniu, widoczny w części bieżnika. Jest to nieduży defekt, który nie ma wpływu na dalszą eksploatację.\n\n") if instance.is_braked else ""
        description += _(
            "Opona została profesjonalnie naprawiona po “przyhamowaniu”. Widoczny ślad po hamowaniu bądź po zablokowanym hamulcu w naczepie, zostaje nadlany nową gumą oraz zwulkanizowany w autoklawie. Taka metoda naprawy pozwala na dalsze, bezpieczne użytkowanie opony.\n\n") if instance.is_braked_repair else ""
        description += (
            _("Opona posiada profesjonalnie wykonaną naprawę w części barku.\n\n") if instance.is_shoulder_repair else ""
        )
        description += _(
            "Opona posiada niewielkie “poprawki” kosmetyczne. Nie nazywamy tego naprawą, ponieważ opona nie była uszkodzona. Opona używana czasami ma drobne pęknięcie lub uszczerbek gumy, np. Od kręcenia kołami w miejscu. Tego typu kosmetykę wykonujemy aby klient dostał oponę w 100 sprawną, gotową do montażu.\n\n") if instance.is_cosmetology else ""
        description += _(
            "Opona jest delikatnie wyząbkowana. Ze względu na to, że jest to wyząbkowanie w niewielkim stopniu, może ona być dalej eksploatowana na osiach napędowych bądź wleczonych.\n\n") if instance.is_toothed_out else ""
        description += _("Opona bieżnikowana.") if instance.is_retreaded else ""
        description += _(
            "Widoczne są koleiny na krawędziach. Nierówności są małe, dlatego opony w pełni nadają się do dalszej jazdy.\n\n") if instance.is_ruts else ""
        description += (
            _("Opona posiada dodatkowy rowek, który został wyżłobiony w bieżniku od ostrego przedmiotu\n\n")
            if instance.is_circumventional_cut
            else ""
        )

        description = description.replace('/n', ' ')
        return description

    def get_ean(self):
        try:
            # Retrieve the relevant values from the instance
            brand_name = self.brand.name
            tread_name = self.tread.name
            width = self.size.width
            profile = self.size.profile  # Not used in the query, but you may want to consider it
            diameter = self.size.diameter

            # If diameter is a Decimal, normalize and format it
            if isinstance(diameter, Decimal):
                diameter = diameter.normalize()
                diameter = str(diameter)
                diameter = "R" + diameter

            # Query the Ean model to find a matching record
            ean_record = Tyre_Ean.objects.filter(
                ean_brand=brand_name,
                ean_tread=tread_name,
                ean_width=width,
                ean_diameter=diameter,
                ean_profile=profile
            ).first()  # Use `first()` to get the first match (or None if no match)

            # Return the EAN if a match is found
            if ean_record:
                return ean_record.ean
            return None  # Return None if no match is found

        except Exception as e:
            # Log the exception or handle it as needed
            print(f"Error: {e}")
            return None

    def get_advert_description(self):

        instance = self
        description = ""
        # description += f"{instance.brand} {instance.tread} {instance.dot} {instance.tread_depth_min} - {instance.tread_depth_max} mm bieżnika {instance.net_price} netto za 1 szt, Cena transportu opony to {self.transportation_cost}\n"
        description += f"UWAGA! Wszystkie zdjęcia dotyczą jednej i tej samej opony. Zdjęcia opony są wykonane z różnych stron.\n"
        description += f"Cena aukcji dotyczy jednej sztuki.\n\n\n"
        description += f"{instance.brand} {instance.tread} \n\n"

        description += f"Rozmiar: {instance.size} \n\n"
        # description += f"Data produkcji opony:{instance.dot}r \n\n"

        if instance.dot == None or instance.dot == 0:
            description += f"Data produkcji opony: Brak \n\n"
        else:
            description += f"Data produkcji opony: {instance.dot}r \n\n"

        description += f"Głębokość bieżnika w najpłytszym miejscu: {instance.tread_depth_min} mm\n\n"
        description += f"Głębokość bieżnika w najgłębszym miejscu: {instance.tread_depth_max} mm \n\n"
        description += f"Cena opony: {float(instance.net_price) * 1.23:.2f} brutto za 1 szt \n\n"
        description += f"Wystawiam fakturę VAT \n\n"

        description += _(
            "Stopka opony posiada niewielki uszczerbek gumy, powstały podczas montażu opony na felgę. Jest to kosmetyczny ubytek, który w zaden sposób nie wpływa na bezpieczeństwo jazdy czy dalszą eksploatację opony.\n\n") if instance.is_tire_bead_damaged else ""
        description += _(
            "Bieżnik opony został profesjonalnie pogłębiony, według zaleceń producenta opon.\n\n") if instance.is_incised else ""
        description += _("Opona posiada profesjonalnie wykonaną naprawę na ścianie bocznej. \
                        Tego typu naprawy, wykonujemy jedynie jeśli uszkodzenie było nieduże i \
                        technologicznie możliwe do naprawy. Dostosowujemy się do zaleceń \
                        producentów wkładów naprawczych, które jasno określają, jakiego \n\n") \
            if instance.is_side_repair else "Opona bez napraw ścian bocznych.\n\n"
        description += (
            _("Guma opony jest w niewielkim stopniu sparciała. Takie oznaki eksploatacji są widoczne czasem nawet po 1 roku użytkowania opony i nie wpływają na jej dalszą eksploatację. Przyczyną zazwyczaj są czynniki zewnętrzne takie jak np. Promienie słoneczne, NIE jest to opona uszkodzona.\n\n") if instance.is_visible_cracks else ""
        )
        description += _(
            "Opona posiada delikatny ślad po hamowaniu, widoczny w części bieżnika. Jest to nieduży defekt, który nie ma wpływu na dalszą eksploatację.\n\n") if instance.is_braked else ""
        description += _(
            "Opona została profesjonalnie naprawiona po “przyhamowaniu”. Widoczny ślad po hamowaniu bądź po zablokowanym hamulcu w naczepie, zostaje nadlany nową gumą oraz zwulkanizowany w autoklawie. Taka metoda naprawy pozwala na dalsze, bezpieczne użytkowanie opony.\n\n") if instance.is_braked_repair else ""
        description += (
            _("Opona posiada profesjonalnie wykonaną naprawę w części barku.\n\n") if instance.is_shoulder_repair else ""
        )
        description += _(
            "Opona posiada niewielkie “poprawki” kosmetyczne. Nie nazywamy tego naprawą, ponieważ opona nie była uszkodzona. Opona używana czasami ma drobne pęknięcie lub uszczerbek gumy, np. Od kręcenia kołami w miejscu. Tego typu kosmetykę wykonujemy aby klient dostał oponę w 100 sprawną, gotową do montażu.\n\n") if instance.is_cosmetology else ""
        description += _(
            "Opona jest delikatnie wyząbkowana. Ze względu na to, że jest to wyząbkowanie w niewielkim stopniu, może ona być dalej eksploatowana na osiach napędowych bądź wleczonych.\n\n") if instance.is_toothed_out else ""
        description += _("Opona bieżnikowana.") if instance.is_retreaded else ""
        description += _(
            "Widoczne są koleiny na krawędziach. Nierówności są małe, dlatego opony w pełni nadają się do dalszej jazdy.\n\n") if instance.is_ruts else ""
        description += (
            _("Opona posiada dodatkowy rowek, który został wyżłobiony w bieżniku od ostrego przedmiotu\n\n")
            if instance.is_circumventional_cut
            else ""
        )
        description += "STAŁE DOSTAWY OPON NA BIEŻĄCO!\n\n"
        description += "Posiadam inne opony oraz pary/ komplety w tym rozmiarze.\n\n"
        description += "Mam także dużą ilość opon używanych w innych rozmiarach.\n\n"
        description += "Udzielamy gwarancji rozruchowej na 1 miesiąc.\n\n"
        description += "Każda z Naszych opon jest sprawdzona ciśnieniowo do 10 bar oraz wizualnie.\n\n"
        description += "Możliwy montaż mobilnie/ stacjonarnie\n\n"
        description += "Możliwa wysyłka kurierem. Przy zakupie większej ilości oferujemy rabaty i darmową wysyłkę!\n\n"
        description += "Nawiążemy stałą współpracę na korzystnych warunkach !\n\n"
        description += "Zapraszam 7.3.3.4.5.6.4.7.4\n\n"
        description = description.replace('/n', ' ')
        return description

    @property
    def transportation_cost(self):
        weight = self.weight
        pal_name = self.size.pallete.name
        if weight and pal_name:
            from django.db.models import Min
            if weight < 40:
                from decimal import Decimal
                # Get the smallest kg greater than or equal to the given weight
                nearest_weight = TransportationCost.objects.filter(
                    pallet__name__icontains=pal_name,  # Filter based on pallet name
                ).aggregate(min_kg=Min('kg'))['min_kg']  # Get the minimum kg value
                if nearest_weight:
                    weight = Decimal(nearest_weight)
            # Get the smallest kg greater than or equal to the given weight
            nearest_kg = TransportationCost.objects.filter(
                pallet__name__icontains=pal_name,  # Filter based on pallet name
                kg__gte=weight  # Get objects where kg is greater than or equal to self.weight
            ).aggregate(min_kg=Min('kg'))['min_kg']  # Get the minimum kg value
            # If a nearest kg is found, filter objects by that kg
            if nearest_kg:
                objects = TransportationCost.objects.filter(
                    pallet__name__icontains=pal_name,
                    kg=nearest_kg  # Only select objects with the nearest kg
                )

                # Check if objects exist
                if objects.exists():
                    # Get the minimum price from the filtered objects
                    min_price = objects.aggregate(
                        min_price=Min('price'))['min_price']
                    return min_price
        return 0

    @property
    def brand_name(self):
        return self.brand.name

    @property
    def tread_name(self):
        return self.tread.name

    @property
    def width_value(self):
        return self.size.width

    @property
    def profile_value(self):

        return self.size.profile

    @property
    def diameter_value(self):
        return f"R{self.size.diameter}"

    @property
    def gross_price(self):
        net_price = self.net_price if self.net_price is not None else 0
        try:
            vat = float(self.get_vat)
        except (TypeError, ValueError):
            vat = 0

        return float(net_price) + vat

    @property
    def get_vat(self):
        """
        return 1.23% of net price
        """
        return (float(self.net_price) * 1.23) / 100

    @property
    def combined_id(self):
        result = (str(self.brand) + str(self.tread) +
                  self.size).replace(" ", "").lower()
        return result

    @property
    def description(self):

        desc = ""

        if self.is_visible_cracks == False:
            return desc + 'Opona ma pęknięcia'

        # if self.is_tire_bead_damaged ==True:
        #     return desc + 'Opona ma uszkodzoną stopkę'

    @property
    def optimized_brand(self):
        result = (str(self.brand).replace(" ", "").lower().replace("-", ""))
        return result

    @property
    def optimized_tread(self):
        result = (str(self.tread).replace(" ", "").lower().replace("-", ""))
        return result

    def __str__(self):
        return (
            f"{self.brand.name}{self.tread.name} {self.size} {self.is_tire_bead_damaged}\
            {self.is_incised} {self.front_repairs}{self.is_front_heat_repair} {self.is_side_repair}\
            {self.is_visible_cracks}{self.is_braked}{self.is_braked_repair}{self.is_shoulder_repair}{self.is_cosmetology}\
            {self.is_toothed_out}{self.is_retreaded}\
            {self.is_ruts}{self.is_circumventional_cut}{self.tread_depth_min}{self.tread_depth_max}{self.dot}{self.net_price}\
            {self.supplier_price}{self.weight}{self.is_label_printed}{self.created}{self.set_number}{self.gross_price}{self.is_label_printed}{self.optimized_brand}{self.optimized_tread}"
        )


class StockItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    row = models.ForeignKey(
        Row, on_delete=models.CASCADE, blank=True, null=True)
    rack = models.ForeignKey(
        Rack, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ('product', 'warehouse', 'rack')

    def __str__(self):
        location = f"on {self.rack}" if self.rack else "on the ground"
        return f"{self.product} in {self.warehouse} {location}"


def get_image_name(instance, filename):
    # print("\n=== get_image_name ===")
    # print(f"Instance PK: {instance.pk}")
    # print(f"Original filename: {filename}")

    if instance.pk:
        # print("Instance has PK - checking for existing image")
        try:
            existing_instance = Image.objects.get(pk=instance.pk)
            if existing_instance.image:
                # print(f"Found existing image: {existing_instance.image.name}")
                # print("Returning existing image name")
                return existing_instance.image.name
            else:
                print("No existing image found for this instance")
        except Image.DoesNotExist:
            print("Instance doesn't exist in DB yet")

    # print("Generating new filename")
    upload_to = 'images'
    ext = filename.split('.')[-1].lower()
    product = instance.product
    brand = product.brand
    size = product.size
    tread = product.tread

    try:
        last_image = Image.objects.filter(
            product=product).order_by('-id').first()
        if last_image:
            # print(f"Last image found: {last_image.image.name}")
            serial_number = int(last_image.image.name.split(
                '-')[-1].split('.')[0]) + 1
            # print(f"Using serial number: {serial_number}")
        else:
            serial_number = 1
            # print("No previous images found - starting with serial number 1")
    except (Image.DoesNotExist, ValueError):
        serial_number = 1
        # print("Error getting last image - using default serial number 1")

    filename = f"{brand}-{tread}-{size}-{product.id}-{serial_number}.{ext}"
    filename = filename.replace("/", "-")
    final_path = os.path.join(upload_to, filename)

    # print(f"Generated new filename: {final_path}")
    return final_path


class Image(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        null=True, blank=True, storage=OverwriteStorage(), upload_to=get_image_name)
    updated_at = models.DateTimeField(auto_now=True)
    force_update = models.BooleanField(default=False)
    allegro_image_url = models.URLField(max_length=500, null=True, blank=True)
    allegro_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.image}"

    def save(self, *args, **kwargs):
        # Force database update by modifying a non-file field
        if self.pk:  # Only for updates, not creations
            self.updated_at = timezone.now()
            self.force_update = not self.force_update

        # Your existing image processing code
        if self.image:
            img = PImage.open(self.image)
            new_size_img = img.resize((900, 900), PImage.LANCZOS)
            output = io.BytesIO()
            new_size_img.convert("RGB")
            new_size_img.save(output, format='JPEG', quality=60)
            output.seek(0)

            # Create new file but keep same name
            self.image = InMemoryUploadedFile(
                output,
                'ImageField',
                self.image.name,  # Keep original name
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )

        super().save(*args, **kwargs)

    def refresh_image(self):
        """Force refresh the image reference"""
        self.image.close()
        self.image.open()
        self.refresh_from_db()
    


# MODEL TO ADD TREADS as many tyres can share the same characteristics
class Tread_Character(models.Model):
    # brand = models.ForeignKey(Brand, on_delete=models.CASCADE,blank=True, null=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    tread = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    new_tire_price = models.FloatField(blank=True, null=True)
    shop_url = models.CharField(max_length=255, null=True, blank=True)
    optimized_tyre_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        null=True,  # temporarily allow null
        blank=True
    )


    def save(self, *args, **kwargs):
        # Combine brand, tread, and size, then optimize
        combined = f"{self.brand}{self.tread}{self.size}"
        self.optimized_tyre_name = optimize_value(combined)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} {self.tread} {self.size} {self.new_tire_price} {self.shop_url} {self.optimized_tyre_name}"


class New_Tread_Depth(models.Model):
    # brand = models.ForeignKey(Brand, on_delete=models.CASCADE,blank=True, null=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    tread = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    new_tire_tread_depth = models.FloatField(blank=True, null=True)
    optimized_tyre_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        null=True,  # temporarily allow null
        blank=True
    )
    
    
    def save(self, *args, **kwargs):
        # Combine brand, tread, and size, then optimize
        combined = f"{self.brand}{self.tread}{self.size}"
        self.optimized_tyre_name = optimize_value(combined)
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f"{self.brand} {self.tread} {self.size} {self.new_tire_tread_depth} {self.optimized_tyre_name}"


class Tread_Image(models.Model):
    tread = models.ForeignKey(Tread_Character, on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True)

    def __str__(self):
        return (
            f"{self.image}"
        )


class Company(models.Model):
    company_name = models.CharField(max_length=255)

    def __str__(self):
        return self.company_name


class TransportationCost(models.Model):
    pallet = models.ForeignKey(Pallete, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    kg = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pal_discounted_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    
    
    @classmethod
    def lowest_price_per_pallet(cls):
        """
        Returns a dictionary with pallet name as key and lowest price as value.
        """
        lowest_prices = cls.objects.values('pallet__name').annotate(
            lowest_price=Min('price')
        )
        return {item['pallet__name']: item['lowest_price'] for item in lowest_prices}
    
    
    


class Tyre_Ean(models.Model):
    ean_brand = models.CharField(max_length=255)
    ean_tread = models.CharField(max_length=255)
    # Handles both integer and decimal values
    ean_width = models.DecimalField(max_digits=10, decimal_places=2)
    ean_profile = models.CharField(
        max_length=20, null=True, blank=True)  # Null and blank allowed
    # Increased from 10 to 20 for flexibility
    ean_diameter = models.CharField(max_length=20)
    ean_size = models.CharField(max_length=50)
    ean_li = models.CharField(max_length=20)  # Load Index as string
    ean_si = models.CharField(max_length=20)   # Speed Index as string
    ean = models.BigIntegerField(unique=True)  # Ensures uniqueness

    def __str__(self):
        return f"{self.ean_brand} {self.ean_tread} ({self.ean_size})"

