# HTTP API Contracts: Increment 1 (TaskControl)

Este documento define el contrato formal de endpoints HTTP para backend y cliente (Principio III de la Constitución).

---

## 1. Authentication Endpoints (`/auth`)

### 1.1 Registro de Usuario (HU-12)
- **Ruta**: `/register`
- **Métodos**: `GET`, `POST`
- **GET**: Renderiza plantilla `auth/register.html`.
- **POST Input**:
  - `Content-Type`: `application/x-www-form-urlencoded` o `application/json`
  - Payload:
    ```json
    {
      "email": "user@example.com",
      "password": "secretpassword"
    }
    ```
- **Validation**:
  - `email`: obligatorio, formato RFC válido, único en el sistema.
  - `password`: obligatorio, longitud mínima 6 caracteres.
- **Output / Responses**:
  - `302 Found`: Redirección a `/login` con mensaje flash de éxito tras creación.
  - `400 Bad Request`: Formato de email inválido o campos vacíos.
  - `409 Conflict`: Correo ya registrado.

### 1.2 Inicio de Sesión (HU-13)
- **Ruta**: `/login`
- **Métodos**: `GET`, `POST`
- **GET**: Renderiza plantilla `auth/login.html`.
- **POST Input**:
  - Payload:
    ```json
    {
      "email": "user@example.com",
      "password": "secretpassword"
    }
    ```
- **Output / Responses**:
  - `302 Found`: Inicializa `session['user_id'] = user.id` y redirige a `/tasks`.
  - `401 Unauthorized`: Credenciales inválidas.

### 1.3 Cierre de Sesión (HU-13)
- **Ruta**: `/logout`
- **Métodos**: `POST` (o `GET` para navegación amigable)
- **Output / Responses**:
  - `302 Found`: Limpia la sesión del usuario (`session.clear()`) y redirige a `/login`.

---

## 2. Task Management Endpoints (`/tasks`)

Todos los endpoints bajo `/tasks` requieren autenticación obligatoria en el backend (Principio VII). Si no hay sesión activa, responden `302 Found` a `/login` o `401 Unauthorized` si es petición AJAX/JSON.

### 2.1 Listado y Filtrado de Tareas (HU-02)
- **Ruta**: `/tasks`
- **Método**: `GET`
- **Query Parameters**:
  - `status` (opcional): `'pending' | 'in_progress' | 'completed'`
- **Output**:
  - `200 OK`: Renderiza `tasks/list.html` pasando la lista de tareas pertenecientes exclusivamente al usuario en sesión.

### 2.2 Formulario de Creación de Tarea
- **Ruta**: `/tasks/new`
- **Método**: `GET`
- **Output**:
  - `200 OK`: Renderiza `tasks/create.html`.

### 2.3 Creación de Tarea (HU-01)
- **Ruta**: `/tasks`
- **Método**: `POST`
- **Input**:
  - Payload:
    ```json
    {
      "title": "Documentar arquitectura",
      "description": "Detallar diagramas y contratos",
      "due_date": "2026-10-15"
    }
    ```
- **Validation**:
  - `title`: obligatorio, string no vacío después de trim (1 a 200 caracteres).
  - `description`: opcional.
  - `due_date`: opcional, formato `YYYY-MM-DD`.
- **Efectos secundarios**:
  - Tarea creada con estado `'pending'`, asignada a `current_user.id`.
  - Evento de auditoría emitido: `TASK_CREATED`.
- **Output**:
  - `302 Found`: Redirige a `/tasks`.
  - `400 Bad Request`: Título ausente o vacío.

### 2.4 Formulario de Edición de Tarea (HU-04)
- **Ruta**: `/tasks/<int:task_id>/edit`
- **Método**: `GET`
- **Output**:
  - `200 OK`: Renderiza `tasks/edit.html` con los datos de la tarea.
  - `404 Not Found` / `403 Forbidden`: Tarea no encontrada o no pertenece al usuario.

### 2.5 Edición de Tarea (HU-04)
- **Ruta**: `/tasks/<int:task_id>/edit`
- **Método**: `POST`
- **Input**:
  - Payload:
    ```json
    {
      "title": "Nuevo título",
      "description": "Nueva descripción",
      "due_date": "2026-10-20"
    }
    ```
- **Validation**:
  - Mismas reglas de validación que en creación (título no vacío).
- **Efectos secundarios**:
  - Evento de auditoría emitido: `TASK_UPDATED`.
- **Output**:
  - `302 Found`: Redirige a `/tasks`.
  - `400 Bad Request`: Título inválido.
  - `403 Forbidden` / `404 Not Found`: Tarea ajena.

### 2.6 Transición de Estado de Tarea (HU-03)
- **Ruta**: `/tasks/<int:task_id>/status`
- **Método**: `POST`
- **Input**:
  - Payload:
    ```json
    {
      "new_status": "in_progress"
    }
    ```
- **Transiciones válidas**:
  - `pending` -> `in_progress`
  - `in_progress` -> `completed`
  - Cualquier otra (p. ej. `completed` -> `pending` o `pending` -> `completed` directo) es rechazada.
- **Efectos secundarios**:
  - Evento de auditoría emitido: `TASK_STATUS_CHANGED`.
- **Output**:
  - `302 Found` (o `200 OK` JSON si `Accept: application/json`): Redirige a `/tasks`.
  - `400 Bad Request`: Transición de estado inválida.
  - `403 Forbidden` / `404 Not Found`: Tarea ajena o inexistente.
