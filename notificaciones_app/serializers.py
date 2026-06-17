from rest_framework import serializers
from .models import Notification, PlantillaNotificacion


class NotificationSerializer(serializers.ModelSerializer):
    tipo_display   = serializers.CharField(source='get_tipo_display',   read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model  = Notification
        fields = [
            'id', 'usuario_id', 'titulo', 'mensaje',
            'tipo', 'tipo_display', 'leida',
            'estado', 'estado_display', 'error',
            'creada', 'actualizada', 'enviada_en', 'datos_adicionales',
        ]
        read_only_fields = ['id', 'creada', 'actualizada', 'enviada_en']


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['usuario_id', 'titulo', 'mensaje', 'tipo', 'datos_adicionales']


class EnviarNotificacionSerializer(serializers.Serializer):
    usuario_id        = serializers.IntegerField()
    tipo_evento       = serializers.CharField(required=False, allow_blank=True)
    variables         = serializers.JSONField(required=False, default=dict)
    titulo            = serializers.CharField(required=False, allow_blank=True)
    mensaje           = serializers.CharField(required=False, allow_blank=True)
    datos_adicionales = serializers.JSONField(required=False, default=dict)


class PlantillaNotificacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = PlantillaNotificacion
        fields = ['id', 'nombre', 'descripcion', 'tipo', 'tipo_display',
                  'titulo', 'mensaje', 'activa', 'creada', 'actualizada']
        read_only_fields = ['id', 'creada', 'actualizada']