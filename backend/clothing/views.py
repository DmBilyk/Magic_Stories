# clothing/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Q, Prefetch
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    ClothingCategory,
    ClothingItem,
    ClothingImage,
    BookingClothingItem,
    ClothingRentalSettings
)
from .serializers import (
    ClothingCategorySerializer,
    ClothingItemListSerializer,
    ClothingItemDetailSerializer,
    ClothingImageSerializer,
    BookingClothingItemSerializer,
    ClothingAvailabilitySerializer,
    ClothingCostCalculationSerializer,
    ClothingRentalSettingsSerializer
)
from .services import (
    ClothingAvailabilityService,
    ClothingCostCalculationService,
    ClothingBookingService
)


class ClothingCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing clothing categories"""
    queryset = ClothingCategory.objects.all()
    serializer_class = ClothingCategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Non-admin users only see active categories
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset


class ClothingItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing clothing items"""
    queryset = ClothingItem.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'check_availability']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ClothingItemListSerializer
        return ClothingItemDetailSerializer


    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category').prefetch_related(
            Prefetch('images', queryset=ClothingImage.objects.order_by('order'))
        )

        # Filters
        category = self.request.query_params.get('category', None)
        size = self.request.query_params.get('size', None)
        available_only = self.request.query_params.get('available_only', 'false')
        search = self.request.query_params.get('search', None)

        # Non-admin users only see active items
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True, is_available=True)

        if category:
            queryset = queryset.filter(category_id=category)

        if size:
            queryset = queryset.filter(size=size)

        if available_only.lower() == 'true':
            queryset = queryset.filter(is_available=True)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    @swagger_auto_schema(
        method='post',
        request_body=ClothingAvailabilitySerializer,
        responses={200: openapi.Response('Availability status')}
    )
    @action(detail=True, methods=['post'], url_path='check-availability')
    def check_availability(self, request, pk=None):
        """Check if clothing item is available for specific date/time"""
        item = self.get_object()
        serializer = ClothingAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ClothingAvailabilityService()
        is_available, message, available_qty = service.check_item_availability(
            str(item.id),
            serializer.validated_data['booking_date'],
            serializer.validated_data['booking_time'],
            serializer.validated_data['duration_hours'],
            serializer.validated_data.get('quantity', 1)
        )

        return Response({
            'item_id': str(item.id),
            'item_name': item.name,
            'available': is_available,
            'available_quantity': available_qty,
            'requested_quantity': serializer.validated_data.get('quantity', 1),
            'message': message
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'image': openapi.Schema(type=openapi.TYPE_FILE),
                'alt_text': openapi.Schema(type=openapi.TYPE_STRING),
                'order': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    )
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload image for clothing item"""
        item = self.get_object()

        # Check max images limit (e.g., 10 images per item)
        if item.images.count() >= 10:
            return Response(
                {'error': 'Maximum 10 images allowed per item'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClothingImageSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        image = ClothingImage.objects.create(
            clothing_item=item,
            **serializer.validated_data
        )

        return Response(
            ClothingImageSerializer(image, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """Delete an image from clothing item"""
        item = self.get_object()
        try:
            image = item.images.get(id=image_id)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClothingImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ClothingAvailabilityViewSet(viewsets.ViewSet):
    """ViewSet for checking clothing availability"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['booking_date', 'booking_time', 'duration_hours'],
            properties={
                'booking_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'booking_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'duration_hours': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    )
    @action(detail=False, methods=['post'], url_path='available-items')
    def available_items(self, request):
        """Get all available clothing items for a time slot"""
        serializer = ClothingAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ClothingAvailabilityService()
        available_items = service.get_available_items_for_slot(
            serializer.validated_data['booking_date'],
            serializer.validated_data['booking_time'],
            serializer.validated_data['duration_hours']
        )

        result = []
        for item_data in available_items:
            # 🔧 FIX: Передаємо context з request
            item_serializer = ClothingItemListSerializer(
                item_data['item'],
                context={'request': request}
            )
            result.append({
                **item_serializer.data,
                'available_quantity': item_data['available_quantity'],
                'total_quantity': item_data['total_quantity']
            })

        return Response({
            'booking_date': str(serializer.validated_data['booking_date']),
            'booking_time': str(serializer.validated_data['booking_time']),
            'duration_hours': serializer.validated_data['duration_hours'],
            'available_items': result
        })

    @swagger_auto_schema(
        method='post',
        request_body=ClothingCostCalculationSerializer
    )
    @action(detail=False, methods=['post'], url_path='calculate-cost')
    def calculate_cost(self, request):
        """Calculate total cost for clothing items"""
        serializer = ClothingCostCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ClothingCostCalculationService()
        cost_data = service.calculate_clothing_cost(
            serializer.validated_data['clothing_items']
        )

        return Response(cost_data)


class ClothingRentalSettingsViewSet(viewsets.ViewSet):
    """ViewSet for clothing rental settings"""

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(responses={200: ClothingRentalSettingsSerializer})
    def retrieve(self, request):
        """Get clothing rental settings"""
        settings = ClothingRentalSettings.get_settings()
        serializer = ClothingRentalSettingsSerializer(settings)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ClothingRentalSettingsSerializer)
    def update(self, request):
        """Update clothing rental settings"""
        settings = ClothingRentalSettings.get_settings()
        serializer = ClothingRentalSettingsSerializer(
            settings,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)