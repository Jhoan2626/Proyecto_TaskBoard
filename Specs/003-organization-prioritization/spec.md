# Feature Specification: Increment 3 — Organización y Priorización

**Feature**: `003-organization-prioritization`
**Branch**: `implementacion-3`
**Date**: 2026-10-05
**Based on**: Incrementos 1 y 2 completados (HU-01–HU-06, HU-12–HU-14)
**Spec version**: 1.0.0

---

## Overview

Este incremento añade capacidades de organización y priorización a las tareas ya existentes.
Cubre tres historias que forman un bloque coherente: asignar prioridad a cada tarea, agruparlas
en categorías opcionales y señalar automáticamente cuáles están vencidas sin cálculos en el navegador.

---

## User Stories

### User Story 1 — Prioridad de Tareas (HU-07) (Priority: P1)

Como usuario autenticado, quiero asignar una prioridad (alta, media, baja) a cada tarea y ordenar
mi listado por prioridad, para decidir en qué orden trabajar.

**Why this priority**: La prioridad es el mecanismo más básico de organización personal; sin ella
el listado carece de ordenación significativa.

**Independent Test**: Crear tareas con distintas prioridades y verificar que el listado ordenado
por prioridad las devuelve en el orden correcto (alta → media → baja).

**Acceptance Scenarios**:

1. **Given** un usuario autenticado crea una tarea sin indicar prioridad, **When** consulta el
   detalle de la tarea, **Then** la prioridad es `media` (valor por defecto).
2. **Given** un usuario con tareas de distintas prioridades, **When** solicita el listado ordenado
   por prioridad, **Then** las tareas aparecen en orden alta → media → baja.
3. **Given** una tarea propia en cualquier estado activo, **When** el usuario cambia su prioridad
   a `alta`, **Then** el cambio se persiste y queda registrado en el log de auditoría.
4. **Given** un usuario intenta cambiar la prioridad con un valor inválido (e.g., `urgente`),
   **When** el sistema valida la petición, **Then** se rechaza con mensaje de error claro.

---

### User Story 2 — Categorías de Tareas (HU-08) (Priority: P2)

Como usuario autenticado, quiero agrupar mis tareas en categorías propias, para organizar trabajo relacionado.

**Why this priority**: Las categorías son complemento de la prioridad; permiten agrupar contexto pero
no son bloqueantes para el valor básico del sistema.

**Independent Test**: Crear una categoría, asignar tareas a ella, luego eliminar la categoría y
verificar que las tareas siguen existiendo sin categoría.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, **When** crea una categoría con nombre válido, **Then** la
   categoría queda asociada exclusivamente a ese usuario y aparece en su listado de categorías.
2. **Given** un usuario con categorías creadas, **When** asigna una tarea a una categoría,
   **Then** esa tarea pertenece a esa categoría y puede filtrarse por ella.
3. **Given** una categoría con tareas asignadas, **When** el usuario elimina la categoría,
   **Then** las tareas permanecen activas con `category_id = NULL` — ninguna tarea se elimina.
4. **Given** un usuario intenta asignar una tarea a una categoría de otro usuario,
   **When** el sistema valida la petición, **Then** se rechaza con error de autorización.
5. **Given** un usuario consulta el listado de tareas, **When** filtra por una categoría propia,
   **Then** solo aparecen las tareas de esa categoría.

---

### User Story 3 — Indicación de Tareas Vencidas (HU-09) (Priority: P3)

Como usuario autenticado, quiero que el sistema identifique automáticamente mis tareas vencidas
(fecha límite superada y no completadas), para priorizar su atención.

**Why this priority**: Complementa a prioridad y categorías; depende de que `due_date` ya exista
(desde HU-01) y del listado (HU-02).

**Independent Test**: Crear una tarea con fecha límite en el pasado y estado `pending`, verificar
que el campo `is_overdue` sea `true` en el listado. Luego completar la tarea y verificar que
`is_overdue` pasa a `false`.

**Acceptance Scenarios**:

1. **Given** una tarea con `due_date` anterior a hoy y estado `pending`, **When** el usuario
   consulta el listado, **Then** la tarea aparece marcada como vencida (`is_overdue = true`).
2. **Given** una tarea con `due_date` anterior a hoy pero estado `completed`, **When** el usuario
   consulta el listado, **Then** la tarea **no** está marcada como vencida (`is_overdue = false`).
3. **Given** una tarea eliminada (soft delete) con `due_date` en el pasado, **When** se evalúa
   el listado, **Then** esa tarea no aparece y por tanto no se marca como vencida.
4. **Given** una tarea sin `due_date`, **When** el usuario consulta el listado, **Then** el campo
   `is_overdue` es `false` independientemente del estado.

---

### Edge Cases

- ¿Qué ocurre si se intenta cambiar la prioridad de una tarea eliminada? → Rechazado (misma
  regla que edición: `get_task_by_id` ya bloquea tareas eliminadas).
- ¿Qué ocurre si se elimina una categoría que no tiene tareas? → Se elimina correctamente sin efecto secundario.
- ¿Puede un usuario ver categorías de otro usuario? → No; el backend filtra por `user_id`.
- ¿Qué ocurre si `due_date` es hoy exacto? → La tarea **no** está vencida (vence al final del día;
  el cálculo es `due_date < date.today()`).
- ¿Puede una tarea pertenecer a más de una categoría? → No; relación estrictamente uno-a-cero-o-uno.

---

## Functional Requirements

### Prioridad (HU-07)

- **FR-01**: El modelo `Task` incluye un campo `priority` (String, valores: `alta`, `media`, `baja`,
  default `media`, not null).
- **FR-02**: `TaskService.update_task_priority(user_id, task_id, priority)` valida que `priority`
  sea uno de los tres valores permitidos y que la tarea pertenezca al usuario y no esté eliminada.
- **FR-03**: `TaskService.get_user_tasks()` acepta parámetro `sort_by` con valor `priority` para
  ordenar alta → media → baja, sin romper el filtrado por estado ya existente.
- **FR-04**: Se registra `AuditLog` con `action=TASK_PRIORITY_CHANGED` tras cada cambio exitoso
  de prioridad.
- **FR-05**: Las tareas existentes creadas en incrementos anteriores quedan con `priority='media'`
  tras la migración (valor por defecto).

### Categorías (HU-08)

- **FR-06**: El modelo `Category` incluye campos: `id`, `user_id` (FK `users.id`, not null),
  `name` (String(100), not null), `created_at`.
- **FR-07**: `CategoryService.create_category(user_id, name)` valida que el nombre no esté vacío
  y que el usuario no tenga ya una categoría con el mismo nombre.
- **FR-08**: `CategoryService.get_user_categories(user_id)` retorna solo las categorías del
  usuario autenticado.
- **FR-09**: `CategoryService.delete_category(user_id, category_id)` verifica propiedad,
  desvincula tareas (`category_id = NULL`) y elimina la categoría.
- **FR-10**: El modelo `Task` incluye `category_id` (Integer, FK `categories.id`, nullable,
  `ondelete='SET NULL'`).
- **FR-11**: `TaskService.assign_category(user_id, task_id, category_id)` verifica que la tarea
  y la categoría pertenezcan al mismo usuario.
- **FR-12**: `TaskService.get_user_tasks()` acepta parámetro `category_id` para filtrar por
  categoría, sin romper filtros de estado ni ordenamiento por prioridad.

### Tareas Vencidas (HU-09)

- **FR-13**: El campo `is_overdue` es un valor **derivado** calculado en `TaskService`; nunca
  se persiste como columna en la base de datos.
- **FR-14**: La fórmula de cálculo: `task.due_date is not None AND task.due_date < date.today()
  AND task.status != STATUS_COMPLETED AND task.deleted_at is None`.
- **FR-15**: El listado de tareas incluye `is_overdue` como atributo accesible desde la plantilla
  Jinja2 (propiedad calculada o diccionario enriquecido).

---

## Key Entities

- **Category**: Entidad nueva que representa una agrupación de tareas de un usuario.
  Atributos: `id`, `user_id` (FK → User), `name` (único por usuario), `created_at`.
  Relación: una categoría tiene cero o más tareas; eliminar una categoría desvincula sus tareas.

- **Task** (extensión aditiva): Se añaden `priority` (enum string con default `media`) y
  `category_id` (FK nullable → Category, `SET NULL` al eliminar categoría).

---

## Out of Scope

- HU-10 (asignación de tareas a otros usuarios) — Incremento 4.
- HU-11 (notificaciones internas) — Incremento 4.
- HU-15 (completar sin recargar la página) — Incremento 5.
- HU-16 (drag-and-drop) — Incremento 5.
- Sub-categorías o categorías jerárquicas.
- Categorías compartidas entre usuarios.

---

## Assumptions

1. La prioridad se representa como string (`alta`, `media`, `baja`) en base de datos; el
   ordenamiento en el backend usa un mapa explícito (`alta`=1, `media`=2, `baja`=3).
2. Un usuario no puede tener dos categorías con el mismo nombre (unicidad por `user_id + name`).
3. El cálculo de `is_overdue` usa `date.today()` del servidor (UTC-aware); no depende de la
   zona horaria del cliente.
4. La migración del Incremento 3 es aditiva: añade columnas y tabla sin romper datos
   de incrementos anteriores.
5. Las plantillas Jinja2 reciben las tareas como objetos con atributo `is_overdue` disponible.

---

## Success Criteria

- **SC-01**: Toda tarea nueva tiene prioridad `media` por defecto sin intervención del usuario.
- **SC-02**: El listado ordenado por prioridad devuelve tareas en orden correcto (alta → media → baja)
  y es combinable con filtros de estado ya existentes.
- **SC-03**: Al eliminar una categoría, el 100% de sus tareas permanecen activas con `category_id = NULL`.
- **SC-04**: Una tarea completada nunca aparece marcada como vencida, aunque su fecha límite
  haya pasado.
- **SC-05**: El 100% de los tests automatizados del Incremento 3 pasan, y los 54 tests de los
  Incrementos 1 y 2 no se rompen.
- **SC-06**: El cambio de prioridad queda registrado en el log de auditoría con actor, acción
  `TASK_PRIORITY_CHANGED`, entidad y timestamp.

