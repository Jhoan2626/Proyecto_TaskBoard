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


# =============================================================================
# Incremento 2 — Tests de Integración de Rutas de Auth (HU-14)
# =============================================================================

def test_forgot_password_get(client):
    """T219: GET /auth/forgot-password devuelve 200."""
    response = client.get("/auth/forgot-password")
    assert response.status_code == 200


def test_forgot_password_post_existing(client, registered_user):
    """T219: POST con email registrado retorna 200 con mensaje neutral."""
    response = client.post(
        "/auth/forgot-password",
        data={"email": registered_user["email"]},
    )
    assert response.status_code == 200
    # Mensaje neutral (no revela si el email existe)
    assert b"enlace" in response.data.lower() or b"correo" in response.data.lower()


def test_forgot_password_post_unknown(client):
    """T219: POST con email desconocido retorna 200 con el mismo mensaje neutral."""
    response = client.post(
        "/auth/forgot-password",
        data={"email": "nobody_unknown@nowhere.com"},
    )
    assert response.status_code == 200
    assert b"enlace" in response.data.lower() or b"correo" in response.data.lower()


def test_reset_password_get_valid_token(client, registered_user):
    """T219: GET /auth/reset-password/<token> valido retorna 200."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel
    from src import create_app
    from src.models import db as _db

    app = client.application
    with app.app_context():
        user = UserModel.query.filter_by(email=registered_user["email"]).first()
        token_obj = PasswordResetToken.generate(user.id)
        _db.session.commit()
        token_str = token_obj.token

    response = client.get(f"/auth/reset-password/{token_str}")
    assert response.status_code == 200


def test_reset_password_get_invalid_token(client):
    """T219: GET con token invalido redirige a forgot-password."""
    response = client.get("/auth/reset-password/invalidtoken123", follow_redirects=False)
    assert response.status_code == 302
    assert "forgot" in response.headers["Location"].lower()


def test_reset_password_post_success(client, registered_user):
    """T219: POST con token valido y password nueva redirige a login."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel
    from src.models import db as _db

    app = client.application
    with app.app_context():
        user = UserModel.query.filter_by(email=registered_user["email"]).first()
        token_obj = PasswordResetToken.generate(user.id)
        _db.session.commit()
        token_str = token_obj.token

    response = client.post(
        f"/auth/reset-password/{token_str}",
        data={"password": "nuevapass99", "confirm_password": "nuevapass99"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_reset_password_post_expired(client, registered_user):
    """T219: POST con token expirado redirige a forgot-password con error."""
    from src.models import PasswordResetToken
    from src.models.user import User as UserModel
    from src.models import db as _db
    from datetime import datetime, timezone, timedelta

    app = client.application
    with app.app_context():
        user = UserModel.query.filter_by(email=registered_user["email"]).first()
        expired = PasswordResetToken(
            user_id=user.id,
            token="expiredintegration" + "y" * 45,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=3),
        )
        _db.session.add(expired)
        _db.session.commit()
        token_str = expired.token

    response = client.post(
        f"/auth/reset-password/{token_str}",
        data={"password": "anypassword99", "confirm_password": "anypassword99"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "forgot" in response.headers["Location"].lower()
