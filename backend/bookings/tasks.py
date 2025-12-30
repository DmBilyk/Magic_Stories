from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

from .models import StudioBooking

logger = logging.getLogger(__name__)


@shared_task
def cleanup_unpaid_bookings():
    """
    Скасовує бронювання, які залишилися в pending_payment більше 30 хвилин.
    Звільняє слот для інших користувачів.
    """
    cutoff_time = timezone.now() - timedelta(minutes=30)

    pending_bookings = StudioBooking.objects.filter(
        status='pending_payment',  # ✅ Правильний статус
        created_at__lt=cutoff_time
    ).select_related('payment', 'location')

    cancelled_count = 0
    errors = []

    for booking in pending_bookings:
        try:
            with transaction.atomic():
                # Перевіряємо статус оплати (можливо вже оплачено)
                if booking.payment and booking.payment.is_paid:
                    logger.info(f"Booking {booking.id} is actually paid, skipping cancellation")
                    continue

                # Скасовуємо бронювання
                booking.status = 'cancelled'
                booking.admin_notes = (
                    f"{booking.admin_notes}\n"
                    f"Auto-cancelled: Payment window expired at {timezone.now()}"
                ).strip()
                booking.save(update_fields=['status', 'admin_notes'])

                cancelled_count += 1
                logger.info(
                    f"✅ Booking {booking.id} cancelled - "
                    f"Location: {booking.location.name}, "
                    f"Date: {booking.booking_date} {booking.booking_time}"
                )

        except Exception as e:
            error_msg = f"Error cancelling booking {booking.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

    # Фінальний звіт
    logger.info(
        f"Cleanup completed: {cancelled_count} bookings cancelled, "
        f"{len(errors)} errors"
    )

    if errors:
        logger.error(f"Cleanup errors: {errors}")

    return {
        'cancelled': cancelled_count,
        'errors': len(errors)
    }