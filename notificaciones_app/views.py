from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Notification, PlantillaNotificacion
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    EnviarNotificacionSerializer,
)
from .tasks import send_notification, get_notification_stats

MENSAJES = {
    "reporte_creado": {
        "titulo": " Reporte publicado",
        "mensaje": "Tu reporte '{nombre}' fue publicado exitosamente.",
    },
    "reporte_fallido": {
        "titulo": " Error al publicar reporte",
        "mensaje": "Hubo un problema al publicar tu reporte '{nombre}'. Intenta de nuevo.",
    },
    "ia_completada": {
        "titulo": " Análisis de IA completado",
        "mensaje": "Se encontraron {cantidad} posible(s) coincidencia(s) para '{nombre}' (mayor similitud: {score}%).",
    },
    "ia_sin_coincidencias": {
        "titulo": " Sin coincidencias por ahora",
        "mensaje": "La IA analizó '{nombre}' pero no encontró coincidencias aún. Te avisaremos si aparece algo.",
    },
    "ia_fallida": {
        "titulo": " Error en análisis de IA",
        "mensaje": "No se pudo analizar la foto de '{nombre}'. Las coincidencias textuales siguen activas.",
    },
    "coincidencia_nueva": {
        "titulo": " Posible coincidencia encontrada",
        "mensaje": "Un nuevo reporte de '{raza}' cerca de tu zona tiene {score}% de similitud con tu mascota.",
    },
}


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        if self.action == 'enviar':
            return EnviarNotificacionSerializer
        return NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.all()
        usuario_id = self.request.query_params.get('usuario_id')
        tipo       = self.request.query_params.get('tipo')
        estado     = self.request.query_params.get('estado')
        leida      = self.request.query_params.get('leida')
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        if leida is not None:
            qs = qs.filter(leida=leida.lower() == 'true')
        return qs

    def create(self, request, *args, **kwargs):
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notif = Notification.objects.create(
            **serializer.validated_data,
            estado='pendiente',
        )
        send_notification.delay(notif.id)
        return Response(NotificationSerializer(notif).data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # POST /api/notificaciones/enviar/
    # Llamado por mascotas_serv con tipo_evento o titulo+mensaje libre
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='enviar')
    def enviar(self, request):
        data        = request.data
        usuario_id  = data.get('usuario_id')
        tipo_evento = data.get('tipo_evento')
        variables   = data.get('variables', {})
        datos_extra = data.get('datos_adicionales', {})

        if not usuario_id:
            return Response({'error': 'Se requiere usuario_id'}, status=status.HTTP_400_BAD_REQUEST)

        if tipo_evento and tipo_evento in MENSAJES:
            template = MENSAJES[tipo_evento]
            titulo   = template['titulo']
            try:
                mensaje = template['mensaje'].format(**variables)
            except KeyError as e:
                return Response({'error': f'Falta variable: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            titulo  = data.get('titulo')
            mensaje = data.get('mensaje')
            if not titulo or not mensaje:
                return Response(
                    {'error': "Envía 'tipo_evento' o 'titulo'+'mensaje'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        notif = Notification.objects.create(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo='inapp',
            estado='enviada',
            enviada_en=timezone.now(),
            datos_adicionales=datos_extra,
        )

        return Response(
            {'status': 'ok', 'message': 'Notificación creada', 'data': NotificationSerializer(notif).data},
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # GET /api/notificaciones/usuario/?usuario_id=1
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='usuario')
    def usuario(self, request):
        usuario_id = request.query_params.get('usuario_id')
        if not usuario_id:
            return Response({'error': 'Se requiere usuario_id'}, status=status.HTTP_400_BAD_REQUEST)

        qs = Notification.objects.filter(usuario_id=usuario_id).order_by('-creada')
        leida = request.query_params.get('leida')
        if leida is not None:
            qs = qs.filter(leida=leida.lower() == 'true')

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(NotificationSerializer(page, many=True).data)
        return Response(NotificationSerializer(qs, many=True).data)

    # ------------------------------------------------------------------
    # GET /api/notificaciones/no-leidas/?usuario_id=1
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='no-leidas')
    def no_leidas(self, request):
        usuario_id = request.query_params.get('usuario_id')
        if not usuario_id:
            return Response({'error': 'Se requiere usuario_id'}, status=status.HTTP_400_BAD_REQUEST)
        count = Notification.objects.filter(usuario_id=usuario_id, leida=False).count()
        return Response({'usuario_id': usuario_id, 'no_leidas': count})

    # ------------------------------------------------------------------
    # POST /api/notificaciones/{id}/marcar-leida/
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='marcar-leida')
    def marcar_leida(self, request, pk=None):
        notif = self.get_object()
        notif.marcar_como_leida()
        return Response({'status': 'ok', 'data': NotificationSerializer(notif).data})

    # ------------------------------------------------------------------
    # POST /api/notificaciones/marcar-todas-leidas/
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        usuario_id = request.data.get('usuario_id')
        if not usuario_id:
            return Response({'error': 'Se requiere usuario_id'}, status=status.HTTP_400_BAD_REQUEST)
        updated = Notification.objects.filter(usuario_id=usuario_id, leida=False).update(leida=True)
        return Response({'status': 'ok', 'marcadas': updated})

    # ------------------------------------------------------------------
    # GET /api/notificaciones/estadisticas/
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request):
        stats = get_notification_stats()
        return Response({'status': 'ok', 'data': stats})


class PlantillaNotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura — las plantillas se crean desde admin."""
    from .serializers import PlantillaNotificacionSerializer
    queryset         = PlantillaNotificacion.objects.all()
    serializer_class = PlantillaNotificacionSerializer