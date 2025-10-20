from typing import List, Dict, Optional
from fast_bitrix24 import Bitrix

import settings


class BitrixClient:
    def __init__(self):
        self.webhook_url = settings.BITRIX24_WEBHOOK_URL
        self.bitrix = Bitrix(self.webhook_url)

    def get_addresses(self) -> List[Dict]:
        """Получение списка адресов из Битрикс24"""
        try:
            addresses = self.bitrix.get_all('crm.address.list', {
                'select': ['ENTITY_ID', 'ADDRESS_1', 'CITY', 'REGION', 'PROVINCE', 'COUNTRY', ]
            })
            return addresses
        except Exception as e:
            print(f"Ошибка при получении адресов: {e}")
            return []

    def get_companies(self) -> List[Dict]:
        """Получение списка компаний из Битрикс24"""
        try:
            companies = self.bitrix.get_all('crm.company.list', {
                'select': ['ID', 'TITLE']
            })
            return companies
        except Exception as e:
            print(f"Ошибка при получении компаний: {e}")
            return []

    def get_company_contacts(self, company_id: int) -> Optional[str]:
        """Получение контактов и логотипа компании"""
        try:
            result = self.bitrix.call('crm.company.get', {
                'id': company_id
            })
            if result.get('order0000000000'):
                if result.get('order0000000000').get('PHONE'):
                    tel = result.get('order0000000000').get('PHONE')[0].get('VALUE', '')
                else:
                    tel = ''
                if result.get('order0000000000').get('EMAIL'):
                    email = result.get('order0000000000').get('EMAIL')[0].get('VALUE', '')
                else:
                    email = ''
                if result.get('order0000000000').get('LOGO'):
                    logo = result.get('order0000000000').get('LOGO').get('showUrl', '')
                else:
                    logo = ''
                return tel, email, logo
            else:
                return None
        except Exception as e:
            print(f"Ошибка при получении контактов и логотипа компании {company_id}: {e}")
            return None
