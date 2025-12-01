from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClothingCategoryViewSet,
    ClothingItemViewSet,
    ClothingAvailabilityViewSet,
    ClothingRentalSettingsViewSet
)

router = DefaultRouter()
router.register(r'categories', ClothingCategoryViewSet, basename='clothing-category')
router.register(r'items', ClothingItemViewSet, basename='clothing-item')
router.register(r'availability', ClothingAvailabilityViewSet, basename='clothing-availability')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', ClothingRentalSettingsViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'update'
    }), name='clothing-settings'),
]