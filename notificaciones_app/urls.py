from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, PlantillaNotificacionViewSet

router = DefaultRouter()
router.register(r'notificaciones', NotificationViewSet,        basename='notification')
router.register(r'plantillas',     PlantillaNotificacionViewSet, basename='plantilla')

urlpatterns = [
    path('', include(router.urls))]