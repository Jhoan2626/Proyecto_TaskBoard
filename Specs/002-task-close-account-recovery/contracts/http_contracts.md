# HTTP Contracts: Increment 2 — Cierre de Gestión de Tareas y Recuperación de Acceso

> Todos los endpoints requieren sesión activa excepto los de `/auth/forgot-password` y `/auth/reset-password/<token>`.

---

## HU-05: Soft Delete de Tarea

### `POST /tasks/<int:task_id>/delete`

**Descripción**: Elimina lógicamente (soft delete) una tarea propia del usuario autenticado.

**Autenticación**: Requerida (`@login_required`).

**Path params**:
| Param | Tipo | Descripción |
|---|---|---|
| `task_id` | integer | ID de la tarea a eliminar. |

**Request body**: Ninguno (form POST vacío con CSRF implícito si aplica).

**Respuestas**:
| Código | Condición | Comportamiento |
|---|---|---|
| `302` | Éxito | Redirect a `GET /tasks` con flash message "Tarea eliminada.". |
| `302` | Tarea no encontrada o de otro usuario | Redirect a `GET /tasks` con flash error "Tarea no encontrada.". |
| `302` | Tarea ya eliminada | Redirect a `GET /tasks` con flash error "La tarea ya fue eliminada.". |
| `302` | Sin sesión | Redirect a `/auth/login`. |

**Efecto en auditoría**: `AuditLog(action=TASK_DELETED, actor_id=..., entity_type="Task", entity_id=task_id)`.

---

## HU-06: Reapertura de Tarea Completada

### `POST /tasks/<int:task_id>/reopen`

**Descripción**: Reabre una tarea en estado `completed`, devolviéndola a `in_progress`.

**Autenticación**: Requerida (`@login_required`).

**Path params**:
| Param | Tipo | Descripción |
|---|---|---|
| `task_id` | integer | ID de la tarea a reabrir. |

**Request body**: Ninguno.

**Respuestas**:
| Código | Condición | Comportamiento |
|---|---|---|
| `302` | Éxito | Redirect a `GET /tasks` con flash "Tarea reabierta y marcada como en progreso.". |
| `302` | No completada | Redirect a `GET /tasks` con flash error "Solo se pueden reabrir tareas completadas.". |
| `302` | Tarea eliminada | Redirect a `GET /tasks` con flash error "No se puede operar sobre una tarea eliminada.". |
| `302` | Sin sesión | Redirect a `/auth/login`. |

**Efecto en auditoría**: `AuditLog(action=TASK_REOPENED, ...)` — **distinto** de `TASK_STATUS_CHANGED`.

---

## HU-14: Recuperación de Contraseña

### `GET /auth/forgot-password`

**Descripción**: Muestra el formulario para solicitar restablecimiento de contraseña.

**Autenticación**: No requerida.

**Respuesta**: `200 OK` con template `auth/forgot_password.html`.

---

### `POST /auth/forgot-password`

**Descripción**: Procesa la solicitud de restablecimiento. Respuesta **siempre neutral**.

**Autenticación**: No requerida.

**Form body**:
| Campo | Tipo | Validación |
|---|---|---|
| `email` | string | Formato de correo electrónico válido. |

**Respuestas**:
| Código | Condición | Comportamiento |
|---|---|---|
| `200` | Siempre (email existe o no) | Renderiza template con mensaje: "Si ese correo está registrado, recibirás un enlace en breve." |
| `200` | Email con formato inválido | Re-renderiza formulario con error "Formato de correo inválido.". |

**Efecto colateral (si email existe)**: Token generado en `password_reset_tokens`, enlace impreso en `app.logger.info`.

---

### `GET /auth/reset-password/<token>`

**Descripción**: Muestra formulario para introducir nueva contraseña, prevalidando el token.

**Autenticación**: No requerida.

**Path params**:
| Param | Tipo | Descripción |
|---|---|---|
| `token` | string (64 hex) | Token de restablecimiento. |

**Respuestas**:
| Código | Condición | Comportamiento |
|---|---|---|
| `200` | Token válido | Renderiza `auth/reset_password.html` con el token. |
| `302` | Token inválido/expirado/usado | Redirect a `/auth/forgot-password` con flash error "El enlace de restablecimiento es inválido o ha expirado.". |

---

### `POST /auth/reset-password/<token>`

**Descripción**: Aplica la nueva contraseña y marca el token como usado.

**Autenticación**: No requerida.

**Path params**: igual que GET.

**Form body**:
| Campo | Tipo | Validación |
|---|---|---|
| `password` | string | Mínimo 8 caracteres. |
| `confirm_password` | string | Debe coincidir con `password`. |

**Respuestas**:
| Código | Condición | Comportamiento |
|---|---|---|
| `302` | Éxito | Redirect a `/auth/login` con flash "Contraseña actualizada. Por favor inicia sesión.". |
| `200` | Contraseña inválida | Re-renderiza con error de validación. |
| `302` | Token inválido/expirado/usado | Redirect a `/auth/forgot-password` con flash error. |
