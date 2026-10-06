# HTTP Contracts: Increment 3 — Organización y Priorización

---

## HU-07: Cambiar Prioridad de una Tarea

### `POST /tasks/<int:task_id>/priority`

**Auth**: Sesión activa requerida (`@login_required`).

**Request body** (form o JSON):

```json
{ "priority": "alta" }
```

Valores válidos de `priority`: `"alta"`, `"media"`, `"baja"`.

**Respuestas**:

| Código | Condición | Body (JSON) / Comportamiento (HTML) |
|---|---|---|
| 302 | Éxito (form) | Redirect a `/tasks` con flash success |
| 200 | Éxito (JSON) | `{ "message": "Prioridad actualizada", "priority": "alta" }` |
| 400 | Valor inválido | `{ "error": "Prioridad inválida. Valores permitidos: alta, media, baja." }` o flash danger |
| 403 | Tarea de otro usuario | `{ "error": "No tiene permiso..." }` |
| 404 | Tarea no existe | `{ "error": "Tarea no encontrada." }` |

---

## HU-07: Listado Ordenado por Prioridad (extensión de GET /tasks)

### `GET /tasks?sort_by=priority[&status=<estado>][&category_id=<id>]`

**Auth**: Sesión activa requerida.

**Query params**:

| Param | Tipo | Descripción |
|---|---|---|
| `sort_by` | string opcional | `priority` → ordena alta→media→baja. Omitido → orden por `created_at` DESC. |
| `status` | string opcional | Filtro por estado (ya existente desde Inc 1). |
| `category_id` | integer opcional | Filtro por categoría (nuevo en Inc 3). |

**Respuesta**:

- `200 OK` con HTML renderizado (lista de tareas con `priority` e `is_overdue` visibles).

---

## HU-08: Listar Categorías

### `GET /categories`

**Auth**: Sesión activa requerida.

**Respuesta**:

- `200 OK` con HTML (lista de categorías del usuario autenticado).

---

## HU-08: Crear Categoría

### `POST /categories`

**Auth**: Sesión activa requerida.

**Request body** (form):

```
name=<nombre de la categoría>
```

**Respuestas**:

| Código | Condición | Comportamiento |
|---|---|---|
| 302 | Éxito | Redirect a `/categories` con flash success |
| 400 | Nombre vacío | Flash danger + re-render formulario |
| 400 | Nombre duplicado | Flash danger + re-render formulario |

---

## HU-08: Eliminar Categoría

### `POST /categories/<int:category_id>/delete`

**Auth**: Sesión activa requerida.

**Respuestas**:

| Código | Condición | Comportamiento |
|---|---|---|
| 302 | Éxito | Redirect a `/categories` con flash success. Tareas desvinculadas. |
| 403 | Categoría de otro usuario | Flash danger + redirect |
| 404 | Categoría no encontrada | Flash danger + redirect |

---

## HU-08: Asignar Tarea a Categoría

### `POST /tasks/<int:task_id>/category`

**Auth**: Sesión activa requerida.

**Request body** (form o JSON):

```json
{ "category_id": 3 }
```

`category_id: null` (o ausente) → desasignar categoría.

**Respuestas**:

| Código | Condición | Body (JSON) / Comportamiento (HTML) |
|---|---|---|
| 302 | Éxito (form) | Redirect a `/tasks` con flash success |
| 200 | Éxito (JSON) | `{ "message": "Categoría asignada" }` |
| 400 | Categoría no pertenece al usuario | `{ "error": "Categoría no válida." }` |
| 404 | Tarea o categoría no encontrada | `{ "error": "..." }` |

