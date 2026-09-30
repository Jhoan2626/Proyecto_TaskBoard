import pytest
from datetime import date
from src.models import db, User, Task, AuditLog
from src.services.auth_service import AuthService
from src.services.task_service import TaskService


# --- Pruebas de AuthService (HU-12 y HU-13) ---

def test_register_user_success(app):
    with app.app_context():
        user, error = AuthService.register_user("newuser@example.com", "validPassword123")
        assert error is None
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.check_password("validPassword123") is True


def test_register_user_duplicate_email(app):
    with app.app_context():
        AuthService.register_user("duplicate@example.com", "pass123")
        user2, error = AuthService.register_user("duplicate@example.com", "anotherPass")
        assert user2 is None
        assert "ya está registrado" in error


def test_register_user_invalid_email(app):
    with app.app_context():
        user, error = AuthService.register_user("not-an-email", "pass123")
        assert user is None
        assert "correo electrónico válido" in error


def test_register_user_empty_or_short_password(app):
    with app.app_context():
        user, error = AuthService.register_user("valid@example.com", "123")
        assert user is None
        assert "al menos 6 caracteres" in error


def test_authenticate_user_success(app):
    with app.app_context():
        AuthService.register_user("auth@example.com", "mypassword")
        user, error = AuthService.authenticate_user("auth@example.com", "mypassword")
        assert error is None
        assert user is not None
        assert user.email == "auth@example.com"


def test_authenticate_user_invalid_password(app):
    with app.app_context():
        AuthService.register_user("auth2@example.com", "mypassword")
        user, error = AuthService.authenticate_user("auth2@example.com", "wrongpassword")
        assert user is None
        assert "Credenciales inválidas" in error


def test_authenticate_user_not_found(app):
    with app.app_context():
        user, error = AuthService.authenticate_user("nonexistent@example.com", "any")
        assert user is None
        assert "Credenciales inválidas" in error


# --- Pruebas de TaskService (HU-01, HU-02, HU-03, HU-04) ---

def test_create_task_success_and_audited(app):
    with app.app_context():
        user, _ = AuthService.register_user("taskmaker@example.com", "pass123")
        task, error = TaskService.create_task(
            user_id=user.id,
            title="Diseñar arquitectura",
            description="Crear diagramas monolito",
            due_date=date(2026, 11, 1),
        )

        assert error is None
        assert task is not None
        assert task.title == "Diseñar arquitectura"
        assert task.status == Task.STATUS_PENDING
        assert task.user_id == user.id

        # Verificación del Log de Auditoría (Principio VIII)
        audit = AuditLog.query.filter_by(
            action=AuditLog.ACTION_TASK_CREATED, entity_id=task.id
        ).first()
        assert audit is not None
        assert audit.actor_id == user.id
        assert audit.entity_type == "Task"


def test_create_task_empty_title_fails(app):
    with app.app_context():
        user, _ = AuthService.register_user("taskmaker2@example.com", "pass123")
        task, error = TaskService.create_task(user_id=user.id, title="   ")
        assert task is None
        assert "El título de la tarea es obligatorio" in error


def test_get_user_tasks_isolation(app):
    with app.app_context():
        user_a, _ = AuthService.register_user("user_a@example.com", "pass123")
        user_b, _ = AuthService.register_user("user_b@example.com", "pass123")

        TaskService.create_task(user_id=user_a.id, title="Tarea de A")
        TaskService.create_task(user_id=user_b.id, title="Tarea de B")

        tasks_a = TaskService.get_user_tasks(user_id=user_a.id)
        assert len(tasks_a) == 1
        assert tasks_a[0].title == "Tarea de A"

        tasks_b = TaskService.get_user_tasks(user_id=user_b.id)
        assert len(tasks_b) == 1
        assert tasks_b[0].title == "Tarea de B"


def test_get_user_tasks_filtering(app):
    with app.app_context():
        user, _ = AuthService.register_user("filteruser@example.com", "pass123")
        t1, _ = TaskService.create_task(user_id=user.id, title="Tarea 1")
        t2, _ = TaskService.create_task(user_id=user.id, title="Tarea 2")
        TaskService.update_task_status(user_id=user.id, task_id=t2.id, new_status=Task.STATUS_IN_PROGRESS)

        pending = TaskService.get_user_tasks(user_id=user.id, status_filter=Task.STATUS_PENDING)
        assert len(pending) == 1
        assert pending[0].id == t1.id

        in_progress = TaskService.get_user_tasks(user_id=user.id, status_filter=Task.STATUS_IN_PROGRESS)
        assert len(in_progress) == 1
        assert in_progress[0].id == t2.id


def test_update_task_status_allowed_and_forbidden_transitions(app):
    with app.app_context():
        user, _ = AuthService.register_user("statususer@example.com", "pass123")
        task, _ = TaskService.create_task(user_id=user.id, title="Ciclo de vida")

        # pending -> in_progress (permitido)
        updated, err = TaskService.update_task_status(user.id, task.id, Task.STATUS_IN_PROGRESS)
        assert err is None
        assert updated.status == Task.STATUS_IN_PROGRESS

        # in_progress -> completed (permitido)
        updated2, err2 = TaskService.update_task_status(user.id, task.id, Task.STATUS_COMPLETED)
        assert err2 is None
        assert updated2.status == Task.STATUS_COMPLETED

        # completed -> pending (PROHIBIDO en este incremento sin reapertura)
        updated3, err3 = TaskService.update_task_status(user.id, task.id, Task.STATUS_PENDING)
        assert updated3 is None
        assert "Transición de estado no permitida" in err3


def test_update_task_content_and_ownership(app):
    with app.app_context():
        user1, _ = AuthService.register_user("edit1@example.com", "pass123")
        user2, _ = AuthService.register_user("edit2@example.com", "pass123")

        task, _ = TaskService.create_task(user_id=user1.id, title="Título Inicial")

        # Modificación válida por el propietario
        edited, err = TaskService.update_task(
            user_id=user1.id,
            task_id=task.id,
            title="Título Actualizado",
            description="Nueva descripción",
            due_date=date(2026, 12, 31),
        )
        assert err is None
        assert edited.title == "Título Actualizado"

        # Modificación rechazada con título vacío
        edited_bad, err_bad = TaskService.update_task(
            user_id=user1.id, task_id=task.id, title="   "
        )
        assert edited_bad is None
        assert "El título de la tarea es obligatorio" in err_bad

        # Modificación rechazada si no es el propietario
        edited_foreign, err_foreign = TaskService.update_task(
            user_id=user2.id, task_id=task.id, title="Hackeado"
        )
        assert edited_foreign is None
        assert "No tiene permiso" in err_foreign
