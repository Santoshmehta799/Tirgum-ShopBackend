from django.db.models.signals import pre_save,post_save
from django.dispatch import receiver
from tyreadderapp.models import Product, Pair
# from otomoto.client
from otomoto.client.otomoto_client import OtomotoClient  
from django.utils import timezone
# from otomoto.utils import create_otomoto_pair_advert

    
    

# @receiver(post_save, sender=Product)
# def create_otomoto_advert(sender, instance: Product, created, **kwargs):
#     if not created:
#         # Only run for newly created products
#         return

#     if instance.is_otomoto_advert_created:
#         return  # Already created, just in case

#     otomoto_client = OtomotoClient()

#     try:
#         otomoto_client.create_and_save_advert(instance)
#         # Mark as created
#         instance.is_otomoto_advert_created = True
#         # Use update_fields to avoid recursion
#         instance.save(update_fields=["is_otomoto_advert_created"])
#     except Exception as e:
#         # Optional: log the error instead of breaking
#         print(f"Error creating otomoto advert: {e}")
        
        


# @receiver(post_save, sender=Pair)
# def create_otomoto_pair_advertisement(sender, instance: Pair, created, **kwargs):
#     if not created:
#         # Only run for newly created products
#         return

#     if instance.is_otomoto_pair_advert_created:
#         return  # Already created, just in case

#     otomoto_client = OtomotoClient()

#     try:
#         success = otomoto_client.create_and_save_pair_advert(instance)
#         if success:
#             instance.is_otomoto_pair_advert_created = True
#             instance.save(update_fields=["is_otomoto_pair_advert_created"])
#             print("Otomoto pair advert created successfully.")
#     except Exception as e:
#         # Optional: log the error instead of breaking
#         print(f"Error creating otomoto advert: {e}")



from django.db import transaction

# @receiver(post_save, sender=Pair)
# def create_otomoto_pair_advertisement(sender, instance, created, **kwargs):
    
#     if not created:
#         return
    
#     if instance.is_otomoto_pair_advert_created:
#         return

#     def create_advert():
#         otomoto_client = OtomotoClient()
#         success = otomoto_client.create_and_save_pair_advert(instance)

#         if success:
#             Pair.objects.filter(pk=instance.pk).update(
#                 is_otomoto_pair_advert_created=True
#             )
#             print("Otomoto pair advert created successfully.")
#         else:
#             print("Failed to create Otomoto pair advert.")

#     transaction.on_commit(create_advert)

# @receiver(post_save, sender=Pair)
# def create_otomoto_pair_advert_signal(sender, instance, created, **kwargs):
#     create_otomoto_pair_advert(instance)





# @receiver(pre_save, sender=Product)
# def store_old_activation_value(sender, instance, **kwargs):
#     if instance.pk:
#         old_value = Product.objects.filter(pk=instance.pk).values_list(
#             "is_otomoto_advert_activated", flat=True
#         ).first()
#     else:
#         old_value = None
#     instance._old_activation_value = old_value
    











    
    





