import requests
from django.conf import settings

fakturowani_url = settings.FAKTUROWNIA_URL
token = settings.FAKTUROWNIA_TOKEN

def generate_invoice(data_req):
    data = {"invoice": {**data_req}, "api_token": token}

    req = requests.post(
        f"{fakturowani_url}invoices.json",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=data,
    )

    # if not req.ok:
    #     raise GenerateInvoiceException(req.text)

    response = req.json()

    req_pdf = requests.get(
        f"{fakturowani_url}invoices/{response['id']}.pdf?api_token={token}",
    )

    # if not req_pdf.ok:
    #     raise GenerateInvoiceException(f"PDF: {req_pdf.text}")
    # return req_pdf.content
    return response

def update_invoice(data_req):
    data = {"invoice": {**data_req}, "api_token": token}
    req = requests.post(
        f"{fakturowani_url}invoices.json",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=data,
    )
    response = req.json()
    return response
