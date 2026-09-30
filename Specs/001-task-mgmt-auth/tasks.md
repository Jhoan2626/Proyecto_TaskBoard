# Implementation Tasks: Increment 1 - Gestión Básica de Tareas con Autenticación de Usuarios

**Branch**: `001-task-mgmt-auth` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic dependencies

- [X] T001 Create `requirements.txt` with Flask, Flask-SQLAlchemy, Flask-Migrate, pytest, pytest-flask
- [X] T002 Create application configuration in `src/config.py` with Development, Testing, and Production settings
- [X] T003 Create test suite setup and pytest fixtures in `tests/conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and data persistence that MUST be complete before user stories can begin

- [X] T004 Create Flask application factory in `src/__init__.py` registering SQLAlchemy and Flask-Migrate
- [X] T005 [P] Implement `User` model in `src/models/user.py` with `email` (string(120), unique, indexed, non-null) and `password_hash` (string(256), non-null)
- [X] T006 [P] Implement `Task` model in `src/models/task.py` with `user_id` FK, `title` (string(200), non-null), `status` (string(20), default 'pending'), `due_date`, and timestamps
- [X] T007 [P] Implement `AuditLog` model in `src/models/audit_log.py` with `actor_id`, `action`, `entity_type`, `entity_id`, `details`, `timestamp`
- [X] T008 Implement centralized `AuditService` in `src/services/audit_service.py` satisfying Constitution Principle VIII
- [X] T009 Implement `@login_required` backend decorator in `src/routes/decorators.py` satisfying Constitution Principle VII
- [X] T010 Setup base Jinja2 template and responsive styling in `src/templates/base.html` and `src/static/css/style.css`

---

## Phase 3: User Story 1 - Registro de Usuario (HU-12) (Priority: P1)

**Goal**: Permitir que un visitante se registre mediante correo y contraseña almacenada con hash seguro.

**Independent Test**: Ejecutar `tests/unit/test_services.py::test_register_user_success` y `tests/integration/test_auth_routes.py::test_register_flow`.

- [X] T011 [P] [US1] Write unit tests for user registration and hashing in `tests/unit/test_services.py`
- [X] T012 [US1] Implement `register_user` in `src/services/auth_service.py` with email validation, uniqueness check, and `generate_password_hash`
- [X] T013 [P] [US1] Write integration tests for registration HTTP endpoint in `tests/integration/test_auth_routes.py`
- [X] T014 [US1] Implement `/register` route in `src/routes/auth_routes.py` and template `src/templates/auth/register.html`

---

## Phase 4: User Story 2 - Inicio y Cierre de Sesión (HU-13) (Priority: P1)

**Goal**: Autenticar usuarios registrados, mantener la sesión en backend y destruirla al cerrar sesión.

**Independent Test**: Ejecutar `tests/unit/test_services.py::test_authenticate_user` y `tests/integration/test_auth_routes.py::test_login_logout_flow`.

- [X] T015 [P] [US2] Write unit tests for authentication logic and credential checking in `tests/unit/test_services.py`
- [X] T016 [US2] Implement `authenticate_user` in `src/services/auth_service.py` with `check_password_hash`
- [X] T017 [P] [US2] Write integration tests for login, logout, and protected route redirection in `tests/integration/test_auth_routes.py`
- [X] T018 [US2] Implement `/login` and `/logout` routes in `src/routes/auth_routes.py` and template `src/templates/auth/login.html`

---

## Phase 5: User Story 3 - Creación de Tareas (HU-01) (Priority: P2)

**Goal**: Permitir a usuarios autenticados crear tareas con título, descripción y fecha límite, registrando auditoría.

**Independent Test**: Ejecutar `tests/unit/test_services.py::test_create_task` y `tests/integration/test_task_routes.py::test_create_task_route`.

- [X] T019 [P] [US3] Write unit tests for task creation, title validation, and audit event emission in `tests/unit/test_services.py`
- [X] T020 [US3] Implement `create_task` in `src/services/task_service.py` with title validation, 'pending' status default, and `AuditService.log_event`
- [X] T021 [P] [US3] Write integration tests for task creation route in `tests/integration/test_task_routes.py`
- [X] T022 [US3] Implement `/tasks/new` and `POST /tasks` routes in `src/routes/task_routes.py` and template `src/templates/tasks/create.html`

---

## Phase 6: User Story 4 - Listado y Filtrado de Tareas (HU-02) (Priority: P2)

**Goal**: Listar tareas pertenecientes exclusivamente al usuario autenticado con opción de filtrado por estado.

**Independent Test**: Ejecutar `tests/unit/test_services.py::test_list_tasks_user_isolation` y `tests/integration/test_task_routes.py::test_list_tasks_filtering`.

- [X] T023 [P] [US4] Write unit tests for user task isolation and status filtering in `tests/unit/test_services.py`
- [X] T024 [US4] Implement `get_user_tasks` in `src/services/task_service.py` with status filtering and strict user ownership filtering
- [X] T025 [P] [US4] Write integration tests for task listing and filter query params in `tests/integration/test_task_routes.py`
- [X] T026 [US4] Implement `GET /tasks` route in `src/routes/task_routes.py` and template `src/templates/tasks/list.html`

---

## Phase 7: User Story 5 - Transición y Cambio de Estado (HU-03) (Priority: P3)

**Goal**: Cambiar el estado de tareas según las transiciones permitidas (pending -> in_progress -> completed) auditando cada cambio.

**Independent Test**: Ejecutar `tests/unit/test_services.py::test_task_status_transitions` y `tests/integration/test_task_routes.py::test_change_status_route`.

- [X] T027 [P] [US5] Write unit tests for valid transitions and rejection of invalid transitions in `tests/unit/test_services.py`
- [X] T028 [US5] Implement `update_task_status` in `src/services/task_service.py` enforcing allowed transitions and logging `TASK_STATUS_CHANGED`
- [X] T029 [P] [US5] Write integration tests for `POST /tasks/<id>/status` in `tests/integration/test_task_routes.py`
- [X] T030 [US5] Implement `POST /tasks/<int:task_id>/status` in `src/routes/task_routes.py` and client-side status actions in `src/static/js/tasks.js`

---

## Phase 8: User Story 6 - Edición de Tareas Existentes (HU-04) (Priority: P3)

**Goal**: Permitir la edición de campos de una tarea propia existente aplicando validaciones y auditoría.

**Independent Test**: Ejecutar `tests/unit/test_services.py::test_update_task` y `tests/integration/test_task_routes.py::test_edit_task_route`.

- [X] T031 [P] [US6] Write unit tests for task editing, ownership validation, and audit emission in `tests/unit/test_services.py`
- [X] T032 [US6] Implement `update_task` in `src/services/task_service.py` validating ownership, non-empty title, and logging `TASK_UPDATED`
- [X] T033 [P] [US6] Write integration tests for edit routes in `tests/integration/test_task_routes.py`
- [X] T034 [US6] Implement `GET /tasks/<int:task_id>/edit` and `POST /tasks/<int:task_id>/edit` in `src/routes/task_routes.py` and template `src/templates/tasks/edit.html`

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: System integration, migration generation, and quickstart end-to-end verification

- [X] T035 Initialize and generate Alembic migrations in `migrations/` via Flask-Migrate
- [X] T036 Run complete test suite (`pytest`) and verify 100% test pass rate
- [X] T037 Validate end-to-end user journeys following `quickstart.md`
