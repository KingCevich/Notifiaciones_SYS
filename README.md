# 🔔 notificaciones_serv

Microservicio de gestión y envío de notificaciones del sistema SanosYSalvos. Recibe eventos de otros microservicios (principalmente `mascotas_serv` vía Celery) y crea notificaciones in-app para los usuarios, alertándoles de coincidencias detectadas, publicaciones de reportes y resultados del análisis IA.

**Puerto:** `8005`

---

## Responsabilidades

- Recibir eventos de notificación desde otros microservicios
- Crear notificaciones in-app a partir de plantillas predefinidas
- Gestionar el estado de lectura de las notificaciones
- Proveer conteo de notificaciones no leídas para el badge del frontend
- Almacenar datos adicionales como coincidencias detectadas por la IA

---

## Modelos

### `Notification`

| Campo | Tipo | Descripción |
|---|---|---|
| `usuario_id` | IntegerField | ID del usuario destinatario |
| `titulo` | CharField | Título de la notificación |
| `mensaje` | TextField | Mensaje de la notificación |
| `tipo` | CharField | Tipo: `inapp`, `email`, `sms`, `push` |
| `leida` | BooleanField | Si el usuario ya leyó la notificación |
| `estado` | CharField | Estado: `pendiente`, `enviada`, `fallida` |
| `error` | TextField | Mensaje de error si falló el envío |
| `creada` | DateTimeField | Fecha de creación automática |
| `enviada_en` | DateTimeField | Fecha en que se marcó como enviada |
| `datos_adicionales` | JSONField | Datos extra (ej: coincidencias de la IA con scores) |

### `PlantillaNotificacion`

| Campo | Tipo | Descripción |
|---|---|---|
| `nombre` | CharField | Identificador único de la plantilla |
| `tipo` | CharField | Tipo de notificación |
| `titulo` | CharField | Título con variables `{nombre}` |
| `mensaje` | TextField | Mensaje con variables `{nombre}`, `{cantidad}`, etc. |
| `activa` | BooleanField | Si la plantilla está activa |

### Plantillas predefinidas

| nombre | Descripción |
|---|---|
| `reporte_creado` | Se dispara al publicar un reporte exitosamente |
| `ia_completada` | Se dispara cuando Celery termina el análisis IA con coincidencias |
| `ia_sin_coincidencias` | Se dispara cuando la IA no encuentra coincidencias |
| `ia_fallida` | Se dispara si el análisis IA falla |

---

## Endpoints

| Método | URL | Auth requerida | Descripción |
|---|---|---|---|
| POST | `/api/notificaciones/enviar/` | No | Crear y enviar una notificación (llamado por otros microservicios) |
| GET | `/api/notificaciones/usuario/` | No | Listar notificaciones de un usuario (`?usuario_id=`) |
| GET | `/api/notificaciones/no-leidas/` | No | Conteo de no leídas (`?usuario_id=`) |
| POST | `/api/notificaciones/{id}/marcar-leida/` | No | Marcar una notificación como leída |
| POST | `/api/notificaciones/marcar-todas-leidas/` | No | Marcar todas las notificaciones del usuario como leídas |
| GET | `/api/notificaciones/estadisticas/` | No | Estadísticas generales de notificaciones |
| GET | `/api/plantillas/` | No | Listar plantillas disponibles |

> Se puede utilizar Thunder o Postman para las peticiones API: http://127.0.0.1:8005/

### Ejemplo de payload para `/api/notificaciones/enviar/`

```json
{
    "usuario_id": 14,
    "tipo_evento": "ia_completada",
    "variables": {
        "nombre": "Max",
        "cantidad": 5,
        "score": 96.5
    },
    "datos_adicionales": {
        "reporte_id": 44,
        "raza_detectada": "Labrador Retriever",
        "coincidencias": [
            {
                "reporte_id": 15,
                "score_final": 96.5,
                "score_visual": 100.0,
                "score_textual": 90.0
            }
        ]
    }
}
```

---

## Tests

- `test_crear_notificacion` — Verifica que se crea una notificación con campos correctos
- `test_marcar_como_leida` — Verifica que `marcar_como_leida()` actualiza el campo `leida`
- `test_marcar_como_enviada` — Verifica que `marcar_como_enviada()` actualiza estado y timestamp
- `test_marcar_como_fallida` — Verifica que `marcar_como_fallida()` guarda el error
- `test_crear_plantilla` — Verifica que se crea una plantilla correctamente

```bash
cd notificaciones_serv
python manage.py test
```

---

## Levantar el servicio

```bash
cd notificaciones_serv
python manage.py migrate
python manage.py runserver 8005
```

> **Nota:** Este servicio es llamado automáticamente por `mascotas_serv` (vía Celery) cuando se detectan coincidencias de IA. No requiere otros microservicios para funcionar de forma independiente.