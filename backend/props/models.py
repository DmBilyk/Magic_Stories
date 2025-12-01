import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class PropCategory(models.Model):
    """Categories for organizing prop items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prop_categories'
        verbose_name = 'Prop Category'
        verbose_name_plural = 'Prop Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class PropItem(models.Model):
    """Individual prop items available for rental"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        PropCategory,
        on_delete=models.PROTECT,
        related_name='items'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Rental price in UAH"
    )
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Total quantity available"
    )
    notes = models.TextField(blank=True, help_text="Internal notes for admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prop_items'
        verbose_name = 'Prop Item'
        verbose_name_plural = 'Prop Items'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['is_active', 'is_available']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be greater than 0'})

    def get_available_quantity_for_date(self, booking_date, booking_time, duration_hours):
        """Calculate available quantity for a specific datetime"""
        from bookings.models import StudioBooking
        from datetime import datetime, timedelta

        # Get bookings that overlap with requested time
        booking_end_time = (
                datetime.combine(booking_date, booking_time) +
                timedelta(hours=duration_hours)
        ).time()

        overlapping_bookings = StudioBooking.objects.filter(
            booking_date=booking_date,
            status__in=['pending_payment', 'paid', 'confirmed'],
        ).filter(
            models.Q(booking_time__lt=booking_end_time) &
            models.Q(booking_time__gte=booking_time)
        )

        # Count how many times this item is rented in overlapping bookings
        rented_count = BookingPropItem.objects.filter(
            booking__in=overlapping_bookings,
            prop_item=self
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

        return max(0, self.quantity - rented_count)


class PropImage(models.Model):
    """Images for prop items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prop_item = models.ForeignKey(
        PropItem,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='prop_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prop_images'
        verbose_name = 'Prop Image'
        verbose_name_plural = 'Prop Images'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.prop_item.name}"


class BookingPropItem(models.Model):
    """Link between Studio Bookings and Prop Items (max 20 items per booking)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        'bookings.StudioBooking',
        on_delete=models.CASCADE,
        related_name='prop_items'
    )
    prop_item = models.ForeignKey(
        PropItem,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    price_at_booking = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price of item at time of booking"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_prop_items'
        verbose_name = 'Booking Prop Item'
        verbose_name_plural = 'Booking Prop Items'
        unique_together = [['booking', 'prop_item']]

    def __str__(self):
        return f"{self.prop_item.name} x{self.quantity} for booking {self.booking.id}"

    def clean(self):
        # Check max 20 items limit per booking
        if self.booking_id:
            existing_count = BookingPropItem.objects.filter(
                booking=self.booking
            ).exclude(id=self.id).count()

            if existing_count >= 20:
                raise ValidationError(
                    'Cannot add more than 20 prop items to a single booking'
                )

        # Check availability
        if self.prop_item_id and self.booking_id:
            available = self.prop_item.get_available_quantity_for_date(
                self.booking.booking_date,
                self.booking.booking_time,
                self.booking.duration_hours
            )
            if self.quantity > available:
                raise ValidationError(
                    f'Only {available} units of {self.prop_item.name} available for this time slot'
                )

    def save(self, *args, **kwargs):
        # Store current price if not set
        if not self.price_at_booking:
            self.price_at_booking = self.prop_item.price
        self.full_clean()
        super().save(*args, **kwargs)

    def get_total_price(self):
        """Calculate total price for this prop rental"""
        return self.price_at_booking * self.quantity


class PropRentalSettings(models.Model):
    """Singleton model for prop rental configuration"""
    max_items_per_booking = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum number of prop items per booking"
    )
    is_rental_enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable prop rental feature"
    )
    rental_terms = models.TextField(
        blank=True,
        help_text="Terms and conditions for prop rental"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prop_rental_settings'
        verbose_name = 'Prop Rental Settings'
        verbose_name_plural = 'Prop Rental Settings'

    def __str__(self):
        return "Prop Rental Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_settings(cls):
        """Get or create singleton settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings