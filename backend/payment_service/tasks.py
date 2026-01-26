"""
Celery tasks для повторної фіскалізації чеків.
Якщо ви не використовуєте Celery, можете використати django-cron або systemd timer.
"""
import logging
from celery import shared_task
from django.db import transaction
from django.core.cache import cache
from .models import StudioPayment
from .services import CheckboxService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    autoretry_for=(Exception,),
    retry_backoff=True,  # 🔒 Exponential backoff
    retry_backoff_max=3600,  # Максимум 1 година
    retry_jitter=True  # Додає випадковість до затримки
)
def retry_checkbox_receipt(self, payment_id: str):
    """
    Повторна спроба створення чека в Checkbox для оплаченого платежу.

    Args:
        payment_id: UUID платежу
    """
    # 🔒 КРИТИЧНО: Distributed lock для запобігання дублів
    lock_key = f"checkbox_retry_{payment_id}"
    lock_acquired = cache.add(lock_key, "locked", timeout=300)  # 5 хвилин

    if not lock_acquired:
        logger.warning(
            f"Task for payment {payment_id} is already running in another worker. Skipping."
        )
        return False

    try:
        with transaction.atomic():
            payment = StudioPayment.objects.select_for_update(nowait=False).get(
                id=payment_id,
                is_paid=True,
                checkbox_receipt_id__isnull=True  # Чек ще не створений
            )

            logger.info(
                f"Retrying Checkbox receipt creation for payment {payment_id}, "
                f"attempt {self.request.retries + 1}/{self.max_retries}"
            )

            # 🔒 КРИТИЧНО: Отримуємо email з бронювання
            client_email = None
            if hasattr(payment, 'booking') and payment.booking and payment.booking.email:
                client_email = payment.booking.email

            if not client_email:
                logger.error(
                    f"❌ Cannot create Checkbox receipt for payment {payment_id}: "
                    "no email available. Marking task as failed."
                )
                # Не ретраїмо, якщо немає email
                return False

            checkbox = CheckboxService()
            receipt_data = checkbox.create_receipt(
                payment,
                client_email=client_email
            )

            if receipt_data:
                payment.checkbox_receipt_id = receipt_data.get('id')
                payment.checkbox_fiscal_code = receipt_data.get('fiscal_code')
                payment.checkbox_status = receipt_data.get('status')
                payment.save(update_fields=[
                    'checkbox_receipt_id',
                    'checkbox_fiscal_code',
                    'checkbox_status'
                ])

                logger.info(
                    f"✅ Successfully created Checkbox receipt for payment {payment_id} "
                    f"on retry attempt {self.request.retries + 1}"
                )
                return True
            else:
                # Чек не створився, пробуємо ще раз
                logger.warning(
                    f"⚠️ Checkbox receipt creation failed for payment {payment_id} "
                    f"on attempt {self.request.retries + 1}/{self.max_retries}"
                )
                raise Exception("Checkbox receipt creation returned None")

    except StudioPayment.DoesNotExist:
        logger.info(
            f"Payment {payment_id} not found or already has receipt. "
            "Task completed."
        )
        return False

    except Exception as e:
        logger.error(
            f"❌ Error retrying Checkbox receipt for payment {payment_id}: {e}",
            exc_info=True
        )

        # Якщо досягли максимум спроб, логуємо критичну помилку
        if self.request.retries >= self.max_retries - 1:
            logger.critical(
                f"🚨 CRITICAL: Failed to create Checkbox receipt for payment {payment_id} "
                f"after {self.max_retries} attempts. Manual intervention required!"
            )
            # Тут можна відправити алерт адміністратору
            # send_admin_alert(payment_id, "Checkbox receipt creation failed")

        # Повторна спроба з exponential backoff (автоматично завдяки retry_backoff=True)
        raise

    finally:
        # Завжди звільняємо lock
        cache.delete(lock_key)


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True
)
def cleanup_expired_payments(self):
    """
    Періодична задача для очищення застарілих платежів.
    Запускати через celery beat кожні 24 години.
    """
    from django.utils import timezone
    from datetime import timedelta

    try:
        # Платежі старші 7 днів без оплати
        expiration_date = timezone.now() - timedelta(days=7)

        expired_payments = StudioPayment.objects.filter(
            is_paid=False,
            created_at__lt=expiration_date
        ).exclude(
            liqpay_status__in=['success', 'sandbox', 'processing']
        )

        count = expired_payments.count()

        if count > 0:
            logger.info(f"Found {count} expired payments to process")

            for payment in expired_payments:
                # Скасовуємо пов'язані бронювання
                if hasattr(payment, 'booking') and payment.booking:
                    booking = payment.booking
                    if booking.status == 'pending_payment':
                        booking.status = 'cancelled'
                        booking.admin_notes += f"\nAuto-cancelled: payment expired"
                        booking.save(update_fields=['status', 'admin_notes'])
                        logger.info(f"Cancelled booking {booking.id} due to payment expiration")

                # Оновлюємо статус платежу
                payment.liqpay_status = 'expired'
                payment.save(update_fields=['liqpay_status'])

            logger.info(f"✅ Successfully processed {count} expired payments")
        else:
            logger.info("No expired payments found")

        return count

    except Exception as e:
        logger.error(f"❌ Error in cleanup_expired_payments: {e}", exc_info=True)
        raise