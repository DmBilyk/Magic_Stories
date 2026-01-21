# clothing/models.py
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

class ClothingCategory(models.Model):
    """Categories for organizing clothing items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clothing_categories'
        verbose_name = 'Clothing Category'
        verbose_name_plural = 'Clothing Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class ClothingItem(models.Model):
    """Individual clothing items available for rental"""
    SIZE_CHOICES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', '2X Large'),
        ('XXXL', '3X Large'),
        ('ONE_SIZE', 'One Size'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        ClothingCategory,
        on_delete=models.PROTECT,
        related_name='items'
    )
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
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
        db_table = 'clothing_items'
        verbose_name = 'Clothing Item'
        verbose_name_plural = 'Clothing Items'
        ordering = ['category', 'name', 'size']
        indexes = [
            models.Index(fields=['is_active', 'is_available']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.size})"

    def clean(self):
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be greater than 0'})

    def get_available_quantity_for_date(self, booking_date, booking_time, duration_hours):
        """Calculate available quantity for a specific datetime"""
        from bookings.models import StudioBooking
        from datetime import datetime, timedelta
        from decimal import Decimal

        # Get bookings that overlap with requested time
        duration_minutes = int(Decimal(str(duration_hours)) * 60)
        booking_end_time = (
                datetime.combine(booking_date, booking_time) +
                timedelta(minutes=duration_minutes)
        ).time()

        overlapping_bookings = StudioBooking.objects.filter(
            booking_date=booking_date,
            status__in=['pending_payment', 'paid', 'confirmed'],
        ).filter(
            models.Q(booking_time__lt=booking_end_time) &
            models.Q(booking_time__gte=booking_time)
        )

        # Count how many times this item is rented in overlapping bookings
        rented_count = BookingClothingItem.objects.filter(
            booking__in=overlapping_bookings,
            clothing_item=self
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

        return max(0, self.quantity - rented_count)


class ClothingImage(models.Model):
    """Images for clothing items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clothing_item = models.ForeignKey(
        ClothingItem,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='clothing_images/')
    # Додаємо поле для мініатюри
    image_thumbnail = models.ImageField(upload_to='clothing_images/thumbnails/', blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clothing_images'
        verbose_name = 'Clothing Image'
        verbose_name_plural = 'Clothing Images'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.clothing_item.name}"

    def save(self, *args, **kwargs):
        # Якщо зображення є, а мініатюри немає або змінилось основне фото
        if self.image:
            self.make_thumbnail()
        super().save(*args, **kwargs)

    def make_thumbnail(self):
        """Generates a thumbnail for the image"""
        if not self.image:
            return

        # Відкриваємо зображення
        img = Image.open(self.image)

        # Конвертуємо в RGB, якщо це PNG/RGBA, щоб зберегти як JPEG
        if img.mode in ('RGBA', 'LA'):
            background = Image.new(img.mode[:-1], img.size, '#fff')
            background.paste(img, img.split()[-1])
            img = background

        # Створюємо копію для мініатюри
        thumb = img.copy()

        # Розмір мініатюри (наприклад, 400x500 для карток товарів)
        thumb.thumbnail((400, 500), Image.Resampling.LANCZOS)

        # Зберігаємо в пам'ять
        thumb_io = BytesIO()
        thumb.save(thumb_io, 'JPEG', quality=85)

        # Створюємо ім'я файлу
        name = os.path.basename(self.image.name)
        thumb_name, _ = os.path.splitext(name)
        thumb_filename = f"{thumb_name}_thumb.jpg"

        # Зберігаємо файл у поле image_thumbnail, save=False щоб не викликати рекурсію
        self.image_thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=False)


class BookingClothingItem(models.Model):
    """Link between Studio Bookings and Clothing Items (max 10 items per booking)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        'bookings.StudioBooking',
        on_delete=models.CASCADE,
        related_name='clothing_items'
    )
    clothing_item = models.ForeignKey(
        ClothingItem,
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
        db_table = 'booking_clothing_items'
        verbose_name = 'Booking Clothing Item'
        verbose_name_plural = 'Booking Clothing Items'
        unique_together = [['booking', 'clothing_item']]

    def __str__(self):
        return f"{self.clothing_item.name} x{self.quantity} for booking {self.booking.id}"

    def clean(self):
        # Check max 10 items limit per booking
        if self.booking_id:
            existing_count = BookingClothingItem.objects.filter(
                booking=self.booking
            ).exclude(id=self.id).count()

            if existing_count >= 10:
                raise ValidationError(
                    'Cannot add more than 10 clothing items to a single booking'
                )

        # Check availability
        if self.clothing_item_id and self.booking_id:
            available = self.clothing_item.get_available_quantity_for_date(
                self.booking.booking_date,
                self.booking.booking_time,
                self.booking.duration_hours
            )
            if self.quantity > available:
                raise ValidationError(
                    f'Only {available} units of {self.clothing_item.name} available for this time slot'
                )

    def save(self, *args, **kwargs):
        # Store current price if not set
        if not self.price_at_booking:
            self.price_at_booking = self.clothing_item.price
        self.full_clean()
        super().save(*args, **kwargs)

    def get_total_price(self):
        """Calculate total price for this clothing rental"""
        return self.price_at_booking * self.quantity


class ClothingRentalSettings(models.Model):
    """Singleton model for clothing rental configuration"""
    max_items_per_booking = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Maximum number of clothing items per booking"
    )
    is_rental_enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable clothing rental feature"
    )
    rental_terms = models.TextField(
        blank=True,
        help_text="Terms and conditions for clothing rental"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clothing_rental_settings'
        verbose_name = 'Clothing Rental Settings'
        verbose_name_plural = 'Clothing Rental Settings'

    def __str__(self):
        return "Clothing Rental Settings"

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