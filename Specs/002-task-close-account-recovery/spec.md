# Feature Specification: Increment 2 — Cierre de Gestión de Tareas y Recuperación de Acceso

**Feature**: `002-task-close-account-recovery`
**Branch**: `implementacion-2`
**Date**: 2026-10-01
**Based on**: Incremento 1 completado (HU-01–HU-04, HU-12–HU-13)
**Spec version**: 1.0.0

---

## Overview

Este incremento cierra la gestión básica de tareas del Incremento 1 añadiendo la eliminación lógica (soft delete), la reapertura explícita de tareas completadas, y la recuperación de contraseña mediante tokens seguros de un solo uso. Las tres historias forman un bloque coherente que completa el ciclo de vida de las tareas y el ciclo de acceso de la cuenta.

---

## User Stories

### HU-05 — Eliminación lógica de tareas

**Como** usuario autenticado, **quiero** eliminar una tarea que ya no es relevante, **para** mantener mi listado limpio sin perder el historial de auditoría.

**Criterios de aceptación**:
1. El usuario puede eliminar una tarea propia desde el listado o la vista de detalle.
2. La eliminación es **lógica** (soft delete): la tarea no se borra físicamente de la base de datos; se marca con un timestamp de eliminación.
3. Una tarea eliminada **no aparece** en el listado de tareas por defecto.
4. No se puede eliminar una tarea que ya fue eliminada (idempotencia rechazada con error claro).
5. No se puede editar ni cambiar el estado de una tarea eliminada.
6. El evento de eliminación queda registrado en el log de auditoría con actor, acción `TASK_DELETED` y timestamp.

---

### HU-06 — Reapertura de tareas completadas

**Como** usuario autenticado, **quiero** reabrir una tarea que marqué como completada por error, **para** continuar trabajando en ella sin perder el historial.

**Criterios de aceptación**:
1. El usuario puede reabrir exclusivamente una tarea en estado `completed`; una tarea `pending` o `in_progress` no puede reabrirse (estado inválido para este caso de uso).
2. Al reabrir, la tarea vuelve al estado `in_progress`.
3. El evento queda registrado en el log de auditoría con acción `TASK_REOPENED` — **distinto** de `TASK_STATUS_CHANGED` — de modo que el historial permita distinguir una reapertura de un cambio de estado ordinario.
4. La acción de reapertura sólo está disponible para el usuario propietario de la tarea (verificación en backend).

---

### HU-14 — Recuperación de contraseña

**Como** usuario que olvidó su contraseña, **quiero** poder restablecerla a través de un enlace enviado a mi correo registrado, **para** recuperar el acceso sin revelar si mi correo existe o no en el sistema.

**Criterios de aceptación**:
1. El usuario solicita el restablecimiento escribiendo su correo. La respuesta del sistema es **siempre neutral** ("Si ese correo está registrado, recibirás un enlace") — nunca revela si el correo existe.
2. Si el correo está registrado, el sistema genera un token de restablecimiento único, seguro y con **tiempo de vida de 1 hora**.
3. El token se **invalida** automáticamente al ser usado una vez (invalidación por uso único).
4. El token se **invalida** automáticamente al expirar, aunque no haya sido usado.
5. No se pueden usar tokens expirados ni ya utilizados.
6. En entorno de desarrollo, el correo se simula mediante logging en consola (no se integra un servicio externo de correo real en este incremento).
7. La nueva contraseña debe cumplir las mismas reglas de validación que el registro (mínimo 8 caracteres).

---

## Actors

- **Usuario autenticado** (HU-05, HU-06): usuario con sesión activa que opera sobre sus propias tareas.
- **Usuario no autenticado** (HU-14): cualquier visitante que solicita restablecimiento de contraseña.

---

## Functional Requirements

### Soft Delete (HU-05)

- FR-01: El modelo `Task` incluye un campo `deleted_at` (DateTime, nullable). Una tarea con `deleted_at IS NOT NULL` está eliminada.
- FR-02: `TaskService.delete_task(user_id, task_id)` verifica propiedad y que la tarea no esté ya eliminada antes de estampar `deleted_at`.
- FR-03: `TaskService.get_user_tasks()` excluye por defecto tareas con `deleted_at IS NOT NULL`.
- FR-04: `TaskService.get_task_by_id()` rechaza operaciones (editar, cambiar estado) sobre tareas eliminadas.
- FR-05: Se registra `AuditLog` con `action=TASK_DELETED` tras la eliminación exitosa.

### Reapertura (HU-06)

- FR-06: `TaskService.reopen_task(user_id, task_id)` verifica que la tarea esté en estado `completed`; rechaza con error descriptivo si no.
- FR-07: La reapertura establece `task.status = 'in_progress'`.
- FR-08: Se registra `AuditLog` con `action=TASK_REOPENED` (constante separada de `TASK_STATUS_CHANGED`).
- FR-09: La transición inversa desde `completed` queda bloqueada en `TaskService.update_task_status()` (ya lo está en el Incremento 1); `reopen_task` es el **único** camino para esa transición.

### Recuperación de contraseña (HU-14)

- FR-10: El modelo `PasswordResetToken` almacena `user_id`, `token` (string URL-safe, 64 hex chars), `expires_at` (DateTime UTC, +1h desde creación), `used_at` (DateTime nullable).
- FR-11: `AuthService.request_password_reset(email)` genera token si el correo existe; responde sin distinguir si existe o no.
- FR-12: `AuthService.reset_password(token, new_password)` valida: token existe, `expires_at > now`, `used_at IS NULL`. Si válido, actualiza hash y marca `used_at`.
- FR-13: Nueva contraseña: mínimo 8 caracteres (mismo criterio que el registro).
- FR-14: En desarrollo, el enlace de restablecimiento se imprime en el log de Flask (`app.logger.info`).

---

## Out of Scope

- HU-07 (prioridad), HU-08 (categorías), HU-09 (vencidas) — Incremento 3.
- HU-10 (asignación), HU-11 (notificaciones) — Incremento 4.
- HU-15 (sin recarga de página), HU-16 (drag-and-drop) — Incremento 5.
- Integración con servicio de correo real (SMTP, SendGrid, etc.).

---

## Assumptions

1. La simulación de correo mediante `app.logger.info` es suficiente para el alcance académico del proyecto.
2. El campo `deleted_at` (nullable DateTime) es la representación canónica de soft delete; no se usa un booleano `is_deleted` adicional.
3. Los tokens de restablecimiento se generan con `secrets.token_hex(32)` (64 caracteres hex, criptográficamente seguro).
4. La migración del Incremento 2 es aditiva: añade columnas y tabla sin romper datos del Incremento 1.

---

## Success Criteria

- Un usuario puede eliminar una tarea y ésta desaparece del listado; el log de auditoría registra el evento `TASK_DELETED`.
- Una tarea eliminada no puede editarse ni cambiar de estado; la UI muestra un error apropiado.
- Un usuario puede reabrir una tarea `completed` y el log registra `TASK_REOPENED` (distinguible de `TASK_STATUS_CHANGED`).
- Un usuario puede solicitar restablecimiento de contraseña; el token aparece en logs de consola; al usarlo la sesión se invalida y puede loguearse con la nueva clave.
- Un token expirado o ya usado es rechazado con mensaje claro.
- El 100% de las pruebas automatizadas del Incremento 1 y del Incremento 2 pasan sin modificar las del Incremento 1.
