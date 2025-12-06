import base64
import hashlib
import json
import uuid
import requests
import logging
from decimal import Decimal
from typing import Optional, Dict

from django.conf import settings
from django.urls import reverse
from .models import StudioPayment

# Configure logging
logger = logging.getLogger(__name__)


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
            'server_url': server_url,
            'result_url': result_url,
        }

        data = self._encode_data(params)
        signature = self._create_signature(data)

        logger.info(
            f"Generated payment form for payment {payment.id}, "
            f"amount: {payment.amount} UAH"
        )

        return {
            'data': data,
            'signature': signature,
            'checkout_url': self.checkout_url
        }

    def verify_callback(self, data: str, signature: str) -> Optional[Dict]:
        """
        Перевіряє підпис `callback`-запиту від LiqPay.
        Повертає розкодовані дані, якщо підпис вірний.
        """
        expected_signature = self._create_signature(data)
        if expected_signature != signature:
            logger.error(
                "LiqPay callback signature mismatch! "
                f"Expected: {expected_signature}, Got: {signature}"
            )
            return None

        try:
            decoded_data = json.loads(base64.b64decode(data).decode('utf-8'))
            logger.info(
                f"LiqPay callback verified for order_id: {decoded_data.get('order_id')}, "
                f"status: {decoded_data.get('status')}"
            )
            return decoded_data
        except Exception as e:
            logger.error(f"LiqPay callback data decode error: {e}", exc_info=True)
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

    def create_receipt(self, payment: StudioPayment, client_email: str = None) -> Optional[Dict]:
        """
        Створює фіскальний чек (чек продажу) в Checkbox.
        """
        # Checkbox очікує суму в копійках
        amount_kopecks = int(payment.amount * 100)

        payload = {
            'id': str(uuid.uuid4()),  # Унікальний ID запиту
            'goods': [
                {
                    'code': 'STUDIO-RENT-PREPAY',
                    'name': payment.description,
                    'price': amount_kopecks,
                    'quantity': 1000,  # 1.000 (одна послуга)
                }
            ],
            'payments': [
                {
                    'type': 'CASHLESS',
                    'value': amount_kopecks,
                }
            ],
        }

        # Додаємо email клієнта, якщо він є
        if client_email:
            payload['delivery'] = {
                'email': client_email
            }

        try:
            response = requests.post(
                f"{self.api_url}/api/v1/receipts/sell",
                headers=self.headers,
                json=payload,
                timeout=30  # Додаємо timeout для безпеки
            )
            response.raise_for_status()

            receipt_data = response.json()
            logger.info(
                f"Checkbox receipt created successfully for payment {payment.id}, "
                f"receipt_id: {receipt_data.get('id')}, "
                f"fiscal_code: {receipt_data.get('fiscal_code')}"
            )
            return receipt_data

        except requests.exceptions.Timeout:
            logger.error(
                f"Checkbox API timeout for payment {payment.id}",
                exc_info=True
            )
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Checkbox API HTTP error for payment {payment.id}: {e}",
                exc_info=True
            )
            if e.response:
                logger.error(f"Checkbox API response: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Checkbox API request error for payment {payment.id}: {e}",
                exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error creating Checkbox receipt for payment {payment.id}: {e}",
                exc_info=True
            )
            return None