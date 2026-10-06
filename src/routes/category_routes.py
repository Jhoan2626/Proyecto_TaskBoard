from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from src.services.category_service import CategoryService
from src.routes.decorators import login_required

category_bp = Blueprint('categories', __name__)

@category_bp.route('', methods=['GET'])
@login_required
def list_categories():
    categories = CategoryService.get_user_categories(g.current_user.id)
    return render_template('categories/list.html', categories=categories)


@category_bp.route('', methods=['POST'])
@login_required
def create_category():
    name = request.form.get('name', '')
    cat, error = CategoryService.create_category(user_id=g.current_user.id, name=name)
    if error:
        flash(error, 'danger')
        categories = CategoryService.get_user_categories(g.current_user.id)
        return render_template('categories/list.html', categories=categories), 400
    flash(f"Categoría '{cat.name}' creada.", 'success')
    return redirect(url_for('categories.list_categories'))


@category_bp.route('/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    _, error = CategoryService.delete_category(user_id=g.current_user.id, category_id=category_id)
    if error:
        flash(error, 'danger')
        return redirect(url_for('categories.list_categories'))
    flash('Categoría eliminada. Las tareas asociadas permanecen sin categoría.', 'success')
    return redirect(url_for('categories.list_categories'))

