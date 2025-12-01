from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PropCategoryViewSet,
    PropItemViewSet,
    PropAvailabilityViewSet,
    PropRentalSettingsViewSet
)

router = DefaultRouter()
router.register(r'categories', PropCategoryViewSet, basename='prop-category')
router.register(r'items', PropItemViewSet, basename='prop-item')
router.register(r'availability', PropAvailabilityViewSet, basename='prop-availability')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', PropRentalSettingsViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'update'
    }), name='prop-settings'),
]