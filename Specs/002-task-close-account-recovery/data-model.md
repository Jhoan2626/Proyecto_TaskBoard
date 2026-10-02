# Data Model: Increment 2 (TaskControl)

> Extiende el modelo del Incremento 1 de forma **aditiva** sin romper datos existentes.

---

## Cambios en entidades existentes

### Task (`tasks` table) — campo añadido

| Campo | Tipo | Constraints | Descripción |
|---|---|---|---|
| `deleted_at` | DateTime | Nullable, Default NULL | UTC timestamp de eliminación lógica. Si IS NOT NULL, la tarea está eliminada y no aparece en el listado. |

**Regla de negocio**: toda query sobre tareas activas añade el filtro `Task.deleted_at == None`.

**Estado de la máquina de estados ampliada**:

```
pending ──► in_progress ──► completed
                 ▲                │
                 └────── reopen ──┘   (solo desde completed, vía reopen_task)

deleted_at: se puede estampar desde cualquier estado activo (pending/in_progress/completed).
Una tarea eliminada es inaccesible para edit/status/reopen.
```

---

## Nuevas entidades

### PasswordResetToken (`password_reset_tokens` table)

| Campo | Tipo | Constraints | Descripción |
|---|---|---|---|
| `id` | Integer | PK, Autoincrement | Identificador interno. |
| `user_id` | Integer | FK `users.id`, Index, Not Null | Usuario al que pertenece el token. |
| `token` | String(64) | Unique, Index, Not Null | `secrets.token_hex(32)` — 64 hex chars, criptográficamente seguro. |
| `expires_at` | DateTime | Not Null | UTC now + 1 hora al crear. |
| `used_at` | DateTime | Nullable | NULL = sin usar. Estampado al consumir con éxito. |
| `created_at` | DateTime | Not Null, Default UTC now | Timestamp de creación. |

**Relaciones**:
- `PasswordResetToken` N-a-1 `User` (un usuario puede tener múltiples tokens pendientes, aunque sólo el más reciente debería usarse).

**Reglas de validez de un token**:
1. `token` existe en la tabla.
2. `expires_at > datetime.now(UTC)`.
3. `used_at IS NULL`.

---

## Diagrama ER (Incremento 2)

```
users ──────────────────────────── tasks
│  id (PK)                         │  id (PK)
│  email                           │  user_id (FK → users.id)
│  password_hash                   │  title
│  created_at                      │  description
│                                  │  due_date
│                                  │  status
│                                  │  created_at
│                                  │  updated_at
│                                  │  deleted_at  ← NUEVO
│
│──────── password_reset_tokens     audit_logs (sin cambios)
           id (PK)                  id (PK)
           user_id (FK)             actor_id
           token                    action
           expires_at               entity_type
           used_at                  entity_id
           created_at               details
                                    timestamp
```

---

## Nuevas constantes de Auditoría

| Constante | Valor string | Historia |
|---|---|---|
| `AuditLog.ACTION_TASK_DELETED` | `"TASK_DELETED"` | HU-05 |
| `AuditLog.ACTION_TASK_REOPENED` | `"TASK_REOPENED"` | HU-06 |
