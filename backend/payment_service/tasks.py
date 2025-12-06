"""
Celery tasks для повторної фіскалізації чеків.
Якщо ви не використовуєте Celery, можете використати django-cron або systemd timer.
"""
import logging
from celery import shared_task
from django.db import transaction
from .models import StudioPayment
from .services import CheckboxService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=600  # 10 хвилин між спробами
)
def retry_checkbox_receipt(self, payment_id: str):
    """
    Повторна спроба створення чека в Checkbox для оплаченого платежу.

    Args:
        payment_id: UUID платежу
    """
    try:
        with transaction.atomic():
            payment = StudioPayment.objects.select_for_update().get(
                id=payment_id,
                is_paid=True,
                checkbox_receipt_id__isnull=True  # Чек ще не створений
            )

            logger.info(
                f"Retrying Checkbox receipt creation for payment {payment_id}, "
                f"attempt {self.request.retries + 1}"
            )

            checkbox = CheckboxService()
            # Тут можна отримати email з пов'язаної моделі користувача
            receipt_data = checkbox.create_receipt(
                payment,
                client_email="client_email@example.com"
            )

            if receipt_data:
                payment.checkbox_receipt_id = receipt_data.get('id')
                payment.checkbox_fiscal_code = receipt_data.get('fiscal_code')
                payment.checkbox_status = receipt_data.get('status')
                payment.save()

                logger.info(
                    f"Successfully created Checkbox receipt for payment {payment_id} "
                    f"on retry attempt {self.request.retries + 1}"
                )
                return True
            else:
                # Чек не створився, пробуємо ще раз
                logger.warning(
                    f"Checkbox receipt creation failed for payment {payment_id} "
                    f"on attempt {self.request.retries + 1}"
                )
                raise Exception("Checkbox receipt creation failed")

    except StudioPayment.DoesNotExist:
        logger.info(
            f"Payment {payment_id} not found or already has receipt. "
            "Task completed."
        )
        return False

    except Exception as e:
        logger.error(
            f"Error retrying Checkbox receipt for payment {payment_id}: {e}",
            exc_info=True
        )

        # Повторна спроба з exponential backoff
        raise self.retry(exc=e)