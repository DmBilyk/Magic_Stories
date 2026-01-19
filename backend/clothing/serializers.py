from rest_framework import serializers
from django.conf import settings
from .models import (
    ClothingCategory,
    ClothingItem,
    ClothingImage,
    BookingClothingItem,
    ClothingRentalSettings
)
import logging

from decimal import Decimal
logger = logging.getLogger(__name__)


class ClothingImageSerializer(serializers.ModelSerializer):
    """Serializer for clothing images"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ClothingImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'order']
        read_only_fields = ['id']

    def get_image_url(self, obj):
        request = self.context.get('request')

        if not obj.image:
            logger.warning(f"No image file for ClothingImage {obj.id}")
            return None

        try:
            image_url = obj.image.url

            # For DEBUG mode, build absolute URI
            if request:
                absolute_url = request.build_absolute_uri(image_url)
                logger.info(f"Image URL for {obj.id}: {absolute_url}")
                return absolute_url

            # Fallback: construct full URL manually
            if not image_url.startswith('http'):
                base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                absolute_url = f"{base_url}{image_url}"
                logger.info(f"Manual URL construction for {obj.id}: {absolute_url}")
                return absolute_url

            return image_url

        except (ValueError, AttributeError) as e:
            logger.error(f"Error getting image URL for {obj.id}: {e}")
            return None


class ClothingCategorySerializer(serializers.ModelSerializer):
    """Serializer for clothing categories"""
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = ClothingCategory
        fields = ['id', 'name', 'description', 'is_active', 'items_count']
        read_only_fields = ['id']

    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()


class ClothingItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing clothing items (compact)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = ClothingItem
        fields = [
            'id', 'name', 'category_name', 'size', 'price',
            'is_available', 'quantity', 'primary_image'
        ]
        read_only_fields = ['id']

    def get_primary_image(self, obj):
        # Get first image ordered by 'order' field
        image = obj.images.order_by('order', 'created_at').first()

        if not image:
            logger.warning(f"No primary image for ClothingItem {obj.id} ({obj.name})")
            return None

        # ВАЖЛИВО: передаємо context з request
        serializer = ClothingImageSerializer(image, context=self.context)
        data = serializer.data

        logger.info(f"Primary image data for {obj.name}: {data}")
        return data


class ClothingItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed clothing item view"""
    category = ClothingCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    images = ClothingImageSerializer(many=True, read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)

    class Meta:
        model = ClothingItem
        fields = [
            'id', 'name', 'description', 'category', 'category_id',
            'size', 'size_display', 'price', 'is_available', 'is_active',
            'quantity', 'notes', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


class BookingClothingItemSerializer(serializers.ModelSerializer):
    """Serializer for clothing items in a booking"""
    clothing_item_details = ClothingItemListSerializer(
        source='clothing_item',
        read_only=True
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = BookingClothingItem
        fields = [
            'id', 'clothing_item', 'clothing_item_details',
            'quantity', 'price_at_booking', 'total_price'
        ]
        read_only_fields = ['id', 'price_at_booking', 'total_price']

    def get_total_price(self, obj):
        return str(obj.get_total_price())


class BookingClothingItemCreateSerializer(serializers.Serializer):
    """Serializer for adding clothing items to booking during creation"""
    clothing_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_clothing_item_id(self, value):
        try:
            item = ClothingItem.objects.get(id=value)
            if not item.is_active or not item.is_available:
                raise serializers.ValidationError(
                    "This clothing item is not available for rental"
                )
            return value
        except ClothingItem.DoesNotExist:
            raise serializers.ValidationError("Clothing item not found")


class ClothingAvailabilitySerializer(serializers.Serializer):
    """Serializer for checking clothing availability"""
    clothing_item_id = serializers.UUIDField()
    booking_date = serializers.DateField()
    booking_time = serializers.TimeField()
    duration_hours = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=Decimal('0.5'),
        max_value=Decimal('24.0')
    )
    quantity = serializers.IntegerField(min_value=1, default=1)


class ClothingCostCalculationSerializer(serializers.Serializer):
    """Serializer for calculating clothing rental costs"""
    clothing_items = BookingClothingItemCreateSerializer(many=True)

    def validate_clothing_items(self, value):
        if len(value) > 10:
            raise serializers.ValidationError(
                "Cannot add more than 10 clothing items to a booking"
            )
        return value


class ClothingRentalSettingsSerializer(serializers.ModelSerializer):
    """Serializer for clothing rental settings"""

    class Meta:
        model = ClothingRentalSettings
        fields = [
            'max_items_per_booking',
            'is_rental_enabled',
            'rental_terms',
            'updated_at'
        ]
        read_only_fields = ['updated_at']