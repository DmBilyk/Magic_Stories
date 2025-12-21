from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import date, datetime

from .models import StudioBooking, BookingSettings
from .serializers import (
    StudioBookingSerializer,
    AdditionalServiceSerializer,
    BookingSettingsSerializer,
    AvailabilityCheckSerializer,
    AvailableSlotSerializer,
    AdminBookingSerializer
)
from studios.models import AdditionalService, Location
from .services import (
    BookingAvailabilityService,
    BookingCalculationService,
    BookingManagementService
)
from payment_service.models import StudioPayment

from payment_service.services import LiqPayService

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class BookingAvailabilityViewSet(viewsets.ViewSet):
    """Manage booking availability checks and slot queries."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='check-availability')
    def check_availability(self, request):
        """Check available time slots for date, duration, and optional location."""
        serializer = AvailabilityCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        check_date = serializer.validated_data['date']
        duration_hours = serializer.validated_data['duration_hours']
        location_id = serializer.validated_data.get('location_id')

        service = BookingAvailabilityService()
        available_slots = service.get_available_slots(
            check_date,
            duration_hours,
            str(location_id) if location_id else None
        )

        return Response({
            'date': check_date,
            'duration_hours': duration_hours,
            'location_id': str(location_id) if location_id else None,
            'slots': available_slots
        })

    @action(detail=False, methods=['post'], url_path='is-slot-available')
    def is_slot_available(self, request):
        """Check if specific time slot is available for location."""
        booking_date = request.data.get('booking_date')
        booking_time = request.data.get('booking_time')
        duration_hours = request.data.get('duration_hours')
        location_id = request.data.get('location_id')

        if not all([booking_date, booking_time, duration_hours, location_id]):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
            booking_time = datetime.strptime(booking_time, '%H:%M').time()
            duration_hours = int(duration_hours)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date/time format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = BookingAvailabilityService()
        is_available, message = service.is_slot_available(
            booking_date,
            booking_time,
            duration_hours,
            str(location_id)
        )

        return Response({
            'available': is_available,
            'message': message
        })

    @action(detail=False, methods=['post'], url_path='calculate-cost')
    def calculate_cost(self, request):
        """Calculate booking cost with optional services and location."""
        duration_hours = request.data.get('duration_hours')
        location_id = request.data.get('location_id')
        additional_service_ids = request.data.get('additional_service_ids', [])

        if not duration_hours:
            return Response(
                {'error': 'duration_hours is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            duration_hours = int(duration_hours)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid duration_hours'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cost_breakdown = BookingCalculationService.calculate_booking_cost(
            duration_hours,
            str(location_id) if location_id else None,
            additional_service_ids
        )

        return Response(cost_breakdown)

    @action(detail=False, methods=['post'], url_path='location-calendar')
    def location_calendar(self, request):
        """Get availability calendar for location within date range."""
        location_id = request.data.get('location_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        duration_hours = request.data.get('duration_hours', 1)

        if not all([location_id, start_date, end_date]):
            return Response(
                {'error': 'location_id, start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            duration_hours = int(duration_hours)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = BookingAvailabilityService()
        calendar = service.get_location_availability_calendar(
            str(location_id),
            start_date,
            end_date,
            duration_hours
        )

        return Response({
            'location_id': str(location_id),
            'calendar': calendar
        })


class StudioBookingViewSet(viewsets.ModelViewSet):
    """Manage studio bookings with payment integration."""

    serializer_class = StudioBookingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter bookings by location or user phone."""
        queryset = StudioBooking.objects.all()

        if self.request.user.is_staff:
            location_id = self.request.query_params.get('location_id')
            if location_id:
                queryset = queryset.filter(location_id=location_id)
        else:
            phone = self.request.query_params.get('phone_number')
            if phone:
                queryset = queryset.filter(phone_number=phone)
            else:
                queryset = StudioBooking.objects.none()

        return queryset.select_related('location', 'payment').prefetch_related('additional_services')

    def get_serializer_class(self):
        """Return admin serializer for staff users."""
        if self.request.user.is_staff and self.action in ['list', 'retrieve']:
            return AdminBookingSerializer
        return StudioBookingSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create booking and initiate payment process."""
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("\n!!! VALIDATION ERRORS !!!")
            print(serializer.errors)
            print("Request Data:", request.data)
            print("!!! END ERRORS !!!\n")
            serializer.is_valid(raise_exception=True)

        serializer.is_valid(raise_exception=True)


        booking = serializer.save()

        payment = StudioPayment.objects.create(
            amount=booking.deposit_amount,
            description=f"Deposit for booking {booking.id} - {booking.first_name} {booking.last_name} on {booking.booking_date}"
        )

        booking.payment = payment
        booking.save()

        scheme = request.scheme

        host = request.META.get('HTTP_X_FORWARDED_HOST') or request.get_host()

        frontend_base_url = f"{scheme}://{host}"

        liqpay_service = LiqPayService()

        payment_form_data = liqpay_service.generate_payment_form(payment, frontend_base_url)

        return Response({
            'booking': StudioBookingSerializer(booking).data,
            'payment': {
                'payment_id': str(payment.id),
                'amount': str(payment.amount),
                'liqpay_url': 'https://www.liqpay.ua/api/3/checkout',
                'liqpay_data': payment_form_data
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='check-payment-status')
    def check_payment_status(self, request, pk=None):
        """Check payment status and update booking accordingly."""
        booking = self.get_object()

        if not booking.payment:
            return Response({
                'status': 'no_payment',
                'message': 'No payment associated with this booking'
            })

        BookingManagementService.update_payment_status(booking)
        booking.refresh_from_db()

        return Response({
            'booking_status': booking.status,
            'payment': {
                'is_paid': booking.payment.is_paid,
                'liqpay_status': booking.payment.liqpay_status,
                'checkbox_status': booking.payment.checkbox_status
            }
        })

    @action(detail=False, methods=['get'], url_path='my-bookings')
    def my_bookings(self, request):
        """Get bookings by phone number or email."""
        phone = request.query_params.get('phone_number')
        email = request.query_params.get('email')

        if not phone and not email:
            return Response(
                {'error': 'phone_number or email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = StudioBooking.objects.none()

        if phone:
            queryset = StudioBooking.objects.filter(phone_number=phone)
        elif email:
            queryset = StudioBooking.objects.filter(email=email)

        queryset = queryset.order_by('-booking_date', '-booking_time')
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path='confirm',
        permission_classes=[IsAuthenticated]
    )
    def confirm_booking(self, request, pk=None):
        """Confirm paid booking (admin only)."""
        booking = self.get_object()

        if BookingManagementService.confirm_booking(booking):
            return Response({
                'status': 'confirmed',
                'message': 'Booking confirmed successfully'
            })

        return Response({
            'error': 'Booking cannot be confirmed'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        url_path='cancel',
        permission_classes=[IsAuthenticated]
    )
    def cancel_booking(self, request, pk=None):
        """Cancel booking with optional reason (admin only)."""
        booking = self.get_object()
        reason = request.data.get('reason', '')

        if BookingManagementService.cancel_booking(booking, reason):
            return Response({
                'status': 'cancelled',
                'message': 'Booking cancelled successfully'
            })

        return Response({
            'error': 'Booking cannot be cancelled'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        url_path='complete',
        permission_classes=[IsAuthenticated]
    )
    def complete_booking(self, request, pk=None):
        """Mark booking as completed (admin only)."""
        booking = self.get_object()

        if BookingManagementService.complete_booking(booking):
            return Response({
                'status': 'completed',
                'message': 'Booking completed successfully'
            })

        return Response({
            'error': 'Booking cannot be completed'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['post'],
        url_path='admin-create',
        permission_classes=[IsAuthenticated]
    )
    @transaction.atomic
    def admin_create(self, request):
        """Create booking directly without payment validation (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can create bookings directly'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AdminBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        settings = BookingSettings.get_settings()
        if 'base_price_per_hour' not in serializer.validated_data:
            serializer.validated_data['base_price_per_hour'] = settings.base_price_per_hour
        if 'deposit_percentage' not in serializer.validated_data:
            serializer.validated_data['deposit_percentage'] = settings.deposit_percentage

        additional_service_ids = request.data.get('additional_service_ids', [])

        booking = StudioBooking.objects.create(**serializer.validated_data)

        if additional_service_ids:
            services = AdditionalService.objects.filter(
                id__in=additional_service_ids,
                is_active=True
            )
            booking.additional_services.set(services)
            booking.services_total = sum(service.price for service in services)

        if 'total_amount' not in serializer.validated_data:
            booking.total_amount = booking.calculate_total()
        if 'deposit_amount' not in serializer.validated_data:
            booking.deposit_amount = booking.calculate_deposit()

        booking.save()

        return Response(
            AdminBookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='location-bookings')
    def location_bookings(self, request):
        """Get all bookings for specific location with date filtering (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can view location bookings'},
                status=status.HTTP_403_FORBIDDEN
            )

        location_id = request.query_params.get('location_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not location_id:
            return Response(
                {'error': 'location_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = BookingManagementService()
        bookings = service.get_location_bookings(location_id, start_date, end_date)

        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)


class BookingSettingsViewSet(viewsets.ViewSet):
    """Manage booking configuration settings."""

    permission_classes = [AllowAny]

    def list(self, request):
        """Get current booking settings."""
        settings = BookingSettings.get_settings()
        serializer = BookingSettingsSerializer(settings)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_settings(self, request):
        """Update booking settings (admin only)."""
        settings = BookingSettings.get_settings()
        serializer = BookingSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
