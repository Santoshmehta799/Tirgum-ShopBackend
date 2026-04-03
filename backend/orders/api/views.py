import requests
from rest_framework import viewsets, status, views
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from orders.models import *
from orders.api.serializers import *
from django.conf import settings
from django.utils.dateparse import parse_date
import os
from django.shortcuts import get_object_or_404

fakturowani_url = settings.FAKTUROWNIA_URL
token = settings.FAKTUROWNIA_TOKEN


class InvoiceViewSet(viewsets.ModelViewSet):
    '''http://127.0.0.1:8000/api/orders/invoice'''
    queryset = OrderInvoice.objects.all()
    serializer_class = OrderInvoiceSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        data = {"invoice": {**request.data}, "api_token": token}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(
                f'{fakturowani_url}/invoices.json',
                json=data,
                headers=headers
            )
            if response.status_code == 201:
                response_data = response.json()

                # Extract necessary data from the response to save into the database
                issue_date = parse_date(response_data['issue_date'])

                req_pdf = requests.get(
                    f"{fakturowani_url}/invoices/{response_data['id']}.pdf?api_token={token}"
                )

                media_folder = "media"
                invoice_folder = os.path.join(media_folder, "invoice")
                file_name = f"fakturownia-{response_data['id']}.pdf"
                file_path = os.path.join(invoice_folder, file_name)

                # Create the directory if it doesn't exist
                os.makedirs(invoice_folder, exist_ok=True)

                try:
                    with open(file_path, "wb") as f:
                        f.write(req_pdf.content)
                except Exception as e:
                    print(f"Error writing PDF file: {e}")

                invoice_status = response_data.get('status', 'generated')

                order_invoice = OrderInvoice(
                    issue_date=issue_date,
                    status=invoice_status,
                    invoice_id=response_data['id'],
                    invoice_path=file_path
                )
                order_invoice.save()

                return Response(response_data, status=status.HTTP_201_CREATED)

            else:
                return Response(response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put', 'patch'])
    def edit(self, request):
        data = {"invoice": {**request.data}, "api_token": token}
        print("Data", data)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.put(
                f"{fakturowani_url}/invoices/{request.GET['id']}.json",
                json=data,
                headers=headers
            )

            if response.status_code == 200:
                response_data = response.json()
                req_pdf = requests.get(
                    f"{fakturowani_url}/invoices/{response_data['id']}.pdf?api_token={token}"
                )

                media_folder = "media"
                invoice_folder = os.path.join(media_folder, "invoice")
                file_name = f"fakturownia-{response_data['id']}.pdf"
                file_path = os.path.join(invoice_folder, file_name)

                # Create the directory if it doesn't exist
                os.makedirs(invoice_folder, exist_ok=True)

                try:
                    with open(file_path, "wb") as f:
                        print(req_pdf.content)
                        f.write(req_pdf.content)
                except Exception:
                    pass

                # invoice_path = file_path
                invoice = OrderInvoice.objects.get(
                    invoice_id=request.GET['id'])
                print("in", invoice)
                serializer = self.get_serializer(
                    invoice, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def send_email(self, request):
        invoice_id=357685236
        # if 'id' not in request.GET:
        #     return Response({'error': 'Invoice ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not invoice_id:
            return Response({'error': 'Invoice ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        url = f"{fakturowani_url}/invoices/{invoice_id}/send_by_email.json?api_token={token}"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers)

            if response.status_code == 200:
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        if 'id' not in request.GET:
            return Response({'error': 'Invoice ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        invoice = get_object_or_404(OrderInvoice, invoice_id=request.GET['id'])
        invoice_path = invoice.invoice_path.replace("\\", "/")
        return Response({'invoice_path': invoice_path}, status=status.HTTP_200_OK)
    

class OrdersDetailsByUser(views.APIView):
    def get(self, request, format=None):
        user = request.user if request.user.is_authenticated else None
        session_id = request.query_params.get("session_id", "")

        if not user and session_id == "":
            return Response({
                "status": "error",
                "message": "Please provide authorized user token or session id.",
            }, status=status.HTTP_400_BAD_REQUEST)

        if user:
            user_order_objs = Order.objects.filter(user=user).order_by('-created_at')
        else:
            user_order_objs = Order.objects.filter(session_id=session_id).order_by('-created_at')

        serialized_orders = OrderSerializer(user_order_objs, many=True)
        
        return Response({
            "status": "success",
            "orders": serialized_orders.data,
        }, status=status.HTTP_200_OK)

