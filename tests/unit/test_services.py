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


def test_new_tasks_keep_newest_first_until_manual_reorder(app):
    with app.app_context():
        user, _ = AuthService.register_user("order-default@example.com", "pass123")
        older, _ = TaskService.create_task(user.id, "Más antigua")
        newer, _ = TaskService.create_task(user.id, "Más nueva")

        tasks = TaskService.get_user_tasks(user.id, scope="mine")

        assert newer.position < older.position
        assert [task.id for task in tasks] == [newer.id, older.id]


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


def test_reorder_user_tasks_persists_complete_order(app):
    with app.app_context():
        user, _ = AuthService.register_user("reorder@example.com", "pass123")
        first, _ = TaskService.create_task(user_id=user.id, title="Primera")
        second, _ = TaskService.create_task(user_id=user.id, title="Segunda")
        third, _ = TaskService.create_task(user_id=user.id, title="Tercera")

        reordered, error = TaskService.reorder_user_tasks(
            user.id, [second.id, third.id, first.id]
        )

        assert error is None
        assert [task.id for task in reordered] == [second.id, third.id, first.id]
        assert [task.position for task in reordered] == [0, 1, 2]
        assert [
            task.id for task in TaskService.get_user_tasks(user.id, scope="mine")
        ] == [second.id, third.id, first.id]


def test_reorder_user_tasks_rejects_foreign_task(app):
    with app.app_context():
        owner, _ = AuthService.register_user("reorder-owner@example.com", "pass123")
        other, _ = AuthService.register_user("reorder-other@example.com", "pass123")
        owned_task, _ = TaskService.create_task(owner.id, "Propia")
        foreign_task, _ = TaskService.create_task(other.id, "Ajena")

        reordered, error = TaskService.reorder_user_tasks(
            owner.id, [owned_task.id, foreign_task.id]
        )

        assert reordered is None
        assert "No tiene permiso" in error


def test_reorder_user_tasks_rejects_incomplete_or_duplicate_order(app):
    with app.app_context():
        user, _ = AuthService.register_user("reorder-invalid@example.com", "pass123")
        first, _ = TaskService.create_task(user.id, "Primera")
        second, _ = TaskService.create_task(user.id, "Segunda")

        incomplete, incomplete_error = TaskService.reorder_user_tasks(
            user.id, [first.id]
        )
        duplicated, duplicated_error = TaskService.reorder_user_tasks(
            user.id, [first.id, first.id]
        )

        assert incomplete is None
        assert "no coincide" in incomplete_error
        assert duplicated is None
        assert "duplicados" in duplicated_error


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

# =============================================================================
# Incremento 3 — HU-07: Prioridad de tareas
# =============================================================================

def _create_test_user(email):
    from src.services.auth_service import AuthService
    user, _ = AuthService.register_user(email, "pass1234")
    return user

def test_task_default_priority(app):
    """Nueva tarea tiene prioridad 'media' por defecto."""
    with app.app_context():
        user = _create_test_user(email='prio1@test.com')
        task, _ = TaskService.create_task(user_id=user.id, title='Tarea default prio')
        assert task.priority == 'media'


def test_update_task_priority_success(app):
    """Cambiar prioridad registra auditoría TASK_PRIORITY_CHANGED."""
    with app.app_context():
        user = _create_test_user(email='prio2@test.com')
        task, _ = TaskService.create_task(user_id=user.id, title='Tarea prio')
        updated, error = TaskService.update_task_priority(user.id, task.id, 'alta')
        assert error is None
        assert updated.priority == 'alta'
        log = AuditLog.query.filter_by(
            entity_id=task.id,
            action=AuditLog.ACTION_TASK_PRIORITY_CHANGED
        ).first()
        assert log is not None


def test_update_task_priority_invalid_value(app):
    """Valor inválido de prioridad devuelve error."""
    with app.app_context():
        user = _create_test_user(email='prio3@test.com')
        task, _ = TaskService.create_task(user_id=user.id, title='Tarea prio invalida')
        updated, error = TaskService.update_task_priority(user.id, task.id, 'urgente')
        assert updated is None
        assert error is not None
        assert 'Prioridad' in error or 'prioridad' in error


def test_update_priority_deleted_task_fails(app):
    """No se puede cambiar prioridad de tarea eliminada."""
    with app.app_context():
        user = _create_test_user(email='prio4@test.com')
        task, _ = TaskService.create_task(user_id=user.id, title='Tarea eliminada prio')
        TaskService.delete_task(user.id, task.id)
        updated, error = TaskService.update_task_priority(user.id, task.id, 'alta')
        assert updated is None
        assert error is not None


def test_sort_tasks_by_priority(app):
    """Ordenamiento por prioridad devuelve alta→media→baja."""
    with app.app_context():
        user = _create_test_user(email='prio5@test.com')
        t_baja, _ = TaskService.create_task(user_id=user.id, title='Baja')
        TaskService.update_task_priority(user.id, t_baja.id, 'baja')
        t_alta, _ = TaskService.create_task(user_id=user.id, title='Alta')
        TaskService.update_task_priority(user.id, t_alta.id, 'alta')
        t_media, _ = TaskService.create_task(user_id=user.id, title='Media')
        # media es default

        tasks = TaskService.get_user_tasks(user.id, sort_by='priority')
        priorities = [t.priority for t in tasks]
        # alta debe ir antes que media, media antes que baja
        idx_alta = priorities.index('alta')
        idx_media = priorities.index('media')
        idx_baja = priorities.index('baja')
        assert idx_alta < idx_media < idx_baja

# =============================================================================
# Incremento 3 — HU-08: Categorías
# =============================================================================

def test_create_category_success(app):
    """Categoría creada correctamente asociada al usuario."""
    with app.app_context():
        from src.services.category_service import CategoryService
        user = _create_test_user(email='cat1@test.com')
        cat, error = CategoryService.create_category(user.id, 'Trabajo')
        assert error is None
        assert cat is not None
        assert cat.name == 'Trabajo'
        assert cat.user_id == user.id


def test_create_category_duplicate_name_fails(app):
    """Nombre duplicado por usuario devuelve error."""
    with app.app_context():
        from src.services.category_service import CategoryService
        user = _create_test_user(email='cat2@test.com')
        CategoryService.create_category(user.id, 'Personal')
        cat2, error = CategoryService.create_category(user.id, 'Personal')
        assert cat2 is None
        assert error is not None


def test_create_category_empty_name_fails(app):
    """Nombre vacío devuelve error."""
    with app.app_context():
        from src.services.category_service import CategoryService
        user = _create_test_user(email='cat3@test.com')
        cat, error = CategoryService.create_category(user.id, '   ')
        assert cat is None
        assert error is not None


def test_delete_category_does_not_delete_tasks(app):
    """Eliminar categoría desvincula sus tareas (category_id=None), no las borra."""
    with app.app_context():
        from src.services.category_service import CategoryService
        from src.models import Task
        user = _create_test_user(email='cat4@test.com')
        cat, _ = CategoryService.create_category(user.id, 'Borrable')
        task, _ = TaskService.create_task(user_id=user.id, title='Tarea en categoría')
        TaskService.assign_category(user.id, task.id, cat.id)

        # Verificar que la tarea tiene la categoría
        from src.models import db
        db.session.refresh(task)
        assert task.category_id == cat.id

        # Eliminar categoría
        _, error = CategoryService.delete_category(user.id, cat.id)
        assert error is None

        # La tarea debe seguir existiendo con category_id=None
        db.session.refresh(task)
        assert task.category_id is None
        assert task.deleted_at is None


def test_assign_task_to_category_success(app):
    """Asignación correcta entre tarea y categoría del mismo usuario."""
    with app.app_context():
        from src.services.category_service import CategoryService
        user = _create_test_user(email='cat5@test.com')
        cat, _ = CategoryService.create_category(user.id, 'MiCategoria')
        task, _ = TaskService.create_task(user_id=user.id, title='Tarea para asignar')
        updated, error = TaskService.assign_category(user.id, task.id, cat.id)
        assert error is None
        assert updated.category_id == cat.id


def test_assign_task_to_foreign_category_fails(app):
    """Categoría de otro usuario → error de autorización."""
    with app.app_context():
        from src.services.category_service import CategoryService
        user1 = _create_test_user(email='cat6a@test.com')
        user2 = _create_test_user(email='cat6b@test.com')
        cat_user2, _ = CategoryService.create_category(user2.id, 'CatDeUser2')
        task_user1, _ = TaskService.create_task(user_id=user1.id, title='Tarea de user1')

        updated, error = TaskService.assign_category(user1.id, task_user1.id, cat_user2.id)
        assert updated is None
        assert error is not None


def test_filter_tasks_by_category(app):
    """Filtrado por categoría retorna solo las tareas de esa categoría."""
    with app.app_context():
        from src.services.category_service import CategoryService
        user = _create_test_user(email='cat7@test.com')
        cat, _ = CategoryService.create_category(user.id, 'Filtrada')
        t1, _ = TaskService.create_task(user_id=user.id, title='En categoría')
        t2, _ = TaskService.create_task(user_id=user.id, title='Sin categoría')
        TaskService.assign_category(user.id, t1.id, cat.id)

        tasks = TaskService.get_user_tasks(user.id, category_id=cat.id)
        ids = [t.id for t in tasks]
        assert t1.id in ids
        assert t2.id not in ids

# =============================================================================
# Incremento 3 — HU-09: Tareas vencidas (is_overdue)
# =============================================================================

def test_is_overdue_pending_past_due(app):
    """Tarea pending con due_date en el pasado → is_overdue=True."""
    from datetime import date, timedelta
    with app.app_context():
        user = _create_test_user(email='ov1@test.com')
        past_date = date.today() - timedelta(days=1)
        task, _ = TaskService.create_task(user_id=user.id, title='Vencida', due_date=past_date)
        assert task.is_overdue is True


def test_is_overdue_completed_task(app):
    """Tarea completed con due_date pasada → is_overdue=False."""
    from datetime import date, timedelta
    with app.app_context():
        user = _create_test_user(email='ov2@test.com')
        past_date = date.today() - timedelta(days=2)
        task, _ = TaskService.create_task(user_id=user.id, title='Completada vencida', due_date=past_date)
        TaskService.update_task_status(user.id, task.id, 'in_progress')
        TaskService.update_task_status(user.id, task.id, 'completed')
        assert task.is_overdue is False


def test_is_overdue_no_due_date(app):
    """Tarea sin due_date → is_overdue=False."""
    with app.app_context():
        user = _create_test_user(email='ov3@test.com')
        task, _ = TaskService.create_task(user_id=user.id, title='Sin fecha')
        assert task.is_overdue is False


def test_is_overdue_due_today(app):
    """Tarea con due_date=hoy → is_overdue=False (vence al final del día)."""
    from datetime import date
    with app.app_context():
        user = _create_test_user(email='ov4@test.com')
        task, _ = TaskService.create_task(user_id=user.id, title='Vence hoy', due_date=date.today())
        assert task.is_overdue is False


def test_is_overdue_in_progress_past_due(app):
    """Tarea in_progress con due_date pasada → is_overdue=True."""
    from datetime import date, timedelta
    with app.app_context():
        user = _create_test_user(email='ov5@test.com')
        past_date = date.today() - timedelta(days=3)
        task, _ = TaskService.create_task(user_id=user.id, title='En progreso vencida', due_date=past_date)
        TaskService.update_task_status(user.id, task.id, 'in_progress')
        assert task.is_overdue is True
