from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from django.db import transaction
from django.db.models import Q, Sum
from .models import (
    ClothingItem,
    BookingClothingItem,
    ClothingRentalSettings
)


class ClothingAvailabilityService:
    """Service for checking clothing availability"""

    def __init__(self):
        self.settings = ClothingRentalSettings.get_settings()

    def check_item_availability(
            self,
            clothing_item_id: str,
            booking_date,
            booking_time,
            duration_hours: int,
            requested_quantity: int = 1,
            exclude_booking_id: str = None
    ) -> Tuple[bool, str, int]:
        """
        Check if clothing item is available for booking

        Returns:
            Tuple[is_available, message, available_quantity]
        """
        try:
            item = ClothingItem.objects.get(id=clothing_item_id)
        except ClothingItem.DoesNotExist:
            return False, "Clothing item not found", 0

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
            item: ClothingItem,
            booking_date,
            booking_time,
            duration_hours: int,
            exclude_booking_id: str = None
    ) -> int:
        """Calculate available quantity for a time slot"""
        from bookings.models import StudioBooking
        from decimal import Decimal

        # Calculate end time
        booking_datetime = datetime.combine(booking_date, booking_time)
        duration_minutes = int(Decimal(str(duration_hours)) * 60)
        end_datetime = booking_datetime + timedelta(minutes=duration_minutes)
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
        rented_count = BookingClothingItem.objects.filter(
            booking__in=overlapping_bookings,
            clothing_item=item
        ).aggregate(total=Sum('quantity'))['total'] or 0

        return max(0, item.quantity - rented_count)

    def get_available_items_for_slot(
            self,
            booking_date,
            booking_time,
            duration_hours: int
    ) -> List[Dict]:
        """
        Get all available clothing items for a specific time slot

        Returns:
            List of dicts with item details and available quantity
        """
        items = ClothingItem.objects.filter(
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
            clothing_items: List[Dict],
            booking_date,
            booking_time,
            duration_hours: int,
            exclude_booking_id: str = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate all clothing items for a booking

        Args:
            clothing_items: List of {'clothing_item_id': str, 'quantity': int}

        Returns:
            Tuple[is_valid, error_messages]
        """
        if not self.settings.is_rental_enabled:
            return False, ["Clothing rental is currently disabled"]

        if len(clothing_items) > self.settings.max_items_per_booking:
            return False, [
                f"Cannot add more than {self.settings.max_items_per_booking} items per booking"
            ]

        errors = []
        for item_data in clothing_items:
            is_available, message, _ = self.check_item_availability(
                item_data['clothing_item_id'],
                booking_date,
                booking_time,
                duration_hours,
                item_data.get('quantity', 1),
                exclude_booking_id
            )

            if not is_available:
                errors.append(message)

        return len(errors) == 0, errors


class ClothingCostCalculationService:
    """Service for calculating clothing rental costs"""

    @staticmethod
    def calculate_clothing_cost(clothing_items: List[Dict]) -> Dict:
        """
        Calculate total cost for clothing items

        Args:
            clothing_items: List of {'clothing_item_id': str, 'quantity': int}

        Returns:
            Dict with cost breakdown
        """
        items_cost = Decimal('0.00')
        items_details = []

        for item_data in clothing_items:
            try:
                item = ClothingItem.objects.get(
                    id=item_data['clothing_item_id'],
                    is_active=True,
                    is_available=True
                )
                quantity = item_data.get('quantity', 1)
                item_total = item.price * quantity

                items_cost += item_total
                items_details.append({
                    'item_id': str(item.id),
                    'name': item.name,
                    'size': item.size,
                    'quantity': quantity,
                    'price_per_item': str(item.price),
                    'total': str(item_total)
                })
            except ClothingItem.DoesNotExist:
                continue

        return {
            'clothing_cost': str(items_cost),
            'items_count': len(items_details),
            'items_details': items_details
        }


class ClothingBookingService:
    """Service for managing clothing in bookings"""

    def __init__(self):
        self.availability_service = ClothingAvailabilityService()
        self.cost_service = ClothingCostCalculationService()

    @transaction.atomic
    def add_clothing_to_booking(
            self,
            booking,
            clothing_items: List[Dict]
    ) -> Tuple[bool, List[str], Decimal]:
        """
        Add clothing items to a booking

        Args:
            booking: StudioBooking instance
            clothing_items: List of {'clothing_item_id': str, 'quantity': int}

        Returns:
            Tuple[success, error_messages, total_clothing_cost]
        """
        # Validate items
        is_valid, errors = self.availability_service.validate_booking_items(
            clothing_items,
            booking.booking_date,
            booking.booking_time,
            booking.duration_hours
        )

        if not is_valid:
            return False, errors, Decimal('0.00')

        # Add items to booking
        total_cost = Decimal('0.00')
        for item_data in clothing_items:
            item = ClothingItem.objects.get(id=item_data['clothing_item_id'])
            quantity = item_data.get('quantity', 1)

            BookingClothingItem.objects.create(
                booking=booking,
                clothing_item=item,
                quantity=quantity,
                price_at_booking=item.price
            )

            total_cost += item.price * quantity

        return True, [], total_cost

    @transaction.atomic
    def update_booking_clothing(
            self,
            booking,
            clothing_items: List[Dict]
    ) -> Tuple[bool, List[str], Decimal]:
        """
        Update clothing items in a booking

        Args:
            booking: StudioBooking instance
            clothing_items: List of {'clothing_item_id': str, 'quantity': int}

        Returns:
            Tuple[success, error_messages, total_clothing_cost]
        """
        # Remove existing clothing items
        BookingClothingItem.objects.filter(booking=booking).delete()

        # Add new items
        return self.add_clothing_to_booking(booking, clothing_items)

    def calculate_booking_with_clothing(
            self,
            duration_hours: int,
            additional_service_ids: List[str],
            clothing_items: List[Dict],
            settings=None
    ) -> Dict:
        """
        Calculate complete booking cost including clothing

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

        # Calculate clothing cost
        clothing_calculation = self.cost_service.calculate_clothing_cost(
            clothing_items
        )

        # Combine costs
        base_total = Decimal(base_calculation['total_amount'])
        clothing_cost = Decimal(clothing_calculation['clothing_cost'])
        grand_total = base_total + clothing_cost

        # Recalculate deposit based on grand total
        deposit_percentage = Decimal(base_calculation['deposit_percentage'])
        deposit_amount = (grand_total * deposit_percentage / 100).quantize(
            Decimal('0.01')
        )

        return {
            'base_cost': base_calculation['base_cost'],
            'services_cost': base_calculation['services_cost'],
            'clothing_cost': str(clothing_cost),
            'clothing_items': clothing_calculation['items_details'],
            'total_amount': str(grand_total),
            'deposit_amount': str(deposit_amount),
            'deposit_percentage': str(deposit_percentage)
        }

    def get_booking_clothing_summary(self, booking) -> Dict:
        """Get summary of clothing items in a booking"""
        items = BookingClothingItem.objects.filter(
            booking=booking
        ).select_related('clothing_item')

        total_cost = Decimal('0.00')
        items_list = []

        for booking_item in items:
            item_total = booking_item.get_total_price()
            total_cost += item_total

            items_list.append({
                'id': str(booking_item.id),
                'name': booking_item.clothing_item.name,
                'size': booking_item.clothing_item.size,
                'quantity': booking_item.quantity,
                'price': str(booking_item.price_at_booking),
                'total': str(item_total)
            })

        return {
            'items': items_list,
            'items_count': len(items_list),
            'total_cost': str(total_cost)
        }