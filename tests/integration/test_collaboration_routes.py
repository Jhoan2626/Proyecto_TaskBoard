from src.models import db, User, Task, Notification
from src.services.task_service import TaskService


def _login(client, email, password="password123"):
    return client.post("/login", data={"email": email, "password": password})


def _setup(app):
    with app.app_context():
        for e in ("owner@example.com", "other@example.com"):
            u = User(email=e)
            u.set_password("password123")
            db.session.add(u)
        db.session.commit()
        owner = User.query.filter_by(email="owner@example.com").one()
        task, _ = TaskService.create_task(owner.id, "Tarea colaborativa")
        return task.id


JSON = {"Accept": "application/json"}


def test_assign_requires_auth(app, client):
    task_id = _setup(app)
    r = client.post(f"/tasks/{task_id}/assign", json={"assignee_email": "other@example.com"})
    assert r.status_code == 401


def test_assign_flow_and_notifications_http(app, client):
    task_id = _setup(app)
    _login(client, "owner@example.com")
    r = client.post(f"/tasks/{task_id}/assign", json={"assignee_email": "other@example.com"})
    assert r.status_code == 200

    # Asignado ve la tarea y la notificación
    other = app.test_client()
    _login(other, "other@example.com")
    page = other.get("/tasks?scope=assigned")
    assert b"Tarea colaborativa" in page.data
    data = other.get("/notifications", headers=JSON).get_json()
    assert data["unread_count"] == 1
    nid = data["notifications"][0]["id"]

    r = other.post(f"/notifications/{nid}/read", headers=JSON)
    assert r.status_code == 200
    data = other.get("/notifications", headers=JSON).get_json()
    assert data["unread_count"] == 0 and len(data["notifications"]) == 1


def test_assign_unknown_email_400(app, client):
    task_id = _setup(app)
    _login(client, "owner@example.com")
    r = client.post(f"/tasks/{task_id}/assign", json={"assignee_email": "ghost@example.com"})
    assert r.status_code == 400


def test_assign_other_users_task_403(app, client):
    task_id = _setup(app)
    _login(client, "other@example.com")
    r = client.post(f"/tasks/{task_id}/assign", json={"assignee_email": "owner@example.com"})
    assert r.status_code == 403


def test_mark_read_foreign_notification_403(app, client):
    task_id = _setup(app)
    _login(client, "owner@example.com")
    client.post(f"/tasks/{task_id}/assign", json={"assignee_email": "other@example.com"})
    with app.app_context():
        nid = Notification.query.one().id
    r = client.post(f"/notifications/{nid}/read", headers=JSON)
    assert r.status_code == 403


def test_mark_read_unknown_404(app, client):
    _setup(app)
    _login(client, "owner@example.com")
    assert client.post("/notifications/999/read", headers=JSON).status_code == 404


def test_notifications_page_renders(app, client):
    _setup(app)
    _login(client, "owner@example.com")
    assert client.get("/notifications").status_code == 200
