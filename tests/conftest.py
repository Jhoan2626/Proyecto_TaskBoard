import pytest
from src import create_app
from src.models import db, User, Task, AuditLog


@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_user(app):
    with app.app_context():
        user = User(email="testuser@example.com")
        user.set_password("securepassword123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "email": user.email, "password": "securepassword123"}


@pytest.fixture
def authenticated_client(client, registered_user):
    client.post(
        "/login",
        data={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    return client
