from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Location(models.Model):
    """Photo studios location model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Studio Name")
    description = models.TextField(verbose_name="Description")
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Hourly Rate (UAH)"
    )
    image = models.ImageField(
        upload_to='locations/',
        null=True,
        blank=True,
        verbose_name="Main Image"
    )
    address = models.TextField(blank=True, verbose_name="Address")
    capacity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Maximum Capacity (people)"
    )
    amenities = models.TextField(
        blank=True,
        help_text="Comma-separated list of amenities",
        verbose_name="Amenities"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ['name']
        verbose_name = 'Studio Location'
        verbose_name_plural = 'Studio Locations'

    def __str__(self):
        return self.name

    def get_amenities_list(self):
        """Return amenities as a list"""
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',') if a.strip()]
        return []


class AdditionalService(models.Model):
    """Additional services offered for studios sessions"""
    SERVICE_TYPES = [
        ('clothing', 'Professional Clothing Rental'),
        ('makeup', 'Makeup Services'),
        ('hair', 'Hair Styling Services'),
        ('equipment', 'Equipment Rental'),
        ('editing', 'Photo Editing Services'),
        ('other', 'Other Services'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_id = models.CharField(
        max_length=50,
        unique=True,
        choices=SERVICE_TYPES,
        verbose_name="Service Type"
    )
    name = models.CharField(max_length=200, verbose_name="Service Name")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Price (UAH)"
    )
    duration_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Estimated duration in minutes (0 if not applicable)",
        verbose_name="Duration (minutes)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Additional Service'
        verbose_name_plural = 'Additional Services'

    def __str__(self):
        return f"{self.name} - {self.price} UAH"


class StudioImage(models.Model):
    """Gallery images for studios locations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name="Studio Location"
    )
    image = models.ImageField(
        upload_to='studio_gallery/',
        verbose_name="Image"
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name="Caption")
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display Order"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['location', 'order', 'created_at']
        verbose_name = 'Studio Image'
        verbose_name_plural = 'Studio Images'

    def __str__(self):
        return f"{self.location.name} - Image {self.order}"