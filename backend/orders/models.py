import uuid
from django.db import models
from django.db.models import JSONField
from libs.payu import PayU, process_order
from django.utils.dateparse import parse_date
from django.contrib.auth import get_user_model

User = get_user_model()
payu = PayU()

import logging

logger = logging.getLogger(__name__)



class OrderInvoice(models.Model):
    invoice_id = models.CharField(max_length=50, blank=True, null=True)
    issue_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    invoice_path = models.CharField(max_length=250, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice Id: {self.invoice_id} issue date: {self.issue_date} Created At: {self.created_at}"


class Order(models.Model):
    PAYMENT_STATUS = (
        ("paid", "Paid"), # Payment has been accepted. PayU will pay out the funds shortly. 
        ("pending", "Pending"), # Payment is currently being processed.
        ("processing", "Processing"), # PayU is currently waiting for the merchant system to receive (capture) the payment. This status is set if auto-receive is disabled on the merchant system.
        ("cancelled", "Cancelled"), # Payment has been cancelled and the buyer has not been charged (no money was taken from buyer's account).
    )

    ORDER_STATUS = (
        ("paid", "Paid"),
        ("pending", "Pending"), 
        ("fulfilled", "Fulfilled"), 
        ("cancelled", "Cancelled"),
    )
    cart = models.ForeignKey('cart.Cart', on_delete=models.CASCADE, null=True, blank=True)
    order_id = models.CharField(max_length=50, blank=True, null=True)
    ext_order_id = models.CharField(max_length=50, blank=True, null=True)

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_id = models.TextField(null=True, blank=True)
    invoice = models.ForeignKey('OrderInvoice', on_delete=models.SET_NULL, blank=True, null=True)
    order_status = models.CharField(choices=ORDER_STATUS, max_length=50, blank=True, null=True, default="pending")
    payment_status = models.CharField(choices=PAYMENT_STATUS, max_length=50, blank=True, null=True, default="pending")

    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_email = models.EmailField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=50, blank=True, null=True)

    total_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    shipping_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    tax_fee = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    
    nip = models.CharField(max_length=10, null=True, blank=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    company_street = models.CharField(max_length=555, null=True, blank=True)
    company_building = models.CharField(max_length=555, null=True, blank=True)
    company_apartment = models.CharField(max_length=555, null=True, blank=True)
    company_zip_code  = models.CharField(max_length=555, null=True, blank=True)
    company_city = models.CharField(max_length=555, null=True, blank=True)


    delivery_street = models.CharField(max_length=555, null=True, blank=True)
    delivery_building = models.CharField(max_length=555, null=True, blank=True)
    delivery_apartment = models.CharField(max_length=555, null=True, blank=True)
    delivery_zip_code = models.CharField(max_length=555, null=True, blank=True)
    delivery_city = models.CharField(max_length=555, null=True, blank=True)
    delivery_phone = models.CharField(max_length=14, null=True, blank=True)
    
    
    
    # company_address = models.CharField(max_length=555, null=True, blank=True)
    # company_delivery = models.CharField(max_length=555, null=True, blank=True)

    # pallet_number = models.PositiveIntegerField(null=True, blank=True)
    pallet_type = JSONField(null=True, blank=True)
    pallet_type_error = JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.order_id} by {self.customer_name if self.customer_name else 'Unknown'}"

    def create_order(self, cart, client_ip):
        if self.total_amount is not None and self.total_amount != 0:
            total_amount = int(self.total_amount)
            order = {
                "customerIp": "127.0.0.1",
                "totalAmount": total_amount,
                "description": "THIS IS DESCRIPTION",
                "email": self.customer_email,
                "phone": self.customer_phone,
                "firstName": self.customer_name.split(' ')[0],
                "lastName": self.customer_name.split(' ')[1] if len(
                    self.customer_name.split(' ')) > 1 else self.customer_name,

                # Products from cart items
                "products": [
                    {
                        "name": str(item.product.brand),
                        "unitPrice": int(item.net_price),
                        "quantity": item.quantity
                    } for item in cart.items.all()
                ],
                "extOrderId":  uuid.uuid1().hex,
            }
            print("ORDER IN MODELS ::> ",order)
            response = process_order(order,client_ip)
            if response.status_code == 302:
                print("I AM HERE TO SAVE",response.json())
                response_data = response.json()  
                self.order_id = response_data.get('orderId')
                self.ext_order_id = response_data.get('extOrderId')
                self.save()
                return True, response_data
        return False


    def cancel_order(self):
        resp = payu.cancel_order(self.order_id)
        if resp.status_code == 200:
            self.order_status = 'cancelled'
            self.save()
            return True
        return False

    def refund_order(self):
        resp = payu.refund_order(self.order_id)
        if resp.status_code == 200:
            self.order_status = "refunded"
            self.save()
            return True
        return False

    #def confirm_payment_status(self):
       # resp = payu.check_order_status(self.order_id)
       # return resp.status_code == 200 and resp.json().get("status") == "COMPLETED"
        
    def confirm_payment_status(self):
        try:
            resp = payu.check_order_status(self.order_id)
            logger.info(f"[Order:{self.pk}] PayU check_order_status response: status_code={resp.status_code}, body={resp.text}")
    
            data = resp.json()
            orders = data.get("orders", [])
            if orders:
                status = orders[0].get("status")
                logger.info(f"[Order:{self.pk}] Payment status from PayU API: {status}")
                return resp.status_code == 200 and status == "COMPLETED"
            else:
                logger.warning(f"[Order:{self.pk}] No orders found in PayU response")
                return False
        except Exception as e:
            logger.error(f"[Order:{self.pk}] Error in confirm_payment_status: {str(e)}", exc_info=True)
            return False
        
    
    def handle_payment_success(self, skip_api_check=True):
        logger.info(f"[Order:{self.pk}] handle_payment_success called")
        try:
            # Skip payment API check for testing
            if skip_api_check:
                logger.info(f"[Order:{self.pk}] Skipping payment confirmation check (test mode)")
                
                cart = self.cart
                if cart:
                    logger.info(f"[Order:{self.pk}] Clearing cart {cart.pk} (test mode)")
                    cart.items.all().delete()
                    #cart.delete()
                
                self.payment_status = "paid"
                self.order_status = "paid"
                self.save()
                logger.info(f"[Order:{self.pk}] Order status updated to PAID (test mode)")
                return True
        except Exception as e:
            logger.error(f"[Order:{self.pk}] Error in handle_payment_success: {str(e)}", exc_info=True)
        return False


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('tyreadderapp.Product', on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(default=0.00, max_digits=8, decimal_places=2)
    total_price = models.DecimalField(default=0.00, max_digits=8, decimal_places=2)
    discount = models.DecimalField(default=0.00, max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.product.brand} ({self.quantity})"


class OrderPayment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payout_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def process_payment(self):
        payout = {
            "amount": float(self.amount),
            "currencyCode": "PLN",
            "description": f"Payment for Order {self.order.order_id}",
            "extPayoutId": str(self.id),

        }
        resp = payu.create_payout(payout, {"name": self.order.customer_name})
        if resp.status_code == 200:
            print('enter 200 respnse data in it.')
            self.order.payment_status = 'paid'
            self.payout_id = resp.json().get('payout', {}).get('payoutId')
            self.order.save()
            return True
        print('enter else conditions...')
        return False

    def get_payout_details(self):
        resp = payu.retrieve_payout(self.payout_id)
        return resp.json()

    def __str__(self):
        return f"Payment for Order {self.order.order_id}"
