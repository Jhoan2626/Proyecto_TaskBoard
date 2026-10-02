# Implementation Tasks: Increment 2 — Cierre de Gestión de Tareas y Recuperación de Acceso

**Branch**: `implementacion-2` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

> **Nota de equipo**: Este incremento NO modifica nada relacionado con prioridad (HU-07), categorías (HU-08) ni tareas vencidas (HU-09), que son responsabilidad del Incremento 3. Los archivos compartidos (`task.py`, `task_service.py`, `task_routes.py`) se modifican de forma aditiva y compatible.

---

## Phase 1: Setup (Migración e Infraestructura de Datos)

**Purpose**: Extender el esquema de BD de forma aditiva antes de implementar lógica de negocio.

- [X] T201 Agregar campo `deleted_at` (DateTime nullable) al modelo `Task` en `src/models/task.py`
- [X] T202 Crear modelo `PasswordResetToken` en `src/models/password_reset_token.py` con campos: `id`, `user_id` (FK), `token` (String 64, unique), `expires_at`, `used_at`, `created_at`
- [X] T203 Exportar `PasswordResetToken` en `src/models/__init__.py`
- [X] T204 Agregar constantes `ACTION_TASK_DELETED` y `ACTION_TASK_REOPENED` al modelo `AuditLog` en `src/models/audit_log.py`
- [X] T205 Generar y aplicar migración Alembic para los cambios del Incremento 2 (`flask db migrate -m "increment2_soft_delete_password_reset"` + `flask db upgrade`)

---

## Phase 2: Tests Bloqueantes — Soft Delete (HU-05)

**Purpose**: Test-First para eliminación lógica de tareas (Principio IV).

- [X] T206 [P] Escribir tests unitarios en `tests/unit/test_services.py` para:
  - `test_delete_task_success`: verifica `deleted_at` se estampa y la tarea deja de aparecer en `get_user_tasks`
  - `test_delete_task_already_deleted`: verifica error al eliminar dos veces
  - `test_delete_task_wrong_owner`: verifica que otro usuario no puede eliminar la tarea
  - `test_edit_deleted_task_fails`: verifica que `update_task` rechaza tarea eliminada
  - `test_change_status_deleted_task_fails`: verifica que `update_task_status` rechaza tarea eliminada
- [X] T207 [P] Escribir test de integración en `tests/integration/test_task_routes.py`:
  - `test_delete_task_route`: POST `/tasks/<id>/delete` redirige y la tarea desaparece del listado

---

## Phase 3: Implementación — Soft Delete (HU-05)

**Purpose**: Implementar servicios y ruta de eliminación lógica.

- [X] T208 Implementar `TaskService.delete_task(user_id, task_id)` en `src/services/task_service.py`:
  - Verifica propiedad (usa `get_task_by_id`)
  - Verifica que `deleted_at` sea None (rechaza si ya eliminada)
  - Estampa `task.deleted_at = datetime.now(UTC)` y hace `db.session.commit()`
  - Llama `AuditService.log_event(..., action=TASK_DELETED, ...)`
- [X] T209 Modificar `TaskService.get_user_tasks()` para excluir `Task.deleted_at != None`
- [X] T210 Modificar `TaskService.get_task_by_id()` para rechazar tareas con `deleted_at != None` con mensaje "La tarea ha sido eliminada."
- [X] T211 Agregar ruta `POST /tasks/<int:task_id>/delete` en `src/routes/task_routes.py`
- [X] T212 Modificar template `src/templates/tasks/list.html` para mostrar botón "Eliminar" con confirmación JavaScript en cada tarea activa

---

## Phase 4: Tests Bloqueantes — Reapertura (HU-06)

**Purpose**: Test-First para reapertura de tareas completadas (Principio IV).

- [X] T213 [P] Escribir tests unitarios en `tests/unit/test_services.py` para:
  - `test_reopen_task_success`: verifica estado → `in_progress` y auditoría `TASK_REOPENED`
  - `test_reopen_pending_task_fails`: verifica error al reabrir tarea `pending`
  - `test_reopen_in_progress_task_fails`: verifica error al reabrir tarea `in_progress`
  - `test_reopen_deleted_task_fails`: verifica error al reabrir tarea eliminada
- [X] T214 [P] Escribir test de integración en `tests/integration/test_task_routes.py`:
  - `test_reopen_task_route`: POST `/tasks/<id>/reopen` desde tarea completed redirige y estado es `in_progress`
  - `test_reopen_non_completed_route`: POST `/tasks/<id>/reopen` desde tarea pending retorna error

---

## Phase 5: Implementación — Reapertura (HU-06)

**Purpose**: Implementar servicio y ruta de reapertura.

- [X] T215 Implementar `TaskService.reopen_task(user_id, task_id)` en `src/services/task_service.py`:
  - Verifica propiedad y que no esté eliminada (vía `get_task_by_id`)
  - Verifica que `task.status == STATUS_COMPLETED` (rechaza cualquier otro estado)
  - Establece `task.status = STATUS_IN_PROGRESS` y commit
  - Llama `AuditService.log_event(..., action=TASK_REOPENED, details={old: completed, new: in_progress})`
- [X] T216 Agregar ruta `POST /tasks/<int:task_id>/reopen` en `src/routes/task_routes.py`
- [X] T217 Modificar template `src/templates/tasks/list.html` para mostrar botón "Reabrir" **únicamente** en tareas con estado `completed`

---

## Phase 6: Tests Bloqueantes — Recuperación de Contraseña (HU-14)

**Purpose**: Test-First para flujo de reset de contraseña (Principio IV).

- [X] T218 [P] Escribir tests unitarios en `tests/unit/test_services.py` para:
  - `test_request_password_reset_existing_email`: verifica creación de token y log del enlace
  - `test_request_password_reset_unknown_email`: verifica que NO se crea token pero respuesta es idéntica (no revela inexistencia)
  - `test_reset_password_valid_token`: verifica hash actualizado y `used_at` estampado
  - `test_reset_password_expired_token`: verifica rechazo con error
  - `test_reset_password_used_token`: verifica rechazo de token ya consumido
  - `test_reset_password_short_password`: verifica rechazo de contraseña < 8 chars
- [X] T219 [P] Escribir tests de integración en `tests/integration/test_auth_routes.py`:
  - `test_forgot_password_get`: GET `/auth/forgot-password` retorna 200
  - `test_forgot_password_post_existing`: POST con email registrado retorna 200 con mensaje neutral
  - `test_forgot_password_post_unknown`: POST con email desconocido retorna 200 con el mismo mensaje
  - `test_reset_password_get_valid_token`: GET con token válido retorna 200
  - `test_reset_password_get_invalid_token`: GET con token inválido redirige a forgot-password
  - `test_reset_password_post_success`: POST con token válido y password nueva redirige a login
  - `test_reset_password_post_expired`: POST con token expirado redirige a forgot-password con error

---

## Phase 7: Implementación — Recuperación de Contraseña (HU-14)

**Purpose**: Implementar modelo, servicios y rutas de reset de contraseña.

- [X] T220 Implementar `AuthService.request_password_reset(email)` en `src/services/auth_service.py`:
  - Busca usuario por email (en silencio si no existe)
  - Si existe: genera `secrets.token_hex(32)`, crea `PasswordResetToken(expires_at=now+1h)`, commit
  - Loguea el enlace con `app.logger.info(f"[DEV] Reset link: /auth/reset-password/{token}")`
  - **Siempre** retorna `(True, None)` sin revelar si el email existe
- [X] T221 Implementar `AuthService.reset_password(token_str, new_password)` en `src/services/auth_service.py`:
  - Busca `PasswordResetToken` por token
  - Valida: existe, `expires_at > now`, `used_at IS NULL`
  - Valida: `len(new_password) >= 8`
  - Actualiza `user.set_password(new_password)`, estampa `token.used_at = now`, commit
  - Retorna `(True, None)` en éxito o `(False, "mensaje de error")` en cualquier fallo
- [X] T222 Agregar rutas `GET/POST /auth/forgot-password` en `src/routes/auth_routes.py`
- [X] T223 Agregar rutas `GET/POST /auth/reset-password/<token>` en `src/routes/auth_routes.py`
- [X] T224 Crear template `src/templates/auth/forgot_password.html` (formulario email + mensaje neutral)
- [X] T225 Crear template `src/templates/auth/reset_password.html` (formulario password + confirm)

---

## Phase 8: Polish & Validación Final

**Purpose**: Verificación integral del Incremento 2 completo.

- [X] T226 Ejecutar suite completa de tests (`pytest -v`) y verificar que **todos** pasan (inc. Incremento 1)
- [X] T227 Verificar en navegador el flujo completo: crear tarea → eliminar → confirmar que no aparece → crear otra → completar → reabrir → verificar estado
- [X] T228 Verificar flujo de recuperación de contraseña: solicitar reset → copiar token del log → abrir enlace → ingresar nueva contraseña → login con nueva contraseña
- [X] T229 Confirmar que los 11 tests nuevos de servicios y los 7 de integración pasan, y los 29 del Incremento 1 no se rompen

---

## Task Summary

| Fase | Tasks | Historia |
|---|---|---|
| Setup (migración) | T201–T205 | Infraestructura |
| Tests HU-05 | T206–T207 | Soft delete |
| Impl HU-05 | T208–T212 | Soft delete |
| Tests HU-06 | T213–T214 | Reapertura |
| Impl HU-06 | T215–T217 | Reapertura |
| Tests HU-14 | T218–T219 | Reset contraseña |
| Impl HU-14 | T220–T225 | Reset contraseña |
| Polish | T226–T229 | Validación integral |
