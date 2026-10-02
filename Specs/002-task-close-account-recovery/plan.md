# Implementation Plan: Increment 2 — Cierre de Gestión de Tareas y Recuperación de Acceso

**Branch**: `implementacion-2` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

---

## Summary

Extender el monolito TaskControl construyendo sobre los modelos, servicios y blueprints del Incremento 1:

1. **Soft delete de tareas (HU-05)**: nuevo campo `deleted_at` en `Task`; filtro en queries; nuevo servicio `delete_task`; ruta y botón de eliminación; migración aditiva.
2. **Reapertura de tareas (HU-06)**: nuevo servicio `reopen_task`; acción de auditoría `TASK_REOPENED` diferenciada; ruta dedicada; botón visible sólo en tareas completadas.
3. **Recuperación de contraseña (HU-14)**: nueva entidad `PasswordResetToken`; servicios `request_password_reset` y `reset_password`; rutas `/auth/forgot-password` y `/auth/reset-password/<token>`; simulación de correo por log.

---

## Technical Context

- **Language/Version**: Python 3.11+ (entorno 3.13 en producción local).
- **Framework**: Flask con blueprints existentes (`auth_bp`, `task_bp`).
- **ORM**: SQLAlchemy con Flask-Migrate/Alembic (Principio VI).
- **Storage**: SQLite (`taskcontrol.db` dev, `:memory:` tests).
- **Testing**: `pytest` + `pytest-flask` — disciplina Test-First (Principio IV).
- **Email simulation**: `app.logger.info` con el enlace de reset (sin SMTP real).

---

## Constitution Compliance Check

| Principio | Requisito | Estado | Justificación |
|---|---|---|---|
| I. Monolito | Un solo proceso | PASS | Sin nuevos procesos ni servicios externos. |
| II. Separación | Modelos→Servicios→Rutas→Presentación | PASS | `delete_task`, `reopen_task`, `request_password_reset` viven en la capa de servicio; las rutas delegan. |
| III. Contrato explícito | Endpoints documentados antes de implementar | PASS | Documentado en `contracts/http_contracts.md`. |
| IV. Test-First | Tests en rojo antes del código | PASS | Tests escritos antes que cada servicio/ruta. |
| V. Simplicidad | Sin abstracciones prematuras | PASS | `deleted_at` nullable, sin capa de repositorio adicional. |
| VI. Integridad de datos | Migraciones versionadas | PASS | Una migración aditiva cubre todos los cambios de esquema. |
| VII. Seguridad | Validación backend, tokens seguros | PASS | `secrets.token_hex(32)`, expiración, uso único, respuesta neutral a email desconocido. |
| VIII. Observabilidad | Audit log para toda mutación | PASS | `TASK_DELETED` y `TASK_REOPENED` persisten en `audit_logs`. |

---

## Data Model Changes

### Task (extensión aditiva)

| Campo nuevo | Tipo | Constraint | Descripción |
|---|---|---|---|
| `deleted_at` | DateTime | Nullable | UTC timestamp de eliminación lógica. NULL = activa. |

**Impacto en queries existentes**: `get_user_tasks` y `get_task_by_id` añaden filtro `Task.deleted_at == None`.

### PasswordResetToken (nueva tabla)

| Campo | Tipo | Constraint | Descripción |
|---|---|---|---|
| `id` | Integer | PK, Autoincrement | Identificador interno. |
| `user_id` | Integer | FK `users.id`, Index, Not Null | Usuario propietario del token. |
| `token` | String(64) | Unique, Index, Not Null | Token URL-safe generado con `secrets.token_hex(32)`. |
| `expires_at` | DateTime | Not Null | UTC now + 1 hora al crear. |
| `used_at` | DateTime | Nullable | NULL = no usado. Estampado al consumir el token. |
| `created_at` | DateTime | Not Null, Default UTC now | Timestamp de creación. |

---

## Endpoint Contract Summary (detallado en `contracts/http_contracts.md`)

| Método | Ruta | Historia | Descripción |
|---|---|---|---|
| `POST` | `/tasks/<id>/delete` | HU-05 | Soft delete de tarea propia. |
| `POST` | `/tasks/<id>/reopen` | HU-06 | Reapertura de tarea completada. |
| `GET`  | `/auth/forgot-password` | HU-14 | Formulario de solicitud de reset. |
| `POST` | `/auth/forgot-password` | HU-14 | Procesa solicitud (respuesta neutral). |
| `GET`  | `/auth/reset-password/<token>` | HU-14 | Formulario para nueva contraseña. |
| `POST` | `/auth/reset-password/<token>` | HU-14 | Aplica nueva contraseña y marca token usado. |

---

## Project Structure Changes

```text
Specs/002-task-close-account-recovery/   ← Artefactos de este incremento
├── spec.md
├── plan.md
├── data-model.md
├── contracts/
│   └── http_contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md

src/models/
├── task.py          ← MODIFICADO: campo deleted_at
├── password_reset_token.py   ← NUEVO
└── __init__.py      ← MODIFICADO: exportar PasswordResetToken

src/services/
├── task_service.py  ← MODIFICADO: delete_task, reopen_task; filtros soft-delete
└── auth_service.py  ← MODIFICADO: request_password_reset, reset_password

src/routes/
├── task_routes.py   ← MODIFICADO: rutas /delete y /reopen
└── auth_routes.py   ← MODIFICADO: rutas /forgot-password y /reset-password/<token>

src/templates/
├── tasks/
│   └── list.html    ← MODIFICADO: botón eliminar, botón reabrir (condicional)
└── auth/
    ├── forgot_password.html  ← NUEVO
    └── reset_password.html   ← NUEVO

migrations/versions/
└── <hash>_increment2_soft_delete_password_reset.py  ← NUEVO

tests/unit/
└── test_services.py  ← MODIFICADO: tests soft delete, reopen, password reset

tests/integration/
├── test_task_routes.py  ← MODIFICADO: tests rutas delete y reopen
└── test_auth_routes.py  ← MODIFICADO: tests forgot/reset password
```

---

## Migration Strategy

- **Una sola migración aditiva** para el Incremento 2.
- Operaciones:
  1. `ALTER TABLE tasks ADD COLUMN deleted_at DATETIME` (nullable, default NULL).
  2. `CREATE TABLE password_reset_tokens (...)`.
- Las tareas existentes del Incremento 1 quedan con `deleted_at = NULL` (activas).
- Los usuarios existentes no se ven afectados.

---

## Testing Strategy

### Tests unitarios bloqueantes (Principio IV)

| Test | Descripción |
|---|---|
| `test_delete_task_success` | Verifica que `deleted_at` se estampa y la tarea deja de aparecer en el listado. |
| `test_delete_task_already_deleted` | Verifica error al intentar eliminar dos veces. |
| `test_delete_task_ownership` | Verifica que no se puede eliminar la tarea de otro usuario. |
| `test_edit_deleted_task_fails` | Verifica que editar una tarea eliminada devuelve error. |
| `test_reopen_task_success` | Verifica que status pasa a `in_progress` y auditoría es `TASK_REOPENED`. |
| `test_reopen_non_completed_task_fails` | Verifica error al intentar reabrir tarea `pending` o `in_progress`. |
| `test_request_password_reset_existing_email` | Verifica que se crea un token y se loguea el enlace. |
| `test_request_password_reset_unknown_email` | Verifica que la respuesta es idéntica (sin revelar inexistencia). |
| `test_reset_password_valid_token` | Verifica que el hash se actualiza y `used_at` se estampa. |
| `test_reset_password_expired_token` | Verifica rechazo de token caducado. |
| `test_reset_password_used_token` | Verifica rechazo de token ya consumido. |

### Tests de integración

| Test | Descripción |
|---|---|
| `test_delete_task_route` | POST a `/tasks/<id>/delete` retorna redirect y la tarea no aparece en GET `/tasks`. |
| `test_reopen_task_route` | POST a `/tasks/<id>/reopen` retorna redirect y la tarea aparece como `in_progress`. |
| `test_forgot_password_route` | POST a `/auth/forgot-password` retorna 200 con mensaje neutral. |
| `test_reset_password_route_valid` | GET+POST a `/auth/reset-password/<token>` con token válido actualiza contraseña. |
| `test_reset_password_route_invalid` | GET a `/auth/reset-password/<expired_token>` muestra mensaje de error. |
