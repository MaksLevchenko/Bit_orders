import requests
from typing import Optional, Tuple

import settings


class YandexGeocoder:
    def __init__(self):
        self.api_key = settings.YANDEX_MAPS_API_KEY
        self.base_url = "https://geocode-maps.yandex.ru/1.x/"

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Геокодирование адреса в координаты"""
        if not address:
            return None

        try:
            params = {
                'apikey': self.api_key,
                'geocode': address,
                'format': 'json'
            }
            response = requests.get(self.base_url, params=params)
            data = response.json()

            features = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])

            if features:
                # Берем первый (наиболее релевантный) результат
                coordinates = features[0]['GeoObject']['Point']['pos']
                lon, lat = map(float, coordinates.split())
                return lat, lon

        except Exception as e:
            print(f"Ошибка геокодирования адреса '{address}': {e}")

        return None