from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudioBookingViewSet,
    BookingAvailabilityViewSet,
    BookingSettingsViewSet
)

app_name = 'bookings'

router = DefaultRouter()
router.register(r'bookings', StudioBookingViewSet, basename='booking')
router.register(r'availability', BookingAvailabilityViewSet, basename='availability')
router.register(r'settings', BookingSettingsViewSet, basename='settings')

urlpatterns = [
    path('', include(router.urls)),
]