from celery import shared_task
from django.utils import timezone
from .models import Notification
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def send_notification(self, notification_id):
    try:
        notif = Notification.objects.get(id=notification_id)
        logger.info(f"📌 Procesando notificación {notification_id} tipo={notif.tipo}")
        print(f"\n{'='*60}\n🔔 {notif.get_tipo_display().upper()}\nPara: usuario_{notif.usuario_id}\nTítulo: {notif.titulo}\nMensaje: {notif.mensaje}\n{'='*60}\n")
        notif.estado = 'enviada'
        notif.enviada_en = timezone.now()
        notif.save(update_fields=['estado', 'enviada_en'])
        logger.info(f"✅ Notificación {notification_id} enviada")
        return f"ok:{notification_id}"
    except Notification.DoesNotExist:
        logger.error(f"❌ Notificación {notification_id} no existe")
        return f"error:not_found"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


# Aliases que views.py llama por tipo — todos usan send_notification
send_email_notification = send_notification
send_sms_notification   = send_notification
send_push_notification  = send_notification
create_inapp_notification = send_notification
send_batch_notifications  = send_notification


@shared_task
def get_notification_stats():
    total     = Notification.objects.count()
    enviadas  = Notification.objects.filter(estado='enviada').count()
    fallidas  = Notification.objects.filter(estado='fallida').count()
    pendientes = Notification.objects.filter(estado='pendiente').count()
    return {
        'total': total, 'enviadas': enviadas,
        'fallidas': fallidas, 'pendientes': pendientes,
        'tasa_exito': round(enviadas / total * 100, 2) if total else 0.0,
    }


@shared_task
def cleanup_old_notifications(days=30):
    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted, _ = Notification.objects.filter(creada__lt=cutoff).delete()
    return f"Eliminadas: {deleted}"