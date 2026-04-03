import uuid
from django.db import models
from tyreadderapp.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # session_id = models.TextField(null=True, blank=True)  # For guest users
    date_created = models.DateTimeField(auto_now_add=True)
    wishlist_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return f"Wishlist {self.wishlist_id} - User: {self.user}"

    def total_items(self):
        return self.items.count()


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} in Wishlist {self.wishlist.wishlist_id}"
