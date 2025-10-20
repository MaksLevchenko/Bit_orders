import csv
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict
from .bitrix_client import BitrixClient
import logging

logger = logging.getLogger(__name__)


class BaseImporter(ABC):
    def __init__(self):
        self.bitrix = BitrixClient()
        self.companies_cache = {}

    def _get_company_id(self, company_name: str) -> int:
        """Получить ID компании по названию (с кэшированием)"""
        if not company_name:
            return None

        if not self.companies_cache:
            self.companies_cache = self.bitrix.get_companies()

        return self.companies_cache.get(company_name.strip())

    def _prepare_contact_data(self, row: Dict) -> Dict:
        """Подготовить данные контакта для Bitrix24"""
        phones = [{"VALUE": row['phone'], "VALUE_TYPE": "WORK"}] if row.get('phone') else []
        emails = [{"VALUE": row['email'], "VALUE_TYPE": "WORK"}] if row.get('email') else []

        company_id = self._get_company_id(row.get('company', '').lower())

        return {
            'fields': {
                'NAME': row.get('first_name', ''),
                'LAST_NAME': row.get('last_name', ''),
                'PHONE': phones,
                'EMAIL': emails,
                'COMPANY_ID': company_id,
            }
        }

    @abstractmethod
    def read_file(self, file_path: str) -> List[Dict]:
        pass

    def import_contacts(self, file_path: str) -> Dict:
        """Основной метод импорта"""
        try:
            contacts_data = self.read_file(file_path)
            batch_data = []

            for row in contacts_data:
                contact_data = self._prepare_contact_data(row)
                batch_data.append(contact_data)

                # Отправляем пачками
                if len(batch_data) >= self.bitrix.batch_size:
                    results = self.bitrix.create_contacts_batch(batch_data)
                    batch_data = []
                    logger.info(f"Imported batch: {results}")

            # Отправляем оставшиеся
            if batch_data:
                results = self.bitrix.create_contacts_batch(batch_data)
                logger.info(f"Imported final batch: {results}")

            return {
                'success': True,
                'processed': len(contacts_data)
            }

        except Exception as e:
            logger.error(f"Import error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class CSVImporter(BaseImporter):
    def read_file(self, file_path: str) -> List[Dict]:
        contacts = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                contacts.append({
                    'first_name': row.get('имя', ''),
                    'last_name': row.get('фамилия', ''),
                    'phone': row.get('номер телефона', ''),
                    'email': row.get('почта', ''),
                    'company': row.get('компания', '')
                })
        return contacts


class XLSXImporter(BaseImporter):
    def read_file(self, file_path: str) -> List[Dict]:
        df = pd.read_excel(file_path)
        contacts = []

        for _, row in df.iterrows():
            contacts.append({
                'first_name': row.get('имя', ''),
                'last_name': row.get('фамилия', ''),
                'phone': str(row.get('номер телефона', '')),
                'email': row.get('почта', ''),
                'company': row.get('компания', '')
            })

        return contacts


class ImporterFactory:
    @staticmethod
    def get_importer(file_extension: str) -> BaseImporter:
        if file_extension.lower() == '.csv':
            return CSVImporter()
        elif file_extension.lower() in ['.xlsx', '.xls']:
            return XLSXImporter()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")