import pytest
from src.models import db
from src.services.category_service import CategoryService


def test_list_categories_route(authenticated_client):
    """GET /categories retorna 200."""
    response = authenticated_client.get('/categories')
    assert response.status_code == 200


def test_create_category_route(authenticated_client):
    """POST /categories crea categoría y redirige."""
    response = authenticated_client.post('/categories', data={'name': 'Proyecto Alpha'},
                           follow_redirects=True)
    assert response.status_code == 200
    with authenticated_client.application.app_context():
        from src.models import Category
        cat = Category.query.filter_by(name='Proyecto Alpha').first()
        assert cat is not None


def test_delete_category_route(authenticated_client):
    """POST /categories/<id>/delete elimina categoría y las tareas persisten."""
    # Crear categoría y tarea
    authenticated_client.post('/categories', data={'name': 'Para Borrar'})
    with authenticated_client.application.app_context():
        from src.models import Category
        cat = Category.query.filter_by(name='Para Borrar').first()
        cat_id = cat.id

    authenticated_client.post('/tasks', data={'title': 'Tarea en cat borrable'})
    with authenticated_client.application.app_context():
        from src.models import Task
        task = Task.query.filter_by(title='Tarea en cat borrable').first()
        task_id = task.id
        # Asignar categoría directo en BD
        task.category_id = cat_id
        db.session.commit()

    # Eliminar categoría
    response = authenticated_client.post(f'/categories/{cat_id}/delete', follow_redirects=True)
    assert response.status_code == 200

    with authenticated_client.application.app_context():
        from src.models import Task, Category
        assert db.session.get(Category, cat_id) is None
        task = db.session.get(Task, task_id)
        assert task is not None
        assert task.category_id is None


def test_filter_tasks_by_category_route(authenticated_client):
    """GET /tasks?category_id=<id> filtra correctamente."""
    authenticated_client.post('/categories', data={'name': 'Filtro Cat'})
    with authenticated_client.application.app_context():
        from src.models import Category
        cat = Category.query.filter_by(name='Filtro Cat').first()
        cat_id = cat.id

    response = authenticated_client.get(f'/tasks?category_id={cat_id}')
    assert response.status_code == 200
