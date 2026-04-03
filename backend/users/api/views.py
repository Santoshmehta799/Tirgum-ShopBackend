from zeep import Client
from users.models import User
from rest_framework import status
import xml.etree.ElementTree as ET
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.utils.crypto import get_random_string
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from users.api.serializers import UserSerializer, LoginSerializer, PasswordResetRequestSerializer, \
    PasswordResetConfirmSerializer

from libs import mailgun


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated, ]
    serializer_class = UserSerializer
    queryset = User.objects.filter()

    def get_permissions(self):
        if self.action == "create":
            return []
        return super().get_permissions()


class CustomObtainAuthToken(ObtainAuthToken):
    authentication_classes = []
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user_data = UserSerializer(instance=user).data
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': user_data})


class PasswordReset(APIView):
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        user = request.user
        new_password = request.data.get("new_password")
        old_password = request.data.get("old_password")

        if user.check_password(old_password):
            user.set_password(raw_password=new_password)
            user.save()
            Token.objects.filter(user=user).delete()
            return Response(data={"Password Changed Successfully"})

        return Response(data={"Password Change Failed"}, status=400)


class LogOut(APIView):
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        user = request.user
        Token.objects.filter(user=user).delete()
        return Response(data={"Logout Successful"})

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                otp = get_random_string(length=6, allowed_chars='0123456789')
                user.otp = otp
                user.save(update_fields=['otp'])
                
                print(f'OTP for {email}: {otp}')
                mailgun.send_otp_email(email, otp)
                
                return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email=email)
                if user.otp != otp:
                    return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
                
                user.set_password(new_password)
                user.otp = None  # Clear OTP after successful reset
                user.save(update_fields=['password', 'otp'])
                
                return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   


class NIPLookupView(APIView):
    """
    API endpoint for looking up company details by NIP (Polish Tax ID)
    """
    permission_classes = [AllowAny]
    authentication_classes = [] 
    
    def parse_address(self, data):
        """Helper method to parse and format address from API response"""
        parts = [
            data.get("Ulica", ""),
            data.get("NrNieruchomosci", ""),
            data.get("KodPocztowy", ""),
            data.get("Miejscowosc", ""),
            data.get("Miejscowosc", "")

        ]
        return ", ".join(part for part in parts if part)
    
    def get(self, request, nip=None):
        # Get NIP from URL parameter or query param
        nip = nip or request.query_params.get('nip')
        
        if not nip:
            return Response(
                {"error": "NIP parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Initialize WSDL client
        WSDL_URL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/wsdl/UslugaBIRzewnPubl-ver11-prod.wsdl"
        API_KEY = 'baad59d034f3425d936e' 
        
        try:
            client = Client(WSDL_URL)
            sid = client.service.Zaloguj(API_KEY)
            
            if not sid:
                return Response(
                    {"error": "Failed to authenticate with REGON API"}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
            # Set session ID in headers
            client.transport.session.headers.update({"sid": sid})
            
            # Search by NIP
            result_xml = client.service.DaneSzukajPodmioty({"Nip": nip})
            
            if not result_xml:
                return Response(
                    {"error": "No company data found for this NIP"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Parse XML response
            root = ET.fromstring(result_xml)
            # The XML structure seems to be different than expected in your original script
            # Let's extract data from the 'dane' element directly
            data_element = root.find(".//dane")
            
            if data_element is None:
                return Response(
                    {"error": "Invalid response format from REGON API"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # Extract basic company data
            company_data = {}
            for child in data_element:
                if child.tag not in company_data:  # Only take the first occurrence of each tag
                    company_data[child.tag] = child.text
            
            regon = company_data.get("Regon")
            if not regon:
                return Response(
                    {"error": "REGON not found in response"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # For companies (type P), fetch full report
            if company_data.get("Typ") == "P":
                try:
                    report_xml = client.service.DanePobierzPelnyRaport(regon, "PublDaneRaportPrawna")
                    if report_xml:
                        report_root = ET.fromstring(report_xml)
                        for child in report_root:
                            company_data[child.tag] = child.text
                except Exception:
                    # Continue with basic data if full report fails
                    pass
            # For individuals (type F), fetch full report
            elif company_data.get("Typ") == "F":
                try:
                    report_xml = client.service.DanePobierzPelnyRaport(regon, "PublDaneRaportFizyczna")
                    if report_xml:
                        report_root = ET.fromstring(report_xml)
                        for child in report_root:
                            company_data[child.tag] = child.text
                except Exception:
                    # Continue with basic data if full report fails
                    pass
            
            # Prepare response
            response_data = {
                "name": company_data.get("Nazwa", "Not available"),
                "regon": regon,
                "nip": nip,
                "address": self.parse_address(company_data) or "Not available",
                "type": "Company" if company_data.get("Typ") == "P" else "Individual",
                "voivodeship": company_data.get("Wojewodztwo", "Not available"),
                "city": company_data.get("Miejscowosc", "Not available"),
                "postal_code": company_data.get("KodPocztowy", "Not available"),
                "street": company_data.get("Ulica", "Not available"),
                "building_number": company_data.get("NrNieruchomosci", "Not available"),
                "apartment_number": company_data.get("NrLokalu", ""),
                "status": "Active" if not company_data.get("DataZakonczeniaDzialalnosci") else "Inactive",
                "raw_data": company_data  # Include raw data for debugging/additional fields
            }
            
            # Always logout at the end
            try:
                client.service.Wyloguj(sid)
            except:
                pass
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"API error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# class NIPLookupView(APIView):
#     """
#     API endpoint for looking up company details by NIP (Polish Tax ID)
#     """
    
#     def parse_address(self, data):
#         """Helper method to parse and format address from API response"""
#         parts = [
#             data.get("Ulica", ""),
#             data.get("NrNieruchomosci", ""),
#             data.get("KodPocztowy", ""),
#             data.get("Miejscowosc", "")
#         ]
#         return ", ".join(part for part in parts if part)
    
#     def get(self, request, nip=None):
#         # Get NIP from URL parameter or query param
#         nip = nip or request.query_params.get('nip')
        
#         # Validate the request
#         request_serializer = NIPLookupRequestSerializer(data={'nip': nip} if nip else {})
#         if not request_serializer.is_valid():
#             return Response(
#                 request_serializer.errors, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
            
#         # Initialize WSDL client
#         WSDL_URL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/wsdl/UslugaBIRzewnPubl-ver11-prod.wsdl"
#         API_KEY = 'baad59d034f3425d936e'
        
#         try:
#             client = Client(WSDL_URL)
#             sid = client.service.Zaloguj(API_KEY)
            
#             if not sid:
#                 return Response(
#                     {"error": "Failed to authenticate with REGON API"}, 
#                     status=status.HTTP_503_SERVICE_UNAVAILABLE
#                 )
                
#             # Set session ID in headers
#             client.transport.session.headers.update({"sid": sid})
            
#             # Search by NIP
#             result_xml = client.service.DaneSzukajPodmioty({"Nip": nip})
            
#             if not result_xml:
#                 return Response(
#                     {"error": "No company data found for this NIP"}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )
                
#             # Parse XML response
#             root = ET.fromstring(result_xml)
#             # The XML structure seems to be different than expected in your original script
#             # Let's extract data from the 'dane' element directly
#             data_element = root.find(".//dane")
            
#             if data_element is None:
#                 return Response(
#                     {"error": "Invalid response format from REGON API"}, 
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
                
#             # Extract basic company data
#             company_data = {}
#             for child in data_element:
#                 if child.tag not in company_data:  # Only take the first occurrence of each tag
#                     company_data[child.tag] = child.text
            
#             regon = company_data.get("Regon")
#             if not regon:
#                 return Response(
#                     {"error": "REGON not found in response"}, 
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
                
#             # For companies (type P), fetch full report
#             if company_data.get("Typ") == "P":
#                 try:
#                     report_xml = client.service.DanePobierzPelnyRaport(regon, "PublDaneRaportPrawna")
#                     if report_xml:
#                         report_root = ET.fromstring(report_xml)
#                         for child in report_root:
#                             company_data[child.tag] = child.text
#                 except Exception:
#                     # Continue with basic data if full report fails
#                     pass
#             # For individuals (type F), fetch full report
#             elif company_data.get("Typ") == "F":
#                 try:
#                     report_xml = client.service.DanePobierzPelnyRaport(regon, "PublDaneRaportFizyczna")
#                     if report_xml:
#                         report_root = ET.fromstring(report_xml)
#                         for child in report_root:
#                             company_data[child.tag] = child.text
#                 except Exception:
#                     # Continue with basic data if full report fails
#                     pass
            
#             # Prepare response data
#             response_data = {
#                 "name": company_data.get("Nazwa", "Not available"),
#                 "regon": regon,
#                 "nip": nip,
#                 "address": self.parse_address(company_data) or "Not available",
#                 "type": "Company" if company_data.get("Typ") == "P" else "Individual",
#                 "voivodeship": company_data.get("Wojewodztwo", "Not available"),
#                 "city": company_data.get("Miejscowosc", "Not available"),
#                 "postal_code": company_data.get("KodPocztowy", "Not available"),
#                 "street": company_data.get("Ulica", "Not available"),
#                 "building_number": company_data.get("NrNieruchomosci", "Not available"),
#                 "apartment_number": company_data.get("NrLokalu", ""),
#                 "status": "Active" if not company_data.get("DataZakonczeniaDzialalnosci") else "Inactive",
#                 "raw_data": company_data  # Include raw data for debugging/additional fields
#             }
            
#             # Validate and serialize the response
#             serializer = NIPLookupSerializer(data=response_data)
#             if not serializer.is_valid():
#                 # If serialization fails, log error and return raw data
#                 return Response(
#                     {"error": "Data serialization error", "raw_data": response_data},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
            
#             # Always logout at the end
#             try:
#                 client.service.Wyloguj(sid)
#             except:
#                 pass
                
#             return Response(serializer.data, status=status.HTTP_200_OK)
            
#         except Exception as e:
#             return Response(
#                 {"error": f"API error: {str(e)}"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
