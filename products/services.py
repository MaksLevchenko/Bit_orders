import base64

import requests
import logging
from django.conf import settings
from typing import Dict, List, Optional
import hashlib
import hmac
from fast_bitrix24 import Bitrix

logger = logging.getLogger(__name__)


class Bitrix24ProductService:
    """Сервис для работы с товарами в Bitrix24"""

    def __init__(self):
        self.webhook_url = settings.BITRIX24_WEBHOOK_URL
        self.session = requests.Session()
        self.bx = Bitrix(self.webhook_url)

    def _make_request(self, method: str, params: Dict = None) -> Dict:
        """Универсальный метод для выполнения запросов к Bitrix24 API"""
        if params is None:
            params = {}

        try:
            if method.split('.')[-1] not in ('list', 'getlist', 'fields', 'getavaliableforpayment', 'types'):
                data = self.bx.call(method, params)
            else:
                data = self.bx.get_all(method, params)

            if 'error' in data:
                error_msg = data.get('error_description', 'Unknown error')
                logger.error(f"Bitrix24 API Error in {method}: {error_msg}")
                return {'error': error_msg}

            return data

        except Exception as e:
            logger.error(f"Error in {method}: {e}")
            return {'error': str(e)}

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Получить товар по ID"""
        try:
            result = self._make_request('crm.product.get', {'id': product_id})
            image_url = self.get_product_image_url(product_id)

            if 'order0000000000' in result:
                if image_url:
                    result['order0000000000']['image_url'] = image_url
                return result['order0000000000']
        except Exception as e:
            return None

    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск товаров по названию"""
        result = self._make_request('crm.product.list', {
            'filter': {'%NAME': query},
            'select': ['id', 'NAME', 'IBLOCKID', 'PRICE', 'DESCRIPTION', 'PREVIEW_PICTURE'],
        })
        return result[:limit]

    def get_product_image_url(self, product_id: int) -> Optional[str]:
        """Получить URL изображения товара"""
        image_url = self.bx.get_all('catalog.productImage.list', {"productId": product_id, "select": ['detailUrl']})
        if image_url[0].get('detailUrl'):
            return image_url[0].get('detailUrl')
        return None


class URLSigner:
    """Класс для создания и проверки подписанных URL"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')

    def generate_signed_token(self, product_id: int) -> str:
        """Генерация подписанного токена для товара"""
        data = f"product_{product_id}".encode('utf-8')
        signature = hmac.new(self.secret_key, data, hashlib.sha256).hexdigest()
        return signature[:16]  # Берем первые 16 символов для удобства

    def verify_token(self, token: str, product_id: int) -> bool:
        """Проверка валидности токена"""
        expected_token = self.generate_signed_token(product_id)
        return hmac.compare_digest(token, expected_token)