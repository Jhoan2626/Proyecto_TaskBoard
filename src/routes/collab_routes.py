from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from src.services.assignment_service import AssignmentService
from src.services.notification_service import NotificationService
from src.routes.decorators import login_required

collab_bp = Blueprint("collab", __name__)


def _wants_json() -> bool:
    return request.is_json or request.headers.get("Accept") == "application/json"


def _error_status(error: str) -> int:
    if "No tiene permiso" in error:
        return 403
    if "no encontrad" in error:
        return 404
    return 400


@collab_bp.route("/tasks/<int:task_id>/assign", methods=["POST"])
@login_required
def assign_task(task_id):
    """Asigna/reasigna (email) o desasigna (email vacío) una tarea propia (HU-10)."""
    email = None
    if request.is_json:
        email = (request.get_json(silent=True) or {}).get("assignee_email")
    elif request.form:
        email = request.form.get("assignee_email")

    task, error = AssignmentService.assign_task(
        actor_id=g.current_user.id, task_id=task_id, assignee_email=email
    )

    if error:
        if _wants_json():
            return jsonify({"error": error}), _error_status(error)
        flash(error, "danger")
        return redirect(url_for("tasks.list_tasks"))

    if _wants_json():
        return jsonify({"message": "Asignación actualizada", "assignee_id": task.assignee_id}), 200
    flash("Asignación actualizada.", "success")
    return redirect(url_for("tasks.list_tasks"))


@collab_bp.route("/notifications", methods=["GET"])
@login_required
def list_notifications():
    unread_only = request.args.get("unread") == "1"
    notifications = NotificationService.list_for_user(g.current_user.id, unread_only=unread_only)

    if _wants_json():
        return jsonify(
            {
                "unread_count": NotificationService.unread_count(g.current_user.id),
                "notifications": [
                    {
                        "id": n.id,
                        "task_id": n.task_id,
                        "type": n.type,
                        "message": n.message,
                        "is_read": n.is_read,
                        "created_at": n.created_at.isoformat(),
                    }
                    for n in notifications
                ],
            }
        ), 200

    return render_template(
        "notifications/list.html", notifications=notifications, unread_only=unread_only
    )


@collab_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    notification, error = NotificationService.mark_as_read(g.current_user.id, notification_id)

    if error:
        if _wants_json():
            return jsonify({"error": error}), _error_status(error)
        flash(error, "danger")
        return redirect(url_for("collab.list_notifications"))

    if _wants_json():
        return jsonify({"message": "Notificación marcada como leída", "is_read": True}), 200
    return redirect(url_for("collab.list_notifications"))


@collab_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    count = NotificationService.mark_all_as_read(g.current_user.id)
    if _wants_json():
        return jsonify({"message": "Notificaciones marcadas como leídas", "updated": count}), 200
    return redirect(url_for("collab.list_notifications"))


@collab_bp.app_context_processor
def inject_unread_notifications():
    user = getattr(g, "current_user", None)
    if user is None:
        return {"unread_notifications": 0}
    return {"unread_notifications": NotificationService.unread_count(user.id)}
