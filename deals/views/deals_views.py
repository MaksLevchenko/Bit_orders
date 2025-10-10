import logging

from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, DetailView

from deals.forms.forms import DealCreateForm
from deals.services import Bitrix24Service
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth


logger = logging.getLogger(__name__)

@main_auth(on_cookies=True)
def success_view(request):
    """Страница успешного создания сделки"""
    return render(request, 'success.html')


@main_auth(on_cookies=True)
def create_deal_view(request):
    if request.method == 'POST':
        form = DealCreateForm(request.POST)
        if form.is_valid():
            bitrix_service = Bitrix24Service()
            bitrix_data = bitrix_service.map_form_to_bitrix_data(form.cleaned_data)
            result = bitrix_service.create_deal(bitrix_data)

            if result['success']:
                return redirect('deal_success')
            else:
                messages.error(request, f'Ошибка: {result["error"]}')
    else:
        form = DealCreateForm()

    return render(request, 'create_deal.html', {'form': form})


# class DealListView(TemplateView):
#     """Представление для списка последних сделок"""
#     template_name = 'deal_list.html'
#
#     @main_auth(on_cookies=True)
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         bitrix_service = Bitrix24Service()
#
#         # Получаем последние 10 сделок
#         deals = bitrix_service.get_recent_deals(limit=10)
#
#         # Получаем справочники для человеко-читаемых названий
#         stages = bitrix_service.get_deal_stages()
#         # types = bitrix_service.get_deal_types()
#
#         # Обогащаем данные сделок
#         enriched_deals = []
#         for deal in deals:
#             enriched_deal = deal.copy()
#
#             # Добавляем человеко-читаемые названия
#             enriched_deal['STAGE_NAME'] = stages.get(deal.get('STAGE_ID', ''), deal.get('STAGE_ID', ''))
#             # enriched_deal['TYPE_NAME'] = types.get(deal.get('TYPE_ID', ''), deal.get('TYPE_ID', ''))
#
#             # Форматируем дату
#             if deal.get('DATE_CREATE'):
#                 enriched_deal['DATE_CREATE_FORMATTED'] = deal['DATE_CREATE'][:10]  # Берем только дату
#
#             # Форматируем сумму
#             opportunity = deal.get('OPPORTUNITY')
#             currency = deal.get('CURRENCY_ID', 'RUB')
#             if opportunity:
#                 enriched_deal['OPPORTUNITY_FORMATTED'] = f"{float(opportunity):,.2f} {currency}"
#             else:
#                 enriched_deal['OPPORTUNITY_FORMATTED'] = 'Не указана'
#
#             enriched_deals.append(enriched_deal)
#
#         context['deals'] = enriched_deals
#         context['deals_count'] = len(enriched_deals)
#
#         return context


# class DashboardView(TemplateView):
#     """Дашборд с формой создания и списком сделок"""
#     template_name = 'dashboard.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         bitrix_service = Bitrix24Service()
#
#         # Форма для создания сделки
#         context['form'] = DealCreateForm()
#
#         # Последние 5 сделок для дашборда
#         recent_deals = bitrix_service.get_recent_deals(limit=5)
#         stages = bitrix_service.get_deal_stages()
#
#         # Обогащаем данные
#         for deal in recent_deals:
#             deal['STAGE_NAME'] = stages.get(deal.get('STAGE_ID', ''), deal.get('STAGE_ID', ''))
#             if deal.get('OPPORTUNITY'):
#                 deal['OPPORTUNITY_FORMATTED'] = f"{float(deal['OPPORTUNITY']):,.2f} {deal.get('CURRENCY_ID', 'RUB')}"
#
#         context['recent_deals'] = recent_deals
#
#         return context
#
@main_auth(on_cookies=True)
def get_deal_list(request):
        bitrix_service = Bitrix24Service()

        # Получаем последние 10 сделок
        deals = bitrix_service.get_recent_deals(limit=10)

        # Получаем справочники для человеко-читаемых названий
        stages = bitrix_service.get_deal_stages()
        types = bitrix_service.get_deal_types()

        # Обогащаем данные сделок
        enriched_deals = []
        for deal in deals:
            enriched_deal = deal.copy()

            # Добавляем человеко-читаемые названия
            enriched_deal['STAGE_NAME'] = stages.get(deal.get('STAGE_ID', ''), deal.get('STAGE_ID', ''))
            enriched_deal['TYPE_NAME'] = types.get(deal.get('TYPE_ID', ''), deal.get('TYPE_ID', ''))

            # Форматируем дату
            if deal.get('DATE_CREATE'):
                enriched_deal['DATE_CREATE_FORMATTED'] = deal['DATE_CREATE'][:10]  # Берем только дату

            # Форматируем сумму
            opportunity = deal.get('OPPORTUNITY')
            currency = deal.get('CURRENCY_ID', 'RUB')
            if opportunity:
                enriched_deal['OPPORTUNITY_FORMATTED'] = f"{float(opportunity):,.2f} {currency}"
            else:
                enriched_deal['OPPORTUNITY_FORMATTED'] = 'Не указана'

            enriched_deals.append(enriched_deal)


        return render(request, 'deal_list.html', {'deals': enriched_deals})

@main_auth(on_cookies=True)
def get_dashboard(request):

        bitrix_service = Bitrix24Service()

        # Форма для создания сделки
        form = DealCreateForm()

        # Последние 5 сделок для дашборда
        recent_deals = bitrix_service.get_recent_deals(limit=5)
        stages = bitrix_service.get_deal_stages()

        # Обогащаем данные
        for deal in recent_deals:
            deal['STAGE_NAME'] = stages.get(deal.get('STAGE_ID', ''), deal.get('STAGE_ID', ''))
            if deal.get('OPPORTUNITY'):
                deal['OPPORTUNITY_FORMATTED'] = f"{float(deal['OPPORTUNITY']):,.2f} {deal.get('CURRENCY_ID', 'RUB')}"


        return render(request, 'dashboard.html', {'recent_deals': recent_deals, 'form': form})


def deal_detail_redirect(request):
    """Перенаправление на страницу сделки по ID из формы"""
    if request.method == 'POST':
        deal_id = request.POST.get('deal_id')
        if deal_id and deal_id.isdigit():
            return redirect('deal_detail', deal_id=int(deal_id))
        else:
            messages.error(request, 'Введите корректный ID сделки')

    return redirect('deal_list')




@main_auth(on_cookies=True)
def get_deal_view(request, pk):
        # deal_id = self.kwargs.get('deal_id')

        try:
            bitrix_service = Bitrix24Service()
            deal_details = bitrix_service.get_deal_details(pk)
            deal_details['deal'] = deal_details['deal']['order0000000000']

            stages = bitrix_service.get_deal_stages()

            if not deal_details or 'deal' not in deal_details:
                raise Http404(f"Сделка с ID {pk} не найдена")


            deal_details['deal']['STAGE_NAME'] = stages.get(deal_details['deal'].get('STAGE_ID', ''), deal_details['deal'].get('STAGE_ID', ''))
            if deal_details['deal'].get('OPPORTUNITY'):
                deal_details['deal']['OPPORTUNITY_FORMATTED'] = f"{float(deal_details['deal']['OPPORTUNITY']):,.2f} {deal_details['deal'].get('CURRENCY_ID', 'RUB')}"

            return render(request, 'deal_detail.html', {'deal_data': deal_details})

        except Exception as e:
            logger.error(f"Ошибка при загрузке сделки {pk}: {e}")
            raise Http404(f"Не удалось загрузить сделку: {str(e)}")
