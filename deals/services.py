from typing import List, Dict

from django.conf import settings
from fast_bitrix24 import Bitrix
import logging

logger = logging.getLogger(__name__)

# webhook_url = settings.BITRIX24_WEBHOOK_URL
# bx = Bitrix(webhook_url)

class Bitrix24Service:
    def __init__(self):
        self.webhook_url = settings.BITRIX24_WEBHOOK_URL
        self.bx = Bitrix(self.webhook_url)

    def create_deal(self, deal_data):
        """Создание сделки в Bitrix24"""
        try:
            result = self.bx.call('crm.deal.add', deal_data)
            logger.info(f"Сделка создана успешно. ID: {result}")
            return {'success': True, 'deal_id': result}
        except Exception as e:
            logger.error(f"Ошибка при создании сделки: {e}")
            return {'success': False, 'error': str(e)}

    def map_form_to_bitrix_data(self, form_data):
        """Преобразование данных формы в формат Bitrix24"""

        # Базовые поля
        bitrix_data = {'FIELDS': {
            'TITLE': form_data['title'],
            'OPPORTUNITY': float(form_data['opportunity']),
            'CURRENCY_ID': form_data['currency_id'],
            'TYPE_ID': form_data['deal_type'],
            'ASSIGNED_BY_ID': 1,
        }
        }

        # Обработка кастомных полей
        comments = []

        # Приоритет (как пользовательское поле или в комментарии)
        if form_data['priority']:
            priority_map = {'LOW': 'Низкий', 'MEDIUM': 'Средний', 'HIGH': 'Высокий'}
            bitrix_data['FIELDS']['UF_CRM_PRIORITY'] = form_data['priority']
            comments.append(f"Приоритет: {priority_map.get(form_data['priority'], form_data['priority'])}")

        # Контактная информация
        if form_data['contact_email']:
            comments.append(f"Email: {form_data['contact_email']}")

        if form_data['contact_phone']:
            comments.append(f"Телефон: {form_data['contact_phone']}")

        # Срок выполнения
        if form_data['project_deadline']:
            bitrix_data['FIELDS']['CLOSEDATE'] = form_data['project_deadline'].strftime('%Y-%m-%d')
            comments.append(f"Срок выполнения: {form_data['project_deadline'].strftime('%d.%m.%Y')}")

        # Описание
        if form_data['description']:
            comments.append(f"Описание: {form_data['description']}")

        # Уведомление (можно реализовать через вебхуки или задачи)
        if form_data['send_notification']:
            comments.append("Требуется уведомление менеджера")

        # Объединяем все в комментарии
        if comments:
            bitrix_data['FIELDS']['COMMENTS'] = "\n".join(comments)

        # Дополнительные пользовательские поля
        custom_fields = {
            'UF_CRM_CREATED_VIA_DJANGO': 'Y',  # Метка что создано через Django
            'UF_CRM_PRIORITY': form_data['priority'],
        }

        bitrix_data.update(custom_fields)

        return bitrix_data

    def get_recent_deals(self, limit: int = 10) -> List[Dict]:
        """Получить последние сделки"""
        try:
            deals = self.bx.get_all(
                'crm.deal.list',
                {
                    'SELECT': [
                        'ID', 'TITLE', 'OPPORTUNITY', 'CURRENCY_ID',
                        'STAGE_ID', 'TYPE_ID', 'DATE_CREATE', 'ASSIGNED_BY_ID',
                        'COMPANY_TITLE', 'CONTACT_NAME', 'COMMENTS'
                    ],
                    'FILTER': {}  # Можно добавить фильтры
                }
            )
            if deals and isinstance(deals, dict) and 'result' in deals:
                return deals['result'][-limit:]
            elif isinstance(deals, list):
                return deals[-limit:][::-1]
            else:
                logger.warning(f"Неожиданный формат ответа: {type(deals)}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return []

    def get_deal_stages(self) -> Dict:
        """Получить справочник стадий сделок"""
        try:
            # Используем call вместо get_all для методов не заканчивающихся на .list
            result = self.bx.get_all('crm.status.list', {
                'filter': {'ENTITY_ID': 'DEAL_STAGE'}
            })

            # Обрабатываем результат правильно
            stages_dict = {}
            if result and 'result' in result:
                for stage in result['result']:
                    stages_dict[stage['STATUS_ID']] = stage['NAME']
            elif isinstance(result, list):
                for stage in result:
                    if isinstance(stage, dict) and 'STATUS_ID' in stage:
                        stages_dict[stage['STATUS_ID']] = stage['NAME']

            return stages_dict

        except Exception as e:
            logger.error(f"Ошибка при получении стадий: {e}")
            return {}

    def get_deal_types(self) -> Dict:
        """Получить справочник типов сделок"""
        try:
            # Используем call и передаем пустой словарь вместо None
            result = self.bx.call('crm.type.list', {})

            types_dict = {}
            if result and 'result' in result:
                for deal_type in result['result']:
                    types_dict[deal_type['ID']] = deal_type['NAME']
            elif isinstance(result, list):
                for deal_type in result:
                    if isinstance(deal_type, dict) and 'ID' in deal_type:
                        types_dict[deal_type['ID']] = deal_type['NAME']

            return types_dict

        except Exception as e:
            logger.error(f"Ошибка при получении типов сделок: {e}")
            return {}

    def get_deal_by_id(self, deal_id: int) -> Dict:
        """Получить сделку по ID"""
        try:
            result = self.bx.call('crm.deal.get', {'id': deal_id})

            if result and isinstance(result, dict):
                return result
            else:
                logger.warning(f"Сделка с ID {deal_id} не найдена")
                return {}

        except Exception as e:
            logger.error(f"Ошибка при получении сделки {deal_id}: {e}")
            return {}

    def get_deal_details(self, deal_id: int) -> Dict:
        """Получить детальную информацию о сделке"""
        try:
            # Получаем основную информацию о сделке
            deal = self.get_deal_by_id(deal_id)
            if not deal:
                return {}

            # Получаем связанные контакты
            contacts = self._get_deal_contacts(deal_id)

            # Получаем связанные компании
            companies = self._get_deal_companies(deal_id)

            # Получаем задачи сделки
            tasks = self._get_deal_tasks(deal_id)
            #
            # Обогащаем данные
            stages = self.get_deal_stages()
            types = self.get_deal_types()

            deal['STAGE_NAME'] = stages.get(deal.get('STAGE_ID', ''), deal.get('STAGE_ID', ''))
            deal['TYPE_NAME'] = types.get(deal.get('TYPE_ID', ''), deal.get('TYPE_ID', ''))

            # Форматируем сумму
            opportunity = deal.get('OPPORTUNITY')
            currency = deal.get('CURRENCY_ID', 'RUB')
            if opportunity:
                try:
                    deal['OPPORTUNITY_FORMATTED'] = f"{float(opportunity):,.2f} {currency}"
                except (ValueError, TypeError):
                    deal['OPPORTUNITY_FORMATTED'] = f"{opportunity} {currency}"
            else:
                deal['OPPORTUNITY_FORMATTED'] = 'Не указана'

            return {
                'deal': deal,
                'contacts': contacts,
                'companies': companies,
                # 'tasks': tasks
            }

        except Exception as e:
            logger.error(f"Ошибка при получении деталей сделки {deal_id}: {e}")
            return {}

    def _get_deal_contacts(self, deal_id: int) -> List[Dict]:
        """Получить контакты связанные со сделкой"""
        try:
            result = self.bx.call('crm.deal.contact.items.get', {'id': deal_id})
            if result and isinstance(result, dict) and 'result' in result:
                return result['result']
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении контактов сделки {deal_id}: {e}")
            return []

    def _get_deal_companies(self, deal_id: int) -> List[Dict]:
        """Получить компании связанные со сделкой"""
        try:
            # В Bitrix24 сделка обычно связана с одной компанией
            deal = self.get_deal_by_id(deal_id)
            company_id = deal.get('COMPANY_ID')
            if company_id:
                company = self.bx.call('crm.company.get', {'id': company_id})
                return [company] if company else []
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении компаний сделки {deal_id}: {e}")
            return []

    def _get_deal_tasks(self, deal_id: int) -> List[Dict]:
        """Получить задачи связанные со сделкой"""
        try:
            result = self.bx.get_all('tasks.task.list', {
                'filter': {'UF_CRM_TASK': [f'D_{deal_id}']},
                'select': ['ID', 'TITLE', 'STATUS', 'CREATED_DATE', 'RESPONSIBLE_ID']
            })
            if result and isinstance(result, dict) and 'tasks' in result:
                return result['tasks']
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении задач сделки {deal_id}: {e}")
            return []


# def _get_deal_tasks(request, deal_id: int) -> List[Dict]:
#         """Получить задачи связанные со сделкой"""
#         try:
#             result = bx.get_all('tasks.task.list', {
#                 'filter': {'UF_CRM_TASK': [f'D_{deal_id}']},
#                 'select': ['ID', 'TITLE', 'STATUS', 'CREATED_DATE', 'RESPONSIBLE_ID']
#             })
#             if result and isinstance(result, dict) and 'tasks' in result:
#                 return result['tasks']
#             return []
#         except Exception as e:
#             logger.error(f"Ошибка при получении задач сделки {deal_id}: {e}")
#             return []