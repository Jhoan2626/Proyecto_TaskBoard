from datetime import date
from src.models import db, Task, AuditLog
from src.services.audit_service import AuditService


class TaskService:
    # Transiciones válidas permitidas en el Incremento 1 (HU-03)
    VALID_TRANSITIONS = {
        Task.STATUS_PENDING: [Task.STATUS_IN_PROGRESS],
        Task.STATUS_IN_PROGRESS: [Task.STATUS_COMPLETED],
        Task.STATUS_COMPLETED: [],  # Sin reapertura en este incremento
    }

    @staticmethod
    def create_task(
        user_id: int,
        title: str,
        description: str | None = None,
        due_date: date | None = None,
    ) -> tuple[Task | None, str | None]:
        """
        Crea una nueva tarea para el usuario autenticado (HU-01).
        Registra un log de auditoría (Principio VIII).
        """
        if not title or not title.strip():
            return None, "El título de la tarea es obligatorio y no puede estar vacío."

        cleaned_title = title.strip()
        cleaned_desc = description.strip() if description else None

        task = Task(
            user_id=user_id,
            title=cleaned_title,
            description=cleaned_desc,
            due_date=due_date,
            status=Task.STATUS_PENDING,
        )

        db.session.add(task)
        db.session.commit()

        # Registro de auditoría obligatorio
        AuditService.log_event(
            actor_id=user_id,
            action=AuditLog.ACTION_TASK_CREATED,
            entity_type="Task",
            entity_id=task.id,
            details={"title": task.title, "status": task.status},
        )

        return task, None

    @staticmethod
    def get_user_tasks(user_id: int, status_filter: str | None = None) -> list[Task]:
        """
        Lista las tareas pertenecientes exclusivamente al usuario autenticado (HU-02).
        Permite filtrado por estado.
        """
        query = Task.query.filter_by(user_id=user_id)

        if status_filter and status_filter in Task.ALLOWED_STATUSES:
            query = query.filter_by(status=status_filter)

        return query.order_by(Task.created_at.desc()).all()

    @staticmethod
    def get_task_by_id(user_id: int, task_id: int) -> tuple[Task | None, str | None]:
        """
        Obtiene una tarea verificando que pertenezca al usuario (Principio VII).
        """
        task = db.session.get(Task, task_id)
        if not task:
            return None, "Tarea no encontrada."

        if task.user_id != user_id:
            return None, "No tiene permiso para acceder a esta tarea."

        return task, None

    @staticmethod
    def update_task_status(
        user_id: int,
        task_id: int,
        new_status: str,
    ) -> tuple[Task | None, str | None]:
        """
        Realiza la transición de estado de una tarea conforme a las reglas permitidas (HU-03).
        Audita el cambio de estado (Principio VIII).
        """
        task, error = TaskService.get_task_by_id(user_id, task_id)
        if error:
            return None, error

        allowed_next = TaskService.VALID_TRANSITIONS.get(task.status, [])
        if new_status not in allowed_next:
            return None, (
                f"Transición de estado no permitida: no se puede pasar de "
                f"'{task.status}' a '{new_status}'."
            )

        old_status = task.status
        task.status = new_status
        db.session.commit()

        AuditService.log_event(
            actor_id=user_id,
            action=AuditLog.ACTION_TASK_STATUS_CHANGED,
            entity_type="Task",
            entity_id=task.id,
            details={"old_status": old_status, "new_status": new_status},
        )

        return task, None

    @staticmethod
    def update_task(
        user_id: int,
        task_id: int,
        title: str,
        description: str | None = None,
        due_date: date | None = None,
    ) -> tuple[Task | None, str | None]:
        """
        Edita una tarea existente perteneciente al usuario (HU-04).
        """
        task, error = TaskService.get_task_by_id(user_id, task_id)
        if error:
            return None, error

        if not title or not title.strip():
            return None, "El título de la tarea es obligatorio y no puede estar vacío."

        task.title = title.strip()
        task.description = description.strip() if description else None
        task.due_date = due_date

        db.session.commit()

        AuditService.log_event(
            actor_id=user_id,
            action=AuditLog.ACTION_TASK_UPDATED,
            entity_type="Task",
            entity_id=task.id,
            details={"title": task.title},
        )

        return task, None
