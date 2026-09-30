# Quickstart & Verification Guide: Increment 1

Esta guía describe cómo levantar el entorno y verificar de extremo a extremo las 6 historias de usuario del Incremento 1.

## 1. Prerrequisitos y Activación del Entorno
Desde el directorio raíz del proyecto:

```powershell
# 1. Activar el entorno virtual
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt
```

## 2. Inicialización de Base de Datos y Migraciones
```powershell
# Aplicar migraciones iniciales
flask db upgrade
```

## 3. Ejecución de la Suite de Pruebas Automatizadas (Test-First)
```powershell
# Correr todas las pruebas unitarias y de integración
pytest
```

## 4. Ejecución del Servidor Web Monolítico
```powershell
flask run
```
Acceder en el navegador a `http://127.0.0.1:5000/`.

## 5. Escenarios de Validación Manual de las 6 Historias
1. **HU-12 (Registro)**: Ir a `/register`, crear usuario `test@example.com` con clave `password123`.
2. **HU-13 (Login/Logout)**: Iniciar sesión en `/login` con el usuario recién creado. Cerrar sesión y verificar que el acceso a `/tasks` se redirige a `/login`.
3. **HU-01 (Creación de tareas)**: Iniciar sesión, presionar "Nueva Tarea", ingresar título "Tarea 1" y fecha límite. Comprobar que aparece con estado "Pendiente".
4. **HU-02 (Listado y filtrado)**: Crear una segunda tarea. Filtrar por estado usando el selector en el tablero y comprobar que solo se muestran las tareas coincidentes del usuario activo.
5. **HU-03 (Cambio de estado)**: Cambiar el estado de "Tarea 1" de "Pendiente" a "En Progreso" y luego a "Completada". Verificar que no permite regresar a "Pendiente".
6. **HU-04 (Edición de tareas)**: Editar el título y descripción de una tarea existente. Comprobar que los cambios se reflejan en el listado.
7. **Auditoría (Principio VIII)**: Comprobar que en la base de datos la tabla `audit_logs` contiene los eventos `TASK_CREATED`, `TASK_STATUS_CHANGED`, `TASK_UPDATED` con el `actor_id` y timestamp correspondientes.
