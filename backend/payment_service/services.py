import base64
import hashlib
import json
import uuid
import requests
from decimal import Decimal

from django.conf import settings
from django.urls import reverse
from .models import StudioPayment


class LiqPayService:
    """
    Сервіс для взаємодії з API LiqPay.
    """

    def __init__(self):
        self.public_key = settings.LIQPAY_PUBLIC_KEY
        self.private_key = settings.LIQPAY_PRIVATE_KEY
        self.checkout_url = "https://www.liqpay.ua/api/3/checkout"

    def _encode_data(self, params: dict) -> str:
        """Кодує параметри в base64."""
        return base64.b64encode(json.dumps(params).encode('utf-8')).decode('utf-8')

    def _create_signature(self, data: str) -> str:
        """Створює підпис для запиту."""
        signature_str = (self.private_key + data + self.private_key).encode('utf-8')
        return base64.b64encode(hashlib.sha1(signature_str).digest()).decode('utf-8')

    def generate_payment_form(self, payment: StudioPayment) -> dict:
        """
        Генерує параметри `data` та `signature` для платіжної форми LiqPay.
        """
        # Ваш домен має бути з HTTPS
        server_url = f"{settings.MY_DOMAIN}{reverse('liqpay_callback')}"
        result_url = f"{settings.MY_DOMAIN}{reverse('payment_success')}"

        params = {
            'action': 'pay',
            'amount': str(payment.amount),
            'currency': 'UAH',
            'description': payment.description,
            'order_id': str(payment.id),
            'version': '3',
            'public_key': self.public_key,
            'server_url': server_url,  # URL для callback-повідомлень
            'result_url': result_url,  # URL для редиректу користувача
        }

        data = self._encode_data(params)
        signature = self._create_signature(data)

        return {
            'data': data,
            'signature': signature,
            'checkout_url': self.checkout_url
        }

    def verify_callback(self, data: str, signature: str) -> dict | None:
        """
        Перевіряє підпис `callback`-запиту від LiqPay.
        Повертає розкодовані дані, якщо підпис вірний.
        """
        expected_signature = self._create_signature(data)
        if expected_signature != signature:
            # TODO: Логувати помилку!
            print("LiqPay callback signature mismatch!")
            return None

        try:
            decoded_data = json.loads(base64.b64decode(data).decode('utf-8'))
            return decoded_data
        except Exception as e:
            # TODO: Логувати помилку!
            print(f"LiqPay callback data decode error: {e}")
            return None


class CheckboxService:
    """
    Сервіс для взаємодії з API Checkbox (РРО/ПРРО).
    """

    def __init__(self):
        self.api_key = settings.CHECKBOX_API_KEY
        self.api_url = settings.CHECKBOX_API_URL.rstrip('/')
        self.headers = {
            'X-License-Key': self.api_key,
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }

    def create_receipt(self, payment: StudioPayment, client_email: str = None) -> dict | None:
        """
        Створює фіскальний чек (чек продажу) в Checkbox.
        """
        # Checkbox очікує суму в копійках
        amount_kopecks = int(payment.amount * 100)

        payload = {
            'id': str(uuid.uuid4()),  # Унікальний ID запиту
            'goods': [
                {
                    'code': 'STUDIO-RENT-PREPAY',  # Ваш внутрішній артикул/код послуги
                    'name': payment.description,
                    'price': amount_kopecks,  # Ціна в копійках
                    'quantity': 1000,  # Кількість: 1.000 (одна послуга)
                }
            ],
            'payments': [
                {
                    'type': 'CASHLESS',  # Тип оплати "Безготівковий" (LiqPay = картка)
                    'value': amount_kopecks,
                }
            ],
        }

        # Додаємо email клієнта, якщо він є, для відправки чека
        if client_email:
            payload['delivery'] = {
                'email': client_email
            }

        try:
            # Увага: перед створенням чека має бути відкрита зміна!
            # /api/v1/shifts/
            response = requests.post(
                f"{self.api_url}/api/v1/receipts/sell",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()  # Генерує помилку для 4xx/5xx статусів

            receipt_data = response.json()
            # receipt_data містить 'id', 'status', 'fiscal_code' тощо.
            return receipt_data

        except requests.exceptions.RequestException as e:
            # TODO: Налаштуйте детальне логування помилок!
            print(f"Checkbox API error: {e}")
            if e.response:
                print(f"Checkbox API response: {e.response.text}")
            return None
