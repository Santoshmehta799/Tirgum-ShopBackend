from django.contrib import admin
from django.contrib.admin import TabularInline
from cart.models import CartItem, Cart
from tyreadderapp.models import Product, Brand, Tread, Size
from users.models import User
# Register your models here.


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_cart_id', 'product_id')
    def get_cart_id(self, obj):
        return obj.cart.cart_id
    get_cart_id.short_description = 'Cart ID'

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart_id', 'session_id', 'user', 'total_price')
    # list_filter = ('payment_status', 'order_status')
    search_fields = ('cart_id', 'user__username')
    inlines = [CartItemInline]


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
