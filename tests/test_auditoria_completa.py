"""Auditoría integral de TaskControl (Incrementos 1-5).

Cubre: jerarquía/capas del código, convivencia de implementaciones, migraciones
(esquema reproducible desde cero), flujos extremo a extremo por incremento,
seguridad de acceso y robustez ante entradas inválidas.
"""
import ast
import os
import re
import sqlite3
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

from src import create_app
from src.models import db, AuditLog, Category, Notification, Task, User

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
JSON = {"Accept": "application/json"}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _register(client, email, password="password123"):
    return client.post("/register", data={"email": email, "password": password})


def _login(client, email, password="password123"):
    return client.post("/login", data={"email": email, "password": password})


def _new_client(app, email):
    client = app.test_client()
    assert _register(client, email).status_code == 302
    assert _login(client, email).status_code == 302
    return client


@pytest.fixture
def alice(app):
    return _new_client(app, "alice@example.com")


@pytest.fixture
def bob(app):
    return _new_client(app, "bob@example.com")


def _create_task(client, title="Tarea", **extra):
    res = client.post("/tasks", json={"title": title, **extra}, headers=JSON)
    assert res.status_code == 201, res.data
    return res.get_json()["task_id"]


def _actions(app):
    with app.app_context():
        return [log.action for log in AuditLog.query.order_by(AuditLog.id)]


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


# ---------------------------------------------------------------------------
# 1. Jerarquía de archivos y capas
# ---------------------------------------------------------------------------

EXPECTED_FILES = [
    "src/__init__.py", "src/config.py", "app.py", "requirements.txt", "pytest.ini",
    "src/models/__init__.py", "src/models/user.py", "src/models/task.py",
    "src/models/audit_log.py", "src/models/category.py", "src/models/notification.py",
    "src/models/password_reset_token.py",
    "src/services/task_service.py", "src/services/auth_service.py",
    "src/services/audit_service.py", "src/services/category_service.py",
    "src/services/assignment_service.py", "src/services/notification_service.py",
    "src/routes/auth_routes.py", "src/routes/task_routes.py", "src/routes/category_routes.py",
    "src/routes/collab_routes.py", "src/routes/decorators.py",
    "src/static/js/tasks.js", "src/static/css/style.css", "src/templates/base.html",
    "src/templates/tasks/list.html", "src/templates/notifications/list.html",
    "src/templates/categories/list.html", "src/templates/auth/login.html",
    "migrations/env.py", "migrations/alembic.ini",
]


@pytest.mark.parametrize("relative", EXPECTED_FILES)
def test_expected_project_files_exist(relative):
    assert (ROOT / relative).is_file(), f"Falta {relative}"


def test_models_do_not_depend_on_upper_layers():
    for path in (SRC / "models").glob("*.py"):
        for module in _imports_of(path):
            assert not module.startswith(("src.services", "src.routes")), (path.name, module)


def test_services_do_not_depend_on_routes_or_flask_request_layer():
    for path in (SRC / "services").glob("*.py"):
        for module in _imports_of(path):
            assert not module.startswith("src.routes"), (path.name, module)


def test_no_duplicate_members_inside_classes():
    """Detecta definiciones repetidas por merges (p. ej. is_overdue / VALID_PRIORITIES)."""
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            names = []
            for node in cls.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.append(node.name)
                elif isinstance(node, ast.Assign):
                    names.extend(t.id for t in node.targets if isinstance(t, ast.Name))
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    names.append(node.target.id)
            duplicated = {n for n in names if names.count(n) > 1}
            assert not duplicated, f"{path.name}:{cls.name} repite {duplicated}"


def test_all_modules_import_cleanly():
    import importlib

    for path in SRC.rglob("*.py"):
        module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        module = module.removesuffix(".__init__")
        importlib.import_module(module)


# ---------------------------------------------------------------------------
# 2. Aplicación: rutas, blueprints, plantillas y recursos estáticos
# ---------------------------------------------------------------------------

def test_blueprints_registered_and_no_route_collisions(app):
    assert {"auth", "tasks", "collab", "categories"} <= set(app.blueprints)

    seen = {}
    for rule in app.url_map.iter_rules():
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            key = (rule.rule, method)
            assert key not in seen, f"Colisión {key}: {seen[key]} vs {rule.endpoint}"
            seen[key] = rule.endpoint

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    required = {
        "auth.register", "auth.login", "auth.logout", "auth.forgot_password", "auth.reset_password",
        "tasks.list_tasks", "tasks.new_task", "tasks.create_task", "tasks.edit_task", "tasks.update_task",
        "tasks.change_status", "tasks.delete_task", "tasks.reopen_task", "tasks.change_priority",
        "tasks.assign_category", "tasks.reorder_tasks", "collab.assign_task", "collab.list_notifications",
        "collab.mark_notification_read", "collab.mark_all_notifications_read",
        "categories.list_categories", "categories.create_category", "categories.delete_category",
    }
    assert required <= endpoints, required - endpoints


def test_every_protected_route_requires_session(app):
    public = {"index", "static", "auth.register", "auth.login", "auth.logout",
              "auth.forgot_password", "auth.reset_password"}
    client = app.test_client()
    for rule in app.url_map.iter_rules():
        if rule.endpoint in public:
            continue
        path = re.sub(r"<[^>]+>", "1", rule.rule)
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            res = client.open(path, method=method)
            assert res.status_code == 302, (method, path, res.status_code)
            assert "/login" in res.headers["Location"], (method, path)
            res = client.open(path, method=method, headers=JSON)
            assert res.status_code == 401, (method, path, res.status_code)


def test_root_redirects_according_to_session(app, alice):
    assert app.test_client().get("/").headers["Location"].endswith("/login")
    assert alice.get("/").headers["Location"].endswith("/tasks")


def test_all_pages_render_for_authenticated_user(alice):
    task_id = _create_task(alice, "Visible")
    for path in ["/tasks", "/tasks?scope=mine", "/tasks?scope=assigned", "/tasks?sort_by=priority",
                 "/tasks?status=completed", "/tasks?category_id=1", "/tasks/new",
                 f"/tasks/{task_id}/edit", "/categories", "/notifications", "/notifications?unread=1"]:
        assert alice.get(path).status_code == 200, path


def test_public_pages_render(app):
    client = app.test_client()
    for path in ["/login", "/register", "/auth/forgot-password"]:
        assert client.get(path).status_code == 200, path


def test_static_assets_and_js_hooks_match_templates(alice):
    assert alice.get("/static/js/tasks.js").status_code == 200
    assert alice.get("/static/css/style.css").status_code == 200

    js = (SRC / "static/js/tasks.js").read_text(encoding="utf-8")
    task_id = _create_task(alice, "Para JS")
    alice.post(f"/tasks/{task_id}/status", data={"new_status": "in_progress"})
    html = alice.get("/tasks?scope=mine").get_data(as_text=True)
    # Cada selector que usa el JS debe existir en la plantilla servida.
    for hook in ["js-status-form", "task-status", "task-card", "data-reopen-url",
                 "data-reorder-url", "task-drag-handle", "task-interaction-message"]:
        assert hook in js or hook.replace("data-", "").replace("-", "") in js.replace("-", "").lower()
        assert hook in html, f"La plantilla no expone '{hook}' que usa tasks.js"
    assert 'data-reorder-enabled="true"' in html


def test_reorder_handle_hidden_when_view_is_not_complete(alice):
    _create_task(alice, "x")
    for query in ["", "?scope=assigned", "?scope=mine&status=pending", "?scope=mine&sort_by=priority"]:
        assert "task-drag-handle" not in alice.get(f"/tasks{query}").get_data(as_text=True), query


# ---------------------------------------------------------------------------
# 3. Migraciones: el esquema debe poder construirse desde cero
# ---------------------------------------------------------------------------

def _flask(db_path, *args):
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}", "FLASK_APP": "app.py",
           "FLASK_ENV": "development"}
    return subprocess.run([sys.executable, "-m", "flask", *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=180)


def test_migrations_have_single_linear_head():
    versions = (ROOT / "migrations" / "versions").glob("*.py")
    revisions, downs = {}, []
    for path in versions:
        text = path.read_text(encoding="utf-8")
        rev = re.search(r"^revision\s*=\s*['\"](\w+)['\"]", text, re.M).group(1)
        down = re.search(r"^down_revision\s*=\s*(None|['\"]\w+['\"])", text, re.M).group(1).strip("'\"")
        revisions[rev] = down
        downs.append(down)
    heads = [rev for rev in revisions if rev not in downs]
    assert len(heads) == 1, f"Debe existir una sola cabeza de migración, hay: {heads}"
    assert downs.count("None") == 1


def test_migrations_build_full_schema_without_drift(tmp_path):
    db_path = tmp_path / "audit.db"
    upgrade = _flask(db_path, "db", "upgrade")
    assert upgrade.returncode == 0, upgrade.stderr[-2000:]

    tables = {r[0] for r in sqlite3.connect(db_path).execute("select name from sqlite_master where type='table'")}
    assert {"users", "tasks", "audit_logs", "password_reset_tokens", "notifications", "categories"} <= tables

    columns = {r[1] for r in sqlite3.connect(db_path).execute("pragma table_info(tasks)")}
    assert {"deleted_at", "priority", "category_id", "assignee_id", "position"} <= columns

    check = _flask(db_path, "db", "check")
    assert check.returncode == 0, "Los modelos difieren de las migraciones:\n" + check.stderr[-2000:]


def test_migrations_downgrade_to_base_and_back(tmp_path):
    db_path = tmp_path / "roundtrip.db"
    assert _flask(db_path, "db", "upgrade").returncode == 0
    down = _flask(db_path, "db", "downgrade", "base")
    assert down.returncode == 0, down.stderr[-2000:]
    assert _flask(db_path, "db", "upgrade").returncode == 0


def test_migrations_preserve_existing_data(tmp_path):
    db_path = tmp_path / "legacy.db"
    assert _flask(db_path, "db", "upgrade", "c71e2a9f4b10").returncode == 0
    conn = sqlite3.connect(db_path)
    conn.execute("insert into users (id,email,password_hash,created_at) values (1,'a@a.com','x','2026-01-01')")
    conn.execute("insert into tasks (id,user_id,title,status,created_at,updated_at,position) "
                 "values (1,1,'vieja','pending','2026-01-01','2026-01-01',0)")
    conn.commit()
    conn.close()

    assert _flask(db_path, "db", "upgrade").returncode == 0
    row = sqlite3.connect(db_path).execute("select title, priority, category_id from tasks").fetchone()
    assert row == ("vieja", "media", None)


# ---------------------------------------------------------------------------
# 4. Incremento 1 — HU-01..04, HU-12, HU-13
# ---------------------------------------------------------------------------

def test_inc1_register_validation_and_hashing(app):
    client = app.test_client()
    assert client.post("/register", json={"email": "no-es-correo", "password": "password123"}).status_code == 400
    assert client.post("/register", json={"email": "a@example.com", "password": "123"}).status_code == 400
    assert client.post("/register", json={"email": "a@example.com", "password": "password123"}).status_code == 201
    assert client.post("/register", json={"email": "A@Example.com", "password": "password123"}).status_code == 409
    with app.app_context():
        user = User.query.filter_by(email="a@example.com").one()
        assert user.password_hash != "password123" and user.check_password("password123")


def test_inc1_login_logout_session(app, alice):
    assert alice.get("/tasks").status_code == 200
    alice.get("/logout")
    assert alice.get("/tasks").status_code == 302
    bad = app.test_client().post("/login", data={"email": "alice@example.com", "password": "mala-clave"})
    assert bad.status_code == 401


@pytest.mark.parametrize("target", ["//evil.example.com", "/\\evil.example.com", "https://evil.example.com"])
def test_inc1_login_next_does_not_allow_open_redirect(app, alice, target):
    client = app.test_client()
    res = client.post(f"/login?next={target}", data={"email": "alice@example.com", "password": "password123"})
    assert res.status_code == 302
    location = res.headers["Location"]
    assert location.startswith("/") and not location.startswith(("//", "/\\")), location


def test_inc1_login_next_local_path_is_honoured(app, alice):
    res = app.test_client().post("/login?next=/categories", data={"email": "alice@example.com", "password": "password123"})
    assert res.headers["Location"].endswith("/categories")


def test_inc1_task_lifecycle_and_audit(app, alice):
    task_id = _create_task(alice, "  Documentar  ", description="desc", due_date="2030-01-01")
    with app.app_context():
        task = db.session.get(Task, task_id)
        assert (task.title, task.status, task.priority) == ("Documentar", "pending", "media")
    # Transiciones inválidas
    bad = alice.post(f"/tasks/{task_id}/status", json={"new_status": "completed"}, headers=JSON)
    assert bad.status_code == 400
    ok = alice.post(f"/tasks/{task_id}/status", json={"new_status": "in_progress"}, headers=JSON)
    assert ok.status_code == 200 and ok.get_json()["status"] == "in_progress"
    assert alice.post(f"/tasks/{task_id}/edit", json={"title": "Nuevo"}, headers=JSON).status_code == 200
    assert alice.post(f"/tasks/{task_id}/status", json={"new_status": "completed"}, headers=JSON).status_code == 200
    assert alice.post(f"/tasks/{task_id}/status", json={"new_status": "pending"}, headers=JSON).status_code == 400
    assert _actions(app) == ["TASK_CREATED", "TASK_STATUS_CHANGED", "TASK_UPDATED", "TASK_STATUS_CHANGED"]


def test_inc1_list_filters_by_status_and_owner(app, alice, bob):
    pending = _create_task(alice, "pendiente")
    started = _create_task(alice, "iniciada")
    alice.post(f"/tasks/{started}/status", json={"new_status": "in_progress"}, headers=JSON)
    _create_task(bob, "de bob")
    body = alice.get("/tasks?status=in_progress").get_data(as_text=True)
    assert "iniciada" in body and "pendiente" not in body and "de bob" not in body
    assert "de bob" not in alice.get("/tasks").get_data(as_text=True)
    assert pending != started


def test_inc1_task_validation_rejects_bad_input_without_500(alice):
    assert alice.post("/tasks", json={"title": "   "}, headers=JSON).status_code == 400
    assert alice.post("/tasks", json={"title": 123}, headers=JSON).status_code == 400
    assert alice.post("/tasks", json={"title": "x" * 201}, headers=JSON).status_code == 400
    assert alice.post("/tasks", json={"title": "ok", "due_date": "31/12/2030"}, headers=JSON).status_code == 400
    assert alice.post("/tasks", json={"title": "ok", "due_date": 20300101}, headers=JSON).status_code == 400
    assert alice.post("/tasks", json={"title": "ok", "description": 5}, headers=JSON).status_code == 201
    assert alice.post("/tasks", data={"title": "ok", "due_date": "mañana"}).status_code == 400
    assert alice.post("/tasks", data={"title": "ok", "due_date": ""}).status_code == 302


def test_inc1_edit_invalid_date_does_not_erase_existing_date(app, alice):
    task_id = _create_task(alice, "con fecha", due_date="2030-05-05")
    res = alice.post(f"/tasks/{task_id}/edit", json={"title": "con fecha", "due_date": "xx"}, headers=JSON)
    assert res.status_code == 400
    with app.app_context():
        assert db.session.get(Task, task_id).due_date == date(2030, 5, 5)


def test_inc1_other_users_cannot_touch_tasks(app, alice, bob):
    task_id = _create_task(alice, "privada")
    assert bob.post(f"/tasks/{task_id}/edit", json={"title": "hack"}, headers=JSON).status_code == 403
    assert bob.post(f"/tasks/{task_id}/status", json={"new_status": "in_progress"}, headers=JSON).status_code == 403
    assert bob.post(f"/tasks/{task_id}/priority", json={"priority": "alta"}, headers=JSON).status_code == 403
    assert bob.post(f"/tasks/{task_id}/delete").status_code == 302
    assert bob.get(f"/tasks/{task_id}/edit").status_code == 302
    # Formulario HTML de un tercero no debe provocar un 500
    assert bob.post(f"/tasks/{task_id}/edit", data={"title": "hack"}).status_code in (302, 400, 403)
    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task.title == "privada" and task.deleted_at is None and task.priority == "media"


def test_inc1_nonexistent_task_returns_404_in_json(alice):
    assert alice.post("/tasks/9999/status", json={"new_status": "in_progress"}, headers=JSON).status_code == 404
    assert alice.post("/tasks/9999/edit", json={"title": "x"}, headers=JSON).status_code == 404
    assert alice.post("/tasks/9999/priority", json={"priority": "alta"}, headers=JSON).status_code == 404
    assert alice.post("/tasks/9999/category", json={"category_id": None}, headers=JSON).status_code == 404


# ---------------------------------------------------------------------------
# 5. Incremento 2 — HU-05, HU-06, HU-14
# ---------------------------------------------------------------------------

def test_inc2_soft_delete_preserves_row_and_audit(app, alice):
    task_id = _create_task(alice, "borrable")
    assert alice.post(f"/tasks/{task_id}/delete").status_code == 302
    assert "borrable" not in alice.get("/tasks").get_data(as_text=True)
    assert alice.post(f"/tasks/{task_id}/edit", json={"title": "x"}, headers=JSON).status_code == 400
    with app.app_context():
        assert db.session.get(Task, task_id).deleted_at is not None
    alice.post(f"/tasks/{task_id}/delete")  # segundo borrado: sin efecto ni error
    assert _actions(app).count("TASK_DELETED") == 1


def test_inc2_reopen_is_distinct_audit_event(app, alice):
    task_id = _create_task(alice, "reabrir")
    alice.post(f"/tasks/{task_id}/status", json={"new_status": "in_progress"}, headers=JSON)
    alice.post(f"/tasks/{task_id}/status", json={"new_status": "completed"}, headers=JSON)
    assert alice.post(f"/tasks/{task_id}/reopen").status_code == 302
    with app.app_context():
        assert db.session.get(Task, task_id).status == "in_progress"
    assert _actions(app)[-1] == "TASK_REOPENED"
    alice.post(f"/tasks/{task_id}/reopen")  # ya no está completada
    assert _actions(app).count("TASK_REOPENED") == 1


def test_inc2_password_reset_full_flow(app, caplog):
    client = _new_client(app, "carol@example.com")
    client.get("/logout")
    caplog.set_level("INFO")
    # Respuesta neutral exista o no el correo
    r1 = client.post("/auth/forgot-password", data={"email": "carol@example.com"})
    r2 = client.post("/auth/forgot-password", data={"email": "fantasma@example.com"})
    assert r1.status_code == r2.status_code == 200
    assert "Si ese correo está registrado".encode() in r1.data and "Si ese correo está registrado".encode() in r2.data

    token = re.search(r"/auth/reset-password/(\w{64})", caplog.text).group(1)
    assert client.get(f"/auth/reset-password/{token}").status_code == 200
    mismatch = client.post(f"/auth/reset-password/{token}", data={"password": "nuevaClave123", "confirm_password": "otra"})
    assert mismatch.status_code == 200
    short = client.post(f"/auth/reset-password/{token}", data={"password": "corta", "confirm_password": "corta"})
    assert short.status_code == 200
    done = client.post(f"/auth/reset-password/{token}", data={"password": "nuevaClave123", "confirm_password": "nuevaClave123"})
    assert done.status_code == 302 and done.headers["Location"].endswith("/login")
    # Token de un solo uso
    assert client.get(f"/auth/reset-password/{token}").status_code == 302
    assert _login(client, "carol@example.com", "nuevaClave123").status_code == 302
    assert _login(app.test_client(), "carol@example.com", "password123").status_code == 401


def test_inc2_invalid_reset_token_is_rejected(app):
    client = app.test_client()
    assert client.get("/auth/reset-password/" + "0" * 64).status_code == 302
    assert client.post("/auth/reset-password/" + "0" * 64, data={"password": "x" * 9, "confirm_password": "x" * 9}).status_code == 302


# ---------------------------------------------------------------------------
# 6. Incremento 3 — HU-07, HU-08, HU-09
# ---------------------------------------------------------------------------

def test_inc3_priority_default_change_and_sort(app, alice):
    low = _create_task(alice, "baja")
    high = _create_task(alice, "alta")
    assert alice.post(f"/tasks/{low}/priority", json={"priority": "baja"}, headers=JSON).status_code == 200
    assert alice.post(f"/tasks/{high}/priority", json={"priority": "alta"}, headers=JSON).status_code == 200
    assert alice.post(f"/tasks/{high}/priority", json={"priority": "urgente"}, headers=JSON).status_code == 400
    body = alice.get("/tasks?sort_by=priority").get_data(as_text=True)
    assert body.index("alta") < body.index("baja")
    assert "TASK_PRIORITY_CHANGED" in _actions(app)


def test_inc3_categories_crud_and_task_detach_on_delete(app, alice, bob):
    assert alice.post("/categories", data={"name": "  Trabajo "}).status_code == 302
    assert alice.post("/categories", data={"name": "Trabajo"}).status_code == 400
    assert alice.post("/categories", data={"name": "  "}).status_code == 400
    assert bob.post("/categories", data={"name": "Trabajo"}).status_code == 302  # único por usuario
    with app.app_context():
        category_id = Category.query.filter_by(name="Trabajo").order_by(Category.id).first().id
    task_id = _create_task(alice, "con categoría")
    assert alice.post(f"/tasks/{task_id}/category", json={"category_id": category_id}, headers=JSON).status_code == 200
    assert "con categoría" in alice.get(f"/tasks?category_id={category_id}").get_data(as_text=True)
    # Categoría ajena o valor basura no deben ser aceptados ni borrar la categoría actual
    with app.app_context():
        foreign = Category.query.filter_by(user_id=2).one().id
    assert alice.post(f"/tasks/{task_id}/category", json={"category_id": foreign}, headers=JSON).status_code == 400
    assert alice.post(f"/tasks/{task_id}/category", json={"category_id": "abc"}, headers=JSON).status_code == 400
    with app.app_context():
        assert db.session.get(Task, task_id).category_id == category_id
    assert bob.post(f"/categories/{category_id}/delete").status_code == 302
    with app.app_context():
        assert db.session.get(Category, category_id) is not None
    alice.post(f"/categories/{category_id}/delete")
    with app.app_context():
        assert db.session.get(Category, category_id) is None
        task = db.session.get(Task, task_id)
        assert task is not None and task.category_id is None and task.deleted_at is None


def test_inc3_overdue_computed_in_backend(app, alice):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    overdue = _create_task(alice, "vencida", due_date=yesterday)
    done = _create_task(alice, "completada", due_date=yesterday)
    future = _create_task(alice, "futura", due_date=(date.today() + timedelta(days=5)).isoformat())
    alice.post(f"/tasks/{done}/status", json={"new_status": "in_progress"}, headers=JSON)
    alice.post(f"/tasks/{done}/status", json={"new_status": "completed"}, headers=JSON)
    with app.app_context():
        assert db.session.get(Task, overdue).is_overdue is True
        assert db.session.get(Task, done).is_overdue is False
        assert db.session.get(Task, future).is_overdue is False
        assert "is_overdue" not in Task.__table__.columns
    assert alice.get("/tasks").get_data(as_text=True).count("Vencida") == 1
    alice.post(f"/tasks/{overdue}/delete")
    assert "Vencida" not in alice.get("/tasks").get_data(as_text=True)


# ---------------------------------------------------------------------------
# 7. Incremento 4 — HU-10, HU-11
# ---------------------------------------------------------------------------

def test_inc4_assignment_notification_and_visibility(app, alice, bob):
    task_id = _create_task(alice, "delegada")
    assert alice.post(f"/tasks/{task_id}/assign", json={"assignee_email": "nadie@example.com"}, headers=JSON).status_code == 400
    assert alice.post(f"/tasks/{task_id}/assign", json={"assignee_email": "alice@example.com"}, headers=JSON).status_code == 400
    assert bob.post(f"/tasks/{task_id}/assign", json={"assignee_email": "bob@example.com"}, headers=JSON).status_code == 403

    res = alice.post(f"/tasks/{task_id}/assign", json={"assignee_email": "BOB@example.com"}, headers=JSON)
    assert res.status_code == 200
    assert alice.post(f"/tasks/{task_id}/assign", json={"assignee_email": "bob@example.com"}, headers=JSON).status_code == 400

    with app.app_context():
        assert Notification.query.count() == 1
    assert "delegada" in bob.get("/tasks?scope=assigned").get_data(as_text=True)
    assert "delegada" not in bob.get("/tasks?scope=mine").get_data(as_text=True)
    # El asignado es de solo lectura
    assert bob.post(f"/tasks/{task_id}/edit", json={"title": "x"}, headers=JSON).status_code == 403
    assert bob.post(f"/tasks/{task_id}/status", json={"new_status": "in_progress"}, headers=JSON).status_code == 403

    data = bob.get("/notifications", headers=JSON).get_json()
    assert data["unread_count"] == 1 and data["notifications"][0]["task_id"] == task_id
    assert alice.post(f"/notifications/{data['notifications'][0]['id']}/read", headers=JSON).status_code == 403
    assert bob.post(f"/notifications/{data['notifications'][0]['id']}/read", headers=JSON).status_code == 200
    after = bob.get("/notifications", headers=JSON).get_json()
    assert after["unread_count"] == 0 and len(after["notifications"]) == 1  # persiste tras leerse
    assert "TASK_ASSIGNED" in _actions(app)


def test_inc4_unassign_and_read_all(app, alice, bob):
    ids = [_create_task(alice, f"t{i}") for i in range(2)]
    for task_id in ids:
        alice.post(f"/tasks/{task_id}/assign", json={"assignee_email": "bob@example.com"}, headers=JSON)
    assert bob.post("/notifications/read-all", headers=JSON).get_json()["updated"] == 2
    assert alice.post(f"/tasks/{ids[0]}/assign", json={"assignee_email": ""}, headers=JSON).status_code == 200
    assert "t0" not in bob.get("/tasks?scope=assigned").get_data(as_text=True)
    with app.app_context():
        assert Notification.query.count() == 2


def test_inc4_navbar_shows_unread_counter(alice, bob):
    task_id = _create_task(alice, "aviso")
    alice.post(f"/tasks/{task_id}/assign", json={"assignee_email": "bob@example.com"}, headers=JSON)
    assert 'badge badge-in_progress">1<' in bob.get("/tasks").get_data(as_text=True)


# ---------------------------------------------------------------------------
# 8. Incremento 5 — HU-15, HU-16
# ---------------------------------------------------------------------------

def test_inc5_complete_without_reload_contract(alice):
    task_id = _create_task(alice, "ajax")
    alice.post(f"/tasks/{task_id}/status", json={"new_status": "in_progress"}, headers=JSON)
    ok = alice.post(f"/tasks/{task_id}/status", json={"new_status": "completed"}, headers=JSON)
    assert ok.status_code == 200 and ok.get_json()["status"] == "completed"
    bad = alice.post(f"/tasks/{task_id}/status", json={"new_status": "pending"}, headers=JSON)
    assert bad.status_code == 400 and "error" in bad.get_json()


def test_inc5_reorder_persists_and_new_tasks_go_first(app, alice, bob):
    a, b, c = (_create_task(alice, name) for name in "abc")
    assert [t for t in _order(alice)] == [c, b, a]
    res = alice.post("/tasks/reorder", json={"task_ids": [a, c, b]}, headers=JSON)
    assert res.status_code == 200 and res.get_json()["task_ids"] == [a, c, b]
    assert _order(alice) == [a, c, b]
    d = _create_task(alice, "d")
    assert _order(alice)[0] == d


def _order(client):
    html = client.get("/tasks?scope=mine").get_data(as_text=True)
    return [int(i) for i in re.findall(r'data-task-id="(\d+)"', html)]


def test_inc5_reorder_rejects_invalid_payloads(alice, bob):
    a = _create_task(alice, "a")
    b = _create_task(alice, "b")
    foreign = _create_task(bob, "ajena")
    post = lambda payload, **kw: alice.post("/tasks/reorder", json=payload, headers=JSON, **kw).status_code
    assert post({"task_ids": [a]}) == 400            # incompleto
    assert post({"task_ids": [a, a, b]}) == 400      # duplicados
    assert post({"task_ids": [a, b, foreign]}) == 403  # ajeno
    assert post({"task_ids": ["1", "2"]}) == 400     # tipos
    assert post({"task_ids": "x"}) == 400
    assert post([1, 2]) == 400
    assert alice.post("/tasks/reorder", data={"task_ids": "1"}).status_code == 400
    assert _order(alice) == [b, a]


def test_inc5_reorder_is_isolated_between_users_and_ignores_deleted(app, alice, bob):
    a, b = _create_task(alice, "a"), _create_task(alice, "b")
    x, y = _create_task(bob, "x"), _create_task(bob, "y")
    alice.post(f"/tasks/{b}/delete")
    assert alice.post("/tasks/reorder", json={"task_ids": [a]}, headers=JSON).status_code == 200
    assert bob.post("/tasks/reorder", json={"task_ids": [x, y]}, headers=JSON).status_code == 200
    assert _order(bob) == [x, y]
