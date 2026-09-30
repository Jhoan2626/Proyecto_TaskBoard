# Data Model: Increment 1 (TaskControl)

## Entities & Relationships

### 1. User (`users` table)
Representa un usuario autenticado del sistema.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Autoincrement | Identificador único del usuario |
| `email` | String(120) | Unique, Index, Not Null | Correo electrónico normalizado |
| `password_hash` | String(256) | Not Null | Hash de contraseña con salt |
| `created_at` | DateTime | Not Null, Default: UTC now | Fecha de registro |

**Relationships**:
- `tasks`: Uno-a-Muchos (`User` 1 -> N `Task`). Clave foránea `tasks.user_id`. `cascade="all, delete-orphan"`.

---

### 2. Task (`tasks` table)
Representa una tarea registrada por un usuario.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Autoincrement | Identificador único de la tarea |
| `user_id` | Integer | Foreign Key (`users.id`), Index, Not Null | Propietario de la tarea |
| `title` | String(200) | Not Null | Título de la tarea (no vacío) |
| `description` | Text | Nullable | Detalle adicional opcional |
| `due_date` | Date | Nullable | Fecha límite en formato YYYY-MM-DD |
| `status` | String(20) | Not Null, Default: 'pending' | Estado actual: 'pending', 'in_progress', 'completed' |
| `created_at` | DateTime | Not Null, Default: UTC now | Timestamp de creación |
| `updated_at` | DateTime | Not Null, Default: UTC now | Timestamp de última actualización |

**Valid State Transitions**:
- `pending` -> `in_progress`
- `in_progress` -> `completed`
- `completed` -> (Cualquier transición queda bloqueada en este incremento sin reapertura)

---

### 3. AuditLog (`audit_logs` table)
Registro inmutable de auditoría para trazabilidad de cambios en tareas (Principio VIII).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Autoincrement | Identificador del evento de auditoría |
| `actor_id` | Integer | Not Null, Index | ID del usuario que realizó la acción |
| `action` | String(50) | Not Null | Tipo de acción: `TASK_CREATED`, `TASK_STATUS_CHANGED`, `TASK_UPDATED` |
| `entity_type` | String(50) | Not Null | Nombre de la entidad (`Task`) |
| `entity_id` | Integer | Not Null, Index | ID de la tarea afectada |
| `details` | Text | Nullable | Representación JSON de los valores modificados |
| `timestamp` | DateTime | Not Null, Default: UTC now | Marca de tiempo UTC del evento |
