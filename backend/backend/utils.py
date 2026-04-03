import sys
import json
from datetime import datetime
import pytz

import requests
from requests import Session
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
import base64


def logger(message: str = "", frame=None):
    """Logs specified message.

    Args:
        message: A message to log.
        frame: A frame object from the call stack.

    See:
        https://docs.python.org/3/library/sys.html#sys._getframe
    """
    function = None
    location = None

    if frame is None:
        try:
            frame = sys._getframe()
        except:
            pass

    if frame is not None:
        try:
            previous = frame.f_back
            function = previous.f_code.co_name
            location = "%s:%s" % (
                previous.f_code.co_filename, previous.f_lineno)
        except:
            pass

    sys.stderr.write("[%s] [%s] %s\r\n" %
                     (function, location, message))


def send_request(url: str, request_type: str = "GET",
                 payload: [str, dict] = None, headers: dict = None, json_response=False, **kwargs):
    """
    Sends an HTTP request.
    Args:
        url: url to send request to
        request_type: [GET, POST, DELETE, PUT, PATCH]
        payload: str or dict type payload
        headers: headers to attach to request

    """
    if url is None or url == "None" or url == "":
        return None
    session = Session()
    session.verify = False

    frame = None
    try:
        frame = sys._getframe()
    except:
        pass

    if payload is not None and str != type(payload):
        payload = json.dumps(payload)

    logger("URL: %s" % url, frame)
    logger("Payload: %s" % payload, frame)
    logger("Headers: %s" % headers, frame)

    response = requests.request(
        request_type, url, headers=headers, data=payload)

    logger("Response: %s %s %s" %
           (response.status_code, response.reason, response.text), frame)
    if json_response:
        return response.json()
    return response


def send_order_email(to_email, subject, message):
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
    response = requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),

        data = {
            'from': (None, f"Tirgum T <mailgun@{settings.MAILGUN_DOMAIN}>"),
            'to': (None, to_email),
            'subject': (None, subject),
            'html': (None, message)
        }
    )


def get_current_datetime():
    """
    Returns the current date and time UTC aware
    """
    return pytz.utc.localize(datetime.now())


def url_encode(data):
    """
    Encodes the data into a URL-encoded format
    """
    return "&".join([f"{key}={value}" for key, value in data.items()])
# utils.py


def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
