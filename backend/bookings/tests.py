from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, time, timedelta
from decimal import Decimal

from .models import StudioBooking, AdditionalService, BookingSettings
from .services import BookingAvailabilityService, BookingCalculationService


class BookingSettingsTestCase(TestCase):
    def setUp(self):
        self.settings = BookingSettings.get_settings()

    def test_settings_singleton(self):
        """Test that only one settings instance exists"""
        settings1 = BookingSettings.get_settings()
        settings2 = BookingSettings.get_settings()
        self.assertEqual(settings1.id, settings2.id)

    def test_default_values(self):
        """Test default settings values"""
        self.assertEqual(self.settings.base_price_per_hour, Decimal('500.00'))
        self.assertEqual(self.settings.deposit_percentage, Decimal('30.00'))
        self.assertTrue(self.settings.is_booking_enabled)


class AdditionalServiceTestCase(TestCase):
    def setUp(self):
        self.service = AdditionalService.objects.create(
            name="Professional Photographer",
            description="Expert photography services",
            price=Decimal('1000.00'),
            is_active=True
        )

    def test_service_creation(self):
        """Test service creation"""
        self.assertEqual(self.service.name, "Professional Photographer")
        self.assertEqual(self.service.price, Decimal('1000.00'))

    def test_service_string_representation(self):
        """Test service __str__ method"""
        expected = f"{self.service.name} - {self.service.price} UAH"
        self.assertEqual(str(self.service), expected)


class StudioBookingTestCase(TestCase):
    def setUp(self):
        self.settings = BookingSettings.get_settings()
        self.service1 = AdditionalService.objects.create(
            name="Lighting Package",
            price=Decimal('500.00'),
            is_active=True
        )
        self.service2 = AdditionalService.objects.create(
            name="Backdrop Set",
            price=Decimal('300.00'),
            is_active=True
        )

        self.booking = StudioBooking.objects.create(
            first_name="John",
            last_name="Doe",
            phone_number="+380501234567",
            email="john@example.com",
            booking_date=date.today() + timedelta(days=7),
            booking_time=time(14, 0),
            duration_hours=2,
            base_price_per_hour=self.settings.base_price_per_hour,
            deposit_percentage=self.settings.deposit_percentage,
            total_amount=Decimal('1000.00'),
            deposit_amount=Decimal('300.00')
        )

    def test_booking_creation(self):
        """Test booking creation"""
        self.assertEqual(self.booking.first_name, "John")
        self.assertEqual(self.booking.status, 'pending_payment')

    def test_calculate_total(self):
        """Test total calculation with services"""
        self.booking.additional_services.add(self.service1, self.service2)
        total = self.booking.calculate_total()
        expected = (self.settings.base_price_per_hour * 2) + Decimal('800.00')
        self.assertEqual(total, expected)

    def test_calculate_deposit(self):
        """Test deposit calculation"""
        self.booking.total_amount = Decimal('1000.00')
        deposit = self.booking.calculate_deposit()
        expected = Decimal('300.00')  # 30% of 1000
        self.assertEqual(deposit, expected)

    def test_get_end_time(self):
        """Test end time calculation"""
        end_time = self.booking.get_end_time()
        expected_end = time(16, 0)  # 14:00 + 2 hours
        self.assertEqual(end_time, expected_end)


class BookingAvailabilityServiceTestCase(TestCase):
    def setUp(self):
        self.settings = BookingSettings.get_settings()
        self.service = BookingAvailabilityService()
        self.test_date = date.today() + timedelta(days=7)

        # Create a booking
        StudioBooking.objects.create(
            first_name="Jane",
            last_name="Smith",
            phone_number="+380501234567",
            booking_date=self.test_date,
            booking_time=time(14, 0),
            duration_hours=2,
            base_price_per_hour=Decimal('500.00'),
            total_amount=Decimal('1000.00'),
            deposit_amount=Decimal('300.00'),
            status='confirmed'
        )

    def test_get_available_slots(self):
        """Test getting available slots"""
        slots = self.service.get_available_slots(self.test_date, 2)
        self.assertIsInstance(slots, list)
        self.assertTrue(len(slots) > 0)

    def test_slot_conflict_detection(self):
        """Test that existing booking creates unavailability"""
        is_available, message = self.service.is_slot_available(
            self.test_date,
            time(14, 0),
            2
        )
        self.assertFalse(is_available)
        self.assertIn("conflict", message.lower())

    def test_slot_available(self):
        """Test that non-conflicting slot is available"""
        is_available, message = self.service.is_slot_available(
            self.test_date,
            time(10, 0),
            2
        )
        self.assertTrue(is_available)

    def test_past_date_validation(self):
        """Test that past dates are rejected"""
        past_date = date.today() - timedelta(days=1)
        is_available, message = self.service.is_slot_available(
            past_date,
            time(14, 0),
            2
        )
        self.assertFalse(is_available)
        self.assertIn("past", message.lower())


class BookingCalculationServiceTestCase(TestCase):
    def setUp(self):
        self.settings = BookingSettings.get_settings()
        self.service1 = AdditionalService.objects.create(
            name="Service 1",
            price=Decimal('500.00'),
            is_active=True
        )
        self.service2 = AdditionalService.objects.create(
            name="Service 2",
            price=Decimal('300.00'),
            is_active=True
        )

    def test_calculate_without_services(self):
        """Test calculation without additional services"""
        result = BookingCalculationService.calculate_booking_cost(2)
        expected_base = self.settings.base_price_per_hour * 2

        self.assertEqual(result['base_cost'], expected_base)
        self.assertEqual(result['services_cost'], Decimal('0.00'))
        self.assertEqual(result['total_amount'], expected_base)

    def test_calculate_with_services(self):
        """Test calculation with additional services"""
        service_ids = [str(self.service1.id), str(self.service2.id)]
        result = BookingCalculationService.calculate_booking_cost(2, service_ids)

        expected_base = self.settings.base_price_per_hour * 2
        expected_services = Decimal('800.00')
        expected_total = expected_base + expected_services
        expected_deposit = (expected_total * self.settings.deposit_percentage / 100).quantize(Decimal('0.01'))

        self.assertEqual(result['base_cost'], expected_base)
        self.assertEqual(result['services_cost'], expected_services)
        self.assertEqual(result['total_amount'], expected_total)
        self.assertEqual(result['deposit_amount'], expected_deposit)


class BookingAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.settings = BookingSettings.get_settings()
        self.service = AdditionalService.objects.create(
            name="Test Service",
            price=Decimal('500.00'),
            is_active=True
        )

    def test_list_services(self):
        """Test listing additional services"""
        url = reverse('bookings:service-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_check_availability(self):
        """Test availability check endpoint"""
        url = reverse('bookings:availability-check-availability')
        test_date = date.today() + timedelta(days=7)
        data = {
            'date': test_date.isoformat(),
            'duration_hours': 2
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('slots', response.data)
        self.assertIsInstance(response.data['slots'], list)

    def test_calculate_cost(self):
        """Test cost calculation endpoint"""
        url = reverse('bookings:availability-calculate-cost')
        data = {
            'duration_hours': 2,
            'additional_service_ids': [str(self.service.id)]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_amount', response.data)
        self.assertIn('deposit_amount', response.data)

    def test_create_booking(self):
        """Test booking creation"""
        url = reverse('bookings:booking-list')
        test_date = date.today() + timedelta(days=7)

        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+380501234567',
            'email': 'john@example.com',
            'booking_date': test_date.isoformat(),
            'booking_time': '14:00',
            'duration_hours': 2,
            'additional_service_ids': [str(self.service.id)]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking', response.data)
        self.assertIn('payment', response.data)

        # Verify booking was created
        booking_id = response.data['booking']['id']
        booking = StudioBooking.objects.get(id=booking_id)
        self.assertEqual(booking.first_name, 'John')
        self.assertEqual(booking.status, 'pending_payment')