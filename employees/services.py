import random
import time

from fast_bitrix24 import Bitrix
import logging
from django.conf import settings
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Bitrix24CompanyService:
    """Сервис для работы с компанией в Bitrix24 через fast-bitrix24"""

    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or settings.BITRIX24_WEBHOOK_URL
        self.bx = Bitrix(self.webhook_url)

    def get_all_users(self) -> List[Dict]:
        """Получить всех активных пользователей"""
        try:
            users = self.bx.get_all('user.get', {
                'filter': {'ACTIVE': True},
                'select': [
                    'ID', 'NAME', 'LAST_NAME', 'SECOND_NAME', 'EMAIL',
                    'WORK_POSITION', 'WORK_PHONE', 'PERSONAL_PHOTO',
                    'UF_DEPARTMENT', 'UF_PHONE_INNER', 'UF_HEAD'
                ]
            })
            logger.info(f"Получено {len(users)} активных пользователей")
            return users
        except Exception as e:
            logger.error(f"Ошибка при получении пользователей: {e}")
            return []

    def get_user_by_id(self, user_id: int) -> List[Dict]:
        """Получить всех активных пользователей"""
        try:
            user = self.bx.call('user.get', {
                'filter': {'ID': user_id},
            })
            return user
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя с ID {user_id}: {e}")
            return []

    def get_departments(self) -> List[Dict]:
        """Получить все отделы"""
        try:
            departments = self.bx.get_all('department.get', {
                'select': ['ID', 'NAME', 'PARENT', 'UF_HEAD']
            })

            logger.info(f"Получено {len(departments)} отделов")
            return departments
        except Exception as e:
            logger.error(f"Ошибка при получении отделов: {e}")
            return []

    def get_user_departments_and_managers(self, users, user_id):

        departments = self.get_departments()

        # Находим пользователя
        user = None
        for u in users:
            if u['ID'] == user_id:
                user = u
                break

        if not user:
            return {"error": "Пользователь не найден"}

        # Получаем ID отделов пользователя
        user_department_ids = user.get('UF_DEPARTMENT', [])

        # Словарь для быстрого доступа к отделам по ID
        dept_dict = {dept['ID']: dept for dept in departments}

        user_departments = [dep['NAME'] for dep_id, dep in dept_dict.items() if int(dep_id) in user_department_ids]


        # Находим все отделы и подотделы пользователя
        all_user_departments = []

        def find_all_departments(dept_id):
            """Рекурсивно находит все родительские отделы"""
            dept = dept_dict.get(dept_id)
            if dept:
                all_user_departments.append(dept)
                # Если есть родительский отдел, ищем его рекурсивно
                if 'PARENT' in dept:
                    find_all_departments(dept['PARENT'])

        # Для каждого отдела пользователя находим все родительские отделы
        for dept_id in user_department_ids:
            find_all_departments(str(dept_id))  # Преобразуем в строку для совместимости

        # Убираем дубликаты
        unique_departments = []
        seen_ids = set()
        for dept in all_user_departments:
            if dept['ID'] not in seen_ids and dept['ID'] != '1':
                unique_departments.append(dept['NAME'])
                seen_ids.add(dept['ID'])

        # Находим всех руководителей
        manager_ids = set()
        managers_info = []

        for dept in departments:
            if 'UF_HEAD' in dept and dept['UF_HEAD'] and dept['UF_HEAD'] != user_id:
                manager_id = dept['UF_HEAD']
                if manager_id not in manager_ids:
                    manager_ids.add(manager_id)
                    # Находим информацию о руководителе
                    for user in users:
                        if user['ID'] == manager_id:
                            managers_info.append(f"{user['LAST_NAME']} {user['NAME']}")
                            break
        return user_departments, managers_info

    def get_call_statistics(self, from_date: datetime, to_date: datetime) -> List[Dict]:
        """Получить статистику звонков через voximplant.statistic.get"""
        try:
            result = self.bx.get_all('voximplant.statistic.get', {
                'FILTER': {
                    'CALL_TYPE': '1',
                    '>CALL_DURATION': 60,
                    '>=CALL_START_DATE': from_date.strftime('%Y-%m-%d %H:%M:%S'),
                    '<=CALL_START_DATE': to_date.strftime('%Y-%m-%d %H:%M:%S')
                },
                'select': [
                    'ID', 'PORTAL_USER_ID', 'CALL_START_DATE', 'CALL_DURATION',
                    'CALL_TYPE', 'COST', 'PHONE_NUMBER', 'CALL_RECORD_URL'
                ]
            })

            if isinstance(result, dict) and 'result' in result:
                result = result['result']
                return result
            elif isinstance(result, list):
                return result
            else:
                return []

        except Exception as e:
            logger.error(f"Ошибка при получении статистики звонков: {e}")
            return []


class BitrixCallGenerator:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or settings.BITRIX24_CALL_WEBHOOK_URL
        self.bx = Bitrix(self.webhook_url)
        self.users = []
        self.contacts = []

    def get_users(self):
        """Получает список пользователей из Битрикс24"""
        try:
            users = self.bx.get_all('user.get', {
                'filter': {'ACTIVE': True},
                'select': ['ID', 'NAME', 'LAST_NAME', 'EMAIL', 'WORK_POSITION']
            })
            self.users = [user for user in users if user.get('ID')]
            print(f"Загружено {len(self.users)} пользователей")
            return self.users
        except Exception as e:
            print(f"Ошибка при загрузке пользователей: {e}")
            return []

    def get_contacts(self):
        """Получает список контактов для звонков"""
        try:
            contacts = self.bx.get_all('crm.contact.list', {
                'select': ['ID', 'NAME', 'LAST_NAME', 'PHONE']
            })
            self.contacts = [contact for contact in contacts if contact.get('PHONE')]
            print(f"Загружено {len(self.contacts)} контактов с телефонами")
            return self.contacts
        except Exception as e:
            print(f"Ошибка при загрузке контактов: {e}")
            return []

    def generate_phone_number(self):
        """Генерирует случайный номер телефона"""
        return f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}"

    def generate_call_data(self, user_id, contact_id=None):
        """Генерирует данные для звонка"""
        call_types = [1, 2]  # 1 - исходящий, 2 - входящий
        start_time = datetime.now() - timedelta(days=random.randint(0, 5))

        call_data = {
            'USER_ID': user_id,
            'TYPE': random.choice(call_types),
            'SHOW': 0,
            'CALL_START_DATE': start_time.isoformat(),
            'PHONE_NUMBER': self.generate_phone_number(),
        }

        # Связываем с контактом в 70% случаев
        if contact_id and random.random() < 0.7:
            call_data['ENTITY_TYPE'] = 'CONTACT'
            call_data['ENTITY_ID'] = contact_id

        return call_data

    def create_call(self, call_data):
        """Создает звонок в Битрикс24"""
        try:
            result = self.bx.call('telephony.externalcall.register', call_data)

            time.sleep(1)
            call_id = result.get('order0000000000', {}).get('CALL_ID')
            call_data = {
                'CALL_ID': call_id,
                'USER_ID': call_data['USER_ID'],
                'DURATION': random.randint(10, 1800),
            }

            result = self.bx.call('telephony.externalcall.finish', call_data)
            return result
        except Exception as e:
            print(f"Ошибка при создании звонка: {e}")
            return None


    def generate_random_calls(self, num_calls=None):
        """Генерирует случайное количество звонков"""
        if not num_calls:
            num_calls = random.randint(5, 15)

        print(f"Создание {num_calls} случайных звонков...")

        # Загружаем пользователей и контакты
        users = self.get_users()
        contacts = self.get_contacts()

        if not users:
            print("Нет активных пользователей для создания звонков")
            return None

        created_calls = []

        for i in range(num_calls):
            # Выбираем случайного пользователя
            user = random.choice(users)
            contact = random.choice(contacts) if contacts else None

            # Генерируем данные звонка
            call_data = self.generate_call_data(user['ID'], contact['ID'] if contact else None)

            print(f"Создание звонка {i + 1}/{num_calls} для пользователя {user.get('NAME')} {user.get('LAST_NAME')}")

            # Создаем звонок

            call_result = self.create_call(call_data)
            if call_result and 'CALL_ID' in call_result['order0000000000']:
                call_id = call_result['order0000000000']['CALL_ID']
                created_calls.append({
                    'call_id': call_id,
                    'user_id': user['ID'],
                    'phone': call_data['PHONE_NUMBER']
                })
                print(f"✅ Создан звонок ID: {call_id}")
            else:
                print(f"❌ Ошибка при создании звонка")

        calls_count = len(created_calls)
        users_calls = []

        # Статистика по пользователям
        user_stats = {}
        for call in created_calls:
            user_id = call['user_id']
            user_stats[user_id] = user_stats.get(user_id, 0) + 1

        for user_id, count in user_stats.items():
            user = next((u for u in users if u['ID'] == user_id), None)
            if user:
                users_calls.append(f"  - {user.get('NAME')} {user.get('LAST_NAME')}: {count} звонков")
        return calls_count, users_calls
