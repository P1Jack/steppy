import os
import time
import requests
import threading
import json
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class GigaChatTokenManager:
    def __init__(self, auth_key, token_file='gigachat_token.json'):
        self.auth_key = auth_key
        self.token_file = token_file
        self.access_token = None
        self.expires_at = None
        self.lock = threading.Lock()

        self.load_token_from_file()
        self.start_token_refresh_thread()

    def load_token_from_file(self):
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)

                expires_at = datetime.fromtimestamp(data['expires_at'] / 1000.0)
                if expires_at > datetime.now() + timedelta(minutes=5):
                    self.access_token = data['access_token']
                    self.expires_at = expires_at
                    logger.info("Токен загружен из файла")
                else:
                    logger.info("Токен в файле истек")
        except Exception as e:
            logger.error(f"Ошибка при загрузке токена из файла: {e}")

    def save_token_to_file(self, token_data):
        """Сохраняет токен в файл"""
        try:
            expires_in = token_data.get('expires_in', 1800)
            expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # минус 5 минут для запаса

            data = {
                'access_token': token_data['access_token'],
                'expires_at': expires_at.isoformat(),
                'issued_at': datetime.now().isoformat()
            }

            with open(self.token_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.access_token = token_data['access_token']
            self.expires_at = expires_at
            logger.info("Токен сохранен в файл")

        except Exception as e:
            logger.error(f"Ошибка при сохранении токена в файл: {e}")

    def get_new_token(self):
        auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.auth_key}'
        }

        payload = {
            'scope': 'GIGACHAT_API_PERS',
        }

        try:
            response = requests.post(
                auth_url,
                headers=headers,
                data=payload,
                verify=False,  # ПОЛУЧИТЬ СЕРТИФИКАТ
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                self.save_token_to_file(token_data)
                return token_data['access_token']
            else:
                logger.error(f"Ошибка получения токена: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Исключение при получении токена: {e}")
            return None

    def get_token(self):
        with self.lock:
            if not self.access_token or self.expires_at < datetime.now() + timedelta(minutes=5):
                logger.info("Токен истек или отсутствует, запрашиваем новый")
                return self.get_new_token()
            return self.access_token

    def refresh_token_if_needed(self):
        with self.lock:
            if not self.access_token or self.expires_at < datetime.now() + timedelta(minutes=10):
                logger.info("Фоновое обновление токена")
                self.get_new_token()

    def start_token_refresh_thread(self):
        def refresh_worker():
            while True:
                try:
                    time.sleep(900)
                    self.refresh_token_if_needed()
                except Exception as e:
                    logger.error(f"Ошибка в фоновом потоке обновления токена: {e}")
                    time.sleep(60)

        thread = threading.Thread(target=refresh_worker, daemon=True)
        thread.start()
        logger.info("Фоновый поток обновления токена запущен")

    def force_refresh(self):
        logger.info("Принудительное обновление токена")
        return self.get_new_token()
