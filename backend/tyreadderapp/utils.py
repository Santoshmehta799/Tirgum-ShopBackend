from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

from tyreadderapp.models import Pair

def delete_old_unpaired_pairs():
    cutoff_time = timezone.now() - timedelta(minutes=30)
    print(f"[Cleanup] Running at: {timezone.now()} | Deleting pairs older than: {cutoff_time}")
    
    pairs_to_delete = Pair.objects.annotate(
        product_count=Count('product')
    ).filter(
        product_count=1,
        pair_listing_status=Pair.PairStatusChoice.LISTED,
        created_at__lt=cutoff_time
    )

    for pair in pairs_to_delete:
        print(f"[Cleanup] Deleting pair: {pair.pk} | Name: {pair.name} | Created: {pair.created_at}")

    count, _ = pairs_to_delete.delete()
    print(f"[Cleanup] Deleted {count} old pairs with only 1 product.")