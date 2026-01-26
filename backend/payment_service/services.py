import base64
import hashlib
import json
import uuid
import requests
import logging
from decimal import Decimal
from typing import Optional, Dict
from datetime import datetime, timezone

from django.conf import settings
from django.urls import reverse
from django.core.cache import cache
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

        🔒 З кешуванням та rate limiting
        """
        logger.info(f"Checking payment status for order_id: {order_id}")

        # 🔒 Перевіряємо кеш (5 секунд TTL для запобігання зайвим API викликам)
        cache_key = f"liqpay_status_{order_id}"
        cached_status = cache.get(cache_key)

        if cached_status:
            logger.info(f"Returning cached status for {order_id}")
            return cached_status

        # 🔒 Rate limiting для API викликів (максимум 5 запитів на хвилину для одного order_id)
        rate_limit_key = f"liqpay_rate_{order_id}"
        request_count = cache.get(rate_limit_key, 0)

        if request_count >= 5:
            logger.warning(f"⚠️ Rate limit exceeded for checking payment {order_id}")
            return None

        cache.set(rate_limit_key, request_count + 1, 60)

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

                # 🔒 Кешуємо результат
                cache.set(cache_key, result, 5)  # 5 секунд

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
        """
        Перевіряє підпис callback-запиту від LiqPay.

        🔒 З перевіркою timestamp для захисту від replay attacks
        """
        sign_string = settings.LIQPAY_PRIVATE_KEY + data + settings.LIQPAY_PRIVATE_KEY
        expected_signature = base64.b64encode(
            hashlib.sha1(sign_string.encode('utf-8')).digest()
        ).decode('ascii')

        if expected_signature != signature:
            logger.error("❌ LiqPay callback signature mismatch!")
            logger.error(f"Expected: {expected_signature}")
            logger.error(f"Received: {signature}")
            return None

        try:
            decoded_data = json.loads(
                base64.b64decode(data).decode('utf-8')
            )

            # 🔒 КРИТИЧНО: Перевірка timestamp (захист від replay attacks)
            # LiqPay може повертати 'create_date' у форматі timestamp
            if 'create_date' in decoded_data:
                try:
                    # Конвертуємо timestamp в datetime
                    callback_timestamp = int(decoded_data['create_date']) / 1000  # мілісекунди в секунди
                    callback_time = datetime.fromtimestamp(callback_timestamp, tz=timezone.utc)
                    current_time = datetime.now(timezone.utc)

                    time_diff = (current_time - callback_time).total_seconds()

                    # Якщо callback старіший за 1 годину - відхиляємо
                    if time_diff > 3600:
                        logger.error(
                            f"❌ Callback timestamp too old: {time_diff} seconds. "
                            "Possible replay attack!"
                        )
                        return None

                    if time_diff < -300:  # 5 хвилин в майбутньому
                        logger.error(
                            f"❌ Callback timestamp in future: {time_diff} seconds. "
                            "Possible clock skew or attack!"
                        )
                        return None

                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Could not parse create_date: {e}")

            # 🔒 Перевірка на дублікати callback (idempotency)
            callback_cache_key = f"liqpay_callback_{decoded_data.get('order_id')}_{signature[:16]}"

            if cache.get(callback_cache_key):
                logger.warning(
                    f"⚠️ Duplicate callback detected for order {decoded_data.get('order_id')}"
                )
                # Все одно повертаємо дані, але позначаємо як дублікат
                decoded_data['_is_duplicate'] = True
            else:
                # Зберігаємо на 1 годину
                cache.set(callback_cache_key, True, 3600)

            logger.info(
                f"✅ LiqPay callback verified for order_id: {decoded_data.get('order_id')}, "
                f"status: {decoded_data.get('status')}"
            )
            return decoded_data

        except Exception as e:
            logger.error(f"❌ LiqPay callback data decode error: {e}", exc_info=True)
            return None


class CheckboxService:
    """
    Сервіс для фіскалізації через Checkbox API.

    🔒 ВАЖЛИВО: Потрібно додати ваші credentials в settings.py:
    CHECKBOX_API_URL = "https://api.checkbox.ua/api/v1"
    CHECKBOX_LICENSE_KEY = "your_license_key"
    CHECKBOX_CASHIER_LOGIN = "your_cashier_login"
    CHECKBOX_CASHIER_PASSWORD = "your_cashier_password"
    """

    def __init__(self):
        self.api_url = getattr(settings, 'CHECKBOX_API_URL', None)
        self.license_key = getattr(settings, 'CHECKBOX_LICENSE_KEY', None)
        self.cashier_login = getattr(settings, 'CHECKBOX_CASHIER_LOGIN', None)
        self.cashier_password = getattr(settings, 'CHECKBOX_CASHIER_PASSWORD', None)

        # Перевіряємо чи налаштовано Checkbox
        self.is_configured = all([
            self.api_url,
            self.license_key,
            self.cashier_login,
            self.cashier_password
        ])

        if not self.is_configured:
            logger.warning(
                "⚠️ Checkbox is not configured. Please add credentials to settings.py"
            )

    def _get_auth_token(self) -> Optional[str]:
        """Отримує токен авторизації від Checkbox API."""
        if not self.is_configured:
            return None

        # Кешуємо токен на 30 хвилин
        cache_key = "checkbox_auth_token"
        cached_token = cache.get(cache_key)

        if cached_token:
            return cached_token

        try:
            response = requests.post(
                f"{self.api_url}/cashier/signin",
                json={
                    "login": self.cashier_login,
                    "password": self.cashier_password
                },
                headers={
                    "X-License-Key": self.license_key
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')

                # Кешуємо на 30 хвилин
                cache.set(cache_key, token, 1800)
                return token
            else:
                logger.error(f"Checkbox auth failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting Checkbox token: {e}", exc_info=True)
            return None

    def create_receipt(self, payment: StudioPayment, client_email: str) -> Optional[Dict]:
        """
        Створює чек в системі Checkbox.

        🔒 КРИТИЧНО: Вимагає реальний email клієнта
        """
        if not self.is_configured:
            logger.info("Checkbox not configured, skipping receipt creation")
            return None

        if not client_email or '@' not in client_email:
            logger.error(
                f"❌ Invalid email '{client_email}' for payment {payment.id}. "
                "Cannot create Checkbox receipt."
            )
            return None

        logger.info(f"Creating Checkbox receipt for payment {payment.id}, email: {client_email}")

        token = self._get_auth_token()
        if not token:
            logger.error("Failed to get Checkbox auth token")
            return None

        try:
            # Формуємо дані чека
            receipt_data = {
                "goods": [
                    {
                        "good": {
                            "code": str(payment.id),
                            "name": payment.description[:128],  # Обмеження Checkbox
                            "price": int(payment.amount * 100)  # В копійках
                        },
                        "quantity": 1000,  # В міліграмах (1000 = 1 шт)
                        "is_return": False
                    }
                ],
                "payment": {
                    "type": "CARD",
                    "value": int(payment.amount * 100)
                },
                "delivery": {
                    "email": client_email
                }
            }

            response = requests.post(
                f"{self.api_url}/receipts/sell",
                json=receipt_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-License-Key": self.license_key,
                    "Content-Type": "application/json"
                },
                timeout=15
            )

            if response.status_code in (200, 201):
                result = response.json()
                logger.info(
                    f"✅ Checkbox receipt created successfully: "
                    f"id={result.get('id')}, fiscal_code={result.get('fiscal_code')}"
                )
                return result
            else:
                logger.error(
                    f"❌ Checkbox receipt creation failed: "
                    f"{response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"❌ Error creating Checkbox receipt: {e}", exc_info=True)
            return None