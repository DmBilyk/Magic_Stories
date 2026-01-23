from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudioBookingViewSet,
    BookingAvailabilityViewSet,
    BookingSettingsViewSet, AllInclusiveRequestViewSet
)


app_name = 'bookings'

router = DefaultRouter()
router.register(r'', StudioBookingViewSet, basename='booking')
router.register(r'availability', BookingAvailabilityViewSet, basename='availability')
router.register(r'all-inclusive-requests', AllInclusiveRequestViewSet, basename='all-inclusive-request')

urlpatterns = [



    path('settings/', BookingSettingsViewSet.as_view({'get': 'list'}), name='booking_settings'),

    path('', include(router.urls)),


]