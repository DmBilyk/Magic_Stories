from rest_framework import serializers
from .models import StudioBooking, BookingSettings
from studios.models import AdditionalService, Location
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from clothing.serializers import (
    BookingClothingItemSerializer,
    BookingClothingItemCreateSerializer
)
from clothing.services import ClothingBookingService


from props.serializers import (
    BookingPropItemSerializer,
    BookingPropItemCreateSerializer
)
from props.services import PropBookingService


class AdditionalServiceSerializer(serializers.ModelSerializer):
    """Serializer for additional services from studios app"""
    class Meta:
        model = AdditionalService
        fields = ['id', 'service_id', 'name', 'description', 'price', 'duration_minutes', 'is_active']
        read_only_fields = ['id']

class LocationBriefSerializer(serializers.ModelSerializer):
    """Brief location info for booking display"""
    class Meta:
        model = Location
        fields = ['id', 'name', 'hourly_rate', 'image_url']
        read_only_fields = ['id']


class BookingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSettings
        fields = [
            'base_price_per_hour',
            'deposit_percentage',
            'opening_time',
            'closing_time',
            'min_booking_hours',
            'max_booking_hours',
            'advance_booking_days',
            'is_booking_enabled',
            'maintenance_message'
        ]


class StudioBookingSerializer(serializers.ModelSerializer):
    # NEW: Location fields
    location = LocationBriefSerializer(read_only=True)
    location_id = serializers.UUIDField(write_only=True)

    additional_services = AdditionalServiceSerializer(many=True, read_only=True)
    additional_service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    clothing_items = BookingClothingItemCreateSerializer(
        many=True,
        write_only=True,
        required=False,
        allow_empty=True
    )
    clothing_items_display = BookingClothingItemSerializer(
        source='clothing_items',
        many=True,
        read_only=True
    )
    clothing_summary = serializers.SerializerMethodField()

    prop_items = BookingPropItemCreateSerializer(
        many=True,
        write_only=True,
        required=False,
        allow_empty=True
    )
    prop_items_display = BookingPropItemSerializer(
        source='prop_items',
        many=True,
        read_only=True
    )
    prop_summary = serializers.SerializerMethodField()

    end_time = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()



    class Meta:
        model = StudioBooking
        fields = [
            'id',
            'location',
            'location_id',
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'booking_date',
            'booking_time',
            'duration_hours',
            'additional_services',
            'additional_service_ids',
            'clothing_items',
            'clothing_items_display',
            'clothing_summary',
            'prop_items',
            'prop_items_display',
            'prop_summary',
            'base_price_per_hour',
            'services_total',
            'total_amount',
            'deposit_amount',
            'deposit_percentage',
            'status',
            'notes',
            'end_time',
            'payment_status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'location',
            'base_price_per_hour',
            'services_total',
            'total_amount',
            'deposit_amount',
            'deposit_percentage',
            'status',
            'end_time',
            'payment_status',
            'clothing_items_display',
            'clothing_summary',
            'prop_items_display',
            'prop_summary',
            'created_at',
            'updated_at'
        ]


    def get_end_time(self, obj):
        return obj.get_end_time()

    def get_payment_status(self, obj):
        if obj.payment:
            return {
                'is_paid': obj.payment.is_paid,
                'liqpay_status': obj.payment.liqpay_status,
                'checkbox_status': obj.payment.checkbox_status
            }
        return None

    def validate_location_id(self, value):
        """Validate location exists and is active"""
        try:
            location = Location.objects.get(id=value, is_active=True)
        except Location.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive location")
        return value

    def validate_additional_service_ids(self, value):
        """Validate services exist and are active"""
        if value:
            services = AdditionalService.objects.filter(
                id__in=value,
                is_active=True
            )
            if services.count() != len(value):
                raise serializers.ValidationError("One or more invalid service IDs")
        return value


    def get_clothing_summary(self, obj):
        """Get summary of clothing rental costs"""
        try:
            service = ClothingBookingService()
            return service.get_booking_clothing_summary(obj)
        except:
            return None

    def validate_clothing_items(self, value):
        """Validate clothing items don't exceed limit"""
        if value and len(value) > 10:
            raise serializers.ValidationError(
                "Не можна додати більше 10 одиниць одягу до одного бронювання"
            )
        return value

    def get_prop_summary(self, obj):
        """Get summary of prop rental costs"""
        try:
            service = PropBookingService()
            return service.get_booking_prop_summary(obj)
        except:
            return None

    def validate_prop_items(self, value):
        """Validate prop items don't exceed limit"""
        if value and len(value) > 20:
            raise serializers.ValidationError(
                "Cannot add more than 20 prop items to a single booking"
            )
        return value

    def validate_booking_date(self, value):
        """Validate booking date is in the future and within allowed range"""
        today = date.today()
        settings = BookingSettings.get_settings()

        if value < today:
            raise serializers.ValidationError("Cannot book dates in the past")

        max_date = today + timedelta(days=settings.advance_booking_days)
        if value > max_date:
            raise serializers.ValidationError(
                f"Cannot book more than {settings.advance_booking_days} days in advance"
            )

        return value

    def validate_duration_hours(self, value):
        """Validate duration is within allowed range"""
        settings = BookingSettings.get_settings()

        if value < settings.min_booking_hours:
            raise serializers.ValidationError(
                f"Minimum booking duration is {settings.min_booking_hours} hour(s)"
            )

        if value > settings.max_booking_hours:
            raise serializers.ValidationError(
                f"Maximum booking duration is {settings.max_booking_hours} hour(s)"
            )

        return value

    def validate(self, data):
        """Validate booking doesn't conflict with existing bookings for this location"""
        settings = BookingSettings.get_settings()

        if not settings.is_booking_enabled:
            raise serializers.ValidationError(
                settings.maintenance_message or "Booking is currently disabled"
            )

        location_id = data.get('location_id')
        booking_date = data.get('booking_date')
        booking_time = data.get('booking_time')
        duration_hours = data.get('duration_hours')

        # Validate time is within working hours
        if booking_time < settings.opening_time:
            raise serializers.ValidationError({
                'booking_time': f"Studio opens at {settings.opening_time}"
            })

        # Calculate end time
        start_datetime = datetime.combine(booking_date, booking_time)
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        end_time = end_datetime.time()

        if end_time > settings.closing_time:
            raise serializers.ValidationError({
                'duration_hours': f"Booking would extend past closing time ({settings.closing_time})"
            })

        # UPDATED: Check for conflicts with existing bookings for THIS LOCATION
        conflicts = StudioBooking.objects.filter(
            location_id=location_id,  # NEW: Filter by location
            booking_date=booking_date,
            status__in=['pending_payment', 'paid', 'confirmed']
        ).exclude(id=self.instance.id if self.instance else None)

        for conflict in conflicts:
            conflict_start = datetime.combine(booking_date, conflict.booking_time)
            conflict_end = conflict_start + timedelta(hours=conflict.duration_hours)

            # Check if times overlap
            if (start_datetime < conflict_end and end_datetime > conflict_start):
                raise serializers.ValidationError({
                    'booking_time': f"Time slot conflicts with existing booking at {conflict.booking_time}"
                })

        clothing_items = data.get('clothing_items', [])
        if clothing_items:
            from clothing.services import ClothingAvailabilityService
            service = ClothingAvailabilityService()

            is_valid, errors = service.validate_booking_items(
                clothing_items,
                booking_date,
                booking_time,
                duration_hours,
                exclude_booking_id=str(self.instance.id) if self.instance else None
            )

            if not is_valid:
                raise serializers.ValidationError({
                    'clothing_items': errors
                })

        prop_items = data.get('prop_items', [])
        if prop_items:
            from props.services import PropAvailabilityService
            service = PropAvailabilityService()

            is_valid, errors = service.validate_booking_items(
                prop_items,
                booking_date,
                booking_time,
                duration_hours,
                exclude_booking_id=str(self.instance.id) if self.instance else None
            )

            if not is_valid:
                raise serializers.ValidationError({
                    'prop_items': errors
                })

        return data

    def create(self, validated_data):
        """Create booking with calculated prices from location"""
        additional_service_ids = validated_data.pop('additional_service_ids', [])
        location_id = validated_data.get('location_id')

        clothing_items = validated_data.pop('clothing_items', [])

        prop_items = validated_data.pop('prop_items', [])

        settings = BookingSettings.get_settings()

        try:
            location = Location.objects.get(id=location_id, is_active=True)
            validated_data['base_price_per_hour'] = location.hourly_rate
        except Location.DoesNotExist:
            validated_data['base_price_per_hour'] = settings.base_price_per_hour

        # Set pricing from settings
        validated_data['deposit_percentage'] = settings.deposit_percentage

        # Create booking
        booking = StudioBooking.objects.create(**validated_data)

        # Add additional services
        if additional_service_ids:
            services = AdditionalService.objects.filter(
                id__in=additional_service_ids,
                is_active=True
            )
            booking.additional_services.set(services)
            booking.services_total = sum(service.price for service in services)

            # Calculate totals
        booking.total_amount = booking.calculate_total()
        booking.deposit_amount = booking.calculate_deposit()
        booking.save()

        if clothing_items:
            clothing_service = ClothingBookingService()
            success, errors, clothing_cost = clothing_service.add_clothing_to_booking(
                booking,
                clothing_items
            )

            if success and clothing_cost > 0:
                # Update booking total to include clothing
                booking.total_amount += clothing_cost
                booking.deposit_amount = booking.calculate_deposit()
                booking.save(update_fields=['total_amount', 'deposit_amount'])

                # Update payment amount if payment exists
                if booking.payment:
                    booking.payment.amount = booking.deposit_amount
                    booking.payment.save(update_fields=['amount'])

        if prop_items:
            prop_service = PropBookingService()
            success, errors, prop_cost = prop_service.add_props_to_booking(
                booking,
                prop_items
            )

            if success and prop_cost > 0:
                # Update booking total to include props
                booking.total_amount += prop_cost
                booking.deposit_amount = booking.calculate_deposit()
                booking.save(update_fields=['total_amount', 'deposit_amount'])

                # Update payment amount if payment exists
                if booking.payment:
                    booking.payment.amount = booking.deposit_amount
                    booking.payment.save(update_fields=['amount'])

        return booking


class AvailabilityCheckSerializer(serializers.Serializer):
    """Serializer for checking availability"""
    date = serializers.DateField()
    duration_hours = serializers.IntegerField(min_value=1, max_value=24)
    location_id = serializers.UUIDField(required=False)

    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Cannot check availability for past dates")
        return value

    def validate_location_id(self, value):
        """Validate location exists and is active"""
        if value:
            try:
                Location.objects.get(id=value, is_active=True)
            except Location.DoesNotExist:
                raise serializers.ValidationError("Invalid or inactive location")
        return value

class AvailableSlotSerializer(serializers.Serializer):
    """Serializer for available time slots"""
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    available = serializers.BooleanField()


class AdminBookingSerializer(serializers.ModelSerializer):
    """Extended serializer for admin views"""
    location = LocationBriefSerializer(read_only=True)
    location_id = serializers.UUIDField(write_only=True, required=False)
    additional_services = AdditionalServiceSerializer(many=True, read_only=True)
    additional_service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    end_time = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()

    class Meta:
        model = StudioBooking
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_end_time(self, obj):
        return obj.get_end_time()

    def get_payment_details(self, obj):
        if obj.payment:
            return {
                'payment_id': str(obj.payment.id),
                'amount': str(obj.payment.amount),
                'is_paid': obj.payment.is_paid,
                'liqpay_status': obj.payment.liqpay_status,
                'checkbox_receipt_id': obj.payment.checkbox_receipt_id,
                'checkbox_fiscal_code': obj.payment.checkbox_fiscal_code,
                'checkbox_status': obj.payment.checkbox_status
            }
        return None

    # Disable most validation for admin
    def validate(self, data):
        # Only validate location if provided
        location_id = data.get('location_id')
        if location_id:
            try:
                Location.objects.get(id=location_id, is_active=True)
            except Location.DoesNotExist:
                raise serializers.ValidationError({
                    'location_id': 'Invalid or inactive location'
                })
        return data
