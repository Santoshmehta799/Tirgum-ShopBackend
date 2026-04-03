# class Product(models.Model):
#     class ProductStatusChoice(models.TextChoices):
#         NEW = "new"
#         LISTED = "listed"

#     class StatusChoices(models.TextChoices):
#         TO_ADD = "Do dodania"
#         ON_SALE = "W sprzedaży"
#         SOLD = "Sprzedane"
    

#     # uuid = models.UUIDField(editable=False, unique=True)
#     brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
#     tread = models.ForeignKey(Tread, on_delete=models.PROTECT)
#     size = models.ForeignKey(
#         Size, on_delete=models.CASCADE, null=True, blank=True)
#     pair = models.ForeignKey(
#         Pair, on_delete=models.SET_NULL, null=True, blank=True)
#     status = models.CharField(
#         max_length=20, choices=StatusChoices.choices, default=StatusChoices.TO_ADD)

#     is_tire_bead_damaged = models.BooleanField(
#         ("Uszkodzona stopka"), default=False)
#     is_incised = models.BooleanField(("Nacinana"), default=False)
#     front_repairs = models.PositiveSmallIntegerField(("Naprawy gwoździowe"),
#                                                      choices=FrontRepairClassChoices.choices,
#                                                      default=FrontRepairClassChoices.ZERO
#                                                      )
#     is_front_heat_repair = models.BooleanField(
#         ("Naprawa czoła na gorąco"), default=False)
#     is_side_repair = models.BooleanField(("Naprawy boczne"), default=False)
#     is_visible_cracks = models.BooleanField(
#         ("Widoczne pęknięcia"), default=False)
#     is_braked = models.BooleanField(("Hamulec"), default=False)
#     is_braked_repair = models.BooleanField(
#         ("Nap. po hamulcu"), default=False)
#     is_shoulder_repair = models.BooleanField(("Naprawa barku"), default=False)
#     is_cosmetology = models.BooleanField(("Kosmetyka"), default=False)
#     # wyząbkowana
#     is_toothed_out = models.BooleanField(("Wyząbkowana"), default=False)
#     is_retreaded = models.BooleanField(("Bieżnikowana"), default=False)
#     is_ruts = models.BooleanField(("Koleiny"), default=False)
#     is_circumventional_cut = models.BooleanField(
#         ("Wycięty rowek"), default=False)
#     tread_depth_min = models.IntegerField(("Bieżnik MIN"))
#     # tread_depth_min = models.PositiveIntegerField(validators=[MinValueValidator(5), MaxValueValidator(20)]( "Bieżnik MIN"))
#     tread_depth_max = models.IntegerField(("Bieżnik MAX"))
#     dot = models.IntegerField(null=True, blank=True)
#     net_price = models.DecimalField(
#         ("Cena netto"), max_digits=8, decimal_places=2, blank=True, null=True)
#     supplier_price = models.DecimalField(
#         max_digits=5, decimal_places=2, default=0)
#     profit = models.DecimalField(max_digits=8, decimal_places=2, default=0)

#     weight = models.DecimalField(
#         ("Waga"), max_digits=8, decimal_places=2, blank=True, null=True)

#     is_label_printed = models.BooleanField(default=False)
#     created = models.DateTimeField(auto_now_add=True, auto_created=True)
#     set_number = models.IntegerField(null=True, blank=True)
#     product_description = models.TextField(blank=True, null=True)
#     # all_apis
#     ean = models.CharField(null=True, blank=True,
#                            max_length=255, verbose_name="ean_number")
#     advert_title = models.CharField(max_length=200)
#     advert_description = models.TextField()

#     # otomoto
#     is_otomoto_advert_created = models.BooleanField(
#         ("Otomoto_advert_created"), default=False)
#     is_otomoto_advert_activated = models.BooleanField(
#         ("Otomoto_advert_activated"), default=False)
    

#     # olx
#     is_olx = models.BooleanField(("Olx"), default=False)
#     is_olx_active = models.BooleanField(("Olx_Advert_Active"), default=False)
#     olx_advert_id = models.PositiveIntegerField(null=True, blank=True)
#     olx_response = models.TextField(null=True, blank=True)
#     olx_active_advert_response = models.TextField(null=True, blank=True)
#     additional_text = models.TextField(max_length=255, null=True, blank=True)
#     olx_advert_status = models.CharField(max_length=50, null=True, blank=True)
#     # allegro
#     is_allegro = models.BooleanField(("Allegro"), default=False)
#     is_allegro_active = models.BooleanField(
#         ("Allegro_Advert_Active"), default=False)
#     allegro_advert_id = models.CharField(max_length=255, null=True, blank=True)
#     allegro_status = models.CharField(
#         max_length=800, null=True, blank=True, verbose_name="Allegro response")
#     allegro_api_respose = models.TextField(
#         max_length=1000, null=True, blank=True)
#     product_listing_status = models.CharField(
#         max_length=20, choices=ProductStatusChoice.choices, default=ProductStatusChoice.NEW)
#     # merchant center
#     is_merchant_center = models.BooleanField(
#         ("Google Merchant"), default=False)
#     image_update_status = models.BooleanField(default=False)
#     # warehouse
#     warehouse = models.ForeignKey(
#         Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
#     rack = models.ForeignKey(
#         Rack, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
#     row = models.ForeignKey(Row, on_delete=models.SET_NULL,
#                             null=True, blank=True, related_name='products')
#     staple = models.ForeignKey(
#         Staple, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
#     sold_at = models.DateTimeField(
#         null=True, blank=True, verbose_name="Date Sold"
#     )
#     on_sale_at = models.DateTimeField(
#         null=True, blank=True, verbose_name="Date On Sale"
#     )
    
    
#     def save(self, *args, **kwargs):
                         

#         super().save(*args, **kwargs)
    
    
    
#     def change_status(self, new_status, *, user=None):
#         print("--------------TRIGGER change status function-----------")
#         old_status = self.status
#         print("******************old_status:", old_status)
#         self.status = new_status
#         print("*******************new_status:", new_status)

#         update_fields = ["status"]

#         if new_status == self.StatusChoices.ON_SALE and not self.on_sale_at:
#             self.on_sale_at = timezone.now()
#             update_fields.append("on_sale_at")

#         if new_status == self.StatusChoices.SOLD and not self.sold_at:
#             self.sold_at = timezone.now()
#             update_fields.append("sold_at")
#             print(f"-------------Setting sold_at for product {self.id} to {self.sold_at}")

#         self.save(update_fields=update_fields)
        
#         if old_status != new_status and new_status == self.StatusChoices.SOLD:
#             try:
#                 self.post_sold_actions(
#                     print("Detected status change to SOLD, triggering post_sold_actions..."),
#                     old_status=old_status,
#                     new_status=new_status,
#                     user=user,
#                 )
#             except Exception as e:
#                 # Log the error, but do not raise
#                 print(f"Failed to trigger pos_sold_actions: {e}")

#         return old_status, new_status
            
    
#     def post_sold_actions(self,old_status, new_status, user=None):
#         #Should be named post_sold_actions
#         print(f"---------------Post_Sold_actions_triggered--------------")
        

#         if old_status == new_status:
#             return
        
#         if new_status != self.StatusChoices.SOLD:
#             return
        
#         # from otomoto.client import OtomotoClient
#         from otomoto.client.otomoto_client import OtomotoClient
#         from otomoto.models import OtoMotoAdvertData
#         from otomoto.models import OtomotoAuthData

#         try:
#             otomoto_data = self.otomoto_data
#         except OtoMotoAdvertData.DoesNotExist:
#             # No external ad exists → nothing to deactivate
#             return

#         if not otomoto_data.otomoto_advert_id:
#             # Record exists but no advert ID
#             return
#         ##############################
#         # if self.pair:
#         #     self.pair.on_product_sold(self)
#         ###############################

        
#         auth_data = OtomotoAuthData.objects.first()  # albo .get(active=True)
#         if not auth_data:
#             return  # lub raise Exception
#         print(f"---------------Auth data found--------------")

#         client = OtomotoClient(auth_data)
#         print(f"---------------Otomoto client created--------------")
#         token = client.get_access_token()
#         print(f"---------------Access token obtained--------------")

        
#         response = client.deactivate_otomoto_advert(
#             otomoto_advert_id=otomoto_data.otomoto_advert_id,
#             access_token=token
# )
        
#         if response.status_code == 204:
#             self.is_otomoto_advert_activated = False
#             self.save(update_fields=["is_otomoto_advert_activated"])