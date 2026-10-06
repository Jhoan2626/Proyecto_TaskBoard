from src.models import db, Task, User, AuditLog, Notification
from src.services.audit_service import AuditService


class AssignmentService:
    """Asignación de tareas a otros usuarios (HU-10) con notificación interna (HU-11).

    La asignación, la notificación y el registro de auditoría se confirman en
    una única transacción (un solo commit), de modo que son atómicos.
    """

    @staticmethod
    def assign_task(
        actor_id: int,
        task_id: int,
        assignee_email: str | None,
    ) -> tuple[Task | None, str | None]:
        """
        Asigna/reasigna una tarea propia a un usuario registrado por correo.
        Si `assignee_email` está vacío, retira la asignación (sin notificación).
        Validación 100 % en backend (Principio VII).
        """
        task = db.session.get(Task, task_id)
        if not task:
            return None, "Tarea no encontrada."
        if task.user_id != actor_id:
            return None, "No tiene permiso para acceder a esta tarea."
        if task.deleted_at is not None:
            return None, "La tarea ha sido eliminada y no se puede operar sobre ella."

        email = (assignee_email or "").strip().lower()
        old_assignee_id = task.assignee_id

        # Desasignación
        if not email:
            if old_assignee_id is None:
                return None, "La tarea no tiene un usuario asignado."
            task.assignee_id = None
            AuditService.log_event(  # commit único
                actor_id=actor_id,
                action=AuditLog.ACTION_TASK_ASSIGNED,
                entity_type="Task",
                entity_id=task.id,
                details={"old_assignee_id": old_assignee_id, "new_assignee_id": None},
            )
            return task, None

        assignee = User.query.filter_by(email=email).first()
        if assignee is None:
            return None, "El usuario destino no está registrado en el sistema."
        if assignee.id == actor_id:
            return None, "No puede asignarse una tarea a sí mismo; ya es el propietario."
        if old_assignee_id == assignee.id:
            return None, "La tarea ya está asignada a ese usuario."

        task.assignee_id = assignee.id
        actor = db.session.get(User, actor_id)
        db.session.add(
            Notification(
                user_id=assignee.id,
                task_id=task.id,
                actor_id=actor_id,
                type=Notification.TYPE_TASK_ASSIGNED,
                message=f"{actor.email} te asignó la tarea \"{task.title}\".",
            )
        )
        # log_event hace commit de la asignación + notificación + auditoría juntas.
        AuditService.log_event(
            actor_id=actor_id,
            action=AuditLog.ACTION_TASK_ASSIGNED,
            entity_type="Task",
            entity_id=task.id,
            details={"old_assignee_id": old_assignee_id, "new_assignee_id": assignee.id},
        )
        return task, None
