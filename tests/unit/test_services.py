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


# =============================================================================
# Incremento 2 — Tests Unitarios de Servicios
# =============================================================================

# --- HU-05: Soft Delete de Tareas ---

def test_delete_task_success(app):
    """T206: delete_task estampa deleted_at y la tarea deja de aparecer en get_user_tasks."""
    with app.app_context():
        user, _ = AuthService.register_user("del_ok@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="Para eliminar")

        deleted, error = TaskService.delete_task(user_id=user.id, task_id=task.id)
        assert error is None
        assert deleted.deleted_at is not None

        # No debe aparecer en el listado activo
        tasks = TaskService.get_user_tasks(user_id=user.id)
        assert all(t.id != task.id for t in tasks)

        # Verificar auditoria TASK_DELETED
        audit = AuditLog.query.filter_by(
            action=AuditLog.ACTION_TASK_DELETED, entity_id=deleted.id
        ).first()
        assert audit is not None
        assert audit.actor_id == user.id


def test_delete_task_already_deleted(app):
    """T206: Intentar eliminar una tarea ya eliminada devuelve error claro."""
    with app.app_context():
        user, _ = AuthService.register_user("del_twice@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="Eliminar dos veces")

        TaskService.delete_task(user_id=user.id, task_id=task.id)
        result, error = TaskService.delete_task(user_id=user.id, task_id=task.id)
        assert result is None
        assert error is not None
        assert "eliminada" in error.lower()


def test_delete_task_wrong_owner(app):
    """T206: Un usuario no puede eliminar la tarea de otro usuario."""
    with app.app_context():
        owner, _ = AuthService.register_user("owner_del@example.com", "pass1234")
        attacker, _ = AuthService.register_user("attacker_del@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=owner.id, title="Tarea del owner")

        result, error = TaskService.delete_task(user_id=attacker.id, task_id=task.id)
        assert result is None
        assert error is not None


def test_edit_deleted_task_fails(app):
    """T206: update_task rechaza operar sobre una tarea eliminada."""
    with app.app_context():
        user, _ = AuthService.register_user("edit_del@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="Editar eliminada")
        TaskService.delete_task(user_id=user.id, task_id=task.id)

        result, error = TaskService.update_task(
            user_id=user.id, task_id=task.id, title="Nuevo titulo"
        )
        assert result is None
        assert error is not None
        assert "eliminada" in error.lower()


def test_change_status_deleted_task_fails(app):
    """T206: update_task_status rechaza operar sobre una tarea eliminada."""
    with app.app_context():
        user, _ = AuthService.register_user("status_del@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="Estado eliminada")
        TaskService.delete_task(user_id=user.id, task_id=task.id)

        result, error = TaskService.update_task_status(
            user_id=user.id, task_id=task.id, new_status=Task.STATUS_IN_PROGRESS
        )
        assert result is None
        assert error is not None
        assert "eliminada" in error.lower()


# --- HU-06: Reapertura de Tareas Completadas ---

def test_reopen_task_success(app):
    """T213: reopen_task desde completed -> in_progress con auditoria TASK_REOPENED."""
    with app.app_context():
        user, _ = AuthService.register_user("reopen_ok@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="Completar y reabrir")
        TaskService.update_task_status(user.id, task.id, Task.STATUS_IN_PROGRESS)
        TaskService.update_task_status(user.id, task.id, Task.STATUS_COMPLETED)

        reopened, error = TaskService.reopen_task(user_id=user.id, task_id=task.id)
        assert error is None
        assert reopened.status == Task.STATUS_IN_PROGRESS

        audit = AuditLog.query.filter_by(
            action=AuditLog.ACTION_TASK_REOPENED, entity_id=task.id
        ).first()
        assert audit is not None
        assert audit.actor_id == user.id


def test_reopen_pending_task_fails(app):
    """T213: Intentar reabrir tarea pending es invalido."""
    with app.app_context():
        user, _ = AuthService.register_user("reopen_pending@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="Pending no reabrir")

        result, error = TaskService.reopen_task(user_id=user.id, task_id=task.id)
        assert result is None
        assert error is not None
        assert "completadas" in error.lower()


def test_reopen_in_progress_task_fails(app):
    """T213: Intentar reabrir tarea in_progress es invalido."""
    with app.app_context():
        user, _ = AuthService.register_user("reopen_ip@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="InProgress no reabrir")
        TaskService.update_task_status(user.id, task.id, Task.STATUS_IN_PROGRESS)

        result, error = TaskService.reopen_task(user_id=user.id, task_id=task.id)
        assert result is None
        assert error is not None
        assert "completadas" in error.lower()


def test_reopen_deleted_task_fails(app):
    """T213: Intentar reabrir tarea eliminada es invalido."""
    with app.app_context():
        user, _ = AuthService.register_user("reopen_del@example.com", "pass1234")
        task, _ = TaskService.create_task(user_id=user.id, title="Deleted no reabrir")
        TaskService.update_task_status(user.id, task.id, Task.STATUS_IN_PROGRESS)
        TaskService.update_task_status(user.id, task.id, Task.STATUS_COMPLETED)
        TaskService.delete_task(user.id, task.id)

        result, error = TaskService.reopen_task(user_id=user.id, task_id=task.id)
        assert result is None
        assert error is not None


# --- HU-14: Recuperacion de Contrasena ---

def test_request_password_reset_existing_email(app):
    """T218: Para email registrado se crea token en BD."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel

    with app.app_context():
        AuthService.register_user("reset_existing@example.com", "oldpassword")
        success, error = AuthService.request_password_reset("reset_existing@example.com")

        assert success is True
        assert error is None

        user = UserModel.query.filter_by(email="reset_existing@example.com").first()
        tokens = PasswordResetToken.query.filter_by(user_id=user.id).all()
        assert len(tokens) >= 1
        assert tokens[-1].is_valid()


def test_request_password_reset_unknown_email(app):
    """T218: Para email desconocido la respuesta es identica (no revela inexistencia)."""
    with app.app_context():
        success, error = AuthService.request_password_reset("nobody@nowhere.com")
        assert success is True
        assert error is None


def test_reset_password_valid_token(app):
    """T218: Token valido actualiza hash y estampa used_at."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel

    with app.app_context():
        AuthService.register_user("reset_valid@example.com", "oldpassword12")
        AuthService.request_password_reset("reset_valid@example.com")

        user = UserModel.query.filter_by(email="reset_valid@example.com").first()
        token_row = PasswordResetToken.query.filter_by(user_id=user.id).first()
        token_str = token_row.token

        success, error = AuthService.reset_password(token_str, "newpassword99")
        assert success is True
        assert error is None

        user_fresh = db.session.get(UserModel, user.id)
        assert user_fresh.check_password("newpassword99") is True
        assert not user_fresh.check_password("oldpassword12")

        token_fresh = db.session.get(PasswordResetToken, token_row.id)
        assert token_fresh.used_at is not None


def test_reset_password_expired_token(app):
    """T218: Token expirado es rechazado."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel
    from datetime import datetime, timezone, timedelta

    with app.app_context():
        AuthService.register_user("reset_exp@example.com", "pass12345")
        user = UserModel.query.filter_by(email="reset_exp@example.com").first()

        expired_token = PasswordResetToken(
            user_id=user.id,
            token="expiredtoken" + "x" * 52,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db.session.add(expired_token)
        db.session.commit()

        success, error = AuthService.reset_password(expired_token.token, "newpass123")
        assert success is False
        assert error is not None


def test_reset_password_used_token(app):
    """T218: Token ya consumido es rechazado."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel

    with app.app_context():
        AuthService.register_user("reset_used@example.com", "pass12345")
        user = UserModel.query.filter_by(email="reset_used@example.com").first()

        AuthService.request_password_reset("reset_used@example.com")
        token_row = PasswordResetToken.query.filter_by(user_id=user.id).first()
        token_str = token_row.token

        AuthService.reset_password(token_str, "firstnewpass99")
        success, error = AuthService.reset_password(token_str, "secondnewpass99")
        assert success is False
        assert error is not None


def test_reset_password_short_password(app):
    """T218: Contrasena < 8 caracteres es rechazada."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel

    with app.app_context():
        AuthService.register_user("reset_short@example.com", "pass12345")
        AuthService.request_password_reset("reset_short@example.com")

        user = UserModel.query.filter_by(email="reset_short@example.com").first()
        token_row = PasswordResetToken.query.filter_by(user_id=user.id).first()

        success, error = AuthService.reset_password(token_row.token, "1234567")
        assert success is False
        assert error is not None
