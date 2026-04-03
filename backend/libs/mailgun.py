from django.conf import settings
from backend.utils import send_request
import requests
from django.http import JsonResponse
from django.template.loader import render_to_string


def send_email(to_email, subject, message):
    """
    Sends an email to the specified email address.
    Args:
        to_email: email address to send email to
        subject: email subject
        message: email message in HTML format
    Returns:
        response: email sending response

    @see: https://documentation.mailgun.com/en/latest/user_manual.html#sending-via-api
    """
    return send_request(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        request_type="POST",
        headers={
            "Authorization": f"Bearer {settings.MAILGUN_API_KEY}"
        },
        payload={
            "from": settings.MAILGUN_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": message
        }
    )


def send_otp_email(to_email, otp, subject="Tirgumpl OTP"):
    """
    Sends an OTP email to the specified email address.
    Args:
        otp: OTP to send
        subject: email subject
        to_email: email address to send email to
    Returns:
        response: email sending response
    """
    data = {
        "from": f"Tirgum PL <{settings.MAILGUN_FROM_EMAIL}>",
        "to": to_email,
        "subject": subject,
        "template": "tirgum pl otp",
        "h:X-Mailgun-Variables": """{"otp_code": "%s"}""" % otp
    }
    print(data)
    response = requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),

        data=data
    )


def test_otp_email(request):
    """
    Test mailgun email sending.
    """
    to = request.GET.get("to", "szymoncseosem@gmail.com")

    data = {"from": "Tirgum PL <brad@mail.tirgumpanel.pl>",
            "to": to,
            "subject": "Password Recovery OTP",
            "template": "tirgum pl otp",
            "h:X-Mailgun-Variables": '{"otp_code": "123456"}'
            }
    response = requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),

        data=data
    )
    # Send an email using your active template with the above snippet
    # You can see a record of this email in your logs: https://app.mailgun.com/app/logs.
    return JsonResponse(response.text, safe=False)
