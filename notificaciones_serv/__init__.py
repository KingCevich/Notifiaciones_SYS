# Importar la instancia de Celery para que se ejecute cuando se inicia Django
from .celery import app as celery_app

__all__ = ('celery_app',)
