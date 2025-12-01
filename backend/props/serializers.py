from rest_framework import serializers
from .models import (
    PropCategory,
    PropItem,
    PropImage,
    BookingPropItem,
    PropRentalSettings
)


class PropImageSerializer(serializers.ModelSerializer):
    """Serializer for prop images"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PropImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'order']
        read_only_fields = ['id']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PropCategorySerializer(serializers.ModelSerializer):
    """Serializer for prop categories"""
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = PropCategory
        fields = ['id', 'name', 'description', 'is_active', 'items_count']
        read_only_fields = ['id']

    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()


class PropItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing prop items (compact)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = PropItem
        fields = [
            'id', 'name', 'category_name', 'price',
            'is_available', 'quantity', 'primary_image'
        ]
        read_only_fields = ['id']

    def get_primary_image(self, obj):
        image = obj.images.first()
        if image:
            return PropImageSerializer(image, context=self.context).data
        return None


class PropItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed prop item view"""
    category = PropCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    images = PropImageSerializer(many=True, read_only=True)

    class Meta:
        model = PropItem
        fields = [
            'id', 'name', 'description', 'category', 'category_id',
            'price', 'is_available', 'is_active',
            'quantity', 'notes', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


class BookingPropItemSerializer(serializers.ModelSerializer):
    """Serializer for prop items in a booking"""
    prop_item_details = PropItemListSerializer(
        source='prop_item',
        read_only=True
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = BookingPropItem
        fields = [
            'id', 'prop_item', 'prop_item_details',
            'quantity', 'price_at_booking', 'total_price'
        ]
        read_only_fields = ['id', 'price_at_booking', 'total_price']

    def get_total_price(self, obj):
        return str(obj.get_total_price())


class BookingPropItemCreateSerializer(serializers.Serializer):
    """Serializer for adding prop items to booking during creation"""
    prop_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_prop_item_id(self, value):
        try:
            item = PropItem.objects.get(id=value)
            if not item.is_active or not item.is_available:
                raise serializers.ValidationError(
                    "This prop item is not available for rental"
                )
            return value
        except PropItem.DoesNotExist:
            raise serializers.ValidationError("Prop item not found")


class PropAvailabilitySerializer(serializers.Serializer):
    """Serializer for checking prop availability"""
    prop_item_id = serializers.UUIDField()
    booking_date = serializers.DateField()
    booking_time = serializers.TimeField()
    duration_hours = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class PropCostCalculationSerializer(serializers.Serializer):
    """Serializer for calculating prop rental costs"""
    prop_items = BookingPropItemCreateSerializer(many=True)

    def validate_prop_items(self, value):
        if len(value) > 20:
            raise serializers.ValidationError(
                "Cannot add more than 20 prop items to a booking"
            )
        return value


class PropRentalSettingsSerializer(serializers.ModelSerializer):
    """Serializer for prop rental settings"""
    class Meta:
        model = PropRentalSettings
        fields = [
            'max_items_per_booking',
            'is_rental_enabled',
            'rental_terms',
            'updated_at'
        ]
        read_only_fields = ['updated_at']