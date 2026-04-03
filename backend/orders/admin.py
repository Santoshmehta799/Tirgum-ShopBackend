from django.contrib import admin

from django.contrib import admin
from .models import Order, OrderInvoice, OrderPayment, OrderItem

class OrderInvoiceInline(admin.TabularInline):
    model = OrderInvoice
    extra = 0  # No extra blank forms by default

class OrderPaymentInline(admin.TabularInline):
    model = OrderPayment
    extra = 0

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer_name', 'order_status', 'payment_status', 'total_amount', 'created_at')
    inlines = [OrderPaymentInline, OrderItemInline]
    search_fields = ('order_id', 'customer_name', 'customer_email')
    list_filter = ('order_status', 'payment_status', 'created_at')

# Registering other models independently
@admin.register(OrderInvoice)
class OrderInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'status', 'issue_date', 'created_at')
    search_fields = ('invoice_id', 'status')
    list_filter = ('status', 'issue_date')

@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_date', 'payout_id', 'created_at')
    search_fields = ('payout_id', 'order__order_id')
    list_filter = ('payment_date',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'total_price')
    search_fields = ('order__order_id', 'product__brand')
    list_filter = ('product',)



