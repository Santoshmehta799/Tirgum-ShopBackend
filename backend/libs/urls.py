from django.urls import path
from libs.payu import get_access_token, process_order, retrieve_payment_methods, payu_notify
from libs.mailgun import test_otp_email

urlpatterns = [
    path('get-access-token/', get_access_token, name='get_access_token'),
    # path('process-order/', process_order, name='process_order'),
    path('retrieve-payment-methods/', retrieve_payment_methods, name='retrieve-payment-methods'),
    path('test-mailgun/', test_otp_email, name='test_mailgun'),

    # path('test-mailgun1/', test_otp_email1, name='test_mailgun1'),
    path('payu/notify/', payu_notify, name='payu_notify'),
]
