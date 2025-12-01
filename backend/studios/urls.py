from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet, AdditionalServiceViewSet, StudioImageViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'services', AdditionalServiceViewSet, basename='service')
router.register(r'studios-images', StudioImageViewSet, basename='studios-image')

urlpatterns = [
    path('', include(router.urls)),
]