# from django.test import TestCase

# # Create your tests here.
# def save(self, *args, **kwargs):
#         # Detect status change
#         status_changed_to_on_sale = False
        
#         if self.pk:  # Only check if object already exists
#             old_status = Product.objects.filter(pk=self.pk).values_list('status', flat=True).first()
#             if old_status != self.status and self.status == self.StatusChoices.ON_SALE:
#                 status_changed_to_on_sale = True

#         # Set net_price if None
#         if self.net_price is None:
#             try:
#                 self.net_price = Decimal(predict_net_price(self))
#             except Exception as e:
#                 self.net_price = None

#         # Calculate profit if adding
#         if self._state.adding:
#             self.profit = (self.net_price or 0) - self.supplier_price
#             # Generate descriptions
#         self.product_description = self.get_product_description()   
#         self.advert_description = self.get_advert_description()
#         self.otomoto_advert_description = self.get_otomoto_advert_description()

#         super().save(*args, **kwargs)

#         # Trigger Otomoto advert creation if status changed to ON_SALE
#         if status_changed_to_on_sale:
#             from otomoto.client import OtomotoClient
#             from otomoto.models import OtomotoAuthData
#             try:
#                 # Get auth_data (assume you have only one row or get the correct one)
#                 auth_data = OtomotoAuthData.objects.last()  # adjust if you have multiple
#                 print("Auth data:", auth_data)
#                 # auth = OtomotoAuthData.objects.last()
#                 # client = OtomotoClient(auth)

#                 # Create Otomoto client and trigger advert creation
#                 client = OtomotoClient(auth_data)
#                 client.create_and_save_advert(self)
#             except Exception as e:
#                 print(f"[ERROR] Failed to create Otomoto advert: {e}")