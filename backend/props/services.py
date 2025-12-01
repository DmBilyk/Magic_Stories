from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from django.db import transaction
from django.db.models import Q, Sum
from .models import (
    PropItem,
    BookingPropItem,
    PropRentalSettings
)


class PropAvailabilityService:
    """Service for checking prop availability"""

    def __init__(self):
        self.settings = PropRentalSettings.get_settings()

    def check_item_availability(
            self,
            prop_item_id: str,
            booking_date,
            booking_time,
            duration_hours: int,
            requested_quantity: int = 1,
            exclude_booking_id: str = None
    ) -> Tuple[bool, str, int]:
        """
        Check if prop item is available for booking

        Returns:
            Tuple[is_available, message, available_quantity]
        """
        try:
            item = PropItem.objects.get(id=prop_item_id)
        except PropItem.DoesNotExist:
            return False, "Prop item not found", 0

        # Check if item is active and available
        if not item.is_active:
            return False, f"{item.name} is no longer available", 0

        if not item.is_available:
            return False, f"{item.name} is currently unavailable", 0

        # Calculate available quantity for the time slot
        available_qty = self._get_available_quantity(
            item,
            booking_date,
            booking_time,
            duration_hours,
            exclude_booking_id
        )

        if requested_quantity > available_qty:
            return (
                False,
                f"Only {available_qty} unit(s) of {item.name} available for this time slot",
                available_qty
            )

        return True, f"{item.name} is available", available_qty

    def _get_available_quantity(
            self,
            item: PropItem,
            booking_date,
            booking_time,
            duration_hours: int,
            exclude_booking_id: str = None
    ) -> int:
        """Calculate available quantity for a time slot"""
        from bookings.models import StudioBooking

        # Calculate end time
        booking_datetime = datetime.combine(booking_date, booking_time)
        end_datetime = booking_datetime + timedelta(hours=duration_hours)
        end_time = end_datetime.time()

        # Find overlapping bookings
        overlapping_bookings = StudioBooking.objects.filter(
            booking_date=booking_date,
            status__in=['pending_payment', 'paid', 'confirmed']
        )

        # Exclude specific booking if updating
        if exclude_booking_id:
            overlapping_bookings = overlapping_bookings.exclude(id=exclude_booking_id)

        # Filter by time overlap
        overlapping_bookings = overlapping_bookings.filter(
            Q(booking_time__lt=end_time) &
            Q(booking_time__gte=booking_time)
        )

        # Count rented quantity in overlapping bookings
        rented_count = BookingPropItem.objects.filter(
            booking__in=overlapping_bookings,
            prop_item=item
        ).aggregate(total=Sum('quantity'))['total'] or 0

        return max(0, item.quantity - rented_count)

    def get_available_items_for_slot(
            self,
            booking_date,
            booking_time,
            duration_hours: int
    ) -> List[Dict]:
        """
        Get all available prop items for a specific time slot

        Returns:
            List of dicts with item details and available quantity
        """
        items = PropItem.objects.filter(
            is_active=True,
            is_available=True
        ).select_related('category').prefetch_related('images')

        result = []
        for item in items:
            available_qty = self._get_available_quantity(
                item,
                booking_date,
                booking_time,
                duration_hours
            )

            if available_qty > 0:
                result.append({
                    'item': item,
                    'available_quantity': available_qty,
                    'total_quantity': item.quantity
                })

        return result

    def validate_booking_items(
            self,
            prop_items: List[Dict],
            booking_date,
            booking_time,
            duration_hours: int,
            exclude_booking_id: str = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate all prop items for a booking

        Args:
            prop_items: List of {'prop_item_id': str, 'quantity': int}

        Returns:
            Tuple[is_valid, error_messages]
        """
        if not self.settings.is_rental_enabled:
            return False, ["Prop rental is currently disabled"]

        if len(prop_items) > self.settings.max_items_per_booking:
            return False, [
                f"Cannot add more than {self.settings.max_items_per_booking} items per booking"
            ]

        errors = []
        for item_data in prop_items:
            is_available, message, _ = self.check_item_availability(
                item_data['prop_item_id'],
                booking_date,
                booking_time,
                duration_hours,
                item_data.get('quantity', 1),
                exclude_booking_id
            )

            if not is_available:
                errors.append(message)

        return len(errors) == 0, errors


class PropCostCalculationService:
    """Service for calculating prop rental costs"""

    @staticmethod
    def calculate_prop_cost(prop_items: List[Dict]) -> Dict:
        """
        Calculate total cost for prop items

        Args:
            prop_items: List of {'prop_item_id': str, 'quantity': int}

        Returns:
            Dict with cost breakdown
        """
        items_cost = Decimal('0.00')
        items_details = []

        for item_data in prop_items:
            try:
                item = PropItem.objects.get(
                    id=item_data['prop_item_id'],
                    is_active=True,
                    is_available=True
                )
                quantity = item_data.get('quantity', 1)
                item_total = item.price * quantity

                items_cost += item_total
                items_details.append({
                    'item_id': str(item.id),
                    'name': item.name,
                    'quantity': quantity,
                    'price_per_item': str(item.price),
                    'total': str(item_total)
                })
            except PropItem.DoesNotExist:
                continue

        return {
            'prop_cost': str(items_cost),
            'items_count': len(items_details),
            'items_details': items_details
        }


class PropBookingService:
    """Service for managing props in bookings"""

    def __init__(self):
        self.availability_service = PropAvailabilityService()
        self.cost_service = PropCostCalculationService()

    @transaction.atomic
    def add_props_to_booking(
            self,
            booking,
            prop_items: List[Dict]
    ) -> Tuple[bool, List[str], Decimal]:
        """
        Add prop items to a booking

        Args:
            booking: StudioBooking instance
            prop_items: List of {'prop_item_id': str, 'quantity': int}

        Returns:
            Tuple[success, error_messages, total_prop_cost]
        """
        # Validate items
        is_valid, errors = self.availability_service.validate_booking_items(
            prop_items,
            booking.booking_date,
            booking.booking_time,
            booking.duration_hours
        )

        if not is_valid:
            return False, errors, Decimal('0.00')

        # Add items to booking
        total_cost = Decimal('0.00')
        for item_data in prop_items:
            item = PropItem.objects.get(id=item_data['prop_item_id'])
            quantity = item_data.get('quantity', 1)

            BookingPropItem.objects.create(
                booking=booking,
                prop_item=item,
                quantity=quantity,
                price_at_booking=item.price
            )

            total_cost += item.price * quantity

        return True, [], total_cost

    @transaction.atomic
    def update_booking_props(
            self,
            booking,
            prop_items: List[Dict]
    ) -> Tuple[bool, List[str], Decimal]:
        """
        Update prop items in a booking

        Args:
            booking: StudioBooking instance
            prop_items: List of {'prop_item_id': str, 'quantity': int}

        Returns:
            Tuple[success, error_messages, total_prop_cost]
        """
        # Remove existing prop items
        BookingPropItem.objects.filter(booking=booking).delete()

        # Add new items
        return self.add_props_to_booking(booking, prop_items)

    def calculate_booking_with_props(
            self,
            duration_hours: int,
            additional_service_ids: List[str],
            prop_items: List[Dict],
            settings=None
    ) -> Dict:
        """
        Calculate complete booking cost including props

        This method is meant to be called from BookingCalculationService
        """
        from bookings.services import BookingCalculationService

        # Get base booking cost (studios + services)
        booking_service = BookingCalculationService()
        base_calculation = booking_service.calculate_booking_cost(
            duration_hours,
            additional_service_ids,
            settings
        )

        # Calculate prop cost
        prop_calculation = self.cost_service.calculate_prop_cost(
            prop_items
        )

        # Combine costs
        base_total = Decimal(base_calculation['total_amount'])
        prop_cost = Decimal(prop_calculation['prop_cost'])
        grand_total = base_total + prop_cost

        # Recalculate deposit based on grand total
        deposit_percentage = Decimal(base_calculation['deposit_percentage'])
        deposit_amount = (grand_total * deposit_percentage / 100).quantize(
            Decimal('0.01')
        )

        return {
            'base_cost': base_calculation['base_cost'],
            'services_cost': base_calculation['services_cost'],
            'prop_cost': str(prop_cost),
            'prop_items': prop_calculation['items_details'],
            'total_amount': str(grand_total),
            'deposit_amount': str(deposit_amount),
            'deposit_percentage': str(deposit_percentage)
        }

    def get_booking_prop_summary(self, booking) -> Dict:
        """Get summary of prop items in a booking"""
        items = BookingPropItem.objects.filter(
            booking=booking
        ).select_related('prop_item')

        total_cost = Decimal('0.00')
        items_list = []

        for booking_item in items:
            item_total = booking_item.get_total_price()
            total_cost += item_total

            items_list.append({
                'id': str(booking_item.id),
                'name': booking_item.prop_item.name,
                'quantity': booking_item.quantity,
                'price': str(booking_item.price_at_booking),
                'total': str(item_total)
            })

        return {
            'items': items_list,
            'items_count': len(items_list),
            'total_cost': str(total_cost)
        }