import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.generic import FormView, TemplateView, DetailView
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import uuid
import hashlib

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from products.forms.forms import ProductSearchForm, QRGenerationForm
from products.services import Bitrix24ProductService, URLSigner
from products.models import ProductQRCode


@main_auth(on_cookies=True)
def product_search_view(request):
    if request.method == 'POST':
        form = ProductSearchForm(request.POST)
        if form.is_valid():
            product = form.get_product()

            if product:

                context = {
                    'form': QRGenerationForm(initial={
                        'product_id': product['ID'],
                        'product_name': product.get('NAME', ''),
                    }),
                    'product': {
                        'id': product['ID'],
                        'name': product.get('NAME', ''),
                        'price': product.get('PRICE', 0),
                        'description': product.get('DESCRIPTION', ''),
                        'image': product.get('image_url', '')
                    }
                }
                return render(request, 'qr_generation.html', context)
            else:
                form = ProductSearchForm()
                messages.error(request, 'Товар не найден. Проверьте ID или название.')
                return render(request, 'generate_qr.html', {'error': 'error', 'form': form})

    else:
        form = ProductSearchForm()
        return render(request, 'generate_qr.html', {'form': form})


@main_auth(on_cookies=True)
def generate_qr_view(request):
    if  request.method == 'POST':
        form = QRGenerationForm(request.POST)

        if form.is_valid():
            try:
                product_id = form.cleaned_data['product_id']
                product_name = form.cleaned_data['product_name']
                notes = form.cleaned_data.get('notes', '')

                bitrix_service = Bitrix24ProductService()
                image_url = bitrix_service.get_product_image_url(product_id)

                # СОЗДАЕМ QR-КОД БЕЗ SECRET_TOKEN
                qr_code = ProductQRCode.objects.create(
                    product_id=product_id,
                    product_name=product_name,
                    product_image_url=image_url,
                )

                # ГЕНЕРИРУЕМ ПОДПИСАННЫЙ URL С ИСПОЛЬЗОВАНИЕМ SIGNER
                qr_url = request.build_absolute_uri(
                    qr_code.get_absolute_url()
                )

                # Генерация QR-изображения
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()

                # Получаем данные продукта для контекста
                product_data = request.session.get('selected_product', {})

                context = {
                    'qr_image': f"data:image/png;base64,{qr_image_base64}",
                    'qr_url': qr_url,
                    'product': product_data,
                    'qr_code': qr_code,
                }

                # Очищаем сессию
                if 'selected_product' in request.session:
                    del request.session['selected_product']
                    request.session.modified = True

                return render(request, 'qr_result.html', context)

            except Exception as e:
                messages.error(request, f'Ошибка при генерации QR-кода: {str(e)}')
                return render(request, 'qr_generation.html', {
                    'form': form,
                    'product': request.session.get('selected_product', {})
                })


def product_qr_detail_view(request, signed_token):
    """Страница товара по подписанной ссылке из QR-кода"""
    try:
        # ПРОВЕРЯЕМ ПОДПИСЬ С ПОМОЩЬЮ SIGNER
        qr_code = ProductQRCode.verify_token(signed_token)

        if not qr_code:
            from django.http import Http404
            raise Http404("QR-код не найден, неактивен или ссылка недействительна")

        # Получаем актуальную информацию о товаре из Bitrix24
        bitrix_service = Bitrix24ProductService()
        product_data = bitrix_service.get_product_by_id(qr_code.product_id)

        if product_data:
            product_name = product_data.get('NAME', qr_code.product_name)
            product_price = product_data.get('PRICE', 0)
            product_description = product_data.get('DESCRIPTION', '')

            # Обновляем URL изображения если он изменился
            current_image_url = bitrix_service.get_product_image_url(qr_code.product_id)
            if current_image_url and current_image_url != qr_code.product_image_url:
                qr_code.product_image_url = current_image_url
                qr_code.save()
        else:
            # Если не удалось получить актуальные данные, используем сохраненные
            product_name = qr_code.product_name
            product_price = 0
            product_description = 'Информация о товаре временно недоступна'

        context = {
            'product_id': qr_code.product_id,
            'product': qr_code,
            'product_name': product_name,
            'product_price': product_price,
            'product_description': product_description,
            'created_at': qr_code.created_at,
            'is_active': qr_code.is_active
        }

        return render(request, 'product_detail.html', context)

    except Exception as e:
        from django.http import Http404
        raise Http404("Недействительная ссылка")


def product_autocomplete(request):
    """API для автодополнения при поиске товаров"""
    query = request.GET.get('query', '')
    if len(query) < 2:
        return HttpResponse('[]', content_type='application/json')

    bitrix_service = Bitrix24ProductService()
    products = bitrix_service.search_products(query, limit=10)

    import json
    results = [
        {
            'id': product['ID'],
            'name': product.get('NAME', ''),
            'price': product.get('PRICE', 0),
        }
        for product in products
    ]

    return HttpResponse(json.dumps(results), content_type='application/json')