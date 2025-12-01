from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class StudioBooking(models.Model):
    """Photo studios booking"""
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('paid', 'Paid'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Studio Location (NEW - reference to studios app)
    location = models.ForeignKey(
        'studios.Location',  # Reference to studios app
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name="Studio Location"
    )

    # Client Information
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    phone_number = models.CharField(max_length=20, verbose_name="Phone Number")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    # Booking Details
    booking_date = models.DateField(verbose_name="Booking Date")
    booking_time = models.TimeField(verbose_name="Booking Time")
    duration_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Duration (hours)"
    )

    # Services (Reference to studios app - CHANGED)
    additional_services = models.ManyToManyField(
        'studios.AdditionalService',  # Reference to studios app
        blank=True,
        related_name='bookings',
        verbose_name="Additional Services"
    )

    # Pricing
    base_price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Base Price per Hour (UAH)"
    )
    services_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Services Total (UAH)"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Total Amount (UAH)"
    )
    deposit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Deposit Amount (UAH)"
    )
    deposit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('30.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Deposit Percentage"
    )

    # Payment Reference
    payment = models.OneToOneField(
        'payment_service.StudioPayment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking',
        verbose_name="Payment"
    )

    # Status and Notes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_payment',
        verbose_name="Status"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    admin_notes = models.TextField(blank=True, verbose_name="Admin Notes")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Studio Booking"
        verbose_name_plural = "Studio Bookings"
        ordering = ['-booking_date', '-booking_time']
        indexes = [
            models.Index(fields=['booking_date', 'booking_time']),
            models.Index(fields=['status']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['location']),
        ]
        # Prevent double booking for the same location (UPDATED)
        constraints = [
            models.UniqueConstraint(
                fields=['location', 'booking_date', 'booking_time'],
                condition=models.Q(status__in=['pending_payment', 'paid', 'confirmed']),
                name='unique_active_booking_location_datetime'
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.location.name} - {self.booking_date} {self.booking_time}"

    def calculate_total(self):
        """Calculate total amount based on duration and services"""
        base_total = self.base_price_per_hour * self.duration_hours
        services_total = sum(
            service.price for service in self.additional_services.all()
        )
        return base_total + services_total

    def calculate_deposit(self):
        """Calculate deposit amount"""
        return (self.total_amount * self.deposit_percentage) / Decimal('100.00')

    def get_end_time(self):
        """Calculate booking end time"""
        from datetime import datetime, timedelta

        if not self.booking_date or not self.booking_time:
            return None

        start_datetime = datetime.combine(self.booking_date, self.booking_time)
        end_datetime = start_datetime + timedelta(hours=self.duration_hours)
        return end_datetime.time()


class BookingSettings(models.Model):
    """Global settings for booking system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Pricing
    base_price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Base Price per Hour (UAH)"
    )
    deposit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('30.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Deposit Percentage"
    )

    # Working Hours
    opening_time = models.TimeField(default='09:00', verbose_name="Opening Time")
    closing_time = models.TimeField(default='21:00', verbose_name="Closing Time")

    # Booking Rules
    min_booking_hours = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Minimum Booking Hours"
    )
    max_booking_hours = models.PositiveIntegerField(
        default=8,
        validators=[MinValueValidator(1)],
        verbose_name="Maximum Booking Hours"
    )
    advance_booking_days = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1)],
        verbose_name="Advance Booking Days"
    )

    # Maintenance
    is_booking_enabled = models.BooleanField(
        default=True,
        verbose_name="Booking Enabled"
    )
    maintenance_message = models.TextField(
        blank=True,
        verbose_name="Maintenance Message"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Booking Settings"
        verbose_name_plural = "Booking Settings"

    def __str__(self):
        return "Booking Settings"

    @classmethod
    def get_settings(cls):
        """Get or create singleton settings instance"""
        settings, created = cls.objects.get_or_create(
            pk=cls.objects.first().pk if cls.objects.exists() else uuid.uuid4())
        return settings