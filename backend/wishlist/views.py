from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import Wishlist, WishlistItem
from tyreadderapp.models import Product

def add_to_wishlist(request, product_id):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "You must be logged in to use the wishlist!"}, status=403)
    
    wishlist, created = Wishlist.objects.get_or_create(user=user)
    product = get_object_or_404(Product, id=product_id)

    # Add the product to the wishlist
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    
    return JsonResponse({"message": "Product added to wishlist!"})


def remove_from_wishlist(request, item_id):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "You must be logged in to use the wishlist!"}, status=403)
    
    item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=user)
    item.delete()
    return JsonResponse({"message": "Product removed from wishlist!"})


def view_wishlist(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "You must be logged in to use the wishlist!"}, status=403)
    
    wishlist = Wishlist.objects.filter(user=user).first()
    items = wishlist.items.all() if wishlist else []

    return JsonResponse({
        "wishlist_id": wishlist.wishlist_id if wishlist else None,
        "items": [{"id": item.id, "product": item.product.id} for item in items],
    })

