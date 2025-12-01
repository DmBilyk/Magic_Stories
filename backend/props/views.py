from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Q, Prefetch
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    PropCategory,
    PropItem,
    PropImage,
    BookingPropItem,
    PropRentalSettings
)
from .serializers import (
    PropCategorySerializer,
    PropItemListSerializer,
    PropItemDetailSerializer,
    PropImageSerializer,
    BookingPropItemSerializer,
    PropAvailabilitySerializer,
    PropCostCalculationSerializer,
    PropRentalSettingsSerializer
)
from .services import (
    PropAvailabilityService,
    PropCostCalculationService,
    PropBookingService
)


class PropCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing prop categories"""
    queryset = PropCategory.objects.all()
    serializer_class = PropCategorySerializer

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


class PropItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing prop items"""
    queryset = PropItem.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'check_availability']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'list':
            return PropItemListSerializer
        return PropItemDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category').prefetch_related(
            Prefetch('images', queryset=PropImage.objects.order_by('order'))
        )

        # Filters
        category = self.request.query_params.get('category', None)
        available_only = self.request.query_params.get('available_only', 'false')
        search = self.request.query_params.get('search', None)

        # Non-admin users only see active items
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True, is_available=True)

        if category:
            queryset = queryset.filter(category_id=category)

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
        request_body=PropAvailabilitySerializer,
        responses={200: openapi.Response('Availability status')}
    )
    @action(detail=True, methods=['post'], url_path='check-availability')
    def check_availability(self, request, pk=None):
        """Check if prop item is available for specific date/time"""
        item = self.get_object()
        serializer = PropAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PropAvailabilityService()
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
        """Upload image for prop item"""
        item = self.get_object()

        # Check max images limit (e.g., 10 images per item)
        if item.images.count() >= 10:
            return Response(
                {'error': 'Maximum 10 images allowed per item'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PropImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = PropImage.objects.create(
            prop_item=item,
            **serializer.validated_data
        )

        return Response(
            PropImageSerializer(image, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """Delete an image from prop item"""
        item = self.get_object()
        try:
            image = item.images.get(id=image_id)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PropImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PropAvailabilityViewSet(viewsets.ViewSet):
    """ViewSet for checking prop availability"""
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
        """Get all available prop items for a time slot"""
        serializer = PropAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PropAvailabilityService()
        available_items = service.get_available_items_for_slot(
            serializer.validated_data['booking_date'],
            serializer.validated_data['booking_time'],
            serializer.validated_data['duration_hours']
        )

        result = []
        for item_data in available_items:
            item_serializer = PropItemListSerializer(
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
        request_body=PropCostCalculationSerializer
    )
    @action(detail=False, methods=['post'], url_path='calculate-cost')
    def calculate_cost(self, request):
        """Calculate total cost for prop items"""
        serializer = PropCostCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PropCostCalculationService()
        cost_data = service.calculate_prop_cost(
            serializer.validated_data['prop_items']
        )

        return Response(cost_data)


class PropRentalSettingsViewSet(viewsets.ViewSet):
    """ViewSet for prop rental settings"""

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(responses={200: PropRentalSettingsSerializer})
    def retrieve(self, request):
        """Get prop rental settings"""
        settings = PropRentalSettings.get_settings()
        serializer = PropRentalSettingsSerializer(settings)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=PropRentalSettingsSerializer)
    def update(self, request):
        """Update prop rental settings"""
        settings = PropRentalSettings.get_settings()
        serializer = PropRentalSettingsSerializer(
            settings,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)