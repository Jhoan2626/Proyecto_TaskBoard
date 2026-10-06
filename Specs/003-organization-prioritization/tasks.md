# Implementation Tasks: Increment 3 — Organización y Priorización

**Branch**: `implementacion-3` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

> **Nota de equipo**: Este incremento NO modifica nada relacionado con asignación (HU-10),
> notificaciones (HU-11) ni JavaScript avanzado (HU-15, HU-16). Los archivos compartidos
> (`task.py`, `task_service.py`, `task_routes.py`) se modifican de forma aditiva y compatible.

---

## Phase 1: Setup (Migración e Infraestructura de Datos)

**Purpose**: Extender el esquema de BD de forma aditiva antes de implementar lógica de negocio.

- [X] T301 Implementar modelo `Category` en `src/models/category.py` (campos: id, user_id FK, name String(100), created_at; UniqueConstraint user_id+name)
- [X] T302 Agregar campos `priority` (String(10), default='media', not null) y `category_id` (Integer, FK categories.id, nullable, ondelete='SET NULL') al modelo `Task` en `src/models/task.py`
- [X] T303 Agregar constantes `VALID_PRIORITIES = ['alta','media','baja']` y `PRIORITY_SORT_KEY` al modelo `Task` en `src/models/task.py`
- [X] T304 Agregar constante `ACTION_TASK_PRIORITY_CHANGED = "TASK_PRIORITY_CHANGED"` al modelo `AuditLog` en `src/models/audit_log.py`
- [X] T305 Exportar `Category` en `src/models/__init__.py`
- [X] T306 Generar y aplicar migración Alembic (`flask db migrate -m "increment3_priority_categories"` + `flask db upgrade`)

---

## Phase 2: Tests Bloqueantes — Prioridad (HU-07)

**Purpose**: Test-First para prioridad de tareas (Principio IV).

- [X] T307 [P] Escribir tests unitarios en `tests/unit/test_services.py` para:
  - `test_task_default_priority`: nueva tarea tiene `priority='media'` por defecto
  - `test_update_task_priority_success`: cambio exitoso registra auditoría `TASK_PRIORITY_CHANGED`
  - `test_update_task_priority_invalid_value`: valor no válido → error descriptivo
  - `test_update_priority_deleted_task_fails`: tarea eliminada → error
  - `test_sort_tasks_by_priority`: orderamiento alta→media→baja correcto
- [X] T308 [P] Escribir test de integración en `tests/integration/test_task_routes.py`:
  - `test_change_priority_route`: POST `/tasks/<id>/priority` cambia prioridad y redirige
  - `test_list_tasks_sorted_by_priority`: GET `/tasks?sort_by=priority` retorna tareas ordenadas

---

## Phase 3: Implementación — Prioridad (HU-07)

**Purpose**: Implementar servicio y ruta de cambio de prioridad.

- [X] T309 Implementar `TaskService.update_task_priority(user_id, task_id, priority)` en `src/services/task_service.py`:
  - Usa `get_task_by_id` (verifica propiedad y que no esté eliminada)
  - Valida `priority in Task.VALID_PRIORITIES`
  - Actualiza `task.priority` y commit
  - Llama `AuditService.log_event(..., action=TASK_PRIORITY_CHANGED, details={old, new})`
- [X] T310 Modificar `TaskService.get_user_tasks()` para aceptar parámetro `sort_by`:
  - Si `sort_by == 'priority'`: ordena por mapa `alta=1, media=2, baja=3` (Python-side sort)
  - Mantiene filtros de `status` y `category_id` existentes sin romper nada
- [X] T311 Agregar ruta `POST /tasks/<int:task_id>/priority` en `src/routes/task_routes.py`
- [X] T312 Modificar ruta `GET /tasks` en `src/routes/task_routes.py` para pasar `sort_by` al servicio
- [X] T313 Modificar template `src/templates/tasks/list.html` para mostrar badge de prioridad (alta/media/baja) en cada tarea y controles de ordenamiento

---

## Phase 4: Tests Bloqueantes — Categorías (HU-08)

**Purpose**: Test-First para categorías (Principio IV).

- [X] T314 [P] Escribir tests unitarios en `tests/unit/test_services.py` para:
  - `test_create_category_success`: categoría creada y asociada al usuario
  - `test_create_category_duplicate_name_fails`: nombre duplicado por usuario → error
  - `test_create_category_empty_name_fails`: nombre vacío → error
  - `test_delete_category_does_not_delete_tasks`: eliminar categoría → tareas con `category_id=None`
  - `test_assign_task_to_category_success`: asignación correcta mismo usuario
  - `test_assign_task_to_foreign_category_fails`: categoría ajena → error de autorización
  - `test_filter_tasks_by_category`: filtrado retorna solo tareas de esa categoría
- [X] T315 [P] Escribir tests de integración en `tests/integration/test_category_routes.py`:
  - `test_list_categories_route`: GET `/categories` retorna 200
  - `test_create_category_route`: POST `/categories` crea categoría y redirige
  - `test_delete_category_route`: POST `/categories/<id>/delete` elimina y tareas persisten
  - `test_filter_tasks_by_category_route`: GET `/tasks?category_id=<id>` filtra correctamente

---

## Phase 5: Implementación — Categorías (HU-08)

**Purpose**: Implementar CategoryService, rutas y templates.

- [X] T316 Crear `src/services/category_service.py` con:
  - `CategoryService.create_category(user_id, name)`: valida nombre no vacío y no duplicado por usuario; crea y commit
  - `CategoryService.get_user_categories(user_id)`: retorna categorías del usuario ordenadas por nombre
  - `CategoryService.delete_category(user_id, category_id)`: verifica propiedad; establece `category_id=NULL` en tareas (via DB cascade `SET NULL`); elimina y commit
  - `CategoryService.get_category_by_id(user_id, category_id)`: verifica propiedad
- [X] T317 Implementar `TaskService.assign_category(user_id, task_id, category_id_or_none)` en `src/services/task_service.py`:
  - Verifica propiedad de la tarea
  - Si `category_id` no es None: verifica que la categoría pertenezca al mismo usuario
  - Actualiza `task.category_id` y commit
- [X] T318 Modificar `TaskService.get_user_tasks()` para aceptar parámetro `category_id` y filtrar por él
- [X] T319 Crear `src/routes/category_routes.py` con blueprint `category_bp` y rutas:
  - `GET /categories` → `list_categories`
  - `POST /categories` → `create_category`
  - `POST /categories/<int:category_id>/delete` → `delete_category`
- [X] T320 Agregar ruta `POST /tasks/<int:task_id>/category` en `src/routes/task_routes.py`
- [X] T321 Registrar `category_bp` en `src/__init__.py` con prefix `/categories`
- [X] T322 Crear template `src/templates/categories/list.html` con formulario de creación y listado con botón eliminar
- [X] T323 Modificar template `src/templates/tasks/list.html` para:
  - Mostrar nombre de categoría en cada tarea
  - Agregar filtro de categoría (selector `<select>` con categorías del usuario)
  - Pasar `categories` al template desde la ruta `list_tasks`
- [X] T324 Modificar ruta `GET /tasks` en `src/routes/task_routes.py` para pasar `category_id` y la lista de categorías al template

---

## Phase 6: Tests Bloqueantes — Tareas Vencidas (HU-09)

**Purpose**: Test-First para cálculo de `is_overdue` (Principio IV).

- [X] T325 [P] Escribir tests unitarios en `tests/unit/test_services.py` para:
  - `test_is_overdue_pending_past_due`: tarea `pending` con `due_date` pasada → `is_overdue=True`
  - `test_is_overdue_completed_task`: tarea `completed` con `due_date` pasada → `is_overdue=False`
  - `test_is_overdue_no_due_date`: tarea sin `due_date` → `is_overdue=False`
  - `test_is_overdue_due_today`: `due_date` == hoy → `is_overdue=False`
  - `test_is_overdue_in_progress_past_due`: tarea `in_progress` con `due_date` pasada → `is_overdue=True`
- [X] T326 [P] Escribir test de integración en `tests/integration/test_task_routes.py`:
  - `test_overdue_field_in_task_list`: tarea vencida expone `is_overdue` en contexto del template

---

## Phase 7: Implementación — Tareas Vencidas (HU-09)

**Purpose**: Implementar cálculo derivado de `is_overdue` en el backend.

- [X] T327 Agregar propiedad `@property is_overdue` al modelo `Task` en `src/models/task.py`:
  - Retorna `True` si: `self.due_date is not None AND self.due_date < date.today() AND self.status != STATUS_COMPLETED AND self.deleted_at is None`
  - Nunca persistida como columna
- [X] T328 Modificar template `src/templates/tasks/list.html` para mostrar badge/indicador visual de "Vencida" cuando `task.is_overdue` sea `True`

---

## Phase 8: Polish & Validación Final

**Purpose**: Verificación integral del Incremento 3 completo.

- [X] T329 Ejecutar suite completa de tests (`pytest -v`) y verificar que **todos** pasan (inc. Incrementos 1 y 2)
- [X] T330 Verificar en navegador: crear tarea con prioridad alta → aparece primero en listado ordenado
- [X] T331 Verificar en navegador: crear categoría → asignar tarea → filtrar por categoría → eliminar categoría → tarea permanece sin categoría
- [X] T332 Verificar en navegador: tarea con fecha límite pasada muestra indicador de vencida; tarea completada no lo muestra
- [X] T333 Confirmar que los tests nuevos del Incremento 3 pasan y los 54 del Incremento 1+2 no se rompen

---

## Task Summary

| Fase | Tasks | Historia |
|---|---|---|
| Setup (migración) | T301–T306 | Infraestructura |
| Tests HU-07 | T307–T308 | Prioridad |
| Impl HU-07 | T309–T313 | Prioridad |
| Tests HU-08 | T314–T315 | Categorías |
| Impl HU-08 | T316–T324 | Categorías |
| Tests HU-09 | T325–T326 | Tareas vencidas |
| Impl HU-09 | T327–T328 | Tareas vencidas |
| Polish | T329–T333 | Validación integral |

