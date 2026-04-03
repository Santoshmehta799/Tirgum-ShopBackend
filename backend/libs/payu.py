import os
import uuid
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend import utils as backend_utils
from libs.models import PayUAuth
from datetime import datetime, timedelta 
from django.utils.timezone import now
from django.http import JsonResponse
import hashlib
import logging
from django.views.decorators.csrf import csrf_exempt


class PayU:
    def __init__(self):
        self.base_url = "https://secure.snd.payu.com"
        self.auth_url = f"{self.base_url}/pl/standard/user/oauth/authorize"
        self.client_id = os.getenv("PAYU_CLIENT_ID")
        self.client_secret = os.getenv("PAYU_CLIENT_SECRET")
        self.redirect_uri = os.getenv("PAYU_REDIRECT_URI")
        self.merchant_pos_id = os.getenv("PAYU_MERCHANT_POS_ID")
        # get or creat PayUAuth object and write those values to this class
        try:
            payu_auth = PayUAuth.objects.get_or_create()[0]
            self.access_token = payu_auth.access_token
            self.token_type = payu_auth.token_type
            self.expires_in = payu_auth.expires_in
            self.access_token_created_at = payu_auth.created_at
        except:
            self.access_token = ""
            self.token_type = ""
            self.expires_in = ""
            self.access_token_created_at = ""

    def get_access_token(self):
        print("I am again here ")
        """
        This function is used to get the access token from PayU
        Returns:
            access_token
        @see https://developers.payu.com/europe/docs/get-started/accept-payment/
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        # url_encode the data
        data = backend_utils.url_encode(data)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = backend_utils.send_request(self.auth_url, "POST", payload=data, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            self.access_token = response_data.get("access_token")
            self.token_type = response_data.get("token_type")
            
            # Convert expires_in seconds to datetime
            expires_in_seconds = response_data.get("expires_in")
            self.access_token_created_at = backend_utils.get_current_datetime()
            self.expires_in = self.access_token_created_at + timedelta(seconds=expires_in_seconds)
            
            self.write_to_db()
            return self.access_token
        return None

    def write_to_db(self):
        """
        This function is used to write the access token to the database
        """
        payu_auth = PayUAuth.objects.get_or_create()[0]
        payu_auth.access_token = self.access_token
        payu_auth.token_type = self.token_type
        payu_auth.expires_in = self.expires_in  
        payu_auth.created_at = self.access_token_created_at
        payu_auth.save()



    def validate_access_token(self):
        """
        Validates the access token by checking its expiry.
        Returns:
            str: The access token if valid, otherwise fetches and returns a new access token.
        """
        # Check if access_token is missing or expired
        if not self.access_token or not self.expires_in or self.expires_in <= now():
            print('validated Token ->',self.get_access_token())
            return self.get_access_token()
        print('validated Token ->', self.access_token)
        return self.access_token


    def get_object_as_dict(self):
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "created_at": self.access_token_created_at
        }

    def get_headers(self):
        """
        This function is used to get the headers
        Returns:
            headers
        """
        return {
            "Authorization": f"{self.token_type} {self.access_token}",
            "Content-Type": "application/json"
        }


    def process_order_final(self, order=None):
        """
        This function is used to process an order
        Args:
            order: Order object
        Returns:
            response from PayU or error message
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/orders"
        headers = self.get_headers()
        
        try:
            # Attempt to send the POST request
            response = requests.post(url, json=order, headers=headers, allow_redirects=False)
            logger.info("== process_order_final ==> %s %s", type(response), response)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            # Handle any exceptions from the request
            print(f"Error occurred while processing the order: {e} {response.text}")
            return str(e) 
        
        print(response)
        logger.info("== process_order_final response lof ==> %s %s", type(response), response)
        return response

    def prepare_order_payload(self, order=None):
        """
        This function is used to prepare the order payload
        Args:
            order: Order object
        Returns:
            order payload
        """
        order_payload = {
            "notifyUrl": "https://tirgumpanel.pl/api/libs/payu/notify/",
            "customerIp": order.get("customerIp"),
            "merchantPosId": self.merchant_pos_id,
            "description": order.get("description"),
            "currencyCode": "PLN",
            "totalAmount": str(round(float(order.get("totalAmount")) * 100)),
            "buyer": {
                "email": order.get("email"),
                "phone": order.get("phone"),
                "firstName": order.get("firstName"),
                "lastName": order.get("lastName"),
                "language": "pl"
            },
            "products": [
                {
                    "name": product.get("name"),
                    "unitPrice": product.get("unitPrice"),
                    "quantity": product.get("quantity"),
                } for product in order.get("products")
            ],
            "extOrderId": order.get("extOrderId"),
            "continueUrl": "https://shop.tirgum.pl/thankyou"
        }
        return order_payload

    def complete_order(self, order_id, order_amount):
        """
        This function is used to complete an order
        Args:
            order_id: Order ID
            order_amount: Order amount
        Returns:
            response from PayU
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/orders/{order_id}/captures"
        data = {
            "amount": order_amount,
        }
        headers = self.get_headers()
        response = backend_utils.send_request(url, "PUT", headers=headers, payload=data)
        return response

    def check_order_status(self, order_id):
        """
        This function is used to check the order status
        Args:
            order_id: Order ID
        Returns:
            response from PayU
        @see: https://developers.payu.com/europe/api/#tag/Order/operation/retrieve-an-order
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/orders/{order_id}"
        headers = self.get_headers()
        response = backend_utils.send_request(url, "GET", headers=headers)

        return response

    def retrieve_payment_methods(self):
        """
        This function is used to retrieve payment methods
        Returns:
            response from PayU
        @see https://developers.payu.com/europe/api/#tag/Payment-Methods
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/paymethods"
        headers = self.get_headers()
        response = backend_utils.send_request(url, "GET", headers=headers)
        return response

    def refund_order(self, order_id):
        """
        This function is used to refund an order
        Returns:
            response from PayU
        @see https://developers.payu.com/europe/api/#tag/Refund
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/orders/{order_id}/refunds"
        data = {
            "description": f"Refund for order {order_id}",
        }
        headers = self.get_headers()
        response = backend_utils.send_request(url, "POST", headers=headers, payload=data)
        return response

    def cancel_order(self, order_id):
        """
        This function is used to cancel an order
        Returns:
            response from PayU
        @see https://developers.payu.com/europe/api/#tag/Order/operation/cancel-an-order
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/orders/{order_id}"
        headers = self.get_headers()
        response = backend_utils.send_request(url, "DELETE", headers=headers)
        return response

    def create_payout(self, payout=None, customer_address=None):
        """
        This function is used to create a payout
        Args:
            payout: Payout object
            customer_address: Customer address
        Returns:
            response from PayU
        @see https://developers.payu.com/europe/api/#tag/Payout
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/payouts"
        data = {
            "payout": payout,
            "shopId": self.merchant_pos_id,
            "customerAddress": customer_address
        }
        headers = self.get_headers()
        response = backend_utils.send_request(url, "POST", headers=headers, payload=data)
        return response

    def retrieve_payout(self, payout_id):
        """
        This function is used to retrieve a payout
        Args:
            payout_id: Payout ID
        Returns:
            response from PayU
        @see https://developers.payu.com/europe/api/#tag/Payout
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/payouts/{payout_id}"
        headers = self.get_headers()
        response = backend_utils.send_request(url, "GET", headers=headers)
        return response

    def delete_card_token(self, token):
        """
        This function is used to delete a card token
        Args:
            token: Card token
        Returns:
            response from PayU
        @see https://developers.payu.com/europe/api/#tag/Card-Tokens
        """
        self.validate_access_token()
        url = f"{self.base_url}/api/v2_1/tokens/{token}"
        headers = self.get_headers()
        response = backend_utils.send_request(url, "DELETE", headers=headers)
        return response


"""
These functions are mare for testing purposes
"""


@api_view(["GET"])
def get_access_token(request):
    payu = PayU()
    payu.validate_access_token()
    return Response(payu.get_object_as_dict())


@api_view(["GET"])
def retrieve_payment_methods(request):
    payu = PayU()
    res = payu.retrieve_payment_methods()
    return Response({f"message":{res} })


# @api_view(["GET"])
# def process_order(request):
#     client_ip = request.META.get('REMOTE_ADDR')
#     payu = PayU()
#     payu.validate_access_token()
#     order = payu.prepare_order_payload(
#         order={
#             "customerIp": client_ip,
#             "merchantPosId": 487364,
#             "totalAmount": 100,
#             "description": "RTV market",
#             "email": "test@abc.com",
#             "phone": "+91 8460688863",
#             "firstName": "John",
#             "lastName": "Doe",
#             "products": [
#                 {
#                     "name": "Product 1",
#                     "unitPrice": 100,
#                     "quantity": 1
#                 }
#             ],
#             "extOrderId": uuid.uuid1().hex,
#         }
#     )
#     response = payu.process_order_final(order)
#     if response.status_code == 302:
#         return Response({"message": "Order processed successfully"})
#     return Response({"message": "Order processing failed"})


# import webbrowser

# @api_view(["GET"])
# def process_order(request):
#     client_ip = request.META.get('REMOTE_ADDR')
#     payu = PayU()
#     payu.validate_access_token()
#     order = payu.prepare_order_payload(
#         order={
#             "customerIp": client_ip,
#             "merchantPosId": 487364,
#             "totalAmount": 500,
#             "description": "BRIDGESTONE TYRE FOR MR MATEUCZ",
#             "email": "test@abc.com",
#             "phone": "+91 8460688863",
#             "firstName": "MATEUCZ",
#             "lastName": "CELEJ",
#             "products": [
#                 {
#                     "name": "Product 1",
#                     "unitPrice": 500,
#                     "quantity": 1
#                 }
#             ],
#             "extOrderId": uuid.uuid1().hex,
#         }
#     )
#     response = payu.process_order_final(order)
    
#     if response.status_code == 302:
#         redirect_uri = response.json().get("redirectUri")
#         if redirect_uri:
#             # Open the redirect URI in a new browser tab
#             webbrowser.open_new_tab(redirect_uri)
#             return Response({"message": "Redirecting to payment gateway", "redirectUri": redirect_uri})
#     return Response({"message": "Order processing failed"})


# @api_view(["GET"])
def process_order(order, client_ip):
    from orders.models import Order
    # print("=====>HERE IN PROCESS ORDER")
    # client_ip = request.META.get('REMOTE_ADDR')
    payu = PayU()
    payu.validate_access_token()
    order_data = payu.prepare_order_payload(order)
    print("ORSDER DATA  ====>",order_data)
    response = payu.process_order_final(order_data)
    print("++++VISITED") #
    if response.status_code == 302:
        return response
    
    return Response({"message": "Order processing failed"})



import hashlib
import hmac
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
import os
import requests
from django.utils.dateparse import parse_date

fakturowani_url = settings.FAKTUROWNIA_URL
fakturowan_token = settings.FAKTUROWNIA_TOKEN

# Configure logging
logger = logging.getLogger(__name__)


def send_invoice_mail(invoice_id):
    status = False
    data = None
    error = ""
    if not invoice_id:
        return Response({'error': 'Invoice ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    url = f"{fakturowani_url}/invoices/{invoice_id}/send_by_email.json?api_token={fakturowan_token}"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            status = True
            data = response.json()
        else:
            data = response.json()
            error = data

        return status, data, error

    except Exception as e:
        print(e)
        error = f"{e}"
        return status, data, error


def generate_invoice_for_payment(order_obj):
    from orders.models import OrderItem, OrderInvoice, Order
    from cart.models import Cart
    invoice_id = None
    order_invoice_obj_id = None
    
    logger.info('=' * 50)
    logger.info('Entering generate_invoice_for_payment function...')
    logger.info(f'Order ID: {order_obj.id}')
    
    # --- Access the related Cart safely ---
    cart_obj = order_obj.cart
    logger.info(f'Cart Object: {cart_obj}')
    logger.info(f'Cart ID: {cart_obj.id if cart_obj else "None"}')
    
    # Log pallet_type data
    logger.info(f'Pallet Type Data: {order_obj.pallet_type}')
    
    fake_transportation_cost = (
        order_obj.pallet_type.get("summary_of_order", {}).get("final_gross_transportation_cost", 0)
    )
    logger.info(f'Transportation Cost from pallet_type: {fake_transportation_cost}')
    logger.info(f'Transportation Cost Type: {type(fake_transportation_cost)}')

    # Check self_pickup value
    self_pickup = getattr(cart_obj, "self_pickup", False)
    logger.info(f'Self Pickup Value: {self_pickup}')
    logger.info(f'Self Pickup Type: {type(self_pickup)}')
    logger.info(f'Should Include Transport Cost: {not self_pickup}')
    
    invoice = {
        "kind": "vat",
        "number": "",
        "sell_date": f"{order_obj.created_at.date()}",
        "issue_date": f"{order_obj.created_at.date()}",
        "payment_to": f"{order_obj.created_at.date()}",
        "seller_name": "TIRGUM MATEUSZ CELEJ",
        "seller_tax_no": " 6452547332",
        "buyer_name": order_obj.company_name or order_obj.customer_name,
        "buyer_tax_no": "6272616681",
        "status": f"{order_obj.payment_status}",
        "buyer_email": f"{order_obj.customer_email}",
        "buyer_post_code": f"{order_obj.company_zip_code or ''}",
        "buyer_city": f"{order_obj.company_city or ''}",
        "positions": []
    }

    logger.debug('Initial Invoice data: %s', invoice)

    order_items = OrderItem.objects.filter(order=order_obj)
    logger.info(f'Total Order Items Found: {order_items.count()}')
    
    if not order_items:
        logger.warning("No order items found!")

    for item in order_items:
        try:
            position = {
                "name": f"{item.product.id} - {item.product.brand.name if item.product.brand else ''} {item.product.tread if hasattr(item.product, 'tread') else ''} {item.product.size if hasattr(item.product, 'size') else ''}".strip(),
                "tax": 23,
                "total_price_gross": round(float(getattr(item.product, "net_price", 0)) * 1.23, 2),
                "quantity": int(item.quantity)
            }
            invoice["positions"].append(position)
            logger.debug(f'Added product position: {position}')
        except AttributeError as e:
            logger.error("Error processing item: %s", e)
    
    # ✅ Add transport cost if self_pickup is False
    logger.info('=' * 50)
    logger.info('CHECKING TRANSPORT COST CONDITION')
    logger.info(f'self_pickup = {self_pickup}')
    logger.info(f'not self_pickup = {not self_pickup}')
    logger.info(f'fake_transportation_cost = {fake_transportation_cost}')
    
    if not self_pickup:
        logger.info('✅ Condition TRUE: Adding transport cost')
        transport_position = {
            "name": "Koszt transportu",
            "tax": 23,
            "total_price_gross": round(float(fake_transportation_cost), 2),
            "quantity": 1
        }
        invoice["positions"].append(transport_position)
        logger.info(f"✅ Transport cost position added: {transport_position}")
    else:
        logger.info('❌ Condition FALSE: NOT adding transport cost (self_pickup is True)')
    
    logger.info(f'Total positions in invoice: {len(invoice["positions"])}')
    logger.info(f'Final Invoice Positions: {invoice["positions"]}')
    logger.info('=' * 50)

    data = {"invoice": invoice, "api_token": fakturowan_token}
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        logger.info('Sending request to Fakturownia API...')
        response = requests.post(
            f'{fakturowani_url}/invoices.json',
            json=data,
            headers=headers
        )
        
        logger.info(f'Response Status Code: {response.status_code}')

        if response.status_code == 201:
            response_data = response.json()
            logger.info(f'Invoice created successfully: {response_data.get("id")}')
            issue_date = parse_date(response_data['issue_date'])

            req_pdf = requests.get(
                f"{fakturowani_url}/invoices/{response_data['id']}.pdf?api_token={fakturowan_token}"
            )

            media_folder = "media"
            invoice_folder = os.path.join(media_folder, "invoice")
            file_name = f"fakturownia-{response_data['id']}.pdf"
            file_path = os.path.join(invoice_folder, file_name)

            os.makedirs(invoice_folder, exist_ok=True)

            try:
                with open(file_path, "wb") as f:
                    f.write(req_pdf.content)
                logger.info(f'PDF saved at: {file_path}')
            except Exception as e:
                logger.error("Error writing PDF file: %s", e)

            invoice_status = response_data.get('status', 'generated')

            order_invoice = OrderInvoice(
                issue_date=issue_date,
                status=invoice_status,
                invoice_id=response_data['id'],
                invoice_path=file_path
            )
            order_invoice.save()

            invoice_id = order_invoice.invoice_id
            order_invoice_obj_id = order_invoice.pk

            logger.info(f"✅ Invoice saved successfully with ID: {invoice_id}")
            return True, invoice_id, order_invoice_obj_id

        elif response.status_code == 422:
            logger.warning(f"Validation Error (422): {response.json()}")
            return False, invoice_id, order_invoice_obj_id

        else:
            logger.error(f"Unexpected response: {response.status_code} - {response.json()}")
            return False, invoice_id, order_invoice_obj_id

    except Exception as e:
        logger.exception(f"Request failed: {e}")
        return False, invoice_id, order_invoice_obj_id

@csrf_exempt
def payu_notify(request):
    '''http://127.0.0.1:8000/api/libs/payu/notify/'''
    '''
        {
            "order": {
                "orderId": "MS1BBL1D1D250126GUEST000P01",
                "extOrderId": "43",
                "orderCreateDate": "2025-01-26T13:46:50.686+01:00",
                "notifyUrl": "https://tirgumpanel.pl/api/libs/payu/notify/",
                "customerIp": "127.0.0.1",
                "merchantPosId": "487364",
                "description": "THIS IS DESCRIPTION",
                "currencyCode": "PLN",
                "totalAmount": "2228",
                "buyer": {
                    "customerId": "guest",
                    "email": "ravichovatiya120@gmail.com",
                    "phone": "8200525530",
                    "firstName": "ravi",
                    "lastName": "chovatiya",
                    "language": "pl"
                },
                "payMethod": {
                    "type": "CARD_TOKEN"
                },
                "status": "COMPLETED",
                "products": [
                    {
                        "name": "Goodyear",
                        "unitPrice": "400",
                        "quantity": "1"
                    },
                    {
                        "name": "Continental",
                        "unitPrice": "1",
                        "quantity": "1"
                    }
                ]
            },
            "localReceiptDateTime": "2025-01-26T13:48:23.280+01:00",
            "properties": [
                {
                    "name": "PAYMENT_ID",
                    "value": "5018739068"
                }
            ]
        }
    '''
    if request.method == 'POST':
        from orders.models import Order, OrderPayment
        from orders.serializers import OrderPaymentSerializer
        from orders.models import OrderItem, OrderInvoice
        # Log the raw request body and headers
        try:
            raw_body = request.body.decode('utf-8')
            headers = request.headers
            logger.info("========================================")
            logger.info("Raw Body from PayU Notify URL: %s", raw_body)
            logger.info("Headers from PayU Notify URL: %s", headers)
            logger.info("========================================")

            notification_data = json.loads(raw_body)
            # notification_data = {'order': {'orderId': 'G2G1GSXPKC250130GUEST000P01', 'extOrderId': '15', 'orderCreateDate': '2025-01-30T10:23:41.267+01:00', 'notifyUrl': 'https://tirgumpanel.pl/api/libs/payu/notify/', 'customerIp': '127.0.0.1', 'merchantPosId': '487364', 'description': 'THIS IS DESCRIPTION', 'currencyCode': 'PLN', 'totalAmount': '1437', 'buyer': {'customerId': 'guest', 'email': 'ravichovatiya120@gmail.com', 'phone': '8200525530', 'firstName': 'ravi', 'lastName': 'chovatiya', 'language': 'pl'}, 'payMethod': {'type': 'CARD_TOKEN'}, 'status': 'COMPLETED', 'products': [{'name': 'Continental', 'unitPrice': '350', 'quantity': '1'}, {'name': 'Hankook', 'unitPrice': '350', 'quantity': '1'}]}, 'localReceiptDateTime': '2025-01-30T10:24:17.646+01:00', 'properties': [{'name': 'PAYMENT_ID', 'value': '5018847205'}]}
            logger.info("Parsed Notification Data: %s", notification_data)

            # Signature verification
            signature_header = headers.get("OpenPayu-Signature")
            if not signature_header:
                logger.error("Missing OpenPayu-Signature header.")
                return JsonResponse({"status": "error", "message": "Signature header missing"}, status=400)

            signature_parts = dict(item.split("=") for item in signature_header.split(";") if "=" in item)
            incoming_signature = signature_parts.get("signature")
            algorithm = signature_parts.get("algorithm", "MD5").lower()
            second_key = "5f790c2cca873777973357111a573e7f"  # Replace with your second key

            # Generate the expected signature
            concatenated = raw_body + second_key
            if algorithm == "md5":
                expected_signature = hashlib.md5(concatenated.encode('utf-8')).hexdigest()
            elif algorithm == "sha256":
                expected_signature = hmac.new(
                    second_key.encode('utf-8'),
                    concatenated.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
            else:
                logger.error("Unsupported hashing algorithm: %s", algorithm)
                return JsonResponse({"status": "error", "message": "Unsupported hashing algorithm"}, status=400)

            # Compare signatures
            if expected_signature != incoming_signature:
                logger.error("Invalid signature. Expected: %s, Received: %s", expected_signature, incoming_signature)
                return JsonResponse({"status": "error", "message": "Invalid signature"}, status=400)

            # Process the notification
            order = notification_data.get("order", {})
            status = order.get("status")
            order_id = order.get("orderId")
            ext_order_id = order.get("extOrderId")
            logger.info("Processing notification for Order ID: %s, Status: %s", order_id, status)
            order_objs = Order.objects.filter(order_id=order_id, ext_order_id=ext_order_id)
            order_obj = None
            if order_objs:
                order_obj = order_objs.first()
                # Handle the order status
                if status == "COMPLETED":
                    order_obj.payment_status = 'paid'
                    order_obj.order_status = 'paid'

                    
                    try:
                        from tyreadderapp.models import Product
                        order_items = OrderItem.objects.filter(order=order_obj)
                        for item in order_items:
                            product = item.product
                            if product:
                                product.status = Product.StatusChoices.SOLD  
                                product.save(update_fields=["status"])
                                logger.info(f"✅ Product {product.id} marked as SOLD for Order {order_obj.order_id}")
                    except Exception as e:
                        logger.error(f"❌ Error marking product SOLD for Order {order_obj.order_id}: {e}", exc_info=True)
                    #-------------------------------------------------
                    try:
                        if hasattr(order_obj, "handle_payment_success"):
                            order_obj.handle_payment_success()
                            logger.info("Cart cleared successfully for Order %s", ext_order_id)
                            
                        order_payment, created = OrderPayment.objects.get_or_create(
                            order=order_obj,
                            amount=float(order_obj.total_amount),
                        )
                        # print('order_payment ->', order_payment)
                        # order_payment_serializer = {}
                        # if order_payment.process_payment():
                        #     order_payment_serializer = Response(OrderPaymentSerializer(order_obj).data)
                        # logger.info("Except Order %s completed successfully and order_payment_serializer: %s.", ext_order_id, order_payment_serializer)
                    except:
                        logger.info("Except Order %s completed successfully", ext_order_id)

                    generate_invoice_status, invoice_id, order_invoice_obj_id = generate_invoice_for_payment(order_obj)
                    if generate_invoice_status:
                        logger.info("Order %s  %s Invoice Generate successfully.", ext_order_id, invoice_id)   
                        if order_invoice_obj_id:
                            invoice_obj = OrderInvoice.objects.filter(id = order_invoice_obj_id).first() if  OrderInvoice.objects.filter(id = order_invoice_obj_id) else None
                            order_obj.invoice = invoice_obj
                            order_obj.save()

                        status, data, error = send_invoice_mail(invoice_id)
                        if status:
                            logger.info("Order %s  %s  %s Main Send successfully.", status, data, error)   

                    logger.info("Order %s completed successfully.", ext_order_id)
                    # Update your database or perform business logic
                elif status in ["PENDING", "WAITING_FOR_CONFIRMATION"]:
                    order_obj.payment_status = 'processing'
                    logger.info("Order %s is in status: %s.", ext_order_id, status)
                elif status == "CANCELED":
                    order_obj.payment_status = 'cancelled'
                    logger.info("Order %s was canceled.", ext_order_id)
                else:
                    logger.warning("Unhandled order status: %s", status)
                order_obj.save()

                # Respond with a 200 status code to acknowledge receipt
                return JsonResponse({"status": "success", "message": "Notification processed"}, status=200)

        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body.")
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.exception("An error occurred while processing the notification: %s", str(e))
            return JsonResponse({"status": "error", "message": f"Internal server error, {e}"}, status=500)

    logger.error("Invalid request method: %s", request.method)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)



