from django.db.models import Case, When, Value, IntegerField, BooleanField
from django.shortcuts import render, redirect
from tyreadderapp.models import Product, Pair, PairAdvertImageProcessor  # adjust import if needed
from django.views.decorators.csrf import csrf_exempt
import tempfile
from io import BytesIO
from django.core.files.base import ContentFile
from weasyprint import HTML
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404

from urllib.parse import urlencode
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse
import json
from django.db.models import F, FloatField, ExpressionWrapper


import numpy as np
# views.py
from django.views.decorators.http import require_POST

from django.contrib import messages
from django.forms import modelformset_factory

from django.db.models import Max

from django.forms import BaseModelForm
from .forms import ProductSearchForm
from .forms import ProductLocationAssignmentForm
from .forms import ProductCreateForm,StapleForm, ProductForm, BrandForm, TreadForm, ImageForm, EditProductForm, StaffLoginForm, Tread_CharacterForm, FormatForm, Image, ImportForm, PairImageForm
from .forms import StapleForm, ProductStatusForm
from .models import Row, Rack, Staple
from .models import Product, New_Tread_Depth
from .models import Brand, Pair, Tread, Image, Tread_Image, Pallete, Size, Tyre_Ean, Rack, Staple, Warehouse, Row
from .models import SimilarTread, Tread_Character, PairImage
from otomoto.client.pair.otomoto_pair_ad import OtomotoPairAd
from django.http import JsonResponse
from operator import attrgetter
from itertools import groupby
from datetime import timedelta

from django.db.models import Q, Count, IntegerField
from collections import defaultdict
from django.core.paginator import Paginator

import io
import os
import json
import tablib
import zipfile
import logging
import traceback
from typing import Any
from PIL import ImageOps
from PIL import Image as PILImage
from decimal import Decimal
from django.db import models
from django.views import View
from orders.models import Order
from olx.client import OlxClient
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework import status

from olx.models import OLXAuthData
from rest_framework import generics
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404

from django.utils.timezone import now
from cart.models import CartItem, Cart

from .pdf import get_pdf_from_template
from rest_framework.views import APIView
from backend.utils import generate_qr_code
from django.db.models import IntegerField
from django.db.models.functions import Cast
from collections import defaultdict, Counter
from rest_framework.response import Response
from cart.serializers import CartSerializers

from django.urls import reverse, reverse_lazy

from django.views.decorators.http import require_POST
from .filters import ProductFilter, TreadCharacterFilter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from tyreadderapp import resources as tyreadderapp_resource
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.generic import CreateView, ListView, DeleteView,DetailView, UpdateView, FormView
from .api.serializers import PalletesSerializer, ProductSerializer, ProductsSearchSerailizer, TyreSizeListSerializer
import signal
import threading

def shutdown_server(request):
    os.kill(os.getpid(), signal.SIGINT)
    return HttpResponse("Server is shutting down...")

def shutdown_server(request):

    def kill():
        import time
        time.sleep(1)
        os.kill(1, signal.SIGTERM)  # 🔥 PID 1 kill

    threading.Thread(target=kill).start()
    
    return HttpResponse("Pod restarting...")


# Product Views

olx_client = OlxClient()


def login(request):
    if request.method == "POST":
        # Login User
        return
    else:
        return render(request, 'tyreadderapp/login.html')


def logout(request):
    return redirect('index')


class Main(LoginRequiredMixin, View):
    ''' View for home page'''

    def get(self, request):
        return render(request, "tyreadderapp/main.html")


class ThankYouView(View):
    '''Thank you View'''

    def get(self, request):
        return render(request, "tyreadderapp/thank-you.html")


class Jobs(LoginRequiredMixin, View):
    '''Views for adding tasks'''

    def get(self, request):
        return render(request, "tyreadderapp/jobs.html")




def product_cards_pdf(request):
    product_cards_pdf = Product.objects.all()
    template_path = 'tyreadderapp/pdfs/product_cards_pdf.html'
    context = {'product_card_pdf': product_cards_pdf}
    filename = 'product_cards_pdf.pdf'
    # return render(request,template_path,context)
    return get_pdf_from_template(template_path, context, filename=filename)


def product_card_pdf(request, pk):
    product_card_pdf = Product.objects.filter(pk=pk)
    template_path = 'tyreadderapp/pdfs/product_card_pdf.html'
    context = {'product_card_pdf': product_card_pdf}
    filename = 'product_card_pdf.pdf'
    # return render(request,template_path,context)
    return get_pdf_from_template(template_path, context, filename=filename)


# DETAIL PAGE TO PDF

def single_label(request, pk):
    # product_id=self.kwargs.get("pk")
    current_url = request.build_absolute_uri()
    qr_code_image = generate_qr_code(current_url)
    single_label = Product.objects.filter(pk=pk)
    template_path = 'tyreadderapp/pdfs/single_label.html'
    context = {'single_label': single_label, 'qr_code_image': qr_code_image}
    filename = 'single_label.pdf'
    # return get_pdf_from_template(template_path, context, filename=filename)
    return render(request, template_path, context)


def select_single_label(request, ids):
    product_ids = ids.split(",")
    products = Product.objects.filter(id__in=product_ids)
    labels = []
    products.update(is_label_printed=True)
    for product in products:
        current_url = request.build_absolute_uri()
        qr_code_image = generate_qr_code(current_url)
        labels.append({
            'product': product,
            'qr_code_image': qr_code_image,
        })
    context = {'labels': labels}
    return render(request, 'tyreadderapp/pdfs/select_multiple_label_pdf.html', context)


def selected_label(request):
    is_label = Product.objects.filter(
        is_label_printed=False, status=Product.StatusChoices.TO_ADD)
    filters = ProductFilter(request.GET, queryset=is_label)
    context = {'filters': filters, 'quantity': is_label}
    return render(request, 'tyreadderapp/select_label.html', context)


def multiple_label_printout(request):
    is_label = Product.objects.filter(
        is_label_printed=False, status=Product.StatusChoices.TO_ADD).prefetch_related('images')
    for product in is_label:
        product.main_image = product.images.filter(
            image__icontains='-1.jpg').first()
    return render(request, 'tyreadderapp/multiple_label_printout.html', {'is_label': is_label})


def process_selected_products(request):
    if request.method == "POST":
        action = request.POST.get('action')
        selected_products = request.POST.getlist('selected_product')

        if action == 'delete_label':
            if selected_products:
                updated_count = Product.objects.filter(
                    id__in=selected_products).update(is_label_printed=True)

            return redirect("tyreadderapp:selected_label")

        if action == "bulk_label_printing":
            if selected_products:
                selected_ids = ",".join(selected_products)
                return redirect(reverse('tyreadderapp:select_single_label', kwargs={'ids': selected_ids}))

    return redirect('tyreadderapp:selected_label')




def workspace(request):
    on_workspace_statuses = [
        Product.StatusChoices.TO_ADD,
        Product.StatusChoices.ON_SALE
    ]

    search_query = request.GET.get("search", "").strip()

    products = Product.objects.filter(
        status__in=on_workspace_statuses
    ).order_by("created")

    if search_query:
        if search_query.isdigit():
            products = products.filter(id=search_query)
        else:
            products = products.filter(
                Q(brand__name__icontains=search_query) |
                Q(tread__name__icontains=search_query) |
                Q(size__size__icontains=search_query)
            )

    filters = ProductFilter(request.GET, queryset=products)
    filtered_products = filters.qs.prefetch_related('images')

    quantity = filtered_products.count()

    # 🔹 Pagination
    paginator = Paginator(filtered_products, 20)  # 20 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 🔹 Annotate only paginated products
    for product in page_obj:
        images = product.images.all()
        main_image = None

        for image in images:
            name = image.image.name.lower()
            if name.endswith('-1.jpg') or name.endswith('-1.jpeg') or name.endswith('-1.png'):
                main_image = image
                break

        if not main_image:
            images_with_numbers = []
            for image in images:
                try:
                    num = int(image.image.name.split('-')[-1].split('.')[0])
                    images_with_numbers.append((num, image))
                except (IndexError, ValueError):
                    continue

            if images_with_numbers:
                images_with_numbers.sort(key=lambda x: x[0])
                main_image = images_with_numbers[0][1]

        if not main_image and images:
            main_image = images[0]

        product.main_image = main_image

    context = {
        'filters': filters,
        'quantity': quantity,
        'search_query': search_query,
        'products': page_obj,        # 👈 paginated products
        'page_obj': page_obj,
        'paginator': paginator,
    }

    return render(request, 'tyreadderapp/workspace.html', context)


def shop(request):
    # products = Product.objects.all()
    on_sale = Product.StatusChoices.ON_SALE
    products = Product.objects.filter(status=on_sale)
    quantity = Product.objects.filter(status=on_sale).count()
    filters = ProductFilter(request.GET, queryset=products)
    context = {'filters': filters, 'quantity': quantity}
    return render(request, 'tyreadderapp/shop.html', context)




def statistics(request):
    # all_products = Product.objects.all().count()

    available_products_count = Product.objects.filter(
        Q(status=Product.StatusChoices.TO_ADD) | Q(status=Product.StatusChoices.ON_SALE)).count()

    available_products_value = Product.objects.filter(
        Q(status=Product.StatusChoices.TO_ADD) | Q(
            status=Product.StatusChoices.ON_SALE)
    ).aggregate(Sum('net_price'))['net_price__sum'] or 0

    top_brand_tread_combinations = (
        Product.objects
        .filter(Q(status=Product.StatusChoices.TO_ADD) | Q(status=Product.StatusChoices.ON_SALE))
        .values('brand__name', 'tread__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    size_315_70_r22_5 = Product.objects.filter(
        size__size__exact="315/70 R22.5").count()
    size_315_60_r22_5 = Product.objects.filter(
        size__size__exact="315/60 R22.5").count()
    size_385_65_r22_5 = Product.objects.filter(
        size__size__exact="385/65 R22.5").count()
    size_385_55_r22_5 = Product.objects.filter(
        size__size__exact="385/55 R22.5").count()
    size_355_50_r22_5 = Product.objects.filter(
        size__size__exact="355/50 R22.5").count()
    size_295_80_r22_5 = Product.objects.filter(
        size__size__exact="295/80 R22.5").count()
    size_435_50_r19_5 = Product.objects.filter(
        size__size__exact="435/50 R19.5").count()

    context = {
        'available_products_count': available_products_count,
        'available_products_value': available_products_value,
        'top_brand_tread_combinations': top_brand_tread_combinations,
        'size_315_70_r22_5': size_315_70_r22_5,
        'size_315_60_r22_5': size_315_60_r22_5,
        'size_385_65_r22_5': size_385_65_r22_5,
        'size_385_55_r22_5': size_385_55_r22_5,
        'size_355_50_r22_5': size_355_50_r22_5,
        'size_295_80_r22_5': size_295_80_r22_5,
        'size_435_50_r19_5': size_435_50_r19_5,
    }
    return render(request, 'tyreadderapp/statistics.html', context)


class SingleProductView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "tyreadderapp/product-detail-view.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # "We are passing pk value from url and image url to template by modifying context"
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get("pk")
        context["images"] = Image.objects.filter(product_id=product_id)
        context["pk"] = product_id
        return context


# CONVERT SINGLE PRODUCT CLASS TO FUNCTION VIEW
# def single_product(request):
#     products = Product.objects.all()
#     context = {'filters': filters}
#     return render(request, 'tyreadderapp/product-detail-view.html', context)

class SingleProductEditView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = "tyreadderapp/tyre-edit-form.html"
    form_class = EditProductForm
    success_message = "✅ Record modified."

    def form_valid(self, form) -> HttpResponse:
        print("✅ Form valid method enter hua")

        # Show success message
        messages.success(self.request, self.success_message)

        # Detect if OLX checkbox changed
        old_instance = self.get_object()
        instance = form.save(commit=False)

        print("Old OLX:", old_instance.is_olx)
        print("New OLX:", form.cleaned_data.get('is_olx'))

        # Save the instance
        instance.save()

        # Redirect if OLX flag changed
        if form.cleaned_data.get('is_olx') != old_instance.is_olx:
            redirect_url = reverse("olx:olx-product-update")
            return redirect(redirect_url)

        return super().form_valid(form)

    def form_invalid(self, form):
        print("❌ FORM INVALID!")
        print("Errors:", form.errors)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('tyreadderapp:edit-detail', args=[self.object.pk])


def tyre_product_view(request):
    product_objs = Product.objects.filter(status=Product.StatusChoices.ON_SALE)
    if request.method == 'GET':
        if 'product_id' in request.GET:
            product_id = request.GET['product_id']
            return redirect(reverse('tyreadderapp:edit_product', args=[product_id]))

    context = {
        "product_objs": product_objs
    }
    return render(request, 'tyreadderapp/product_view.html', context)


@login_required
def tyre_product_edit_view(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
    except Http404:
        return render(request, 'tyreadderapp/edit_product.html', {'error_message': "Product id not found."})

    if request.method == 'POST':
        # Debug: Print the POST data to see what's being sent
        # print("POST data:", request.POST)
        # print("Status from POST:", request.POST.get('status'))
        # print("Current product status:", product.status)

        form = ProductForm(request.POST, request.FILES, instance=product)
        pair_id = request.POST.get('pair')
        if form.is_valid():
            # print("Form is valid--------------->>")
            product = form.save()
            # print("Product status after form save:", product.status)

            if pair_id:
                # Check if the pair still exists before setting it
                try:
                    pair = Pair.objects.get(id=pair_id)
                    product.pair_id = pair_id
                    product.save()
                except Pair.DoesNotExist:
                    print(
                        f"Pair {pair_id} no longer exists, skipping pair assignment")
            else:
                # Only save again if we're not setting pair_id
                product.save()

            # print("Product status after final save:", product.status)

            product_images = request.FILES.getlist('product_image')
            if product_images:
                for img in product_images:
                    # Check if an image with the same file exists, if not create a new one
                    existing_image = Image.objects.filter(
                        product=product, image=img).order_by('id').first()
                    if not existing_image:
                        Image.objects.create(product=product, image=img)
            return redirect(reverse('tyreadderapp:edit_product', args=[product.pk]))
        else:
            print("Form errors:", form.errors)
            print("Form data:", form.data)
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product,
        'images': Image.objects.filter(product=product)
    }

    return render(request, 'tyreadderapp/edit_product.html', context)


class DeleteImageView(LoginRequiredMixin, View):
    def post(self, request, image_id):
        image = get_object_or_404(Image, id=image_id)
        product_id = image.product.id
        image.delete()
        return redirect(reverse('tyreadderapp:edit_product', kwargs={'pk': product_id}))


class UpdateImageView(LoginRequiredMixin, View):
    def post(self, request, image_id):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            image = get_object_or_404(Image, id=image_id)
            new_image = request.FILES.get('new_image')
            if new_image:
                image.image = new_image
                image.save()
                return JsonResponse({
                    'success': True,
                    'new_image_url': image.image.url
                })
            return JsonResponse({'success': False})
        else:
            # Handle non-AJAX requests as before
            image = get_object_or_404(Image, id=image_id)
            new_image = request.FILES.get('new_image')
            if new_image:
                image.image = new_image
                image.save()
            return redirect(reverse('tyreadderapp:edit_product', kwargs={'pk': image.product.id}))


class TyreProductDeleteView(DeleteView):
    model = Product
    template_name = 'tyreadderapp/product_delete.html'
    success_url = reverse_lazy('tyreadderapp:thank-you')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                product.delete()
                messages.success(
                    request, f'Product #{product_id} has been deleted.')
            except Product.DoesNotExist:
                messages.error(request, f'Product #{product_id} not found.')
        else:
            messages.error(request, 'No product selected.')
        return redirect('tyreadderapp:delete_product')


def tyre_product_delete_view(request, pk):
    if request.method == 'GET':
        if pk:
            try:
                product = Product.objects.get(id=pk)
                product.delete()
                messages.success(request, f'Product #{pk} has been deleted.')
                return redirect('/tyreadderapp/main')
            except Product.DoesNotExist:
                messages.error(request, f'Product #{pk} not found.')
                return redirect('/tyreadderapp/main')
        else:
            messages.error(request, 'Product with this id Does not exist.')
            return redirect('/tyreadderapp/main')


class SingleProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = "tyreadderapp/tyre-delete.html"
    success_url = reverse_lazy("tyreadderapp:thank-you")


def tyre_form(request):
    if request.method == "POST":
        form = ProductCreateForm(request.POST, request.FILES)
        files = request.FILES.getlist("image")

        if form.is_valid():
            try:
                f = form.save(commit=False)
                f.advert_title = f.get_advert_title()
                f.advert_description = f.get_advert_description()
                f.ean = f.get_ean()
                f.save()

                for uploaded_file in files:
                    img = PILImage.open(uploaded_file)
                    img = ImageOps.exif_transpose(img)
                    output = io.BytesIO()
                    format = uploaded_file.name.split('.')[-1].upper()
                    if format == 'JPG':
                        format = 'JPEG'
                    img.save(output, format=format, quality=85)
                    output.seek(0)

                    processed_img = InMemoryUploadedFile(
                        output,
                        'ImageField',
                        uploaded_file.name,
                        uploaded_file.content_type,
                        output.getbuffer().nbytes,
                        None
                    )
                    Image.objects.create(product=f, image=processed_img)

                messages.success(request, f"Dodałeś oponę z ID: {f.id}")
                return redirect("tyreadderapp:form")

            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")

    # GET request or after redirect
    form = ProductCreateForm()

    last_id = Product.objects.aggregate(Max('id'))['id__max']
    next_product_id = last_id + 1 if last_id else 1

    context = {
        "form": form,
        "this_product_id": next_product_id
    }

    return render(request, "tyreadderapp/tyre_form_new.html", context)


class Test(LoginRequiredMixin, View):
    ''' Test View'''

    def get(self, request):
        return render(request, "tyreadderapp/test.html")

# CONVERT SINGLE PRODUCT CLASS TO FUNCTION VIEW


def distinct_treads(request):
    # distinct_treads = Product.objects.values('brand').distinct('brand')
    distinct_treads = Product.objects.all().values('brand').distinct()
    context = {'distinct_treads': distinct_treads}
    return render(request, 'tyreadderapp/distinct-treads.html', context)


# class StaffLoginView(UpdateView):
#     model = Staff
#     template_name = "tyreadderapp/login.html"
#     form_class = EditProductForm
#     success_url = "http://127.0.0.1:8000/tyreadderapp/main"


def stafflogin(request):
    form = StaffLoginForm()
    return render(request, "tyreadderapp/stafflogin.html", {"form": form})


def getTreads(request):
    brand_id = request.GET.get("brand")
    if brand_id == '':
        treads = None
    else:
        treads = Tread.objects.filter(brand_id=brand_id)

    return render(request, "tyreadderapp/options.html", {"treads": treads})


class DownloadListView(LoginRequiredMixin, ListView, FormView):
    model = Product
    template_name = 'tyreadderapp/downloads.html'
    form_class = FormatForm

    def post(self, request, **kwargs):
        format = request.POST.get('format')
        model = request.POST.get('model')
        resource = getattr(tyreadderapp_resource, model.title() + "Resource")
        dataset = resource().export()
        ds = getattr(dataset, format)
        response = HttpResponse(ds, content_type=f"{format}")
        response['Content-Disposition'] = f"attachment; filename = {model}.{format}"
        return response


class ImportView(LoginRequiredMixin, FormView):
    template_name = 'tyreadderapp/imports.html'
    form_class = ImportForm
    success_url = "imports"

    def form_valid(self, form):
        file = self.request.FILES.get("file")
        format = form.cleaned_data['format']
        model = form.cleaned_data['model']
        ds = tablib.Dataset()
        dataset = ds.load(file.read().decode('utf-8'), format=format)
        resource = getattr(tyreadderapp_resource, model.title() + "Resource")
        results = resource().import_data(dataset, dry_run=False,
                                         collect_failed_rows=True, raise_errors=True)
        response = super().form_valid(form)
        if results.has_errors():
            messages.error(self.request, "error")
        else:
            messages.error(self.request, "Success")
        return response




def add_product_images(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        files = request.FILES.getlist("image")

        for uploaded_file in files:
            # Open the uploaded image with Pillow
            img = PILImage.open(uploaded_file)

            # Auto-rotate the image based on EXIF data (this preserves orientation)
            img = ImageOps.exif_transpose(img)

            # Convert the processed image back to a file-like object
            output = io.BytesIO()

            # Save the image in the same format as the original
            format = uploaded_file.name.split('.')[-1].upper()
            if format == 'JPG':
                format = 'JPEG'

            # Save with original format and quality
            img.save(output, format=format, quality=85)
            output.seek(0)

            # Create a new InMemoryUploadedFile with the processed image
            processed_img = InMemoryUploadedFile(
                output,
                'ImageField',
                uploaded_file.name,
                uploaded_file.content_type,
                output.getbuffer().nbytes,
                None
            )

            # Save the processed image
            Image.objects.create(product_id=product_id, image=processed_img)

        messages.success(request, "Dodałeś oponę")
        return HttpResponseRedirect(request.path_info)

    return render(request, "tyreadderapp/add_product_images.html", {"product": product})


class PalletesAPIView(APIView):

    def get_object(self, pk):
        try:
            return Pallete.objects.get(pk)
        except Pallete.DoesNotExist:
            raise Http404

    def get(self, request, pk=None):
        if pk:
            pallete = self.get_object(pk)
            serializer = PalletesSerializer(pallete, many=False)
            return Response(serializer.data)
        palletes = Pallete.objects.all()
        serializer = PalletesSerializer(palletes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PalletesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'created successfully'},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        pallete = self.get_object(pk)
        serializer = PalletesSerializer(
            pallete, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        pallete = self.get_object(pk)
        serializer = PalletesSerializer(pallete, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        pallete = self.get_object(pk)
        pallete.delete()
        return Response({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


def calculate_final_price(cart, transportation_pallet=None):
    final_price = sum(item.total_price for item in cart.cartitem_set.all())
    if transportation_pallet:
        final_price += transportation_pallet.net_price
    return final_price


def get_transportation_pallet(cart):
    tire_sizes = Counter(
        item.product.size.size for item in cart.cartitem_set.all())
    max_size = max(tire_sizes.items(), key=lambda x: x[1])[0]
    tire_size = Size.objects.get(size=max_size)
    suitable_pallets = Pallete.objects.filter(
        X__gte=tire_size.width,
        Y__gte=tire_size.diameter
    ).order_by('net_price')
    if suitable_pallets:
        return suitable_pallets[0]
    return None


def apply_discounts(cart, final_price):
    # Discount for buying 2 tires
    tire_sizes = Counter(
        item.product.size.size for item in cart.cartitem_set.all())
    for size, count in tire_sizes.items():
        if count >= 2:
            size_obj = Size.objects.get(size=size)
            if (
                    count >= 2 and
                    count < size_obj.stack_quantity and
                    size_obj.stack_winner != 'odbiór_osobisty'
            ):
                discount_amount = sum(
                    item.total_price * Decimal('0.05')
                    for item in cart.cartitem_set.filter(product__size__size=size)[1:]
                )
                final_price -= discount_amount

    # Discount for filling up pallet
    for size, count in tire_sizes.items():
        size_obj = Size.objects.get(size=size)
        if count == size_obj.stack_quantity:
            transportation_pallet = get_transportation_pallet(cart)
            if transportation_pallet:
                final_price -= transportation_pallet.net_price

    # Discount for quantity of tires >= 30
    total_quantity = sum(item.quantity for item in cart.cartitem_set.all())
    if total_quantity >= 30:
        discount_amount = final_price * Decimal('0.3')
        final_price -= discount_amount

    # Discount for mix of tires
    tire_classes = Counter(
        item.product.get_tyre_class for item in cart.cartitem_set.all())
    if all(count >= 10 for count in tire_classes.values()):
        final_price *= Decimal('0.65')

    return final_price


class SummarizeTyreSizeAPIView(APIView):
    def get(self, request, cart_id):
        cart_items = CartItem.objects.filter(cart_id=cart_id)

        size_summary = defaultdict(int)
        for item in cart_items:
            tyre_size = f"{item.product.size.width}/{item.product.size.profile} R{item.product.size.diameter}"
            size_summary[tyre_size] += item.quantity

        size_summary_list = [
            {
                'tyre_size': tyre_size,
                'quantity': quantity
            }
            for tyre_size, quantity in size_summary.items()
        ]

        return JsonResponse(size_summary_list, safe=False)


class CartSummaryAPIView(APIView):
    def get(self, request, cart_id):
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            return JsonResponse({'error': 'Cart not found'}, status=404)

        transportation_pallet = get_transportation_pallet(cart)
        final_price = calculate_final_price(cart, transportation_pallet)
        final_price = apply_discounts(cart, final_price)

        response_data = {
            'cart_id': str(cart.cart_id),
            'total_price': float(final_price),
            'transportation_pallet': transportation_pallet.name if transportation_pallet else None,
            'items': [
                {
                    'product': item.product.id,
                    'brand': item.product.brand_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                }
                for item in cart.cartitem_set.all()
            ]
        }

        return JsonResponse(response_data)


class ApplyDiscountsAPIView(APIView):
    def get(self, request, cart_id):
        cart = get_object_or_404(Cart, id=cart_id)
        transportation_pallet = get_transportation_pallet(cart)
        final_price = calculate_final_price(cart, transportation_pallet)
        discounted_price = apply_discounts(cart, final_price)

        response_data = {
            'final_price': float(final_price),
            'discounted_price': float(discounted_price),
        }

        return JsonResponse(response_data)


class GetTransportationPalletAPIView(APIView):
    def get(self, request, cart_id):
        cart = get_object_or_404(Cart, id=cart_id)
        transportation_pallet = get_transportation_pallet(cart)

        if transportation_pallet:
            pallet_data = {
                'name': transportation_pallet.name,
                'net_price': float(transportation_pallet.net_price),
                'gross_price': float(transportation_pallet.gross_price),
                'mht': transportation_pallet.mht,
                'x': float(transportation_pallet.x),
                'y': float(transportation_pallet.y),
            }
            return JsonResponse(pallet_data)
        else:
            return JsonResponse({'error': 'No suitable transportation pallet found'}, status=404)


class TyreSearchView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductsSearchSerailizer

    def get_queryset(self):
        queryset = super().get_queryset()
        tread = self.request.query_params.get('tread')
        tyre_class = self.request.query_params.get('tyre_class')

        if tread and tyre_class:
            queryset = [
                product for product in queryset
                if product.tread.name == tread and str(product.get_tyre_class) == tyre_class
            ]
        elif tread:
            queryset = queryset.filter(tread__name__icontains=tread)
        elif tyre_class:
            queryset = [product for product in queryset if str(
                product.get_tyre_class) == tyre_class]

        return queryset


class TreadListView(APIView):
    def get(self, request):
        treads = Tread.objects.values_list('name', flat=True).distinct()
        return Response(treads, status=status.HTTP_200_OK)


def load_treads(request):
    brand_id = request.GET.get('brand')
    print("brand_id ::>", brand_id)
    treads = Tread.objects.filter(brand_id=brand_id).values()
    print("Filtered Treads Count:", treads.count())
    return JsonResponse(list(treads), safe=False)


class SingleTreadCreateView(LoginRequiredMixin, CreateView):
    model = Tread
    form_class = TreadForm
    template_name = "tyreadderapp/add-tread.html"
    success_url = reverse_lazy("tyreadderapp:thank-you")



def pair_search(request):
    # Fetch all products and pairs
    products = Product.objects.exclude(status='Sprzedane') \
        .order_by('brand', 'tread', 'size', 'tread_depth_min', 'tread_depth_max') \
        .prefetch_related('images')

    pairs = Pair.objects.annotate(
        product_count=Count('products'),
        name_as_int=Cast('name', IntegerField())
    ).order_by('name_as_int')

    # Additional: Only pairs with exactly 1 product
    single_product_pairs = pairs.filter(product_count=1)
    # Apply filters (if any) using ProductFilter
    filters = ProductFilter(request.GET, queryset=products)

    if request.method == 'POST':
        with transaction.atomic():  # Ensure atomicity of the database update
            for product in products:
                pair_id = request.POST.get(f'pair_{product.pk}')
                if pair_id:
                    selected_pair = get_object_or_404(Pair, pk=pair_id)
                    product.pair = selected_pair
                    product.save()
        # Refresh the page after saving
        return redirect('tyreadderapp:pair_search')

    # Process images for each product
    for product in filters.qs:
        # Get all images for the product
        images = product.images.all()
        main_image = None

        # First try to find image ending with -1 before extension
        for image in images:
            image_name = image.image.name
            if image_name.endswith('-1.jpg') or image_name.endswith('-1.jpeg') or image_name.endswith('-1.png'):
                main_image = image
                break

        # If no -1 image found, try to find the first image with the lowest number before extension
        if not main_image:
            images_with_numbers = []
            for image in images:
                image_name = image.image.name
                # Extract the number before extension
                try:
                    num = int(image_name.split('-')[-1].split('.')[0])
                    images_with_numbers.append((num, image))
                except (IndexError, ValueError):
                    continue

            if images_with_numbers:
                # Sort by the number and get the smallest
                images_with_numbers.sort(key=lambda x: x[0])
                main_image = images_with_numbers[0][1]

        # If still no main image, just take the first one
        if not main_image and images:
            main_image = images[0]

        # Add main_image to the product object
        product.main_image = main_image

    context = {
        'filters': filters,
        'pairs': pairs,
        'single_product_pairs': single_product_pairs,
    }
    return render(request, 'olx/pair/pair_search.html', context)


# def olx_advert_sync(request):
#     current_date_time = now()
#     olx_auth_data = OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)
#     if olx_auth_data.exists():
#         for data in olx_auth_data:
#             difference = (data.refresh_token_expired_time - current_date_time).days
#             if difference <= 4:
#                 return redirect("olx:update_refresh_token")
#     else:
#         return redirect("olx:update_refresh_token")
#     access_token = olx_client.get_access_token()
#     if not access_token:
#         return HttpResponse("Failed to get access token", status=500)

#     olx_response = olx_client.get_advert_list(access_token)
#     response = olx_response.json()

#     active_olx_advert_ids = set()
#     if response.get('data'):
#         for advert in response['data']:
#             olx_advert_id = advert.get('id')
#             status = advert.get('status')

#             Product.objects.filter(olx_advert_id=olx_advert_id).update(
#                 olx_advert_status=status,
#                 product_listing_status = Product.ProductStatusChoice.LISTED
#             )

#             if status == 'active':
#                 active_olx_advert_ids.add(olx_advert_id)

#         Pair.objects.filter(pair_olx_advert_id__in=active_olx_advert_ids).update(
#             pair_is_olx=True, pair_is_olx_active=True,  pair_listing_status = Pair.PairStatusChoice.LISTED
#         )

#         Product.objects.filter(olx_advert_id__in=active_olx_advert_ids).update(
#             is_olx=True, is_olx_active=True
#         )

#         Product.objects.exclude(olx_advert_id__in=active_olx_advert_ids).update(is_olx_active=False)
#         # for product in olx_add_products:
#     #     olx_client.add_advert(product,access_token)

#         return redirect("main")


# def olx_advert_sync(request):
#     current_date_time = now()
#     olx_auth_data = OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)

#     if olx_auth_data.exists():
#         for data in olx_auth_data:
#             difference = (data.refresh_token_expired_time - current_date_time).days
#             if difference <= 4:
#                 return redirect("olx:update_refresh_token")
#     else:
#         return redirect("olx:update_refresh_token")

#     # Get access token
#     access_token = olx_client.get_access_token()
#     if not access_token:
#         return HttpResponse("Failed to get access token", status=500)

#     # Fixed indentation here - this was causing issues
#     olx_response = olx_client.get_advert_list(access_token)
#     response = olx_response.json()

#     active_olx_advert_ids = set()

#     if response.get('data'):
#         for advert in response['data']:
#             olx_advert_id = advert.get('id')
#             status = advert.get('status')

#             # Update product status based on OLX advert status
#             Product.objects.filter(olx_advert_id=olx_advert_id).update(
#                 olx_advert_status=status

#             )
#             # Track active adverts
#             if status == 'active':
#                 active_olx_advert_ids.add(olx_advert_id)

#     # Update pairs with active olx adverts
#     if active_olx_advert_ids:
#         Pair.objects.filter(pair_olx_advert_id__in=active_olx_advert_ids).update(
#             pair_is_olx=True,
#             pair_is_olx_active=True,
#             pair_listing_status=Pair.PairStatusChoice.LISTED
#         )

#         # Update products with active olx adverts
#         Product.objects.filter(olx_advert_id__in=active_olx_advert_ids).update(
#             is_olx=True,
#             is_olx_active=True,
#             product_listing_status=Product.ProductStatusChoice.LISTED
#         )

#         # Update products that are not active on OLX
#         Product.objects.filter(olx_advert_id__isnull=False).exclude(
#             olx_advert_id__in=active_olx_advert_ids
#         ).update(
#             olx_advert_status="",
#             is_olx_active=False,
#             product_listing_status=Product.ProductStatusChoice.NEW
#         )

#     return redirect("main")

# def pairadverts(request):

#     current_date_time=timezone.now()
#     olx_auth_data=OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)
#     if not olx_auth_data.exists():
#         return redirect("olx:update_refresh_token")

#     # Fetch pairs with is_olx=True first
#     pairs_with_olx = Pair.objects.filter(pair_is_olx=True)
#     other_pairs = Pair.objects.exclude(pair_is_olx=True)

#     # Combine the two querysets
#     pairs = list(pairs_with_olx) + list(other_pairs)
#     pairs_with_images = []
#     for pair in pairs:
#         first_image = pair.PairImage.first()  # Use related_name if set
#         image_url = first_image.image.url if first_image else None
#         pairs_with_images.append({
#             'pair': pair,
#             'first_image_url': image_url
#         })
#     context = {
#         'pairs_with_images': pairs_with_images
#     }
#     return render(request, 'tyreadderapp/pairadverts.html', context)


def pairadverts(request):
    current_date_time = timezone.now()

    # Search query
    search_name = request.GET.get('name', '').strip()
    # olx_auth_data = OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)
    # if not olx_auth_data.exists():
    #     return redirect("olx:update_refresh_token")

    # Fetch pairs with is_olx=True and exclude blocked pairs
    pairs_with_olx = Pair.objects.filter(
        pair_is_olx=True).exclude(blocked_pair=True)
    # Fetch other pairs and exclude blocked pairs
    other_pairs = Pair.objects.exclude(
        pair_is_olx=True).exclude(blocked_pair=True)

    # Combine the two querysets
    pairs = list(pairs_with_olx) + list(other_pairs)

    # If search input exists, filter pairs by name
    if search_name:
        pairs = [pair for pair in pairs if search_name.lower()
                 in pair.name.lower()]

    # Add first image URL to each pair
    for pair in pairs:
        first_image = PairImage.objects.filter(pair=pair).last()
        pair.first_image_url = first_image.image.url if first_image else None

    context = {
        'pairs': pairs,
    }

    return render(request, 'olx/pair/pairadverts.html', context)


# def addpair_olx_bulk(request):
#     current_date_time = timezone.now()
#     olx_auth_data = OLXAuthData.objects.filter(refresh_token_expired_time__gt=current_date_time)

#     if not olx_auth_data.exists():
#         return redirect("olx:update_refresh_token")

#     if request.method == "POST":
#         selected_pair_ids = request.POST.getlist('pair_ids')
#         action_type = request.POST.get('action_type', None)  # Get the action type
#         print("===== ACTION TYPE ===== :: ",action_type)
#         if selected_pair_ids:
#             pairs_to_update = Pair.objects.filter(id__in=selected_pair_ids)
#             access_token = olx_client.get_access_token()

#             if not access_token:
#                 return HttpResponse("Failed to get access token", status=500)

#             for pair in pairs_to_update:
#                 try:
#                     if action_type == 'bulk_save_olx':
#                         # Action to add pair advert on OLX
#                         olx_client.add_pair_advert(pair, access_token)
#                     elif action_type == 'Olx_update':
#                         # Action to update pair advert on OLX
#                         olx_client.update_pair_advert(pair, access_token)
#                     elif action_type == 'Allegro':
#                         pass
#                         # Action to delete pair advert on OLX
#                         # olx_client.delete_pair_advert(pair, access_token)
#                     else:
#                         return HttpResponse("Invalid action type specified.", status=400)

#                 except Exception as e:
#                     return HttpResponse(f"Failed to process pair {pair.id}: {str(e)}", status=500)

#             return redirect('pairadverts')

#         return HttpResponse("No pairs selected.", status=400)

#     return redirect('pairadverts')


def add_pair_image(request):
    if request.method == 'POST':
        form = PairImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Redirect to a list or any other page
            return redirect('add_pair_image')
    else:
        form = PairImageForm()

    return render(request, 'tyreadderapp/add_pair_image.html', {'form': form})


# Configure logging for debugging
logger = logging.getLogger(__name__)


def image_update(request):
    if request.method == "POST":
        if 'images' in request.FILES:
            files = request.FILES.getlist('images')
            updated_products = set()

            for file in files:
                filename = file.name
                try:
                    with transaction.atomic():
                        image_obj = Image.objects.select_related(
                            'product').get(image__endswith=filename)
                        # Get the full existing image path
                        old_image_path = image_obj.image.path
                        old_image_name = os.path.basename(old_image_path)
                        # Delete the old image file if it exists
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                        else:
                            pass
                        image_obj.image.save(old_image_name, file, save=True)

                        product = image_obj.product
                        product.image_update_status = True
                        product.save()

                        updated_products.add(product.id)

                except Image.DoesNotExist:
                    continue
                except Exception as e:
                    continue

            if updated_products:
                return redirect("tyreadderapp:main")

            return HttpResponse("No matching products found for the uploaded images.")

        # Handle ZIP download (unchanged)
        product_ids = request.POST.getlist('products')
        images = Image.objects.filter(product_id__in=product_ids)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for img in images:
                file_path = img.image.path
                zip_file.write(file_path, os.path.basename(file_path))
        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="images.zip"'
        return response

    # products = Product.objects.all().order_by('-image_update_status').prefetch_related('images')
    products = Product.objects.all().order_by('id').prefetch_related('images')
    # Add main image to each product, following the logic from workspace view
    for product in products:
        # Get all images for the product
        images = product.images.all()
        main_image = None

        # First try to find image ending with -1 before extension
        for image in images:
            image_name = image.image.name
            if image_name.endswith('-1.jpg') or image_name.endswith('-1.jpeg') or image_name.endswith('-1.png'):
                main_image = image
                break

        # If no -1 image found, try to find the first image with the lowest number before extension
        if not main_image:
            images_with_numbers = []
            for image in images:
                image_name = image.image.name
                # Extract the number before extension
                try:
                    num = int(image_name.split('-')[-1].split('.')[0])
                    images_with_numbers.append((num, image))
                except (IndexError, ValueError):
                    continue

            if images_with_numbers:
                # Sort by the number and get the smallest
                images_with_numbers.sort(key=lambda x: x[0])
                main_image = images_with_numbers[0][1]

        # If still no main image, just take the first one
        if not main_image and images:
            main_image = images[0]

        # Add main_image to the product object
        product.main_image = main_image

    return render(request, 'tyreadderapp/image_update.html', {'products': products})


def filter_on_sale(request):
    # products_on_sale = Product.objects.filter(
    #     status=Product.StatusChoices.ON_SALE).order_by('-created').prefetch_related('images')
    
    products_on_sale = (
    Product.objects
    .filter(status=Product.StatusChoices.ON_SALE)
    .select_related("pair", "warehouse", "rack", "row")
    .prefetch_related("images")
)
    
    # 🔹 Annotate tread_remaining_percent so we can filter & sort in the DB
    products_on_sale = products_on_sale.annotate(
        tread_remaining_percent=Case(
            # Only calculate if new_tire_tread_depth and tread_depth_min exist and are > 0
            When(
                new_tire_tread_depth__isnull=False,
                tread_depth_min__isnull=False,
                new_tire_tread_depth__gt=0,
                then=ExpressionWrapper(
                    100.0 * F('tread_depth_min') / F('new_tire_tread_depth'),
                    output_field=FloatField()
                )
            ),
            default=Value(None),
            output_field=FloatField()
        )
    )
    
    form = ProductSearchForm(request.GET or None)
    
    if form.is_valid():
        if form.cleaned_data.get("product_id"):
            products_on_sale = products_on_sale.filter(id=form.cleaned_data["product_id"])
        
        if form.cleaned_data.get("brand"):
            products_on_sale = products_on_sale.filter(brand__name__icontains=form.cleaned_data["brand"])
        
        if form.cleaned_data.get("tread"):
            products_on_sale = products_on_sale.filter(tread__name__icontains=form.cleaned_data["tread"])
        
        if form.cleaned_data.get("size"):
            products_on_sale = products_on_sale.filter(size__size__icontains=form.cleaned_data["size"])
        
            # NEW: Tread type filters
        if form.cleaned_data.get("is_steer"):
            products_on_sale = products_on_sale.filter(tread__is_steer=True)
            
        if form.cleaned_data.get("is_drive"):
            products_on_sale = products_on_sale.filter(tread__is_drive=True)
            
        if form.cleaned_data.get("is_trailer"):
            products_on_sale = products_on_sale.filter(tread__is_trailer=True)
        
        if form.cleaned_data.get("pair_name"):
            products_on_sale = products_on_sale.filter(pair__name__icontains=form.cleaned_data["pair_name"])
        
        if form.cleaned_data.get("only_pairs"):
            products_on_sale = products_on_sale.filter(pair__name__isnull=False)
            
        if form.cleaned_data.get("no_side_repairs"):
            products_on_sale = products_on_sale.filter(is_side_repair=False)
        
        if form.cleaned_data.get("no_incised"):
            products_on_sale = products_on_sale.filter(is_incised=False)
        
        if form.cleaned_data.get("no_retreaded"):
            products_on_sale = products_on_sale.filter(is_retreaded=False)
        
        if form.cleaned_data.get("only_retreaded"):
            products_on_sale = products_on_sale.filter(is_retreaded=True)
        
        if form.cleaned_data.get("is_brand_new_price"):
            products_on_sale = products_on_sale.filter(new_tire_price__isnull=False)
        
        if form.cleaned_data.get("is_brand_new_tread"):
            products_on_sale = products_on_sale.filter(new_tire_tread_depth__isnull=False)       
            
        
        min_percent = form.cleaned_data.get("tread_remaining_min")
        if min_percent is not None:
            products_on_sale = products_on_sale.filter(tread_remaining_percent__gte=min_percent)

        max_percent = form.cleaned_data.get("tread_remaining_max")
        if max_percent is not None:
            products_on_sale = products_on_sale.filter(tread_remaining_percent__lte=max_percent)
                     
            
            
    
    # 🔥 SORTING
    sort = request.GET.get("sort")

    # Default fallback: sort by created
    ordering = ["-created"]

    if sort == "pair_asc":
        ordering = [
            Case(
                When(pair__isnull=True, then=Value(1)),  # no pair → last
                When(pair__name="", then=Value(1)),      # empty name → treat as no pair
                default=Value(0),                        # has pair → first
                output_field=IntegerField(),
            ),
            "pair__name"  # A → Z
        ]
    elif sort == "pair_desc":
        ordering = [
            Case(
                When(pair__isnull=True, then=Value(1)),  # no pair → last
                When(pair__name="", then=Value(1)),      # empty name → treat as no pair
                default=Value(0),                        # has pair → first
                output_field=IntegerField(),
            ),
            F("pair__name").desc()  # Z → A
        ]

    elif sort == "price_asc":
        ordering = ["net_price"]
    elif sort == "price_desc":
        ordering = ["-net_price"]
    
    # Apply the ordering once, before pagination
    products_on_sale = products_on_sale.order_by(*ordering)   

    

    paginator = Paginator(products_on_sale, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    for product in page_obj:
        product.main_image = product.images.filter(
            image__icontains='-1.jpg').first()
        warehouse = product.warehouse
        if warehouse:
            product.warehouse_name = warehouse.name
        else:
            product.warehouse_name = "Brak magazynu"
            
        rack = product.rack
        if rack:
            product.rack_name = rack.code
        else:
            product.rack_name = "Brak regału"
        row = product.row
        if row:
            product.row_name = row.code
        else:           
            product.row_name = "Brak rzędu"
        
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_params.pop('sort', None) 
            
    return render(request, 'tyreadderapp/statuses/filter_on_sale.html', {
        'page_obj': page_obj,
        'form': form,
        'status_choices': Product.StatusChoices.choices,
        'query_string': query_params.urlencode(),
        'current_sort': sort,
    })




def filter_to_sold(request):
    products_sold = (
        Product.objects
        .filter(status=Product.StatusChoices.SOLD)
        .order_by('-sold_at')
        .prefetch_related('images')
    )
    
    form = ProductSearchForm(request.GET or None)
    
    if form.is_valid():
        if form.cleaned_data.get("product_id"):
            products_sold = products_sold.filter(id=form.cleaned_data["product_id"])
        
        if form.cleaned_data.get("brand"):
            products_sold = products_sold.filter(brand__name__icontains=form.cleaned_data["brand"])
        
        if form.cleaned_data.get("tread"):
            products_sold = products_sold.filter(tread__name__icontains=form.cleaned_data["tread"])
        
        if form.cleaned_data.get("size"):
            products_sold = products_sold.filter(size__size__icontains=form.cleaned_data["size"])
            

    paginator = Paginator(products_sold, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    

    for product in page_obj:
        product.main_image = product.images.filter(
            image__icontains='-1.jpg'
        ).first()
        
        if product.sold_at:
            if timezone.is_naive(product.sold_at):
                product.sold_at_local = timezone.make_aware(
                    product.sold_at,
                    timezone.get_current_timezone()
                )
            else:
                product.sold_at_local = timezone.localtime(product.sold_at)
        else:
            product.sold_at_local = None
    
    query_params = request.GET.copy()
    query_params.pop('page', None)

    return render(
        request,
        'tyreadderapp/statuses/filter_sold.html',
        {
            'page_obj': page_obj,
            'form': form,
            'status_choices': Product.StatusChoices.choices,
            'query_string': query_params.urlencode(),
        }
    )


def filter_to_add(request):
    products_to_add = Product.objects.filter(
        status=Product.StatusChoices.TO_ADD).order_by('id').prefetch_related('images')
    for product in products_to_add:
        product.main_image = product.images.filter(
            image__icontains='-1.jpg').first()
    return render(request, 'tyreadderapp/statuses/filter_to_add.html', {'products': products_to_add})


def update_product_status(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        new_status = request.POST.get("status")
        if new_status in dict(Product.StatusChoices.choices):
            product.status = new_status
            product.save()
            return JsonResponse({"success": True, "new_status": product.status})
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


# views.py


@csrf_exempt  # if you use CSRF tokens in AJAX, you can remove this
@require_POST
@login_required
def bulk_update_status(request):
    """
    Updates status of multiple products based on POSTed IDs and new status.
    """
    product_ids = request.POST.get("product_ids", "")
    new_status = request.POST.get("status", "").strip()

    if not product_ids or not new_status:
        return JsonResponse({"success": False, "error": "Missing product IDs or status."})

    id_list = [int(pid) for pid in product_ids.split(",") if pid.isdigit()]

    updated_ids = []
    for product_id in id_list:
        try:
            product = Product.objects.get(id=product_id)
            product.change_status(new_status, user=request.user)
            updated_ids.append(product_id)
        except Product.DoesNotExist:
            continue  # Skip invalid IDs

    if updated_ids:
        return JsonResponse({"success": True, "updated_ids": updated_ids})
    else:
        return JsonResponse({"success": False, "error": "No valid products found."})


# def bulk_create_otomoto_ads(request):
#     if request.method == "POST":
#         product_ids = request.POST.get("product_ids", "")
#         product_ids = [int(pk) for pk in product_ids.split(",") if pk.isdigit()]

#         if not product_ids:
#             return JsonResponse({"success": False, "error": "No product IDs"})

#         # Bulk update
#         Product.objects.filter(id__in=product_ids).update(is_otomoto_advert_created=True)

#         return JsonResponse({"success": True})

#     return JsonResponse({"success": False, "error": "Invalid method"})

def bulk_create_otomoto_ads(request):
    if request.method == "POST":
        product_ids = request.POST.get("product_ids", "")
        product_ids = [int(pk)
                       for pk in product_ids.split(",") if pk.isdigit()]

        if not product_ids:
            return JsonResponse({"success": False, "error": "No product IDs"})

        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            product.is_otomoto_advert_created = True
            product.save()   # 🔥 TRIGGERS THE SIGNAL

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid method"})


def load_ean_data(request):
    static_folder = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'static')
    json_file_path = os.path.join(static_folder, 'json/EAN.json')
    if not os.path.exists(json_file_path):
        return JsonResponse({"error": "JSON file not found in static directory."}, status=404)
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)
    created, updated = 0, 0
    for item in data:
        ean, created_flag = Tyre_Ean.objects.update_or_create(
            ean=item["EAN"],
            defaults={
                "ean_brand": item["Brand"],
                "ean_tread": item["Tread"],
                "ean_width": item["Width"],
                "ean_profile": item.get("Profile"),
                "ean_diameter": item["Diameter"],
                "ean_size": item["Size"],
                "ean_li": item["LI"],
                "ean_si": item["SI"],
            },
        )
        if created_flag:
            created += 1
        else:
            updated += 1
    return JsonResponse({
        "message": "Data loaded successfully.",
        "created_records": created,
        "updated_records": updated,
    })


def payment_dashboard(request):
    # Get all orders with payment_status = "paid"
    paid_orders = Order.objects.filter(
        payment_status="paid").order_by('-created_at')
    dashboard_data = []

    for order in paid_orders:
        # Split customer name into first and last name if available
        name_parts = order.customer_name.split(
        ) if order.customer_name else ['', '']
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        # Extract pallet information from the JSONField
        pallets = []
        if order.pallet_type and isinstance(order.pallet_type, dict):
            # If it's formatted as in your example with "pallets" key
            if "pallets" in order.pallet_type:
                for pallet in order.pallet_type["pallets"]:
                    # Extract individual tyre details including ID and size
                    tyres = []
                    if "items" in pallet:
                        for item in pallet["items"]:
                            tyre_id = item.get("id", "")
                            size = item.get("size", "")
                            if tyre_id and size:
                                tyres.append(f"ID: {tyre_id}, Size: {size}")

                    pallets.append({
                        'pallet_number': pallet.get('pallet_number', ''),
                        'pal_type': pallet.get('pal_type', ''),
                        'position': pallet.get('position', ''),
                        'courier': pallet.get('courier', ''),
                        'tyres': tyres,
                        'items_quantity': pallet.get('items_quantity', 0)
                    })
            # If it's directly pallet data without the "pallets" key (handle alternative format)
            else:
                for pallet_key, pallet_info in order.pallet_type.items():
                    if isinstance(pallet_info, dict):
                        tyres = []
                        if "items" in pallet_info:
                            for item in pallet_info.get("items", []):
                                tyre_id = item.get("id", "")
                                size = item.get("size", "")
                                if tyre_id and size:
                                    tyres.append(
                                        f"ID: {tyre_id}, Size: {size}")

                        pallets.append({
                            'pallet_number': pallet_info.get('pallet_number', pallet_key),
                            'pal_type': pallet_info.get('pal_type', ''),
                            'position': pallet_info.get('position', ''),
                            'courier': pallet_info.get('courier', ''),
                            'tyres': tyres,
                            'items_quantity': len(pallet_info.get('items', [])) if 'items' in pallet_info else 0
                        })

        # Create order data dictionary
        order_data = {
            'order_id': order.id,
            'date': order.created_at,
            'first_name': first_name,
            'last_name': last_name,
            'email': order.customer_email or '',
            'mobile': order.customer_phone,
            'self_pickup': False,
            'delivery_street': order.delivery_street or '',
            'delivery_apartment': order.delivery_apartment or '',
            'delivery_zip_code': order.delivery_zip_code or '',
            'delivery_city': order.delivery_city or '',
            'pallets': pallets,
            'is_completed': order.is_completed,
        }

        dashboard_data.append(order_data)

    return render(request, 'tyreadderapp/payment_dashboard.html', {'dashboard_data': dashboard_data})


# from django.shortcuts import render, get_object_or_404, redirect


# def payment_detail_view(request, order_id):
#     order = get_object_or_404(Order, id=order_id, payment_status="paid")

#     if request.method == "POST":
#         action = request.POST.get("action")  # Get which button was clicked

#         if action == "update_completion":
#             # Only update is_completed if this button was pressed
#             is_completed = request.POST.get('is_completed') == 'true' or request.POST.get('is_completed') == 'on'
#             if is_completed != order.is_completed:  # Only save if changed
#                 order.is_completed = is_completed
#                 order.save()
#                 if is_completed:
#                     # Remove products from warehouse/row/rack/staple
#                     removed_products = Product.objects.filter(order_items__order=order)
#                     if removed_products.exists():
#                         removed_products.update(warehouse=None, row=None, rack=None, staple=None)

#         elif action == "print_order":
#             pass

#     # --- Prepare context for GET and after POST
#     name_parts = order.customer_name.split() if order.customer_name else ['', '']
#     first_name = name_parts[0] if name_parts else ''
#     last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

#     pallets = []
#     if order.pallet_type and isinstance(order.pallet_type, dict):
#         if "pallets" in order.pallet_type:
#             for pallet in order.pallet_type["pallets"]:
#                 tyres = []
#                 if "items" in pallet:
#                     for item in pallet["items"]:
#                         tyre_id = item.get("id", "")
#                         size = item.get("size", "")

#                         if tyre_id and size:
#                             tyres.append(f"ID: {tyre_id}, Size: {size}")
#                 pallets.append({
#                     'pallet_number': pallet.get('pallet_number', ''),
#                     'pal_type': pallet.get('pal_type', ''),
#                     'position': pallet.get('position', ''),
#                     'courier': pallet.get('courier', ''),
#                     'tyres': tyres,
#                     'items_quantity': pallet.get('items_quantity', 0),

#                 })
#         else:
#             for pallet_key, pallet_info in order.pallet_type.items():
#                 if isinstance(pallet_info, dict):
#                     tyres = []
#                     if "items" in pallet_info:
#                         for item in pallet_info.get("items", []):
#                             tyre_id = item.get("id", "")
#                             size = item.get("size", "")
#                             if tyre_id and size:
#                                 tyres.append(f"ID: {tyre_id}, Size: {size}")
#                     pallets.append({
#                         'pallet_number': pallet_info.get('pallet_number', pallet_key),
#                         'pal_type': pallet_info.get('pal_type', ''),
#                         'position': pallet_info.get('position', ''),
#                         'courier': pallet_info.get('courier', ''),
#                         'tyres': tyres,
#                         'items_quantity': len(pallet_info.get('items', [])) if 'items' in pallet_info else 0
#                     })

#     context = {
#         'order_id': order.id,
#         'date': order.created_at,
#         'first_name': first_name,
#         'last_name': last_name,
#         'email': order.customer_email or '',
#         'mobile': order.customer_phone,
#         'self_pickup': False,
#         'delivery_street': order.delivery_street or '',
#         'delivery_apartment': order.delivery_apartment or '',
#         'delivery_zip_code': order.delivery_zip_code or '',
#         'delivery_city': order.delivery_city or '',
#         'pallets': pallets,
#         'is_completed': order.is_completed,
#     }

#     return render(request, 'tyreadderapp/payment_detail.html', context)

def payment_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, payment_status="paid")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_completion":
            is_completed = request.POST.get('is_completed') in ['true', 'on']
            if is_completed != order.is_completed:
                order.is_completed = is_completed
                order.save()
                if is_completed:
                    # Remove product warehouse info
                    removed_products = Product.objects.filter(
                        order_items__order=order)
                    if removed_products.exists():
                        removed_products.update(
                            warehouse=None, row=None, rack=None, staple=None)

        elif action == "print_order":
            pass

    # Split customer name
    name_parts = order.customer_name.split(
    ) if order.customer_name else ['', '']
    first_name = name_parts[0] if name_parts else ''
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

    # Pallet logic (unchanged)
    pallets = []
    if order.pallet_type and isinstance(order.pallet_type, dict):
        if "pallets" in order.pallet_type:
            for pallet in order.pallet_type["pallets"]:
                tyres = []
                if "items" in pallet:
                    for item in pallet["items"]:
                        tyre_id = item.get("id", "")
                        size = item.get("size", "")
                        if tyre_id and size:
                            tyres.append(f"ID: {tyre_id}, Size: {size}")
                pallets.append({
                    'pallet_number': pallet.get('pallet_number', ''),
                    'pal_type': pallet.get('pal_type', ''),
                    'position': pallet.get('position', ''),
                    'courier': pallet.get('courier', ''),
                    'tyres': tyres,
                    'items_quantity': pallet.get('items_quantity', 0),
                })
        else:
            for pallet_key, pallet_info in order.pallet_type.items():
                if isinstance(pallet_info, dict):
                    tyres = []
                    if "items" in pallet_info:
                        for item in pallet_info.get("items", []):
                            tyre_id = item.get("id", "")
                            size = item.get("size", "")
                            if tyre_id and size:
                                tyres.append(f"ID: {tyre_id}, Size: {size}")
                    pallets.append({
                        'pallet_number': pallet_info.get('pallet_number', pallet_key),
                        'pal_type': pallet_info.get('pal_type', ''),
                        'position': pallet_info.get('position', ''),
                        'courier': pallet_info.get('courier', ''),
                        'tyres': tyres,
                        'items_quantity': len(pallet_info.get('items', [])) if 'items' in pallet_info else 0
                    })

    # 🔹 Add product location info here
    order_products = []
    for item in order.items.select_related('product__warehouse', 'product__row', 'product__rack', 'product__staple').order_by('product__warehouse__name'):
        product = item.product
        order_products.append({
            'id': product.id,
            'brand': product.brand.name,
            'tread': product.tread.name,
            'size': product.size.size if product.size else '',
            'warehouse': product.warehouse.name if product.warehouse else 'N/A',
            'row': product.row.code if product.row else 'N/A',
            'rack': product.rack.code if product.rack else 'N/A',
            'staple': product.staple.code if product.staple else 'N/A',
        })

    context = {
        'order': order,
        'order_id': order.id,
        'date': order.created_at,
        'first_name': first_name,
        'last_name': last_name,
        'email': order.customer_email or '',
        'mobile': order.customer_phone,
        'self_pickup': False,
        'delivery_street': order.delivery_street or '',
        'delivery_apartment': order.delivery_apartment or '',
        'delivery_zip_code': order.delivery_zip_code or '',
        'delivery_city': order.delivery_city or '',
        'delivery_phone': order.delivery_phone or '',
        'pallets': pallets,
        'is_completed': order.is_completed,
        'order_products': order_products,  # 👈 add this
    }

    return render(request, 'tyreadderapp/payment_detail.html', context)


def get_tires_by_size(request):
    # Get size parameter from URL
    search_size = request.GET.get('size')

    # Base query
    query = Product.objects.filter(size__size=search_size)

    # Get the counts
    tire_counts = query.values(
        'size__size',
        'size__width',
        'size__profile',
        'size__diameter',
        'brand__name'
    ).annotate(
        total_tires=Count('id')
    ).order_by('size__size', 'brand__name')

    # Format the response
    result = {
        'sizes': [
            {
                'size': item['size__size'],
                'dimensions': {
                    'width': item['size__width'],
                    'profile': item['size__profile'],
                    'diameter': float(item['size__diameter'])
                },
                'quantity': item['total_tires'],
                'brand': item['brand__name']
            }
            for item in tire_counts if item['size__size'] is not None
        ]
    }

    return JsonResponse(result)


@require_POST
def merge_pair_images(request):
    pair_id = request.POST.get('pair_id')
    try:
        pair = Pair.objects.get(id=pair_id)
        new_image = pair.process_and_save_pair_image()
        if new_image:
            return JsonResponse({
                'success': True,
                'message': 'Images merged successfully',
                'image_url': new_image.image.url
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No images available to merge'
            })

    except Pair.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pair not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


def payu_payment_dashboard(request):

    success_orders = Order.objects.filter(
        Q(payment_status__in=["paid", "fulfilled"]) & Q(payment_status="paid")
    )

    pending_orders = Order.objects.filter(
        Q(payment_status="pending") | Q(
            payment_status__in=["pending", "processing"])
    )

    failed_orders = Order.objects.filter(
        Q(payment_status="cancelled") | Q(payment_status="cancelled")
    )

    context = {
        "success_orders": success_orders,
        "pending_orders": pending_orders,
        "failed_orders": failed_orders,
    }

    return render(request, "tyreadderapp/payu_payment_dashboard.html", context)


class SizeDetailApiView(APIView):
    def get(self, request, slug):
        try:
            size = Size.objects.get(slug=slug)
        except Size.DoesNotExist:
            return Response({'error': 'Size not found'}, status=404)

        products = size.product_set.select_related(
            'brand', 'tread', 'size').prefetch_related('images').all()

        data = {
            'size': size.size,
            'description': size.description,
            'tyres': [
                {
                    'id': p.id,
                    'brand_name': p.brand.name,
                    'tread_name': p.tread.name,
                    'size_text': p.size.size if p.size else None,
                    'dot': p.dot,
                    'tread_depth_min': p.tread_depth_min,
                    'tread_depth_max': p.tread_depth_max,
                    'net_price': str(p.net_price) if p.net_price else None,
                    'image': request.build_absolute_uri(p.images.first().image.url) if p.images.exists() and p.images.first().image else None
                }
                for p in products
            ]
        }
        return Response(data)


class TyreSizeListAPIView(APIView):
    def get(self, request):
        sizes = Size.objects.all()
        serializer = TyreSizeListSerializer(
            sizes, many=True, context={'request': request})
        return Response(serializer.data)


def similar_tread_dashboard(request):
    brands = Brand.objects.all().order_by('name')
    treads = Tread.objects.all().order_by('name')
    similar_treads = SimilarTread.objects.all()

    if request.method == "POST":
        brand_id = request.POST.get('brand')
        tread_id = request.POST.get('tread')
        selected_treads = request.POST.getlist('similar_treads')

        brand = get_object_or_404(Brand, id=brand_id)
        tread = get_object_or_404(Tread, id=tread_id)

        obj, created = SimilarTread.objects.get_or_create(
            brand=brand, tread=tread)
        obj.similar_tread_combinations.clear()
        obj.similar_tread_combinations.add(
            *SimilarTread.objects.filter(id__in=selected_treads))

        return redirect('tyreadderapp:similar_tread_dashboard')

    return render(request, 'tyreadderapp/similar_tread_dashboard.html', {
        'brands': brands,
        'treads': treads,
        'similar_treads': similar_treads
    })


def get_treads(request, brand_id):
    print("---brand_id---->>>", brand_id)
    treads = Tread.objects.filter(brand_id=brand_id).order_by('name')
    tread_list = [{"id": t.id, "name": t.name} for t in treads]
    return JsonResponse(tread_list, safe=False)


# views.py


def prospects_for_pairs(request):
    # Handle saving pair assignments on POST
    if request.method == 'POST':
        with transaction.atomic():
            all_products = Product.objects.filter(
                status__in=[
                    Product.StatusChoices.TO_ADD,
                    Product.StatusChoices.ON_SALE
                ]
            )
            for product in all_products:
                pair_id = request.POST.get(f'pair_{product.pk}')
                if pair_id:
                    selected_pair = get_object_or_404(Pair, pk=pair_id)
                    product.pair = selected_pair
                    product.save()
        # Replace with your actual URL name
        return redirect('tyreadderapp:prospects_for_pairs')

    # Time threshold: 5 days ago
    recent_threshold = now() - timedelta(days=5)

    # Filter products by status
    filtered_products = Product.objects.filter(
        status__in=[
            Product.StatusChoices.TO_ADD,
            Product.StatusChoices.ON_SALE
        ]
    )

    # Group by brand, tread, and size
    grouped_qs = (
        filtered_products
        .values('brand', 'brand__name', 'tread', 'tread__name', 'size')
        .annotate(
            total_count=Count('id'),
            unpaired_count=Count('id', filter=Q(pair__isnull=True))
        )
        .filter(total_count__gt=1, unpaired_count__gte=1)
        .order_by('brand__name', 'tread__name', 'size')
    )

    grouped_data = []

    for group in grouped_qs:
        products = (
            filtered_products
            .filter(
                brand=group['brand'],
                tread=group['tread'],
                size=group['size']

            )
            .select_related('brand', 'tread', 'size', 'pair')
            .prefetch_related('images')
            .order_by('pair__name')
        )

        # Check if any product in this group is newer than 5 days
        has_recent_product = products.filter(
            created__gte=recent_threshold).exists()

        for product in products:
            product.main_image = product.images.filter(
                image__icontains='-1.jpg').first()

        grouped_data.append({
            'brand': {'id': group['brand'], 'name': group['brand__name']},
            'tread': {'id': group['tread'], 'name': group['tread__name']},
            'size': group['size'],
            'total_count': group['total_count'],
            'unpaired_count': group['unpaired_count'],
            'products': products,
            'has_recent_product': has_recent_product,  # used for sorting
        })

    # Sort so groups with recent products are placed at the bottom
    grouped_data.sort(key=lambda g: g['has_recent_product'])

    # Get all pairs to populate the dropdowns
    pairs = Pair.objects.annotate(
        product_count=Count('products'),
        name_as_int=Cast('name', IntegerField())
    ).order_by('name_as_int')

    return render(request, 'tyreadderapp/prospects_for_pairs.html', {
        'groups': grouped_data,
        'pairs': pairs,
    })


def product_tread_depth_combinations(request):
    seen_combinations = set()
    with_depth = []
    without_depth = []

    products = Product.objects.select_related('brand', 'tread', 'size')

    # Preload all tread depth records
    td_records = list(New_Tread_Depth.objects.all())

    # Prepare a fast-lookup dictionary with normalized keys
    td_lookup = {}
    for td in td_records:
        brand = (td.brand or "").strip().lower().replace(
            " ", "").replace("-", "")
        tread = (td.tread or "").strip().lower().replace(
            " ", "").replace("-", "")
        size = td.size.strip() if td.size else ""
        key = (brand, tread, size)
        td_lookup[key] = td

    for product in products:
        if not product.brand or not product.tread or not product.size:
            continue  # skip incomplete entries

        brand_raw = product.brand.name
        tread_raw = product.tread.name
        size_raw = product.size.size

        brand_key = brand_raw.strip().lower().replace(" ", "").replace("-", "")
        tread_key = tread_raw.strip().lower().replace(" ", "").replace("-", "")
        size_key = size_raw.strip()

        key = (brand_key, tread_key, size_key)

        if key in seen_combinations:
            continue
        seen_combinations.add(key)

        matching_td = td_lookup.get(key)

        if matching_td and matching_td.new_tire_tread_depth is not None:
            with_depth.append({
                'brand': brand_raw,
                'tread': tread_raw,
                'size': size_raw,
                'depth': matching_td.new_tire_tread_depth
            })
        else:
            without_depth.append({
                'brand': brand_raw,
                'tread': tread_raw,
                'size': size_raw
            })

    # ✅ Sort results
    with_depth = sorted(with_depth, key=lambda x: (
        x['brand'].lower(), x['tread'].lower(), x['size']))
    without_depth = sorted(without_depth, key=lambda x: (
        x['brand'].lower(), x['tread'].lower(), x['size']))

    context = {
        'with_depth': with_depth,
        'without_depth': without_depth,
    }

    return render(request, 'tyreadderapp/tread_depth_combinations.html', context)


def warehouse_list_view(request):
    warehouses = Warehouse.objects.prefetch_related(
        'rows__products__brand', 'rows__products__size'
    ).order_by('name', 'location')

    return render(request, 'tyreadderapp/warehouse_list.html', {
        'warehouses': warehouses
    })


def warehouse_detail_view(request, warehouse_id):
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    ProductFormSet = modelformset_factory(Product, form=ProductForm, extra=5)

    if request.method == 'POST':
        formset = ProductFormSet(request.POST, queryset=Product.objects.none())
        if formset.is_valid():
            products = formset.save(commit=False)
            for product in products:
                product.warehouse = warehouse
                product.save()
            return redirect('tyreadderapp:warehouse_detail', warehouse_id=warehouse.id)
    else:
        formset = ProductFormSet(queryset=Product.objects.none())

    existing_products = Product.objects.filter(warehouse=warehouse)

    return render(request, 'tyreadderapp/warehouse_detail.html', {
        'warehouse': warehouse,
        'formset': formset,
        'existing_products': existing_products,
    })


def assign_product_location_view(request):
    updated_products = None

    if request.method == 'POST':
        form = ProductLocationAssignmentForm(request.POST)
        if form.is_valid():
            updated_products = form.save()
            form = ProductLocationAssignmentForm()
    else:
        form = ProductLocationAssignmentForm()

    return render(request, 'tyreadderapp/assign_location_form.html', {
        'form': form,
        'updated_products': updated_products
    })


def product_ean_combinations(request):
    seen_combinations = set()
    with_ean = []
    without_ean = []

    products = Product.objects.select_related('brand', 'tread', 'size')

    for product in products:
        if not product.brand or not product.tread or not product.size:
            continue  # skip incomplete entries

        brand_raw = product.brand.name
        tread_raw = product.tread.name
        size_raw = product.size.size
        ean_raw = product.ean
        id_raw = product.id

        brand_key = brand_raw.strip().lower().replace(" ", "").replace("-", "")
        tread_key = tread_raw.strip().lower().replace(" ", "").replace("-", "")
        size_key = size_raw.strip()

        key = (brand_key, tread_key, size_key)

        if key in seen_combinations:
            continue
        seen_combinations.add(key)

        if ean_raw:
            with_ean.append({
                'id': id_raw,
                'brand': brand_raw,
                'tread': tread_raw,
                'size': size_raw,
                'ean': ean_raw
            })
        else:
            without_ean.append({
                'id': id_raw,
                'brand': brand_raw,
                'tread': tread_raw,
                'size': size_raw
            })

    # Sort results
    with_ean = sorted(with_ean, key=lambda x: (
        x['brand'].lower(), x['tread'].lower(), x['size']))
    without_ean = sorted(without_ean, key=lambda x: (
        x['brand'].lower(), x['tread'].lower(), x['size']))

    context = {
        'with_ean': with_ean,
        'without_ean': without_ean,
    }

    return render(request, 'tyreadderapp/ean_combinations.html', context)


def load_location_data(request):
    warehouse_id = request.GET.get('warehouse')

    # Filter based on selected warehouse
    rows = Row.objects.filter(warehouse_id=warehouse_id)
    racks = Rack.objects.filter(warehouse_id=warehouse_id)
    staples = Staple.objects.filter(warehouse_id=warehouse_id)

    # Prepare data to send back as JSON
    data = {
        'rows': [{'id': row.id, 'code': row.code} for row in rows],
        'racks': [{'id': rack.id, 'code': rack.code} for rack in racks],
        'staples': [{'id': staple.id, 'code': staple.code} for staple in staples],
    }

    return JsonResponse(data)


def create_staple_view(request):
    if request.method == 'POST':
        form = StapleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tyreadderapp:create_staple')
    else:
        form = StapleForm()

    staples = Staple.objects.all().order_by('-id')
    return render(request, 'tyreadderapp/create_staple.html', {'form': form, 'staples': staples})


def delete_staple_view(request, pk):
    staple = get_object_or_404(Staple, pk=pk)
    if request.method == 'POST':
        staple.delete()
        return redirect('tyreadderapp:create_staple')
    return render(request, 'tyreadderapp/confirm_delete_staple.html', {'staple': staple})


def print_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # --- Build order_products like in payment_detail_view ---
    order_products = []
    for item in order.items.select_related('product__warehouse', 'product__row', 'product__rack', 'product__staple').order_by('product__warehouse__name'):
        product = item.product
        order_products.append({
            'id': product.id,
            'brand': product.brand.name if product.brand else '',
            'tread': product.tread.name if product.tread else '',
            'size': product.size.size if product.size else '',
            'warehouse': product.warehouse.name if product.warehouse else 'N/A',
            'row': product.row.code if product.row else 'N/A',
            'rack': product.rack.code if product.rack else 'N/A',
            'staple': product.staple.code if product.staple else 'N/A',
        })

    # --- Build pallets (same as payment_detail_view) ---
    pallets = []
    if order.pallet_type and isinstance(order.pallet_type, dict):
        if "pallets" in order.pallet_type:
            for pallet in order.pallet_type["pallets"]:
                tyres = []
                if "items" in pallet:
                    for item in pallet["items"]:
                        tyre_id = item.get("id", "")
                        size = item.get("size", "")
                        if tyre_id and size:
                            tyres.append(f"ID: {tyre_id}, Size: {size}")
                pallets.append({
                    'pallet_number': pallet.get('pallet_number', ''),
                    'pal_type': pallet.get('pal_type', ''),
                    'position': pallet.get('position', ''),
                    'courier': pallet.get('courier', ''),
                    'tyres': tyres,
                    'items_quantity': pallet.get('items_quantity', 0),
                })

    # --- Render to HTML and convert to PDF ---
    html_string = render_to_string('tyreadderapp/order_print.html', {
        'order_id': order.id,
        'first_name': order.customer_name.split()[0] if order.customer_name else '',
        'last_name': ' '.join(order.customer_name.split()[1:]) if order.customer_name else '',
        'email': order.customer_email,
        'mobile': order.customer_phone,
        'delivery_street': order.delivery_street,
        'delivery_apartment': order.delivery_apartment,
        'delivery_zip_code': order.delivery_zip_code,
        'delivery_city': order.delivery_city,
        'delivery_phone': order.delivery_phone,
        'date': order.created_at,
        'is_completed': order.is_completed,
        'order_products': order_products,
        'pallets': pallets,
        'summary_of_order': {
            'tyres_qty': sum(p['items_quantity'] for p in pallets)
        },
        'self_pickup': False,
    })

    # --- Create PDF response ---
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="order_{order.id}.pdf"'

    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        HTML(string=html_string, base_url=request.build_absolute_uri()
             ).write_pdf(tmp.name)
        tmp.seek(0)
        response.write(tmp.read())

    return response


# BULK SINGLE SALE VIEW

# views.py


def update_product_status(request):
    if request.method == "POST":
        form = ProductStatusForm(request.POST)
        if form.is_valid():
            updated_qs = form.save()
            messages.success(
                request,
                f"Successfully updated status for {updated_qs.count()} product(s)."
            )
            return redirect("tyreadderapp:update-items-status")
    else:
        form = ProductStatusForm()

    return render(request, "tyreadderapp/update_product_status.html", {
        "form": form
    })

#view which allowes to see pair images in dashboard
def modify_pair_image_view(request):
    pairs = Pair.objects.all().select_related(
        'otomoto_advert').prefetch_related('pairimages', 'products').order_by('created_at')
    
    BASE_MEDIA_URL = "https://www.tirgumpanel.pl/media/pair_images"
    
    for pair in pairs:
        # Build main image filename from save_pair_image pattern
        main_filename = f"pair_{pair.id}_combined.jpg"
        main_img_url = f"{BASE_MEDIA_URL}/{main_filename}"
        
        # Check if PairImage exists, otherwise generate it
        # pair_image_obj = PairImage.objects.filter(pair=pair).first()
        # if not pair_image_obj or not os.path.exists(pair_image_obj.image.path):
        #     # Generate the main image if missing
        #     try:
        #         processor = PairAdvertImageProcessor(pair)
        #         processor.generate_main_pair_image()
        #     except Exception as e:
        #         print(f"Failed to generate main image for pair {pair.id}: {e}")
        
        # Assign to pair for template
        pair.main_img = main_img_url
        
        # List of product IDs for convenience
        pair.product_ids = list(pair.products.values_list('id', flat=True))

    # ad = OtomotoPairAd()
    # for pair in pairs:
    #     images = ad.get_images(pair)
    #     pair.main_img = images.get("1")
    #     pair.second_img = images.get("2")
        
    #     products = list(pair.products.all().order_by('id'))
        
    #     # 👇 list of product IDs belonging to this pair
    #     pair.product_ids = list(
    #         pair.products.values_list('id', flat=True)
    #     )
        
        
    #     # helper to build image url
    #     def tyre_img(product):
    #         if not product:
    #             return None
            # return f"/media/products/{product.id}-1.jpg"  # 👈 adjust path if needed

        # pair.tyre_one = tyre_img(products[0]) if len(products) > 0 else None
        # pair.tyre_two = tyre_img(products[1]) if len(products) > 1 else None
        # pair.tyre_three = tyre_img(products[2]) if len(products) > 2 else None
        # pair.tyre_four = tyre_img(products[3]) if len(products) > 3 else None

    paginator = Paginator(pairs, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "tyreadderapp/modify-pair-image.html", {"page_obj": page_obj})

    


def generate_main_pair_image(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        pair_ids = data.get("pair_ids", [])
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    results = []

    for pair_id in pair_ids:
        try:
            pair = Pair.objects.get(id=pair_id)
            PairAdvertImageProcessor(pair)
            results.append({"pair_id": pair_id, "success": True})
        except Exception as e:
            results.append({"pair_id": pair_id, "success": False, "error": str(e)})

    return JsonResponse({
        "success": all(r["success"] for r in results),
        "results": results
    })





@require_POST
def create_missing_pairs(request):
    
    missing_numbers = Pair.get_missing_pair_numbers()

    created = []
    for number in missing_numbers:
        pair, was_created = Pair.objects.get_or_create(
            name=str(number)
        )
        if was_created:
            created.append(pair.name)

    if created:
        messages.success(
            request,
            f"Dodałeś {len(created)} nowych par: {', '.join(created)}"
            
        )
        
    else:
        messages.info(request, "No new pairs needed.")

    return redirect(request.META.get("HTTP_REFERER", "/"))






from django.shortcuts import render

from django.http import HttpResponse
from django.utils import timezone
from weasyprint import HTML
from .models import Product
from django.template.loader import render_to_string
import random

from tyreadderapp.logistics_calculator import (
    aggregate_sizes_from_items,
    calculate_pallets,
    # has_multiple_sizes,
    calculate_shipping_amount
)


from django.db.models.functions import Lower

def create_pdf_offer(request):
    product_ids = request.GET.get("product_ids", "")
    ids = [int(pk) for pk in product_ids.split(",") if pk.isdigit()]
    today = timezone.now().date()
    offer_number = f"OF/{today.year}/{today.month:02d}/{random.randint(100,999)}"

    if not ids:
        return render(
            request,
            "tyreadderapp/no_products.html",
            {"error": "No products selected"}
        )
    

    products = Product.objects.filter(id__in=ids).select_related("pair", "brand", "tread", "size").order_by(Lower("pair__name").asc(nulls_last=True))    
    aggregates = aggregate_sizes_from_items(products, 1960)
    calculated_pallettes = calculate_pallets(aggregates)
    # calculated_shipping_amount = calculate_shipping_amount(calculated_pallettes)
    
    total_value = sum(product.net_price for product in products if product.net_price)
    
    context = {
        "products": products,
        "product_ids": ids,
        "date": today,
        "total_value": total_value,
        "offer_number": offer_number,
        "aggregates":aggregates,
        # "calculated_pallettes":calculated_pallettes,
    }

    # Render HTML template to string
    html_string = render_to_string(
        "tyreadderapp/bulk_pdf_offer.html",
        context,
        request=request  # IMPORTANT for static files
    )

    # Create PDF response (inline preview)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=oferta.pdf"

    # Generate PDF
    HTML(
        string=html_string,
        base_url=request.build_absolute_uri("/")  # Important for static/images
    ).write_pdf(response)

    return response




    


      

            
            


