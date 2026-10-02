from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from src.models import Task
from src.services.task_service import TaskService
from src.routes.decorators import login_required

task_bp = Blueprint("tasks", __name__)


def parse_date(date_str):
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


@task_bp.route("", methods=["GET"])
@login_required
def list_tasks():
    status_filter = request.args.get("status")
    tasks = TaskService.get_user_tasks(user_id=g.current_user.id, status_filter=status_filter)
    return render_template(
        "tasks/list.html",
        tasks=tasks,
        current_filter=status_filter or "all",
        allowed_statuses=Task.ALLOWED_STATUSES,
    )


@task_bp.route("/new", methods=["GET"])
@login_required
def new_task():
    return render_template("tasks/create.html")


@task_bp.route("", methods=["POST"])
@login_required
def create_task():
    title = None
    description = None
    due_date_raw = None

    if request.is_json:
        data = request.get_json() or {}
        title = data.get("title")
        description = data.get("description")
        due_date_raw = data.get("due_date")
    elif request.form:
        title = request.form.get("title")
        description = request.form.get("description")
        due_date_raw = request.form.get("due_date")

    due_date = parse_date(due_date_raw)

    task, error = TaskService.create_task(
        user_id=g.current_user.id,
        title=title,
        description=description,
        due_date=due_date,
    )

    if error:
        if request.is_json:
            return jsonify({"error": error}), 400
        flash(error, "danger")
        return render_template("tasks/create.html", title=title, description=description, due_date=due_date_raw), 400

    if request.is_json:
        return jsonify({"message": "Tarea creada exitosamente", "task_id": task.id}), 201

    flash("Tarea creada exitosamente.", "success")
    return redirect(url_for("tasks.list_tasks"))


@task_bp.route("/<int:task_id>/edit", methods=["GET"])
@login_required
def edit_task(task_id):
    task, error = TaskService.get_task_by_id(user_id=g.current_user.id, task_id=task_id)
    if error:
        flash(error, "danger")
        return redirect(url_for("tasks.list_tasks"))

    return render_template("tasks/edit.html", task=task)


@task_bp.route("/<int:task_id>/edit", methods=["POST"])
@login_required
def update_task(task_id):
    title = None
    description = None
    due_date_raw = None

    if request.is_json:
        data = request.get_json() or {}
        title = data.get("title")
        description = data.get("description")
        due_date_raw = data.get("due_date")
    elif request.form:
        title = request.form.get("title")
        description = request.form.get("description")
        due_date_raw = request.form.get("due_date")

    due_date = parse_date(due_date_raw)

    task, error = TaskService.update_task(
        user_id=g.current_user.id,
        task_id=task_id,
        title=title,
        description=description,
        due_date=due_date,
    )

    if error:
        if request.is_json:
            status_code = 403 if "No tiene permiso" in error else 400
            return jsonify({"error": error}), status_code
        flash(error, "danger")
        # Obtenemos la tarea original para no romper el formulario
        original_task, _ = TaskService.get_task_by_id(user_id=g.current_user.id, task_id=task_id)
        return render_template("tasks/edit.html", task=original_task, title=title, description=description), 400

    if request.is_json:
        return jsonify({"message": "Tarea actualizada exitosamente"}), 200

    flash("Tarea actualizada exitosamente.", "success")
    return redirect(url_for("tasks.list_tasks"))


@task_bp.route("/<int:task_id>/status", methods=["POST"])
@login_required
def change_status(task_id):
    new_status = None
    if request.is_json:
        data = request.get_json() or {}
        new_status = data.get("new_status")
    elif request.form:
        new_status = request.form.get("new_status")

    task, error = TaskService.update_task_status(
        user_id=g.current_user.id,
        task_id=task_id,
        new_status=new_status,
    )

    if error:
        if request.is_json or request.headers.get("Accept") == "application/json":
            status_code = 403 if "No tiene permiso" in error else 400
            return jsonify({"error": error}), status_code
        flash(error, "danger")
        return redirect(url_for("tasks.list_tasks"))

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({"message": "Estado actualizado", "status": task.status}), 200

    flash(f"Estado de la tarea actualizado a '{task.status}'.", "success")
    return redirect(url_for("tasks.list_tasks"))


# =============================================================================
# Incremento 2 — HU-05: Eliminación lógica de tarea
# =============================================================================

@task_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    """Soft-delete de una tarea propia (HU-05)."""
    task, error = TaskService.delete_task(user_id=g.current_user.id, task_id=task_id)

    if error:
        flash(error, "danger")
        return redirect(url_for("tasks.list_tasks"))

    flash("Tarea eliminada.", "success")
    return redirect(url_for("tasks.list_tasks"))


# =============================================================================
# Incremento 2 — HU-06: Reapertura de tarea completada
# =============================================================================

@task_bp.route("/<int:task_id>/reopen", methods=["POST"])
@login_required
def reopen_task(task_id):
    """Reabre una tarea completada devolviéndola a in_progress (HU-06)."""
    task, error = TaskService.reopen_task(user_id=g.current_user.id, task_id=task_id)

    if error:
        flash(error, "danger")
        return redirect(url_for("tasks.list_tasks"))

    flash("Tarea reabierta y marcada como en progreso.", "success")
    return redirect(url_for("tasks.list_tasks"))
