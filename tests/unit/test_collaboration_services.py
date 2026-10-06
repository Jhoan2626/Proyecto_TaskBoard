import json
import pytest
from src.models import db, User, Task, AuditLog, Notification
from src.services.task_service import TaskService
from src.services.assignment_service import AssignmentService
from src.services.notification_service import NotificationService


def _user(email):
    u = User(email=email)
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def ctx(app):
    with app.app_context():
        owner = _user("owner@example.com")
        other = _user("other@example.com")
        task, _ = TaskService.create_task(owner.id, "Tarea A")
        yield {"owner": owner.id, "other": other.id, "task": task.id}


# --- Servicio: asignación (HU-10) ---

def test_assign_creates_exactly_one_notification(ctx):
    task, err = AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    assert err is None and task.assignee_id == ctx["other"]
    notes = Notification.query.all()
    assert len(notes) == 1
    n = notes[0]
    assert (n.user_id, n.task_id, n.is_read) == (ctx["other"], ctx["task"], False)


def test_assign_unregistered_email_rejected(ctx):
    task, err = AssignmentService.assign_task(ctx["owner"], ctx["task"], "ghost@example.com")
    assert task is None and "no está registrado" in err
    assert Notification.query.count() == 0
    assert db.session.get(Task, ctx["task"]).assignee_id is None


def test_assign_only_by_owner(ctx):
    task, err = AssignmentService.assign_task(ctx["other"], ctx["task"], "owner@example.com")
    assert task is None and "No tiene permiso" in err


def test_assign_to_self_rejected(ctx):
    _, err = AssignmentService.assign_task(ctx["owner"], ctx["task"], "owner@example.com")
    assert err is not None and Notification.query.count() == 0


def test_assign_deleted_task_rejected(ctx):
    TaskService.delete_task(ctx["owner"], ctx["task"])
    _, err = AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    assert err is not None


def test_assign_same_user_twice_rejected_no_duplicate_notification(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    _, err = AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    assert err is not None
    assert Notification.query.count() == 1


def test_assign_is_audited_with_old_and_new(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    log = AuditLog.query.filter_by(action=AuditLog.ACTION_TASK_ASSIGNED).one()
    assert log.actor_id == ctx["owner"] and log.timestamp is not None
    details = json.loads(log.details)
    assert details == {"old_assignee_id": None, "new_assignee_id": ctx["other"]}


def test_reassign_notifies_new_assignee_and_audits(ctx):
    third = _user("third@example.com")
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "third@example.com")
    assert db.session.get(Task, ctx["task"]).assignee_id == third.id
    assert Notification.query.filter_by(user_id=third.id).count() == 1
    last = AuditLog.query.filter_by(action=AuditLog.ACTION_TASK_ASSIGNED).order_by(AuditLog.id.desc()).first()
    assert json.loads(last.details)["old_assignee_id"] == ctx["other"]


def test_unassign_clears_without_notification(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    task, err = AssignmentService.assign_task(ctx["owner"], ctx["task"], "")
    assert err is None and task.assignee_id is None
    assert Notification.query.count() == 1


# --- Servicio: listado ---

def test_assignee_listing_includes_task(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    assert [t.id for t in TaskService.get_user_tasks(ctx["other"])] == [ctx["task"]]
    assert TaskService.get_user_tasks(ctx["other"], scope="mine") == []
    assert len(TaskService.get_user_tasks(ctx["other"], scope="assigned")) == 1
    assert TaskService.get_user_tasks(ctx["owner"], scope="assigned") == []
    assert len(TaskService.get_user_tasks(ctx["owner"], scope="mine")) == 1


def test_unrelated_user_does_not_see_task(ctx):
    third = _user("third@example.com")
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    assert TaskService.get_user_tasks(third.id) == []


def test_deleted_assigned_task_hidden_from_assignee(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    TaskService.delete_task(ctx["owner"], ctx["task"])
    assert TaskService.get_user_tasks(ctx["other"]) == []


def test_assignee_cannot_edit_or_delete(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    _, err = TaskService.delete_task(ctx["other"], ctx["task"])
    assert "No tiene permiso" in err
    _, err = TaskService.update_task(ctx["other"], ctx["task"], "Hack")
    assert "No tiene permiso" in err


# --- Servicio: notificaciones (HU-11) ---

def test_mark_as_read_persists_notification(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    n = Notification.query.one()
    assert NotificationService.unread_count(ctx["other"]) == 1
    _, err = NotificationService.mark_as_read(ctx["other"], n.id)
    assert err is None
    assert NotificationService.unread_count(ctx["other"]) == 0
    assert len(NotificationService.list_for_user(ctx["other"])) == 1  # no se descarta


def test_cannot_read_others_notification(ctx):
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    n = Notification.query.one()
    _, err = NotificationService.mark_as_read(ctx["owner"], n.id)
    assert "No tiene permiso" in err
    assert db.session.get(Notification, n.id).is_read is False


def test_mark_all_as_read(ctx):
    t2, _ = TaskService.create_task(ctx["owner"], "Tarea B")
    AssignmentService.assign_task(ctx["owner"], ctx["task"], "other@example.com")
    AssignmentService.assign_task(ctx["owner"], t2.id, "other@example.com")
    assert NotificationService.mark_all_as_read(ctx["other"]) == 2
    assert NotificationService.unread_count(ctx["other"]) == 0
