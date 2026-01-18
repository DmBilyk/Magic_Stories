from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from django.db.models import Q
import logging

from .models import StudioBooking, BookingSettings
from studios.models import AdditionalService, Location

logger = logging.getLogger(__name__)


class BookingAvailabilityService:
    """Check and manage booking availability and time slots."""

    def __init__(self):
        self.settings = BookingSettings.get_settings()

    def get_available_slots(
            self,
            check_date: date,
            duration_hours: int,
            location_id: str = None
    ) -> List[Dict]:
        """Get all available time slots for date, duration, and optional location."""
        if check_date < date.today():
            return []

        existing_bookings = StudioBooking.objects.filter(
            booking_date=check_date,
            status__in=['pending_payment', 'paid', 'confirmed']
        )

        if location_id:
            existing_bookings = existing_bookings.filter(location_id=location_id)

        existing_bookings = existing_bookings.order_by('booking_time')

        available_slots = []
        current_time = self.settings.opening_time

        while True:
            start_datetime = datetime.combine(check_date, current_time)
            end_datetime = start_datetime + timedelta(hours=float(duration_hours))
            end_time = end_datetime.time()

            if end_time > self.settings.closing_time:
                break

            is_available = self._check_slot_availability(
                check_date,
                current_time,
                end_time,
                existing_bookings
            )

            available_slots.append({
                'start_time': current_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'available': is_available
            })

            next_datetime = start_datetime + timedelta(minutes=30)
            current_time = next_datetime.time()

            if current_time >= self.settings.closing_time:
                break

        return available_slots

    def _check_slot_availability(
            self,
            check_date: date,
            start_time: time,
            end_time: time,
            existing_bookings
    ) -> bool:
        """Check if specific time slot conflicts with existing bookings."""
        slot_start = datetime.combine(check_date, start_time)
        slot_end = datetime.combine(check_date, end_time)

        for booking in existing_bookings:
            booking_start = datetime.combine(check_date, booking.booking_time)
            booking_end = booking_start + timedelta(hours=booking.duration_hours)

            if slot_start < booking_end and slot_end > booking_start:
                return False

        return True

    def is_slot_available(
            self,
            booking_date: date,
            booking_time: time,
            duration_hours: int,
            location_id: str,
            exclude_booking_id: str = None
    ) -> Tuple[bool, str]:
        """Check if specific slot is available for location."""
        try:
            location = Location.objects.get(id=location_id, is_active=True)
        except Location.DoesNotExist:
            return False, "Invalid or inactive location"

        if booking_date < date.today():
            return False, "Cannot book dates in the past"

        max_date = date.today() + timedelta(days=self.settings.advance_booking_days)
        if booking_date > max_date:
            return False, f"Cannot book more than {self.settings.advance_booking_days} days in advance"

        if booking_time < self.settings.opening_time:
            return False, f"Studio opens at {self.settings.opening_time}"

        start_datetime = datetime.combine(booking_date, booking_time)
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        end_time = end_datetime.time()

        if end_time > self.settings.closing_time:
            return False, f"Booking extends past closing time ({self.settings.closing_time})"

        conflicts = StudioBooking.objects.filter(
            location=location,
            booking_date=booking_date,
            status__in=['pending_payment', 'paid', 'confirmed']
        )

        if exclude_booking_id:
            conflicts = conflicts.exclude(id=exclude_booking_id)

        for conflict in conflicts:
            conflict_start = datetime.combine(booking_date, conflict.booking_time)
            conflict_end = conflict_start + timedelta(hours=conflict.duration_hours)

            if start_datetime < conflict_end and end_datetime > conflict_start:
                return False, f"Time slot conflicts with existing booking at {conflict.booking_time}"

        return True, "Slot is available"

    def get_next_available_slot(
            self,
            start_date: date,
            duration_hours: int,
            location_id: str = None,
            days_to_check: int = 7
    ) -> Optional[Dict]:
        """Find next available slot starting from given date."""
        current_date = start_date
        end_date = start_date + timedelta(days=days_to_check)

        while current_date <= end_date:
            slots = self.get_available_slots(current_date, duration_hours, location_id)
            available = [s for s in slots if s['available']]

            if available:
                return {
                    'date': current_date.isoformat(),
                    'time_slot': available[0]
                }

            current_date += timedelta(days=1)

        return None

    def get_location_availability_calendar(
            self,
            location_id: str,
            start_date: date,
            end_date: date,
            duration_hours: int = 1
    ) -> Dict[str, List[Dict]]:
        """Get availability calendar for specific location within date range."""
        calendar = {}
        current_date = start_date

        while current_date <= end_date:
            slots = self.get_available_slots(current_date, duration_hours, location_id)
            calendar[current_date.isoformat()] = slots
            current_date += timedelta(days=1)

        return calendar


class BookingCalculationService:
    """Calculate booking costs and pricing breakdown."""

    @staticmethod
    def calculate_booking_cost(
            duration_hours: int,
            location_id: str = None,
            additional_service_ids: List[str] = None,
            settings: BookingSettings = None
    ) -> Dict[str, Decimal]:
        """Calculate total cost, deposit, and breakdown using location or default rate."""
        if settings is None:
            settings = BookingSettings.get_settings()

        if location_id:
            try:
                location = Location.objects.get(id=location_id, is_active=True)
                hourly_rate = location.hourly_rate
            except Location.DoesNotExist:
                hourly_rate = settings.base_price_per_hour
        else:
            hourly_rate = settings.base_price_per_hour

        base_cost = hourly_rate * duration_hours
        services_cost = Decimal('0.00')

        if additional_service_ids:
            services = AdditionalService.objects.filter(
                id__in=additional_service_ids,
                is_active=True
            )
            services_cost = sum(service.price for service in services)

        total = base_cost + services_cost
        deposit = (total * settings.deposit_percentage) / Decimal('100.00')

        return {
            'base_cost': base_cost,
            'hourly_rate': hourly_rate,
            'services_cost': services_cost,
            'total_amount': total,
            'deposit_amount': deposit.quantize(Decimal('0.01')),
            'deposit_percentage': settings.deposit_percentage
        }


class BookingManagementService:
    """Manage booking lifecycle and status transitions."""

    @staticmethod
    def cancel_booking(booking: StudioBooking, reason: str = None) -> bool:
        """Cancel booking with optional reason."""
        if booking.status in ['completed', 'cancelled']:
            return False

        booking.status = 'cancelled'
        if reason:
            booking.admin_notes = f"{booking.admin_notes}\nCancellation reason: {reason}"
        booking.save()

        return True

    @staticmethod
    def confirm_booking(booking: StudioBooking) -> bool:
        """Confirm paid booking."""
        if booking.status != 'paid':
            return False

        booking.status = 'confirmed'
        booking.save()

        return True

    @staticmethod
    def complete_booking(booking: StudioBooking) -> bool:
        """Mark booking as completed."""
        if booking.status != 'confirmed':
            return False

        booking.status = 'completed'
        booking.save()

        return True

    @staticmethod
    def update_payment_status(booking: StudioBooking) -> bool:
        """Update booking status based on payment status."""
        if not booking.payment:
            logger.warning(f"Booking {booking.id} has no payment attached")
            return False

        try:
            # Оновлюємо payment з БД на випадок, якщо він змінився
            booking.payment.refresh_from_db()

            logger.info(
                f"Checking payment for booking {booking.id}: "
                f"is_paid={booking.payment.is_paid}, "
                f"liqpay_status={booking.payment.liqpay_status}, "
                f"current_booking_status={booking.status}"
            )

            # Якщо оплата успішна і статус все ще 'pending_payment'
            if booking.payment.is_paid and booking.status == 'pending_payment':
                booking.status = 'paid'
                booking.save(update_fields=['status'])
                logger.info(f"✅ Booking {booking.id} status updated to 'paid' via update_payment_status")
                return True

            # Якщо оплата не успішна і статус 'pending_payment', можна скасувати
            if not booking.payment.is_paid and booking.status == 'pending_payment':
                # Опціонально: автоматично скасовувати через деякий час
                logger.info(f"Booking {booking.id} still pending payment, no action taken")
                return False

            logger.info(f"No status update needed for booking {booking.id}")
            return False

        except Exception as e:
            logger.error(f"Error updating payment status for booking {booking.id}: {e}", exc_info=True)
            return False

    @staticmethod
    def get_upcoming_bookings(
            days: int = 7,
            location_id: str = None
    ) -> List[StudioBooking]:
        """Get upcoming bookings, optionally filtered by location."""
        today = date.today()
        end_date = today + timedelta(days=days)

        queryset = StudioBooking.objects.filter(
            booking_date__range=[today, end_date],
            status__in=['paid', 'confirmed']
        )

        if location_id:
            queryset = queryset.filter(location_id=location_id)

        return queryset.order_by('booking_date', 'booking_time')

    @staticmethod
    def get_bookings_by_status(
            status: str,
            location_id: str = None
    ) -> List[StudioBooking]:
        """Get bookings by status, optionally filtered by location."""
        queryset = StudioBooking.objects.filter(status=status)

        if location_id:
            queryset = queryset.filter(location_id=location_id)

        return queryset.order_by('-created_at')

    @staticmethod
    def get_location_bookings(
            location_id: str,
            start_date: date = None,
            end_date: date = None
    ) -> List[StudioBooking]:
        """Get all bookings for specific location in date range."""
        queryset = StudioBooking.objects.filter(location_id=location_id)

        if start_date:
            queryset = queryset.filter(booking_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(booking_date__lte=end_date)

        return queryset.order_by('booking_date', 'booking_time')