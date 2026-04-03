from django.core.management.base import BaseCommand
from tyreadderapp.models import Product, Tread_Character
from django.db import transaction
from ...helpers import optimize_value


class Command(BaseCommand):
    help = "Fill optimized_tyre_name for existing Products"

    def handle(self, *args, **options):
        self.stdout.write("Filling optimized_tyre_name for Products...")

        updated = 0

        products = Product.objects.select_related("brand", "tread", "size")

        for product in products:
            if not (product.brand and product.tread and product.size):
                continue

            combined = f"{product.brand.name}{product.tread.name}{product.size.size}"
            optimized_name = optimize_value(combined)

            if product.optimized_tyre_name != optimized_name:
                product.optimized_tyre_name = optimized_name
                product.save(update_fields=["optimized_tyre_name"])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done. Updated {updated} products.")
        )
