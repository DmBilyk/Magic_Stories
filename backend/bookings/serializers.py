from rest_framework import serializers
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from .models import StudioBooking, BookingSettings, AllInclusiveRequest
from studios.models import AdditionalService, Location
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
    """Additional service data from studios app."""

    class Meta:
        model = AdditionalService
        fields = ['id', 'service_id', 'name', 'description', 'price', 'duration_minutes', 'is_active']
        read_only_fields = ['id']


class LocationBriefSerializer(serializers.ModelSerializer):
    """Brief location info for booking display."""

    class Meta:
        model = Location
        fields = ['id', 'name', 'hourly_rate', 'image']
        read_only_fields = ['id']


class BookingSettingsSerializer(serializers.ModelSerializer):
    """Booking configuration settings."""

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
    """Main booking serializer with location, services, clothing, and props."""

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

    duration_hours = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=Decimal('0.5')
    )

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
            'updated_at',
            'is_all_inclusive',
            'all_inclusive_package',
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
            'is_all_inclusive',
            'all_inclusive_package',
        ]

    def get_end_time(self, obj):
        """Calculate and return booking end time."""
        return obj.get_end_time()

    def get_payment_status(self, obj):
        """Return payment status details if payment exists."""
        if obj.payment:
            return {
                'is_paid': obj.payment.is_paid,
                'liqpay_status': obj.payment.liqpay_status,
                'checkbox_status': obj.payment.checkbox_status
            }
        return None

    def get_clothing_summary(self, obj):
        """Get summary of clothing rental costs."""
        try:
            service = ClothingBookingService()
            return service.get_booking_clothing_summary(obj)
        except:
            return None

    def get_prop_summary(self, obj):
        """Get summary of prop rental costs."""
        try:
            service = PropBookingService()
            return service.get_booking_prop_summary(obj)
        except:
            return None

    def validate_location_id(self, value):
        """Validate location exists and is active."""
        try:
            location = Location.objects.get(id=value, is_active=True)
        except Location.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive location")
        return value

    def validate_additional_service_ids(self, value):
        """Validate services exist and are active."""
        if value:
            services = AdditionalService.objects.filter(
                id__in=value,
                is_active=True
            )
            if services.count() != len(value):
                raise serializers.ValidationError("One or more invalid service IDs")
        return value

    def validate_clothing_items(self, value):
        """Validate clothing items don't exceed limit."""
        if value and len(value) > 10:
            raise serializers.ValidationError(
                "Не можна додати більше 10 одиниць одягу до одного бронювання"
            )
        return value

    def validate_prop_items(self, value):
        """Validate prop items don't exceed limit."""
        if value and len(value) > 20:
            raise serializers.ValidationError(
                "Cannot add more than 20 prop items to a single booking"
            )
        return value

    def validate_booking_date(self, value):
        """Validate booking date is in future and within allowed range."""
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
        from decimal import Decimal

        settings = BookingSettings.get_settings()
        value = Decimal(str(value))

        if (value * 2) % 1 != 0:
            raise serializers.ValidationError(
                "Duration must be in 30-minute increments (e.g., 0.5, 1.0, 1.5)"
            )

        min_hours = Decimal(str(settings.min_booking_hours))
        max_hours = Decimal(str(settings.max_booking_hours))

        if value < min_hours:
            raise serializers.ValidationError(
                f"Minimum booking duration is {min_hours} hour(s)"
            )

        if value > max_hours:
            raise serializers.ValidationError(
                f"Maximum booking duration is {max_hours} hour(s)"
            )

        return value

    def validate(self, data):
        """Validate booking constraints and check for conflicts."""
        settings = BookingSettings.get_settings()

        if not settings.is_booking_enabled:
            raise serializers.ValidationError(
                settings.maintenance_message or "Booking is currently disabled"
            )

        location_id = data.get('location_id')
        booking_date = data.get('booking_date')
        booking_time = data.get('booking_time')
        duration_hours = data.get('duration_hours')

        if booking_time < settings.opening_time:
            raise serializers.ValidationError({
                'booking_time': f"Studio opens at {settings.opening_time}"
            })

        start_datetime = datetime.combine(booking_date, booking_time)
        duration_decimal = Decimal(str(duration_hours))
        duration_minutes = int(duration_decimal * 60)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_time = end_datetime.time()

        if end_time > settings.closing_time:
            raise serializers.ValidationError({
                'duration_hours': f"Booking would extend past closing time ({settings.closing_time})"
            })

        conflicts = StudioBooking.objects.filter(
            location_id=location_id,
            booking_date=booking_date,
            status__in=['pending_payment', 'paid', 'confirmed']
        ).exclude(id=self.instance.id if self.instance else None)

        for conflict in conflicts:
            conflict_start = datetime.combine(booking_date, conflict.booking_time)
            conflict_duration_minutes = int(Decimal(str(conflict.duration_hours)) * 60)
            conflict_end = conflict_start + timedelta(minutes=conflict_duration_minutes)

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
        """Create booking with calculated prices from location."""
        additional_service_ids = validated_data.pop('additional_service_ids', [])
        location_id = validated_data.get('location_id')
        clothing_items = validated_data.pop('clothing_items', [])
        prop_items = validated_data.pop('prop_items', [])

        settings = BookingSettings.get_settings()

        # 1. Визначаємо ціну за годину
        try:
            location = Location.objects.get(id=location_id, is_active=True)
            validated_data['base_price_per_hour'] = location.hourly_rate
        except Location.DoesNotExist:
            validated_data['base_price_per_hour'] = settings.base_price_per_hour

        validated_data['deposit_percentage'] = settings.deposit_percentage

        # 2. Розраховуємо вартість послуг ЗАЗДАЛЕГІДЬ (щоб не було NULL)
        services_total = Decimal('0.00')
        services_to_add = []

        if additional_service_ids:
            services_to_add = AdditionalService.objects.filter(
                id__in=additional_service_ids,
                is_active=True
            )
            services_total = sum(service.price for service in services_to_add)

        # Додаємо пораховану суму послуг у дані для створення
        validated_data['services_total'] = services_total

        # 3. Розраховуємо початкову загальну вартість (Оренда + Послуги)
        # Формула: (ціна_за_годину * години) + послуги
        duration = Decimal(str(validated_data['duration_hours']))
        base_cost = validated_data['base_price_per_hour'] * duration
        initial_total = base_cost + services_total


        half_total = initial_total * Decimal('0.50')
        max_deposit = validated_data['base_price_per_hour']
        initial_deposit = min(half_total, max_deposit)

        # Додаємо ці значення, щоб база даних не сварилася на NULL
        validated_data['total_amount'] = initial_total
        validated_data['deposit_amount'] = initial_deposit

        # 4. Тепер безпечно створюємо запис (INSERT)
        booking = StudioBooking.objects.create(**validated_data)

        # 5. Прив'язуємо послуги (Many-to-Many)
        if services_to_add:
            booking.additional_services.set(services_to_add)

        # 6. Обробка одягу та реквізиту (це змінить total_amount, якщо щось додано)
        # (Тут код залишається майже без змін, але ми оновлюємо вже існуючі значення)
        items_added = False

        if clothing_items:
            clothing_service = ClothingBookingService()
            success, errors, clothing_cost = clothing_service.add_clothing_to_booking(
                booking,
                clothing_items
            )
            if success and clothing_cost > 0:
                booking.total_amount += clothing_cost
                items_added = True

        if prop_items:
            prop_service = PropBookingService()
            success, errors, prop_cost = prop_service.add_props_to_booking(
                booking,
                prop_items
            )
            if success and prop_cost > 0:
                booking.total_amount += prop_cost
                items_added = True


        if items_added:

            half_total = booking.total_amount * Decimal('0.50')
            max_deposit = booking.base_price_per_hour
            booking.deposit_amount = min(half_total, max_deposit)
            booking.save(update_fields=['total_amount', 'deposit_amount', 'services_total'])

        # Якщо оплата вже створена (що малоймовірно в create, але можливо), оновлюємо її
        if hasattr(booking, 'payment') and booking.payment:
            booking.payment.amount = booking.deposit_amount
            booking.payment.save(update_fields=['amount'])

        return booking


class AvailabilityCheckSerializer(serializers.Serializer):
    """Check availability for specific date, duration, and location."""

    date = serializers.DateField()
    duration_hours = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=Decimal('0.5'),
        max_value=Decimal('24.0')
    )
    location_id = serializers.UUIDField(required=False)

    def validate_date(self, value):
        """Validate date is not in the past."""
        if value < date.today():
            raise serializers.ValidationError("Cannot check availability for past dates")
        return value

    def validate_location_id(self, value):
        """Validate location exists and is active."""
        if value:
            try:
                Location.objects.get(id=value, is_active=True)
            except Location.DoesNotExist:
                raise serializers.ValidationError("Invalid or inactive location")
        return value


class AvailableSlotSerializer(serializers.Serializer):
    """Available time slot representation."""

    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    available = serializers.BooleanField()


class AdminBookingSerializer(serializers.ModelSerializer):
    """Extended booking serializer for admin views with payment details."""

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

    duration_hours = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=Decimal('0.5'),
        required=False
    )

    class Meta:
        model = StudioBooking
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_end_time(self, obj):
        """Calculate and return booking end time."""
        return obj.get_end_time()

    def get_payment_details(self, obj):
        """Return detailed payment information if available."""
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

    def validate(self, data):
        """Minimal validation for admin use - only validate location if provided."""
        location_id = data.get('location_id')
        if location_id:
            try:
                Location.objects.get(id=location_id, is_active=True)
            except Location.DoesNotExist:
                raise serializers.ValidationError({
                    'location_id': 'Invalid or inactive location'
                })
        return data




class AdminBookingSerializer(serializers.ModelSerializer):
    """Extended booking serializer for admin views with payment details."""

    location = LocationBriefSerializer(read_only=True)
    location_id = serializers.UUIDField(write_only=True, required=False)
    additional_services = AdditionalServiceSerializer(many=True, read_only=True)
    additional_service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    # ✅ ДОДАНО: Підтримка clothing items
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

    # ✅ ДОДАНО: Підтримка prop items
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

    end_time = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()

    class Meta:
        model = StudioBooking
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_end_time(self, obj):
        """Calculate and return booking end time."""
        return obj.get_end_time()

    def get_payment_details(self, obj):
        """Return detailed payment information if available."""
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

    def validate(self, data):
        """Minimal validation for admin use - only validate location if provided."""
        location_id = data.get('location_id')
        if location_id:
            try:
                Location.objects.get(id=location_id, is_active=True)
            except Location.DoesNotExist:
                raise serializers.ValidationError({
                    'location_id': 'Invalid or inactive location'
                })
        return data

    # ✅✅✅ ДОДАНО: Метод create() для admin booking
    def create(self, validated_data):
        """Create admin booking with automatic price calculation from location."""
        additional_service_ids = validated_data.pop('additional_service_ids', [])
        clothing_items = validated_data.pop('clothing_items', [])
        prop_items = validated_data.pop('prop_items', [])
        location_id = validated_data.get('location_id')

        settings = BookingSettings.get_settings()

        # 1️⃣ Визначаємо ціну за годину з локації або налаштувань
        try:
            location = Location.objects.get(id=location_id, is_active=True)
            validated_data['base_price_per_hour'] = location.hourly_rate
        except Location.DoesNotExist:
            validated_data['base_price_per_hour'] = settings.base_price_per_hour

        # 2️⃣ Розраховуємо вартість послуг (НЕ може бути NULL)
        services_total = Decimal('0.00')
        services_to_add = []

        if additional_service_ids:
            services_to_add = AdditionalService.objects.filter(
                id__in=additional_service_ids,
                is_active=True
            )
            services_total = sum(service.price for service in services_to_add)

        validated_data['services_total'] = services_total

        # 3️⃣ Розраховуємо початкову загальну вартість (Оренда + Послуги)
        duration = Decimal(str(validated_data['duration_hours']))
        base_cost = validated_data['base_price_per_hour'] * duration
        initial_total = base_cost + services_total

        # 4️⃣ Встановлюємо deposit_percentage
        validated_data['deposit_percentage'] = settings.deposit_percentage

        # 5️⃣ Якщо адмін передав total_amount і deposit_amount явно - використовуємо їх
        # Інакше - розраховуємо автоматично
        if 'total_amount' not in validated_data:
            validated_data['total_amount'] = initial_total

        if 'deposit_amount' not in validated_data:

            half_total = validated_data['total_amount'] * Decimal('0.50')
            max_deposit = validated_data['base_price_per_hour']
            validated_data['deposit_amount'] = min(half_total, max_deposit)

        # 6️⃣ Створюємо booking (INSERT в БД)
        booking = StudioBooking.objects.create(**validated_data)

        # 7️⃣ Прив'язуємо послуги (Many-to-Many)
        if services_to_add:
            booking.additional_services.set(services_to_add)

        # 8️⃣ Обробка одягу та реквізиту (це змінить total_amount, якщо щось додано)
        items_added = False

        if clothing_items:
            from clothing.services import ClothingBookingService
            clothing_service = ClothingBookingService()
            success, errors, clothing_cost = clothing_service.add_clothing_to_booking(
                booking,
                clothing_items
            )
            if success and clothing_cost > 0:
                booking.total_amount += clothing_cost
                items_added = True

        if prop_items:
            from props.services import PropBookingService
            prop_service = PropBookingService()
            success, errors, prop_cost = prop_service.add_props_to_booking(
                booking,
                prop_items
            )
            if success and prop_cost > 0:
                booking.total_amount += prop_cost
                items_added = True


        if items_added:

            half_total = booking.total_amount * Decimal('0.50')
            max_deposit = booking.base_price_per_hour
            booking.deposit_amount = min(half_total, max_deposit)
            booking.save(update_fields=['total_amount', 'deposit_amount', 'services_total'])

        return booking


class AllInclusiveRequestSerializer(serializers.ModelSerializer):
    """Serializer for All-Inclusive package requests."""

    class Meta:
        model = AllInclusiveRequest
        fields = [
            'id',
            'package_type',
            'first_name',
            'last_name',
            'phone_number',
            'status',
            'admin_notes',
            'booking',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'booking']

    def validate_phone_number(self, value):
        """Validate phone number format."""
        cleaned = value.replace('+', '').replace(' ', '').replace('-', '')
        if not cleaned.isdigit() or len(cleaned) < 10:
            raise serializers.ValidationError("Invalid phone number format")
        return value