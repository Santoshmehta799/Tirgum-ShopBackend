# py manage.py fill_descriptions

from django.core.management.base import BaseCommand
# from tyreadderapp.models import Product

# class Command(BaseCommand):
#     help = "Fill description field for all existing products"

#     def handle(self, *args, **kwargs):
#         products = Product.objects.all()
#         for product in products:
#             product.product_description = product.get_product_description()
#             product.save(update_fields=["product_description"])
#         self.stdout.write(self.style.SUCCESS("✅ All product descriptions updated successfully"))


from django.core.management.base import BaseCommand
from tyreadderapp.models import Product, Tread

# class Command(BaseCommand):
#     help = "Update has_image field for all existing treads"

#     def handle(self, *args, **kwargs):
#         treads = Tread.objects.all()
#         updated_count = 0

#         for tread in treads:
#             tread.has_image = bool(tread.image)
#             tread.save(update_fields=["has_image"])
#             updated_count += 1

#         self.stdout.write(self.style.SUCCESS(f"✅ {updated_count} treads updated with has_image field"))




# class Command(BaseCommand):
#     help = 'Update advert descriptions for all products'

#     def handle(self, *args, **kwargs):
#         products = Product.objects.all()
#         total = products.count()
        
#         self.stdout.write(f'Starting update for {total} products...')
        
#         updated = 0
#         for product in products:
#             try:
#                 product.advert_description = product.get_advert_description()
#                 product.save()
#                 updated += 1
                
#                 # Progress dikhane ke liye
#                 if updated % 100 == 0:
#                     self.stdout.write(f'Updated {updated}/{total}...')
            
#             except Exception as e:
#                 self.stdout.write(
#                     self.style.ERROR(f'Error updating product {product.id}: {str(e)}')
#                 )
        
#         self.stdout.write(
#             self.style.SUCCESS(f'Successfully updated {updated} products!')
#         )




class Command(BaseCommand):
    help = "Recalculate and update EAN for all existing products. If no match, clear invalid EAN."

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        total = products.count()
        updated = 0
        cleared = 0
        errors = 0

        self.stdout.write(f" Found {total} products. Recalculating EANs...")

        for product in products:
            try:
                new_ean = product.get_ean()

                if new_ean and product.ean != new_ean:
                    # ✅ Update EAN if changed
                    product.ean = new_ean
                    product.save(update_fields=["ean"])
                    updated += 1
                    self.stdout.write(f"✅ Updated Product ID {product.id} → EAN: {new_ean}")

                elif not new_ean and product.ean:
                    # ⚠️ Clear old wrong EAN
                    product.ean = ""
                    product.save(update_fields=["ean"])
                    cleared += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"️ Cleared old EAN for Product ID {product.id} (no valid match found)"
                        )
                    )

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f" Error on Product ID {product.id}: {e}"))

        self.stdout.write("\n--- Summary ---")
        self.stdout.write(f"Total Products: {total}")
        self.stdout.write(f" Updated: {updated}")
        self.stdout.write(f" Cleared old EANs: {cleared}")
        self.stdout.write(f" Errors: {errors}")
        self.stdout.write(self.style.SUCCESS(" Done! All products processed."))