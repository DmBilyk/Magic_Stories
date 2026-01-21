from rest_framework import serializers
from .models import Location, AdditionalService, StudioImage


class StudioImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudioImage
        fields = ['id', 'image', 'image_thumbnail', 'caption', 'order', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Додаємо повні URL для зображень
        image_url = data.get('image')
        thumbnail_url = data.get('image_thumbnail')

        if request and image_url:
            image_url = request.build_absolute_uri(image_url)
        if request and thumbnail_url:
            thumbnail_url = request.build_absolute_uri(thumbnail_url)

        return {
            'id': str(data['id']),
            'imageUrl': image_url,
            'thumbnailUrl': thumbnail_url,  # Додаємо мініатюру
            'caption': data.get('caption'),
            'order': data.get('order'),
            'createdAt': data.get('created_at'),
        }


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    gallery_images = StudioImageSerializer(many=True, read_only=True)
    amenities_list = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            'id',
            'name',
            'description',
            'hourly_rate',
            'image',
            'image_thumbnail',
            'address',
            'capacity',
            'amenities',
            'amenities_list',
            'gallery_images',
            'created_at',
            'updated_at',
            'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'image_thumbnail']

    def get_amenities_list(self, obj):
        """Get amenities as a list"""
        return obj.get_amenities_list()

    def to_representation(self, instance):
        """Convert to camelCase for frontend"""
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Додаємо повні URL
        image_url = data.get('image')
        thumbnail_url = data.get('image_thumbnail')

        if request and image_url:
            image_url = request.build_absolute_uri(image_url)
        if request and thumbnail_url:
            thumbnail_url = request.build_absolute_uri(thumbnail_url)

        return {
            'id': str(data['id']),
            'name': data['name'],
            'description': data['description'],
            'hourlyRate': float(data['hourly_rate']),
            'imageUrl': image_url,
            'thumbnailUrl': thumbnail_url,  # Додаємо мініатюру
            'address': data['address'],
            'capacity': data['capacity'],
            'amenities': data['amenities_list'],
            'galleryImages': data['gallery_images'],
            'createdAt': data['created_at'],
            'updatedAt': data['updated_at'],
            'isActive': data['is_active'],
        }


class LocationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating locations"""

    class Meta:
        model = Location
        fields = [
            'name',
            'description',
            'hourly_rate',
            'image',
            'address',
            'capacity',
            'amenities',
            'is_active'
        ]

    def validate_hourly_rate(self, value):
        """Validate hourly rate is positive"""
        if value <= 0:
            raise serializers.ValidationError("Hourly rate must be greater than 0")
        return value

    def validate_capacity(self, value):
        """Validate capacity is at least 1"""
        if value < 1:
            raise serializers.ValidationError("Capacity must be at least 1")
        return value


class AdditionalServiceSerializer(serializers.ModelSerializer):
    """Serializer for AdditionalService model"""

    class Meta:
        model = AdditionalService
        fields = [
            'id',
            'service_id',
            'name',
            'description',
            'price',
            'duration_minutes',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """Convert to camelCase for frontend"""
        data = super().to_representation(instance)
        return {
            'id': str(data['id']),
            'serviceId': data['service_id'],
            'name': data['name'],
            'description': data['description'],
            'price': float(data['price']),
            'durationMinutes': data['duration_minutes'],
            'isActive': data['is_active'],
            'createdAt': data['created_at'],
            'updatedAt': data['updated_at'],
        }


class AdditionalServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating services"""

    class Meta:
        model = AdditionalService
        fields = [
            'service_id',
            'name',
            'description',
            'price',
            'duration_minutes',
            'is_active'
        ]

    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    def validate_duration_minutes(self, value):
        """Validate duration is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Duration cannot be negative")
        return value


class StudioImageCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating studio images"""
    location_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = StudioImage
        fields = ['location_id', 'image', 'caption', 'order']

    def validate_location_id(self, value):
        """Validate location exists and is active"""
        try:
            location = Location.objects.get(id=value, is_active=True)
        except Location.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive location")
        return value

    def create(self, validated_data):
        """Create studio image"""
        location_id = validated_data.pop('location_id')
        validated_data['location_id'] = location_id
        return StudioImage.objects.create(**validated_data)