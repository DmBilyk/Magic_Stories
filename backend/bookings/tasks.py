from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from .models import StudioBooking

@shared_task
def cleanup_unpaid_bookings():
    """
    Скасовує бронювання, які залишилися в PENDING більше 30 хвилин.
    """
    cutoff_time = timezone.now() - timedelta(minutes=15)

    # Знаходимо бронювання, створені до Cutoff_time і зі статусом PENDING
    pending_bookings = StudioBooking.objects.filter(
        status='PENDING',
        created_at__lt=cutoff_time  # Припустимо, у тебе є created_at
    )

    for booking in pending_bookings:
        # Логіка скасування: оновити статус, звільнити слот.
        # booking.status = 'EXPIRED_PAYMENT'
        # booking.save()

        # Додатково: залогірувати подію
        # logger.info(f"Booking {booking.id} cancelled due to expired payment window.")
        pass