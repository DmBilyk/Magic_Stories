from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Location, AdditionalService, StudioImage
from .serializers import (
    LocationSerializer,
    LocationCreateUpdateSerializer,
    AdditionalServiceSerializer,
    AdditionalServiceCreateUpdateSerializer,
    StudioImageSerializer,
    StudioImageCreateUpdateSerializer,
)


class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing studios locations
    """

    queryset = Location.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    def get_permissions(self):
        """Allow read access to anyone, write access to staff only"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Show only active locations to non-staff users"""
        if self.request.user.is_staff:
            return Location.objects.all()
        return Location.objects.filter(is_active=True)

    def get_serializer_class(self):
        """Use different serializers for read vs write operations"""
        if self.action in ['create', 'update', 'partial_update']:
            return LocationCreateUpdateSerializer
        return LocationSerializer

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Search locations by name or description
        """
        search_term = request.query_params.get('q', '')
        queryset = self.get_queryset()

        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(address__icontains=search_term)
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='gallery')
    def gallery(self, request, pk=None):
        """Get all gallery images for a location"""
        location = self.get_object()
        images = location.gallery_images.all()
        serializer = StudioImageSerializer(images, many=True)
        return Response(serializer.data)


class AdditionalServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing additional services
    """

    queryset = AdditionalService.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'service_id']

    def get_permissions(self):
        """Allow read access to anyone, write access to staff only"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Show only active services to non-staff users"""
        if self.request.user.is_staff:
            return AdditionalService.objects.all()
        return AdditionalService.objects.filter(is_active=True)

    def get_serializer_class(self):
        """Use different serializers for read vs write operations"""
        if self.action in ['create', 'update', 'partial_update']:
            return AdditionalServiceCreateUpdateSerializer
        return AdditionalServiceSerializer

    @action(detail=False, methods=['get'], url_path='by-type')
    def by_type(self, request):
        """
        Get services grouped by type
        """
        service_types = request.query_params.get('type', '').split(',')
        service_types = [t.strip() for t in service_types if t.strip()]

        queryset = self.get_queryset()

        if service_types:
            queryset = queryset.filter(service_id__in=service_types)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudioImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing studios gallery images
    """

    queryset = StudioImage.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['location']

    def get_serializer_class(self):
        """Use different serializers for read vs write operations"""
        if self.action in ['create', 'update', 'partial_update']:
            return StudioImageCreateUpdateSerializer
        return StudioImageSerializer

    def perform_create(self, serializer):
        """Create studios image"""
        serializer.save()

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request):
        """
        Reorder images for a location
        """
        location_id = request.data.get('location_id')
        image_orders = request.data.get('image_orders', [])

        if not location_id or not image_orders:
            return Response(
                {'error': 'location_id and image_orders are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            location = Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return Response(
                {'error': 'Location not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        updated_count = 0
        for item in image_orders:
            image_id = item.get('image_id')
            order = item.get('order')

            if image_id and order is not None:
                try:
                    image = StudioImage.objects.get(id=image_id, location=location)
                    image.order = order
                    image.save()
                    updated_count += 1
                except StudioImage.DoesNotExist:
                    continue

        return Response(
            {
                'message': f'Updated order for {updated_count} images',
                'updated_count': updated_count,
            }
        )