# Implementation Tasks: Increment 4 - Colaboración

**Branch**: `implementacion-4` | **Date**: 2026-10-05 | **Base**: Incrementos 1 y 2 (en `main`)

> **Nota de equipo**: Este incremento NO toca prioridad (HU-07), categorías (HU-08) ni vencimiento (HU-09), responsabilidad del Incremento 3 (rama `implementacion-3`). Cambios en archivos compartidos (`task.py`, `task_service.py`, `task_routes.py`, `list.html`, `__init__.py`) son aditivos y mínimos. La lógica nueva vive en archivos propios (`assignment_service.py`, `notification_service.py`, `collab_routes.py`, `notification.py`).
>
> **Al fusionar con Inc. 3**: la migración `a4c0ab04c001` tiene `down_revision = 49aefa834f53`, igual que la del Inc. 3. Resolver con `flask db merge heads` o re-encadenando `down_revision`. Además `get_user_tasks` (firma con `scope`) y `list.html` pueden requerir un merge manual simple.

## Decisiones de diseño (respuestas a las preguntas abiertas del spec)

| Tema | Decisión |
|---|---|
| Propietario vs asignado | Campos separados: `Task.user_id` (propietario/creador, intacto) + `Task.assignee_id` (nullable, FK `users.id`). Mantiene la validación de propiedad de Inc. 1–2 sin reinterpretarla. |
| Destino de la asignación | Por correo; debe existir en `users` (validado en backend). Auto-asignación rechazada. Correo vacío = desasignar. |
| Usuario "activo" | El modelo `User` no tiene bandera de estado; "existe" equivale a activo. |
| Listado | Une creadas + asignadas. Se distingue visualmente ("Asignada por…") y con filtro `?scope=all\|mine\|assigned`. |
| Permisos del asignado | Solo lectura: editar, eliminar, cambiar estado, reabrir y reasignar siguen siendo solo del propietario. |
| Notificación | Tabla `notifications`; se marca leída (`is_read`) y **persiste**. Se crea solo al asignar/reasignar (no al desasignar). |
| Atomicidad | Asignación + notificación + auditoría se confirman en un único commit (`AuditService.log_event`). |
| Auditoría | `TASK_ASSIGNED` con `old_assignee_id` / `new_assignee_id`, actor y timestamp. |

## Contrato HTTP

| Método y ruta | Entrada | Salida / errores |
|---|---|---|
| `POST /tasks/<id>/assign` | `assignee_email` (JSON o form); vacío = desasignar | 200 `{message, assignee_id}`; 400 correo no registrado / auto-asignación / ya asignada; 403 no propietario; 404 tarea inexistente; 401 sin sesión |
| `GET /notifications[?unread=1]` | — | HTML, o JSON (`Accept: application/json`) `{unread_count, notifications[]}` |
| `POST /notifications/<id>/read` | — | 200 `{is_read:true}`; 403 ajena; 404 inexistente |
| `POST /notifications/read-all` | — | 200 `{updated}` |
| `GET /tasks?scope=mine\|assigned` | — | listado extendido (filtro `status` se conserva) |

## Phase 1: Datos
- [X] T401 `Task.assignee_id` + relaciones (`foreign_keys` explícitos en `Task.user` / `User.tasks`)
- [X] T402 Modelo `Notification` (`user_id`, `task_id`, `actor_id`, `type`, `message`, `is_read`, `created_at`) y export en `models/__init__.py`
- [X] T403 `AuditLog.ACTION_TASK_ASSIGNED`
- [X] T404 Migración Alembic `a4c0ab04c001` (aditiva; tareas existentes quedan sin asignar)

## Phase 2: Tests bloqueantes (Principio IV)
- [X] T405 `tests/unit/test_collaboration_services.py`: asignar genera exactamente 1 notificación; correo inexistente rechazado; solo propietario; auto-asignación; tarea eliminada; sin duplicados; auditoría old/new; reasignación; desasignación; listado del asignado; asignado no edita/elimina; marcar leída persiste; leída ajena rechazada
- [X] T406 `tests/integration/test_collaboration_routes.py`: 401/400/403/404 y flujo end-to-end

## Phase 3: Servicios y rutas
- [X] T407 `AssignmentService.assign_task`
- [X] T408 `NotificationService` (listar, contar, marcar leída/todas)
- [X] T409 `TaskService.get_user_tasks(..., scope=)` (creadas + asignadas)
- [X] T410 `collab_routes.py` + registro en `create_app` + context processor `unread_notifications`

## Phase 4: UI
- [X] T411 `tasks/list.html`: filtro de ámbito, "Asignada por/a", formulario de asignación, acciones solo para propietario
- [X] T412 `notifications/list.html` y enlace con contador en `base.html`
