def test_register_get_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Registro" in response.data or b"registrarse" in response.data.lower()


def test_register_post_success(client):
    response = client.post(
        "/register",
        data={"email": "route_register@example.com", "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_register_post_duplicate_email(client, registered_user):
    response = client.post(
        "/register",
        data={"email": registered_user["email"], "password": "anypassword"},
    )
    assert response.status_code == 400
    assert "ya está registrado".encode("utf-8") in response.data


def test_login_get_form(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_login_post_success(client, registered_user):
    response = client.post(
        "/login",
        data={"email": registered_user["email"], "password": registered_user["password"]},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]


def test_login_post_invalid_credentials(client):
    response = client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "badpassword"},
    )
    assert response.status_code == 401
    assert "Credenciales inválidas".encode("utf-8") in response.data


def test_logout(authenticated_client):
    response = authenticated_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_protected_route_denied_without_auth(client):
    response = client.get("/tasks", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
