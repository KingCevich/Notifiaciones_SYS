from django.db import models
from django.utils import timezone


TIPO_CHOICES = [
    ('inapp', 'In-App'),
    ('email', 'Email'),
    ('sms',   'SMS'),
    ('push',  'Push'),
]

ESTADO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('enviada',   'Enviada'),
    ('fallida',   'Fallida'),
]


class Notification(models.Model):
    usuario_id        = models.IntegerField()
    titulo            = models.CharField(max_length=255)
    mensaje           = models.TextField()
    tipo              = models.CharField(max_length=10, choices=TIPO_CHOICES, default='inapp')
    leida             = models.BooleanField(default=False)
    estado            = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    error             = models.TextField(blank=True, null=True)
    creada            = models.DateTimeField(auto_now_add=True)
    actualizada       = models.DateTimeField(auto_now=True)
    enviada_en        = models.DateTimeField(null=True, blank=True)
    datos_adicionales = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-creada']
        indexes  = [
            models.Index(fields=['usuario_id', '-creada']),
            models.Index(fields=['leida']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"[{self.tipo}] {self.titulo} → usuario {self.usuario_id}"

    def marcar_como_leida(self):
        self.leida = True
        self.save(update_fields=['leida', 'actualizada'])

    def marcar_como_enviada(self):
        self.estado    = 'enviada'
        self.enviada_en = timezone.now()
        self.save(update_fields=['estado', 'enviada_en', 'actualizada'])

    def marcar_como_fallida(self, error_msg):
        self.estado = 'fallida'
        self.error  = error_msg
        self.save(update_fields=['estado', 'error', 'actualizada'])


class PlantillaNotificacion(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES)
    titulo      = models.CharField(max_length=255)
    mensaje     = models.TextField(help_text="Puede incluir {variables}")
    activa      = models.BooleanField(default=True)
    creada      = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"