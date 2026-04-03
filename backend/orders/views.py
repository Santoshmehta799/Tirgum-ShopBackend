# views.py

import json
import uuid
import logging
import datetime
import requests
from decimal import Decimal
from cart.models import Cart
from django.contrib import messages
from backend.utils import send_order_email
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Order, OrderItem, OrderPayment
from django.shortcuts import get_object_or_404, redirect, render
from cart.serializers import CartSerializer, CreateCartSerializer, CartSerializers
from .serializers import OrderSerializer, OrderPaymentSerializer, OrderItemSerializer

logger = logging.getLogger(__name__)

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, uuid.UUID):
        return str(obj)  # Convert UUID to string
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()  # Convert datetime to ISO 8601 string
    raise TypeError(f"Type {type(obj)} not serializable")

@api_view(['POST'])
def create_order_from_cart(request, cart_id):
    client_ip = request.META.get('REMOTE_ADDR')
    print("=====>", client_ip)
    print("=== here in funct", cart_id)
    cart = get_object_or_404(Cart, cart_id=cart_id)
    print("=== here in fun", cart)
    

    pallet_type = None
    pallet_type_error = None

    try:
        serializer = CartSerializers(cart, context={'request': request})
        data = dict(serializer.data)  # Convert to dict format to ensure compatibility

        # Convert decimals, UUIDs, and datetime objects in data to appropriate types using custom function
        pallet_type  = json.loads(json.dumps(data, default=custom_serializer))

    except Exception as e:
        pallet_type_error = {"error": str(e)}

    if cart.self_pickup:
        total_amount_value = cart.tyres_gross_value or 0
    else:
        total_amount_value = cart.tyres_and_transport_gross_value or 0
    
    order = Order.objects.create(
        user=cart.user if cart.user else None,
        session_id=cart.session_id,
        customer_name=cart.full_name,
        customer_email=cart.email,
        customer_phone=cart.mobile,
        total_amount=total_amount_value,
        shipping_amount=cart.shipping_amount,
        tax_fee=cart.tax_fee,
        order_status='pending',
        payment_status='pending',
        
        nip=cart.nip,
        company_name=cart.company_name,
        
        company_street=cart.company_street,
        company_building=cart.company_street,
        company_apartment=cart.company_apartment,
        company_zip_code=cart.company_zip_code,
        company_city=cart.company_city,    

        delivery_street=cart.delivery_street,
        delivery_building=cart.delivery_building,
        delivery_apartment=cart.delivery_apartment,
        delivery_zip_code=cart.delivery_zip_code,
        delivery_city=cart.delivery_city,        
            
        # company_address=cart.company_address,
        # company_delivery=cart.company_delivery,
        pallet_type=pallet_type,
        pallet_type_error=pallet_type_error
        
    )
    success, response_data = order.create_order(cart, client_ip)
    if success:
        payemnt_link = response_data.get('redirectUri')
        send_order_email(cart.email, 'Dziękujemy za złożenie zamówienia w Tirgum', 
            f'Witaj {cart.full_name}, <br>Id zamówienia to: <b>#00-{order.pk}</b> <br> Payment Order Id: <b>{order.order_id}</b> <br> Prosimy o dokończenie płatności:<br><hr>Kliknij w poniższy link: {payemnt_link}.')
        print("=== here in if")
        # Create order items
        for item in cart.items.all():
            print("ITEM", item)
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.net_price,
                total_price=item.total_price,
            )
        # Clear the cart
        # cart.items.all().delete()
        # cart.delete()

        order.cart = cart
        order.save()

        # Return the redirectUri along with the order data
        return Response({
            "order": OrderSerializer(order).data,
            "response": response_data
        })
    else:
        print("Please check the payload for order serializer")
        return Response({"error": "Order creation failed"}, status=400)



@api_view(['POST'])
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    print('order id ->', order)
    # Make payment confirmation
    order_payment, created = OrderPayment.objects.get_or_create(
        order=order,
        amount=float(order.total_amount),
    )
    print('order_payment ->', order_payment)
    if order_payment.process_payment():
        # Update order status
        order.payment_status = "paid"
        order.order_status = "confirmed"
        order.save()

        # ✅ Now clear cart after payment success
        if order.cart:
            order.cart.items.all().delete()
            order.cart.delete()

        return Response(OrderPaymentSerializer(order).data)

    return Response({"error": "Payment creation failed"}, status=400)


# @api_view(['POST'])
# def order_confirmation(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     print('order id ->', order)
#     # Make payment confirmation
#     order_payment, created = OrderPayment.objects.get_or_create(
#         order=order,
#         amount=float(order.total_amount),
#     )
#     print('order_payment ->', order_payment)
#     if order_payment.process_payment():
#         return Response(OrderPaymentSerializer(order).data)
#     return Response({"error": "Payment creation failed"}, status=400)

def get_access_token():
    client_id = '487364'
    client_secret = '37aadb01ff54cb426aae43262c4a5b0f'
    url = 'https://secure.snd.payu.com/pl/standard/user/oauth/authorize'

    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, data=payload, headers=headers)
    return response.json().get('access_token') if response.status_code == 200 else None

def payu_refund_form(request, order_id):
    return render(request, 'tyreadderapp/payu_refund_form.html', {'order_id': order_id})

def process_refund(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        description = request.POST.get('description', 'Customer requested refund')
        refund_amount = int(float(request.POST.get('amount')) * 100)  # PLN to grosze

        logger.info(f"Received refund request: order_id={order_id}, amount={refund_amount}, description={description}")

        token = get_access_token()
        if not token:
            logger.error("Access token not received.")
            messages.error(request, 'Failed to get access token.')
            return redirect('orders:payu_refund_form', order_id=order_id)

        url = f'https://secure.snd.payu.com/api/v2_1/orders/{order_id}/refunds'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        data = {
            "refund": {
                "description": description,
                "amount": refund_amount
            }
        }

        logger.debug(f"Sending refund request to PayU API: URL={url}, Headers={headers}, Payload={data}")
        response = requests.post(url, headers=headers, data=json.dumps(data))

        logger.info(f"PayU response status: {response.status_code}")
        logger.debug(f"PayU response body: {response.text}")

        if response.status_code == 200:
            messages.success(request, 'Refund successful.')
        else:
            error_code = response.json().get('status', {}).get('statusCode')
            logger.error(f"Refund failed. Error code: {error_code}")
            messages.error(request, f"Refund failed: {error_code}")

        return redirect('tyreadderapp:payu_payment_dashboard')
