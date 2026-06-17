from django.test import TestCase
from .models import Notification, PlantillaNotificacion
from .tasks import (
    send_email_notification,
    send_sms_notification,
    send_push_notification,
    get_notification_stats,
)


class NotificationModelTests(TestCase):
    """Tests para el modelo Notification."""
    
    def setUp(self):
        """Crear datos de prueba."""
        self.notification = Notification.objects.create(
            usuario_id=1,
            titulo="Test Notification",
            mensaje="Este es un mensaje de prueba",
            tipo="email",
            estado="pendiente"
        )
    
    def test_crear_notificacion(self):
        """Verificar que se crea una notificación correctamente."""
        self.assertEqual(self.notification.usuario_id, 1)
        self.assertEqual(self.notification.tipo, "email")
        self.assertEqual(self.notification.estado, "pendiente")
    
    def test_marcar_como_leida(self):
        """Verificar que se puede marcar como leída."""
        self.notification.marcar_como_leida()
        self.assertTrue(self.notification.leida)
    
    def test_marcar_como_enviada(self):
        """Verificar que se puede marcar como enviada."""
        self.notification.marcar_como_enviada()
        self.assertEqual(self.notification.estado, "enviada")
        self.assertIsNotNone(self.notification.enviada_en)
    
    def test_marcar_como_fallida(self):
        """Verificar que se puede marcar como fallida."""
        self.notification.marcar_como_fallida("Error de prueba")
        self.assertEqual(self.notification.estado, "fallida")
        self.assertEqual(self.notification.error, "Error de prueba")


class PlantillaNotificacionTests(TestCase):
    """Tests para el modelo PlantillaNotificacion."""
    
    def setUp(self):
        self.plantilla = PlantillaNotificacion.objects.create(
            nombre="bienvenida",
            tipo="email",
            titulo="Bienvenido {nombre}",
            mensaje="Hola {nombre}, te damos la bienvenida a nuestra plataforma",
            activa=True
        )
    
    def test_crear_plantilla(self):
        """Verificar que se crea una plantilla."""
        self.assertEqual(self.plantilla.nombre, "bienvenida")
        self.assertTrue(self.plantilla.activa)
