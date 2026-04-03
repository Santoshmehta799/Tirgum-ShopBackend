from io import BytesIO
import re
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import render


# def get_pdf_from_template(template_path,context,filename="pdf_file"):
#     template = get_template(template_path)
#     html = template.render(context)
#     pdf_bytes = BytesIO()
#     pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf_bytes)
#     pdf_bytes.seek(0)
#     response = HttpResponse(pdf_bytes.read(), content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{filename}"'
#     return response

def get_html_preview(pdf_bytes, filename='pdf_file'):
    html_preview = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PDF Preview</title>
        </head>
        <body>
            <embed src="data:application/pdf;base64,{pdf_bytes}" type="application/pdf" width="100%" height="600px" />
            <br>

        </body>
        </html>
        """
    preview_response = HttpResponse(html_preview)
    return preview_response


def get_pdf_bytes_from_template(template_path, context):
    template = get_template(template_path)
    html = template.render(context)
    pdf_bytes = BytesIO()
    pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes


def get_pdf_download_file_from_template(template_path, context, filename="pdf_file.pdf"):
    pdf_bytes = get_pdf_bytes_from_template(template_path, context)
    download_response = HttpResponse(pdf_bytes.read(), content_type='application/pdf')
    download_response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return download_response


def get_pdf_preview_from_template(template_path, context, filename="pdf_file.pdf"):
    pdf_bytes = get_pdf_bytes_from_template(template_path, context)
    preview_response = get_html_preview(pdf_bytes, filename)  # Assuming you have this function defined
    return preview_response


def get_pdf_from_template(template_path, context, filename="pdf_file.pdf"):
    return get_pdf_download_file_from_template(template_path, context, filename)
