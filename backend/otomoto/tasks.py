# # otomoto/tasks.py
# from celery import shared_task
# from otomoto.client import OtomotoClient
# from otomoto.models import OtoMotoAdvertData, OtomotoAuthData
# from tyreadderapp.models import Product

# @shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 5})
# def deactivate_otomoto_advert_task(self, product_id):
#     product = Product.objects.get(id=product_id)

#     try:
#         otomoto_data = product.otomoto_data
#     except OtoMotoAdvertData.DoesNotExist:
#         return

#     if not otomoto_data.otomoto_advert_id:
#         return

#     auth_data = OtomotoAuthData.objects.first()
#     if not auth_data:
#         raise Exception("Missing Otomoto auth data")

#     client = OtomotoClient(auth_data)
#     token = client.get_access_token()

#     response = client.deactivate_otomoto_advert(
#         otomoto_advert_id=otomoto_data.otomoto_advert_id,
#         access_token=token
#     )

#     if response.status_code == 204:
#         product.is_otomoto_advert_activated = False
#         product.save(update_fields=["is_otomoto_advert_activated"])
#     else:
#         raise Exception(f"Otomoto returned {response.status_code}")
