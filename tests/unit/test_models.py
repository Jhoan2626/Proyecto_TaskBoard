from datetime import date
from src.models import db, User, Task, AuditLog


def test_user_password_hashing(app):
    with app.app_context():
        user = User(email="hash@example.com")
        user.set_password("MyPassword!123")
        assert user.password_hash != "MyPassword!123"
        assert user.check_password("MyPassword!123") is True
        assert user.check_password("WrongPassword") is False


def test_task_creation_and_defaults(app):
    with app.app_context():
        user = User(email="owner@example.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

        task = Task(
            user_id=user.id,
            title="Aprender Flask Monolito",
            description="Revisar blueprints y servicios",
            due_date=date(2026, 10, 1),
        )
        db.session.add(task)
        db.session.commit()

        assert task.id is not None
        assert task.status == Task.STATUS_PENDING
        assert task.user.email == "owner@example.com"
        assert task.created_at is not None
        assert task.updated_at is not None


def test_audit_log_model(app):
    with app.app_context():
        audit = AuditLog(
            actor_id=1,
            action=AuditLog.ACTION_TASK_CREATED,
            entity_type="Task",
            entity_id=10,
            details='{"title": "Test"}',
        )
        db.session.add(audit)
        db.session.commit()

        saved = db.session.get(AuditLog, audit.id)
        assert saved.actor_id == 1
        assert saved.action == "TASK_CREATED"
        assert saved.entity_id == 10
        assert saved.timestamp is not None
