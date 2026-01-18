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

logger = logging.getLogger(__name__)

try:
    from liqpay.liqpay import LiqPay
except ImportError:
    from liqpay import LiqPay


class LiqPayService:
    """Сервіс для взаємодії з API LiqPay."""

    def __init__(self):
        self.liqpay = LiqPay(settings.LIQPAY_PUBLIC_KEY, settings.LIQPAY_PRIVATE_KEY)
        self.checkout_url = "https://www.liqpay.ua/api/3/checkout"
        self.api_url = "https://www.liqpay.ua/api/request"

    def generate_payment_form(self, payment: StudioPayment, frontend_base_url: str) -> dict:
        """Генерує параметри для платіжної форми LiqPay."""


        server_url = f"{frontend_base_url}{reverse('liqpay_callback')}"


        result_url = f"{frontend_base_url}{reverse('payment_success')}?order_id={payment.id}"

        params = {
            'action': 'pay',
            'amount': str(payment.amount),
            'currency': 'UAH',
            'description': payment.description,
            'order_id': str(payment.id),
            'version': '3',
            'server_url': server_url,
            'result_url': result_url,
        }

        data = self.liqpay.cnb_data(params)
        signature = self.liqpay.cnb_signature(params)

        logger.info(
            f"Generated payment form for payment {payment.id}, amount: {payment.amount} UAH"
        )
        logger.info(f"Data: {data[:50]}... Signature: {signature[:20]}...")

        return {
            'data': data,
            'signature': signature,
            'checkout_url': self.checkout_url
        }

    def check_payment_status(self, order_id: str) -> Optional[Dict]:
        """
        Перевіряє статус платежу через LiqPay API.
        Використовується коли callback не спрацював.
        """
        logger.info(f"Checking payment status for order_id: {order_id}")

        try:
            params = {
                'action': 'status',
                'version': '3',
                'order_id': str(order_id)
            }

            # Генеруємо data і signature
            data = self.liqpay.cnb_data(params)
            signature = self.liqpay.cnb_signature(params)

            # Відправляємо запит до LiqPay API
            response = requests.post(
                self.api_url,
                data={
                    'data': data,
                    'signature': signature
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"LiqPay API response for {order_id}: {result}")
                return result
            else:
                logger.error(f"LiqPay API error: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Error calling LiqPay API: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error in check_payment_status: {e}", exc_info=True)
            return None

    def verify_callback(self, data: str, signature: str) -> Optional[Dict]:
        """Перевіряє підпис callback-запиту від LiqPay."""
        sign_string = settings.LIQPAY_PRIVATE_KEY + data + settings.LIQPAY_PRIVATE_KEY
        expected_signature = base64.b64encode(
            hashlib.sha1(sign_string.encode('utf-8')).digest()
        ).decode('ascii')

        if expected_signature != signature:
            logger.error("LiqPay callback signature mismatch!")
            logger.error(f"Expected: {expected_signature}")
            logger.error(f"Received: {signature}")
            return None

        try:
            decoded_data = json.loads(
                base64.b64decode(data).decode('utf-8')
            )
            logger.info(
                f"LiqPay callback verified for order_id: {decoded_data.get('order_id')}, "
                f"status: {decoded_data.get('status')}"
            )
            return decoded_data
        except Exception as e:
            logger.error(f"LiqPay callback data decode error: {e}", exc_info=True)
            return None


class CheckboxService:
    """Placeholder для Checkbox інтеграції."""

    def create_receipt(self, payment: StudioPayment, client_email: str = None) -> Optional[Dict]:
        logger.info(f"Checkbox receipt creation called for payment {payment.id}")
        # TODO: Імплементувати інтеграцію з Checkbox
        return None