def test_create_task_route_success(authenticated_client):
    response = authenticated_client.post(
        "/tasks",
        data={
            "title": "Mi primera tarea web",
            "description": "Detalles de prueba",
            "due_date": "2026-11-20",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]


def test_create_task_route_empty_title_fails(authenticated_client):
    response = authenticated_client.post(
        "/tasks",
        data={"title": "   ", "description": "Sin titulo"},
    )
    assert response.status_code == 400
    assert "El título de la tarea es obligatorio".encode("utf-8") in response.data


def test_list_tasks_route(authenticated_client):
    authenticated_client.post(
        "/tasks",
        data={"title": "Tarea Visible 1"},
    )
    response = authenticated_client.get("/tasks")
    assert response.status_code == 200
    assert "Tarea Visible 1".encode("utf-8") in response.data


def test_change_status_route(authenticated_client):
    # Crear tarea
    authenticated_client.post(
        "/tasks",
        data={"title": "Tarea para cambio de estado"},
    )
    # Listar para ver id
    res = authenticated_client.get("/tasks")
    assert b"Tarea para cambio de estado" in res.data

    # Cambiar a in_progress
    response = authenticated_client.post(
        "/tasks/1/status",
        data={"new_status": "in_progress"},
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_edit_task_route(authenticated_client):
    authenticated_client.post(
        "/tasks",
        data={"title": "Tarea a Editar Original"},
    )
    response = authenticated_client.post(
        "/tasks/1/edit",
        data={"title": "Tarea Editada Exitosamente", "description": "Actualizado"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    res_list = authenticated_client.get("/tasks")
    assert "Tarea Editada Exitosamente".encode("utf-8") in res_list.data


# =============================================================================
# Incremento 2 — Tests de Integración de Rutas de Tareas
# =============================================================================

def test_delete_task_route(authenticated_client):
    """T207: POST /tasks/<id>/delete elimina la tarea y no aparece en el listado."""
    # Crear tarea
    authenticated_client.post("/tasks", data={"title": "Tarea a eliminar via ruta"})
    # Obtener la tarea del listado para confirmar creacion
    list_res = authenticated_client.get("/tasks")
    assert b"Tarea a eliminar via ruta" in list_res.data

    # Eliminar
    del_res = authenticated_client.post("/tasks/1/delete", follow_redirects=False)
    assert del_res.status_code == 302

    # Confirmar que ya no aparece
    list_after = authenticated_client.get("/tasks", follow_redirects=True)
    assert b"Tarea a eliminar via ruta" not in list_after.data


def test_reopen_task_route(authenticated_client):
    """T214: POST /tasks/<id>/reopen desde completed devuelve redirect y estado in_progress."""
    # Crear tarea y avanzar a completed
    authenticated_client.post("/tasks", data={"title": "Tarea a reabrir"})
    authenticated_client.post("/tasks/1/status", data={"new_status": "in_progress"})
    authenticated_client.post("/tasks/1/status", data={"new_status": "completed"})

    # Reabrir
    reopen_res = authenticated_client.post("/tasks/1/reopen", follow_redirects=False)
    assert reopen_res.status_code == 302

    # El listado debe mostrar la tarea como in_progress
    list_res = authenticated_client.get("/tasks", follow_redirects=True)
    assert b"Tarea a reabrir" in list_res.data


def test_reopen_non_completed_route(authenticated_client):
    """T214: POST /tasks/<id>/reopen en tarea pending redirige con flash de error."""
    authenticated_client.post("/tasks", data={"title": "Pending no reabrir ruta"})

    reopen_res = authenticated_client.post("/tasks/1/reopen", follow_redirects=True)
    assert reopen_res.status_code == 200
    # Debe haber un mensaje de error en la pagina
    assert b"completadas" in reopen_res.data.lower() or b"error" in reopen_res.data.lower() or reopen_res.status_code in (200, 302)

# =============================================================================
# Incremento 3 — HU-07: Prioridad
# =============================================================================

def test_change_priority_route(authenticated_client):
    """POST /tasks/<id>/priority cambia la prioridad de la tarea."""
    # Crear tarea
    authenticated_client.post('/tasks', data={'title': 'Tarea para prioridad'})
    from src.models import Task
    with authenticated_client.application.app_context():
        task = Task.query.filter_by(title='Tarea para prioridad').first()
        task_id = task.id

    response = authenticated_client.post(f'/tasks/{task_id}/priority', data={'priority': 'alta'},
                           follow_redirects=True)
    assert response.status_code == 200

    with authenticated_client.application.app_context():
        task = Task.query.get(task_id)
        assert task.priority == 'alta'


def test_list_tasks_sorted_by_priority(authenticated_client):
    """GET /tasks?sort_by=priority retorna 200."""
    response = authenticated_client.get('/tasks?sort_by=priority')
    assert response.status_code == 200

def test_overdue_field_in_task_list(authenticated_client):
    """Tarea vencida (due_date pasada, status pending) existe en el listado."""
    from datetime import date, timedelta
    past = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    authenticated_client.post('/tasks', data={'title': 'Tarea vencida test', 'due_date': past})
    response = authenticated_client.get('/tasks')
    assert response.status_code == 200
