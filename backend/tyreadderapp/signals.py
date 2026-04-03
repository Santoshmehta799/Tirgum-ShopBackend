from django.db import transaction
import requests
from otomoto.client.otomoto_client import OtomotoClient
from otomoto.models import OtomotoAuthData
from django.dispatch import receiver
from django.db.models.signals import post_save
import logging

from .models import Product, PairAdvertImageProcessor
from olx.client import OlxClient
from django.utils import timezone
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_delete
from tyreadderapp.models import Image, Product, Pair
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_delete, post_save, pre_save
from .predictor import predict_net_price
from decimal import Decimal
from django.db import models

olx_client = OlxClient()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Image)
def update_image_record(sender, instance, **kwargs):
    """Force update the image record when saved"""
    if instance.image:
        # This forces the database to recognize the change
        Image.objects.filter(pk=instance.pk).update(
            updated_at=timezone.now(),
            force_update=not instance.force_update
        )


@receiver(pre_delete, sender=Image)
def image_file_delete(sender, instance, **kwargs):
    """
    Signal handler to delete physical image file when an Image model instance is deleted.

    This signal ensures that the actual image file is removed from storage when 
    the corresponding Image model record is deleted, preventing orphaned files 
    and saving disk space.

    Note:
        - Triggered before the Image model instance is permanently deleted
        - Removes the physical file associated with the image field
        - Helps maintain clean file storage by removing unused image files
    """
    if instance.image:
        instance.image.delete(save=False)

# ======================PRE-PRODUCT=======================================================================================


@receiver(pre_save, sender=Product)
def store_old_pair(sender, instance, **kwargs):
    """
    Signal handler to store the original pair before a Product is updated.

    This signal captures the existing pair associated with a Product 
    before any modifications are made, allowing for comparison or 
    tracking of changes.

    Note:
        - Only attempts to store pair for existing Product instances
        - Uses a temporary attribute to avoid persistent storage
        - Provides a mechanism for tracking pair changes during save
    """
    if instance.id:
        try:
            old_instance = Product.objects.get(id=instance.id)
            instance._old_pair = old_instance.pair
        except Product.DoesNotExist:
            instance._old_pair = None
            

@receiver(post_save, sender=Product)
def generate_pair_image(sender, instance, created, **kwargs):
    pair = instance.pair
    if not pair:
        # No pair assigned, nothing to do
        return
    if  pair.products.count() > 1:
        try:
            processor = PairAdvertImageProcessor(pair)
            processor.generate_main_pair_image()
            print(f"***************Generated pair image for Pair(id={pair.id})")
        except Exception as e:
            print(f"***************Error generating pair image for Pair(id={pair.id}): {e}")


# @receiver(pre_save, sender=Product)
# def remove_olx_advert_when_sold(sender, instance, **kwargs):
#     """
#     Remove OLX advert when product status is changed to 'SOLD'
#     """
#     try:
#         if instance.pk:
#             old_instance = Product.objects.get(pk=instance.pk)
#             logger.debug(
#                 f"remove_olx_advert_when_sold => [OLX] Checking product {instance.pk}: old_status={old_instance.status}, new_status={instance.status}")

#             if old_instance.status != Product.StatusChoices.SOLD and instance.status == Product.StatusChoices.SOLD:
#                 logger.info(
#                     f"[OLX] Product {instance.pk} marked as SOLD, starting OLX deactivation process.")

#                 if instance.is_olx:
#                     logger.debug(
#                         f"[OLX] Product {instance.pk} has is_olx=True")
#                 else:
#                     logger.warning(
#                         f"[OLX] Product {instance.pk} is not marked as OLX, skipping.")

#                 if instance.olx_advert_id is not None:
#                     logger.debug(
#                         f"[OLX] Product {instance.pk} has OLX advert id={instance.olx_advert_id}")
#                 else:
#                     logger.warning(
#                         f"[OLX] Product {instance.pk} has no OLX advert_id, skipping.")

#                 if instance.is_olx and instance.olx_advert_id is not None:
#                     logger.debug(
#                         f"[OLX] Trying to get access token for Product {instance.pk}")
#                     access_token = olx_client.get_access_token()

#                     if access_token:
#                         logger.debug(
#                             f"[OLX] Got access token for Product {instance.pk}, calling deactivate_advert...")
#                         try:
#                             advert_deactivate = olx_client.deactivate_advert(
#                                 instance.olx_advert_id,
#                                 access_token
#                             )
#                             logger.debug(
#                                 f"[OLX] Deactivate response code: {advert_deactivate.status_code}")

#                             if advert_deactivate.status_code == 204:
#                                 logger.info(
#                                     f"[OLX] Product {instance.pk} successfully deactivated on OLX.")
#                                 olx_client.remove_advert(
#                                     instance, access_token)
#                             else:
#                                 logger.warning(
#                                     f"[OLX] Failed to deactivate advert for Product {instance.pk}, "
#                                     f"status_code={advert_deactivate.status_code}, response={advert_deactivate.text}"
#                                 )
#                         except Exception as olx_error:
#                             logger.exception(
#                                 f"[OLX] Exception while deactivating advert for Product {instance.pk}: {olx_error}")
#                     else:
#                         logger.error(
#                             f"[OLX] Could not get access token for Product {instance.pk}, skipping deactivation.")
#     except Exception as e:
#         logger.exception(
#             f"[OLX] Unexpected error in OLX advert removal for SOLD product {getattr(instance, 'pk', None)}: {e}")

# =====================POST-PRODUCT==============================================================================================

# @receiver(post_save, sender=Product)
# def delete_product_images(sender, instance, **kwargs):
#     """
#     Signal handler to delete all images associated with a Product when it is marked as SOLD.

#     This signal automatically removes all Image instances linked to a Product
#     when the Product's status changes to SOLD, helping to clean up unused images
#     and maintain database integrity.

#     Behavior:
#         - Checks if the Product status is set to SOLD
#         - Deletes all Image instances associated with this Product
#         - Useful for automating image cleanup after a product is sold

#     Note:
#         - Only triggers when the Product is saved
#         - Does not delete the Product itself, only its associated images
#     """
#     if instance.status==Product.StatusChoices.SOLD:
#         Image.objects.filter(product=instance).delete()


@receiver(post_save, sender=Product)
def prepend_id_to_description(sender, instance, created, **kwargs):
    """
    Signal handler to automatically prepend a Product's ID to its description 
    when first created.

    This signal modifies the advert description to include the Product's unique 
    ID, ensuring that each advertisement has a clear identifier in its description.

    Behavior:
        - Only triggers when a new Product is created
        - Prepends a formatted message including the Product's ID to the description
        - Automatically saves the modified description
    """
    if created and instance.id:
        instance.advert_description = f"Uwaga ! Dzwoniąc podaj nam poniższy numer ID opony.\n\nID opony: {instance.id}\n\n" + \
            instance.advert_description
        instance.save()


# @receiver(post_save, sender=Product)
# def remove_sold_product_from_pair(sender, instance, **kwargs):
#     try:
#         # Only run if status is SOLD and product has a pair
#         if instance.status == Product.StatusChoices.SOLD and instance.pair:
#             pair = instance.pair

#             # Get all products in this pair except SOLD ones
#             products_in_pair = Product.objects.filter(
#                 pair=pair).exclude(status=Product.StatusChoices.SOLD)

#             if products_in_pair.exists():
#                 pair.pair_description = pair.get_pair_advert_description()
#                 pair.pair_title = pair.get_pair_advert_title()
#                 pair.pair_price = pair.get_pair_advert_price()
#                 pair.process_and_save_pair_image()
#                 pair.save()
#             else:
#                 # If no products left, delete the pair
#                 pair.delete()
#     except Exception as e:
#         print(f"Error in remove_sold_product_from_pair: {e}")


@receiver(post_save, sender=Product)
def update_pair_title_description(sender, instance, created, **kwargs):
    """
    Signal handler to update Pair details after Product is saved.

    Synchronizes Pair information with the latest Product data, 
    including title, description, price, and images.

    Note:
        - Uses methods of the Pair model to generate updated information
        - Saves all identified pairs with new details
        - Provides comprehensive pair update mechanism
    """
    try:
        current_pair = instance.pair if hasattr(
            instance, 'pair_id') and instance.pair_id else None
        old_pair = getattr(instance, '_old_pair',
                           None) if not created else None
        pairs_to_update = set(filter(None, [current_pair, old_pair]))

        for pair in pairs_to_update:
            pair.pair_title = pair.get_pair_advert_title()
            pair.pair_description = pair.get_pair_advert_description()
            pair.pair_price = pair.get_pair_advert_price()
            pair.process_and_save_pair_image()
            pair.save()
    except Exception as e:
        print(f"Error in update_pair_title_description: {str(e)}")


# @receiver(post_save, sender=Product)
# def update_pair_block_status(sender, instance, created, **kwargs):
#     """
#     Signal handler to manage Pair blocking status based on Product status.

#     Handles blocking and potential deletion of Pairs when Products 
#     are sold or reach specific conditions.

#     Args:
#         sender (Model): The model class sending the signal (Product)
#         instance (Product): The specific Product instance being saved
#         created (bool): Flag indicating if this is a new Product instance
#         **kwargs: Additional keyword arguments passed by the signal
#     """
#     if not instance.pair:
#         return
   
#     pair_instance = instance.pair
#     products = Product.objects.filter(pair=pair_instance)
#     quantity = products.count()
#     if quantity <= 1 and pair_instance.blocked_pair == True:
#         print(f"pair will be deleted {pair_instance.id} =={ quantity}")
#         # pair_instance.delete()
#     else:
#         pass


@receiver(post_save, sender=Product)
def add_ean(sender, instance, created, **kwargs):
    """
    Signal handler to automatically add EAN (European Article Number) to a Product.

    Generates and assigns an EAN to the Product during save, with safeguards 
    against recursive saving.

    Note:
        - Uses a flag to prevent infinite save loops
        - Assumes a method `get_ean()` exists on the Product model
        - Only assigns EAN if a value is generated
    """
    if not hasattr(instance, '_ean_handled'):  # Check if the flag is already set
        instance._ean_handled = True  # Set the flag to avoid recursion
        ean = instance.get_ean()
        if ean:
            instance.ean = ean  # Assuming the `ean` field exists in the `Product` model
            instance.save()


@receiver(post_save, sender=Product)
def check_old_pair_after_update(sender, instance, created, **kwargs):
    """
    After updating a Product, check if the old Pair (if changed) now has 1 Product.
    If so, delete the old Pair.
    """
    if not created:
        old_pair = getattr(instance, '_old_pair', None)

        # Safely get the new pair, handling the case where it might have been deleted
        try:
            new_pair = instance.pair
        except Pair.DoesNotExist:
            new_pair = None

        if old_pair != new_pair and old_pair:
            # Check if the old_pair still exists before calling the method
            try:
                # Refresh from database to make sure it still exists
                old_pair.refresh_from_db()
                old_pair.check_and_destroy_if_single_product()
            except Pair.DoesNotExist:
                # Old pair was already deleted, nothing to do
                logger.info(
                    f"Old pair {old_pair.id if hasattr(old_pair, 'id') else 'unknown'} was already deleted")
                pass


# @receiver(post_save, sender=Product)
# def delete_pair_if_only_one_active(sender, instance, **kwargs):
#     logger.info(
#         f"[delete_pair_if_only_one_active] Product ID: {instance.id}, status: {instance.status}")

#     # Check if status is SOLD and product has a pair
#     if instance.status == 'Sprzedane' and instance.pair:
#         try:
#             pair = instance.pair
#             logger.debug(
#                 f"Product {instance.id} belongs to Pair ID: {pair.id}")

#             # Check if pair still exists and has a valid ID
#             if not pair.id:
#                 logger.warning(
#                     f"Pair has no ID, skipping deletion logic for Product {instance.id}")
#                 return

#             # Count active tyres in this pair (excluding current sold product)
#             active_tyres = pair.product_set.exclude(
#                 id=instance.id
#             ).filter(
#                 status__in=['Do dodania', 'W sprzedaży']
#             ).count()

#             logger.debug(
#                 f"Active tyres in pair {pair.id} (excluding current product): {active_tyres}")

#             # If 1 or fewer active tyres remain, delete the pair
#             if active_tyres <= 1:
#                 logger.warning(
#                     f"Deleting Pair ID: {pair.id} because only {active_tyres} active tyre(s) remain."
#                 )
#                 try:
#                     # Store pair_id before deletion for logging
#                     pair_id = pair.id

#                     # Break the FK reference first for all products in this pair
#                     pair_products = pair.product_set.all()
#                     for product in pair_products:
#                         product.pair = None
#                         product.save(update_fields=['pair'])
#                         logger.debug(
#                             f"Product {product.id} detached from Pair {pair_id}")

#                     # Now delete the pair
#                     pair.delete()
#                     logger.info(f"Pair {pair_id} deleted successfully.")

#                 except Exception as e:
#                     logger.error(
#                         f"Error while detaching products or deleting Pair {pair.id}: {e}",
#                         exc_info=True
#                     )
#             else:
#                 logger.debug(
#                     f"Pair {pair.id} still has {active_tyres} active tyres, not deleting")

#         except Pair.DoesNotExist:
#             logger.error(
#                 f"Pair for Product ID: {instance.id} does not exist.", exc_info=True)
#         except Exception as e:
#             logger.error(
#                 f"Unexpected error in pair deletion logic for Product {instance.id}: {e}", exc_info=True)
#     else:
#         logger.debug(
#             f"No action taken for Product ID: {instance.id} (status: {instance.status}, has_pair: {bool(instance.pair)})")


@receiver(post_save, sender=Product)
def calculate_profit_on_save(sender, instance, **kwargs):
    if instance.net_price is not None:
        new_profit = instance.net_price - instance.supplier_price
    else:
        new_profit = 0

    # Only update if profit is different, to avoid infinite loop
    if instance.profit != new_profit:
        instance.profit = new_profit
        instance.save(update_fields=['profit'])


# ==================POST DELETE PRODUCT ========================================================================================

# @receiver(post_delete, sender=Product)
# def delete_pair_when_product_deleted(sender, instance, **kwargs):
#     """
#     Primary signal handler for deleting the associated pair when a Product is deleted.

#     This signal ensures that when a Product is permanently removed from the database, 
#     its corresponding Pair is also deleted, maintaining data integrity.

#     Args:
#         sender (Model): The model class sending the signal (Product)
#         instance (Product): The specific Product instance that was deleted
#         **kwargs: Additional keyword arguments passed by the signal
#     """
#     try:
#         pair = instance.pair
#         if pair:
#             pair.delete()
#     except ObjectDoesNotExist:
#         logger.info(f"No pair found for deleted product {instance.id}")
#     except Exception as e:
#         logger.error(f"Error deleting pair for product {instance.id}: {e}")


# @receiver(post_delete, sender=Product)
# def delete_pair_on_product_removal(sender, instance, **kwargs):
#     """
#     Secondary signal handler for OLX-specific pair deletion process.

#     This signal handles the removal of OLX adverts when a Product is deleted:
#     - Checks if the pair is an OLX advert
#     - Attempts to deactivate and remove the advert from OLX
#     - Ensures OLX-specific cleanup for pair deletion

#     Note:
#         - Attempts to deactivate and remove OLX advert if possible
#         - Logs any failures in OLX advert removal process
#         - Does not block pair deletion if OLX operations fail
#     """
#     try:
#         pair = instance.pair
#         if not pair:
#             return

#         if pair.pair_is_olx and pair.pair_olx_advert_id is not None:
#             try:
#                 access_token = olx_client.get_access_token()
#                 if not access_token:
#                     logger.warning(
#                         f"No access token available for OLX advert {pair.pair_olx_advert_id}")
#                     return

#                 advert_deactivate = olx_client.deactivate_advert(
#                     pair.pair_olx_advert_id, access_token)
#                 if advert_deactivate.status_code == 204:
#                     remove_pair = olx_client.remove_advert(pair, access_token)

#                     # Log if removal fails
#                     if remove_pair.status_code != 204:
#                         logger.warning(
#                             f"Failed to remove OLX advert {pair.pair_olx_advert_id}")
#                 else:
#                     logger.warning(
#                         f"Failed to deactivate OLX advert {pair.pair_olx_advert_id}")

#             except Exception as olx_error:
#                 logger.error(f"Error in OLX advert handling: {olx_error}")

#     except Exception as e:
#         logger.error(f"Unexpected error in OLX pair deletion signal: {e}")


# ==========================PRE DELETE PRODUCT=================================================================================

# @receiver(pre_delete, sender=Product)
# def delete_olx_advert(sender, instance, **kwargs):
#     """
#     Signal handler to remove OLX advert when a Product is being deleted.

#     Attempts to:
#     - Deactivate the OLX advert
#     - Remove the OLX advert from OLX

#     Logs detailed reasons for failures and successes for easier debugging.
#     """
#     olx_id = instance.olx_advert_id

#     try:
#         # Step 1: Check if this product is OLX-listed
#         if not instance.is_olx:
#             logger.info(
#                 f"[OLX Removal] Product {instance.id} is not marked as OLX. Skipping OLX removal.")
#             return

#         if olx_id is None:
#             logger.warning(
#                 f"[OLX Removal] Product {instance.id} is OLX but has no olx_advert_id. Skipping removal.")
#             return

#         logger.info(
#             f"[OLX Removal] Starting OLX advert removal for Product {instance.id} | OLX Advert ID: {olx_id}")

#         # Step 2: Get access token
#         access_token = olx_client.get_access_token()
#         if not access_token:
#             logger.error(
#                 f"[OLX Removal] No access token available. Cannot remove OLX advert {olx_id}.")
#             return

#         # Step 3: Deactivate advert
#         try:
#             logger.info(
#                 f"[OLX Removal] Attempting to deactivate OLX advert {olx_id}...")
#             advert_deactivate = olx_client.deactivate_advert(
#                 olx_id, access_token)

#             if advert_deactivate.status_code == 204:
#                 logger.info(
#                     f"[OLX Removal] OLX advert {olx_id} deactivated successfully.")

#                 # Step 4: Remove advert
#                 logger.info(
#                     f"[OLX Removal] Attempting to remove OLX advert {olx_id}...")
#                 remove_response = olx_client.remove_advert(
#                     instance, access_token)

#                 if remove_response.status_code == 204:
#                     logger.info(
#                         f"[OLX Removal] OLX advert {olx_id} removed successfully.")
#                 else:
#                     logger.warning(
#                         f"[OLX Removal] Failed to remove OLX advert {olx_id}. "
#                         f"Status Code: {remove_response.status_code} | Response: {remove_response.text}"
#                     )
#             else:
#                 logger.warning(
#                     f"[OLX Removal] Failed to deactivate OLX advert {olx_id}. "
#                     f"Status Code: {advert_deactivate.status_code} | Response: {advert_deactivate.text}"
#                 )

#         except Exception as olx_error:
#             logger.error(
#                 f"[OLX Removal] Exception occurred while handling OLX advert {olx_id}: {olx_error}")

#     except Exception as e:
#         logger.error(
#             f"[OLX Removal] Unexpected error during OLX advert removal for Product {instance.id}: {e}")


# @receiver(pre_save, sender=Product)
# def set_net_price(sender, instance, **kwargs):
#     print(f"[pre_save] wywołany, net_price przed: {instance.net_price!r}")

#     if instance.net_price is None:
#         try:
#             predicted = predict_net_price(instance)
#             instance.net_price = Decimal(str(predicted))
#             print(f"[pre_save] ustawiono predicted price: {predicted}")
#         except Exception as e:
#             print(f"[pre_save] błąd predykcji: {e}")





# products/signals.py

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Product


# @receiver(pre_save, sender=Product)
# def product_pre_save(sender, instance, **kwargs):
#     print( "================= product_pre_save triggered =================" )
#     """
#     Store previous status on instance before saving
#     """
#     if not instance.pk:
#         instance._previous_status = None
#         return

#     try:
#         previous = sender.objects.get(pk=instance.pk)
#         instance._previous_status = previous.status
#         print(f"PRE_SAVE: Stored previous status: {instance._previous_status}")
#     except sender.DoesNotExist:
#         instance._previous_status = None
#         print("PRE_SAVE: No previous instance found")


# @receiver(post_save, sender=Product)
# def product_post_save(sender, instance, created, **kwargs):
#     print( "================= product_post_save triggered =================" )
#     """
#     React to status change AFTER save
#     """
    

#     if (
#         instance._previous_status != Product.StatusChoices.SOLD
#         and instance.status == Product.StatusChoices.SOLD
        
#     ):
        
#         print("Hurra! Product sold")
        
#     else:
#         print("No status change to SOLD detected")


# @receiver(post_save, sender=Product)
# def product_saved(sender, instance, created, **kwargs):
#     if created:
#         print(f"---------------------New product created with status: {instance.status}")
#     else:
#         print(f"---------------------Existing product updated with status: {instance.status}")






