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
