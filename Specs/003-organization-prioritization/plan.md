# Implementation Plan: Increment 3 — Organización y Priorización

**Branch**: `implementacion-3` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

---

## Summary

Extender el monolito TaskControl construyendo sobre los modelos, servicios y blueprints de los
Incrementos 1 y 2:

1. **Prioridad de tareas (HU-07)**: nuevo campo `priority` en `Task` (default `media`); servicio
   `update_task_priority`; extensión del listado con ordenamiento; auditoría `TASK_PRIORITY_CHANGED`.
2. **Categorías (HU-08)**: nueva entidad `Category` con FK nullable en `Task` (`ondelete=SET NULL`);
   `CategoryService` CRUD; rutas `/categories`; asignación de tarea a categoría; filtrado en listado.
3. **Tareas vencidas (HU-09)**: campo derivado `is_overdue` calculado en el servicio — nunca
   persistido; accesible desde la plantilla Jinja2.

---

## Technical Context

- **Language/Version**: Python 3.11+ (entorno 3.14 en local).
- **Framework**: Flask con blueprints existentes (`auth_bp`, `task_bp`) + nuevo `category_bp`.
- **ORM**: SQLAlchemy con Flask-Migrate/Alembic (Principio VI).
- **Storage**: SQLite (`taskcontrol.db` dev, `:memory:` tests).
- **Testing**: `pytest` + `pytest-flask` — disciplina Test-First (Principio IV).

---

## Constitution Compliance Check

| Principio | Requisito | Estado | Justificación |
|---|---|---|---|
| I. Monolito | Un solo proceso | PASS | Sin nuevos procesos ni servicios externos. |
| II. Separación | Modelos→Servicios→Rutas→Presentación | PASS | `CategoryService` vive en capa de servicio; rutas delegan. |
| III. Contrato explícito | Endpoints documentados antes de implementar | PASS | Documentado en `contracts/http_contracts.md`. |
| IV. Test-First | Tests en rojo antes del código | PASS | Tests escritos antes que cada servicio/ruta. |
| V. Simplicidad | Sin abstracciones prematuras | PASS | `is_overdue` derivado; sin columna extra. |
| VI. Integridad de datos | Migraciones versionadas | PASS | Una migración aditiva cubre todos los cambios. |
| VII. Seguridad | Validación backend, propiedad de recursos | PASS | `category.user_id == current_user.id` verificado en servicio. |
| VIII. Observabilidad | Audit log para toda mutación | PASS | `TASK_PRIORITY_CHANGED` persiste en `audit_logs`. |

---

## Data Model Changes

### Task (extensión aditiva)

| Campo nuevo | Tipo | Constraint | Descripción |
|---|---|---|---|
| `priority` | String(10) | Not Null, Default `'media'` | Prioridad: `alta`, `media` o `baja`. |
| `category_id` | Integer | FK `categories.id`, Nullable, `ON DELETE SET NULL` | Categoría opcional. |

**Constante de orden para query**:

```python
PRIORITY_ORDER = {'alta': 1, 'media': 2, 'baja': 3}
VALID_PRIORITIES = ['alta', 'media', 'baja']
```

### Category (nueva tabla)

| Campo | Tipo | Constraint | Descripción |
|---|---|---|---|
| `id` | Integer | PK, Autoincrement | Identificador interno. |
| `user_id` | Integer | FK `users.id`, Not Null, Index | Propietario de la categoría. |
| `name` | String(100) | Not Null | Nombre de la categoría (único por usuario). |
| `created_at` | DateTime | Not Null, Default UTC now | Timestamp de creación. |

**Unicidad**: constraint `UniqueConstraint('user_id', 'name')` en la tabla.

**Relación Task→Category**: `db.relationship` con `backref='category'` y `passive_deletes=True`.

---

## Endpoint Contract Summary (detallado en `contracts/http_contracts.md`)

| Método | Ruta | Historia | Descripción |
|---|---|---|---|
| `POST` | `/tasks/<id>/priority` | HU-07 | Cambiar prioridad de una tarea propia. |
| `GET`  | `/tasks?sort_by=priority` | HU-07 | Listado ordenado por prioridad (extensión existente). |
| `GET`  | `/categories` | HU-08 | Listar categorías del usuario. |
| `POST` | `/categories` | HU-08 | Crear nueva categoría. |
| `POST` | `/categories/<id>/delete` | HU-08 | Eliminar categoría (desvincula tareas). |
| `POST` | `/tasks/<id>/category` | HU-08 | Asignar/desasignar tarea a categoría. |
| `GET`  | `/tasks?category_id=<id>` | HU-08 | Filtrar tareas por categoría. |

---

## Project Structure Changes

```text
Specs/003-organization-prioritization/     ← Artefactos de este incremento
├── spec.md
├── plan.md
├── data-model.md
├── contracts/
│   └── http_contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md

src/models/
├── task.py          ← MODIFICADO: campos priority, category_id
├── category.py      ← IMPLEMENTADO (actualmente vacío)
└── __init__.py      ← MODIFICADO: exportar Category

src/services/
├── task_service.py     ← MODIFICADO: update_task_priority, filtros, is_overdue
└── category_service.py ← NUEVO

src/routes/
├── task_routes.py      ← MODIFICADO: ruta /priority, /category; filtros extendidos
└── category_routes.py  ← NUEVO

src/templates/
├── tasks/
│   └── list.html       ← MODIFICADO: mostrar prioridad, badge vencida, filtro categoría
└── categories/         ← NUEVO (directorio + templates)
    ├── list.html
    └── create.html (inline en list.html)

tests/unit/
└── test_services.py    ← MODIFICADO: tests bloqueantes Inc 3

tests/integration/
├── test_task_routes.py    ← MODIFICADO: tests prioridad, is_overdue, filtro categoría
└── test_category_routes.py ← NUEVO

migrations/versions/
└── <hash>_increment3_priority_categories.py ← NUEVO (via flask db migrate)
```

---

## Migration Strategy

- **Una sola migración aditiva** para el Incremento 3.
- Operaciones:
  1. `CREATE TABLE categories (id, user_id FK, name, created_at, UNIQUE(user_id, name))`
  2. `ALTER TABLE tasks ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'media'`
  3. `ALTER TABLE tasks ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL`
- Las tareas existentes del Incremento 1+2 quedan con `priority='media'` y `category_id=NULL`.

---

## Testing Strategy

### Tests unitarios bloqueantes (Principio IV)

| Test | Descripción |
|---|---|
| `test_task_default_priority` | Nueva tarea tiene `priority='media'` por defecto. |
| `test_update_task_priority_success` | Cambiar prioridad valida valores y registra auditoría `TASK_PRIORITY_CHANGED`. |
| `test_update_task_priority_invalid` | Valor inválido rechazado con error descriptivo. |
| `test_update_priority_deleted_task_fails` | Tarea eliminada → error. |
| `test_sort_tasks_by_priority` | Ordenamiento alta→media→baja funciona correctamente. |
| `test_create_category_success` | Categoría creada correctamente asociada al usuario. |
| `test_create_category_duplicate_name_fails` | Nombre duplicado por usuario → error. |
| `test_delete_category_does_not_delete_tasks` | Eliminar categoría → tareas con `category_id=None`. |
| `test_assign_task_to_category_success` | Asignación correcta entre tarea y categoría del mismo usuario. |
| `test_assign_task_to_foreign_category_fails` | Categoría de otro usuario → error de autorización. |
| `test_is_overdue_pending_past_due` | Tarea `pending` con `due_date` pasada → `is_overdue=True`. |
| `test_is_overdue_completed_task` | Tarea `completed` con `due_date` pasada → `is_overdue=False`. |
| `test_is_overdue_no_due_date` | Tarea sin `due_date` → `is_overdue=False`. |

### Tests de integración

| Test | Descripción |
|---|---|
| `test_change_priority_route` | POST `/tasks/<id>/priority` cambia prioridad y redirige. |
| `test_list_tasks_sorted_by_priority` | GET `/tasks?sort_by=priority` ordena correctamente. |
| `test_create_category_route` | POST `/categories` crea categoría y redirige. |
| `test_list_categories_route` | GET `/categories` retorna 200 con categorías del usuario. |
| `test_delete_category_route` | POST `/categories/<id>/delete` elimina categoría, tareas persisten. |
| `test_filter_tasks_by_category` | GET `/tasks?category_id=<id>` filtra correctamente. |
| `test_overdue_badge_in_list` | Tarea vencida aparece con indicador en la plantilla. |

