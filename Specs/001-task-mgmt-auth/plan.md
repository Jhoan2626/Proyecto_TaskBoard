# Implementation Plan: Increment 1 - Gestión Básica de Tareas con Autenticación de Usuarios

**Branch**: `001-task-mgmt-auth` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-task-mgmt-auth/spec.md` y prompt `plan_increment_1.txt`.

## Summary

Implementar el primer incremento funcional del monolito TaskControl en Flask:
1. Autenticación de usuarios (registro HU-12 y login/logout HU-13) con contraseñas cifradas y sesiones seguras en backend.
2. Gestión básica de tareas (creación HU-01, listado/filtrado HU-02, cambio de estado HU-03, edición HU-04) con aislamiento estricto por usuario.
3. Observabilidad y trazabilidad mediante log de auditoría estructurado para toda mutación de tareas.
4. Arquitectura en capas estrictas (modelos, servicios, rutas Blueprint, templates Jinja2) bajo disciplina Test-First.

## Technical Context

**Language/Version**: Python 3.11+ (Entorno configurado con Python 3.14).

**Primary Dependencies**:
- `Flask`: Framework web monolítico.
- `Flask-SQLAlchemy`: ORM relacional.
- `Flask-Migrate`: Gestión de migraciones con Alembic.
- `Werkzeug`: Seguridad criptográfica (`generate_password_hash`, `check_password_hash`).

**Storage**: SQLite (`taskcontrol.db` para desarrollo, `:memory:` para pruebas) vía SQLAlchemy.

**Testing**: `pytest`, `pytest-flask` para pruebas unitarias de servicios/modelos y pruebas de integración de rutas HTTP.

**Target Platform**: Servidor Web / Navegador de escritorio y móvil.

**Project Type**: Aplicación web monolítica (Flask + Jinja2 + Vanilla JS).

**Performance Goals**: Tiempo de respuesta de endpoints < 100ms para operaciones CRUD de tareas.

**Constraints**:
- Ningún framework SPA pesado del lado cliente por defecto.
- Cero lógica de negocio ni manipulación de base de datos directa en las capas de presentación o rutas.
- 100% de operaciones de mutación de tareas auditadas.
- Verificación estricta de sesión en backend para toda ruta privada.

**Scale/Scope**: Incremento inicial acotado estrictamente a HU-01 a HU-04 y HU-12 a HU-13. Fuera de alcance: borrado, reapertura, categorías, asignaciones, drag-and-drop.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Compliance Status | Justification |
|---|---|---|---|
| I. Monolito por diseño | Un solo repo, un solo proceso, una sola BD relacional | PASS | Proyecto monolítico Flask desplegable en un único proceso con SQLite/SQLAlchemy. |
| II. Separación de responsabilidades | Capas aisladas: Modelos -> Servicios -> Rutas -> Presentación | PASS | Estructura modular estricta; las rutas llaman exclusivamente a servicios, sin ORM directo. |
| III. Contrato explícito backend-JS | Endpoints documentados antes de implementar | PASS | Documentado formalmente en `contracts/http_contracts.md`. |
| IV. Test-First para lógica de negocio | Pruebas automatizadas en rojo antes de código de dominio | PASS | Pruebas unitarias de servicios y modelos implementadas como primer paso de cada tarea. |
| V. Simplicidad sobre generalidad | Sin abstracciones prematuras ni plugins innecesarios | PASS | Implementación directa sin librerías externas superfluas ni capas de repositorio ficticias. |
| VI. Integridad de datos | Migraciones versionadas y reproducibles | PASS | Flask-Migrate con Alembic gestiona el esquema de la base de datos. |
| VII. Seguridad por defecto | Validación y hashing en backend, verificación de sesión | PASS | `werkzeug.security` para passwords, validación de inputs en servidor, decorador `@login_required`. |
| VIII. Observabilidad mínima viable | Log estructurado con actor, acción, entidad y timestamp | PASS | Servicio `AuditService` persistiendo en `audit_logs` y logging estructurado. |

## Project Structure

### Documentation (this feature)

```text
specs/001-task-mgmt-auth/
├── spec.md              # Especificación funcional validada
├── plan.md              # Este plan de implementación técnica
├── research.md          # Investigación y decisiones técnicas
├── data-model.md        # Esquema y entidades de datos
├── quickstart.md        # Guía de verificación de extremo a extremo
├── contracts/
│   └── http_contracts.md # Contratos formales de endpoints HTTP
├── checklists/
│   └── requirements.md  # Checklist de calidad de requisitos
└── tasks.md             # Tareas ejecutables (generado por /speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py          # Application Factory (create_app)
├── config.py            # Configuración de entornos (Dev, Test, Prod)
├── models/              # Capa 1: Modelos de datos SQLAlchemy
│   ├── __init__.py
│   ├── user.py          # Entidad User (email, password_hash)
│   ├── task.py          # Entidad Task (title, status, due_date, user_id)
│   └── audit_log.py     # Entidad AuditLog (actor_id, action, entity, timestamp)
├── services/            # Capa 2: Lógica de negocio (Dominio puro)
│   ├── __init__.py
│   ├── auth_service.py  # Registro, hashing, autenticación
│   ├── task_service.py  # CRUD de tareas, validación y transiciones de estado
│   └── audit_service.py # Emisión y persistencia de eventos de auditoría
├── routes/              # Capa 3: Controladores HTTP (Flask Blueprints)
│   ├── __init__.py
│   ├── auth_routes.py   # Rutas /register, /login, /logout
│   ├── task_routes.py   # Rutas /tasks (crear, listar, editar, cambiar estado)
│   └── decorators.py    # Decorador @login_required de backend
├── static/              # Capa 4: Presentación e interactividad cliente
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── tasks.js     # Interactividad fluida para filtros y confirmaciones
└── templates/           # Plantillas Jinja2
    ├── base.html
    ├── auth/
    │   ├── login.html
    │   └── register.html
    └── tasks/
        ├── list.html
        ├── create.html
        └── edit.html

migrations/              # Control de versiones de esquema Alembic
tests/
├── conftest.py          # Fixtures de pytest: app, client, test_db, authenticated_client
├── unit/
│   ├── test_models.py   # Pruebas unitarias de modelos
│   └── test_services.py # Pruebas unitarias de lógica de negocio (bloqueantes)
└── integration/
    ├── test_auth_routes.py # Pruebas de integración de autenticación
    └── test_task_routes.py # Pruebas de integración de gestión de tareas
```

**Structure Decision**: Monolito Flask clásico con separación modular en capas explícitas y aplicación Factory, respetando rigurosamente el Principio II.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Ninguna | No se introdujeron violaciones ni complejidades arquitectónicas innecesarias | No aplica |
