import csv
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime, timedelta
from .bitrix_client import BitrixClient
import logging

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    def __init__(self):
        self.bitrix = BitrixClient()

    def _prepare_contact_row(self, contact: Dict) -> Dict:
        """Подготовить строку контакта для экспорта"""
        phone = contact.get('PHONE', [{}])[0].get('VALUE', '') if contact.get('PHONE') else ''
        email = contact.get('EMAIL', [{}])[0].get('VALUE', '') if contact.get('EMAIL') else ''

        company_name = ''
        if contact.get('COMPANY_ID'):
            company_name = self.bitrix.get_company_name(contact['COMPANY_ID'])

        return {
            'имя': contact.get('NAME', ''),
            'фамилия': contact.get('LAST_NAME', ''),
            'номер телефона': phone,
            'почта': email,
            'компания': company_name
        }

    def get_contacts_with_filters(self, filters: Dict = None) -> List[Dict]:
        """Получить контакты с применением фильтров"""
        filter_params = {}

        if filters:
            if filters.get('last_days'):
                date_from = datetime.now() - timedelta(days=filters['last_days'])
                filter_params['>DATE_CREATE'] = date_from.isoformat()

            if filters.get('company'):
                # Здесь нужно сначала найти ID компании по названию
                companies = self.bitrix.get_companies()
                company_id = companies.get(filters['company'])
                if company_id:
                    filter_params['COMPANY_ID'] = company_id

        return self.bitrix.get_contacts(filter_params)

    @abstractmethod
    def export_to_file(self, contacts: List[Dict], file_path: str):
        pass

    def export_contacts(self, file_path: str, filters: Dict = None) -> Dict:
        """Основной метод экспорта"""
        try:
            contacts = self.get_contacts_with_filters(filters)
            processed_contacts = []

            for contact in contacts:
                processed_contacts.append(self._prepare_contact_row(contact))

            self.export_to_file(processed_contacts, file_path)

            return {
                'success': True,
                'exported_count': len(processed_contacts),
                'file_path': file_path
            }

        except Exception as e:
            logger.error(f"Export error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class CSVExporter(BaseExporter):
    def export_to_file(self, contacts: List[Dict], file_path: str):
        if not contacts:
            return

        with open(file_path, 'w', encoding='utf-8', newline='') as file:
            fieldnames = ['имя', 'фамилия', 'номер телефона', 'почта', 'компания']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(contacts)


class XLSXExporter(BaseExporter):
    def export_to_file(self, contacts: List[Dict], file_path: str):
        if not contacts:
            return

        df = pd.DataFrame(contacts)
        df.to_excel(file_path, index=False)


class ExporterFactory:
    @staticmethod
    def get_exporter(file_extension: str) -> BaseExporter:
        if file_extension.lower() == '.csv':
            return CSVExporter()
        elif file_extension.lower() in ['.xlsx', '.xls']:
            return XLSXExporter()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")