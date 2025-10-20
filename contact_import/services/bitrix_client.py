from fast_bitrix24 import Bitrix
import logging

import settings

logger = logging.getLogger(__name__)


class BitrixClient:
    def __init__(self):
        self.bitrix = Bitrix(settings.BITRIX24_WEBHOOK_URL)
        self.batch_size = settings.BITRIX_BATCH_SIZE

    def search_companies(self, query: str, limit: int = 10):
        """Быстрый поиск компаний через Bitrix API"""
        try:
            # Используем поиск Bitrix для больших объемов данных
            companies = self.b.get_all('crm.company.list', {
                'select': ['ID', 'TITLE'],
                'filter': {'%TITLE': query},
                'order': {'TITLE': 'ASC'},
                'start': 0
            })

            # Сортируем по релевантности (сначала те, что начинаются с запроса)
            companies_sorted = sorted(
                companies,
                key=lambda x: (
                    0 if x['TITLE'].lower().startswith(query.lower()) else 1,
                    x['TITLE']
                )
            )

            return [company['TITLE'] for company in companies_sorted[:limit]]

        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            return []

    def get_companies(self):
        """Получить все компании для матчинга по названию"""
        try:
            companies = self.bitrix.get_all('crm.company.list', {
                'select': ['ID', 'TITLE']
            })
            return {company['TITLE'].lower(): company['ID'] for company in companies}
        except Exception as e:
            logger.error(f"Error fetching companies: {e}")
            return {}

    def create_contacts_batch(self, contacts_data):
        """Создание контактов пачками"""
        try:
            results = self.bitrix.call('crm.contact.add', contacts_data)
            # results = self.add_company_to_contact(contact_id=results, company_id=contacts_data[0])

            return results
        except Exception as e:
            logger.error(f"Error creating contacts batch: {e}")
            return None

    def get_contacts(self, filter_params=None):
        """Получить контакты с фильтрацией"""
        params = {
            'select': [
                'NAME', 'LAST_NAME', 'PHONE', 'EMAIL', 'COMPANY_ID', 'DATE_CREATE'
            ]
        }

        if filter_params:
            params['filter'] = filter_params

        try:
            contacts = self.bitrix.get_all('crm.contact.list', params)
            return contacts
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            return []

    def get_company_name(self, company_id):
        """Получить название компании по ID"""
        if not company_id:
            return ""

        try:
            company = self.bitrix.call('crm.company.get', {'ID': company_id})
            company_name = company.get('order0000000000').get('TITLE', '')
            return company_name
        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {e}")
            return ""


    # def add_company_to_contact(self, contact_id: str, company_id: str):
    #     """Добавляет компанию к контакту"""
    #     try:
    #         contact = self.bitrix.call(
    #             'crm.contact.company.add', {
    #                 'id': contact_id,
    #                 'fields': {
    #                     'COMPANY_ID': company_id
    #                 }
    #             }
    #         )
    #         if contact.get('result'):
    #             return True
    #         else:
    #             return False
    #         print(contact)
    #     except Exception as e:
    #         return None