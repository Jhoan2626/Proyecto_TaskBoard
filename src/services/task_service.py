from datetime import date, datetime, timezone
from sqlalchemy import or_
from src.models import db, Task, AuditLog
from src.services.audit_service import AuditService


class TaskService:
    # Transiciones válidas en Incremento 1 (HU-03).
    # La reapertura desde 'completed' se maneja con reopen_task (HU-06), no aquí.
    VALID_TRANSITIONS = {
        Task.STATUS_PENDING: [Task.STATUS_IN_PROGRESS],
        Task.STATUS_IN_PROGRESS: [Task.STATUS_COMPLETED],
        Task.STATUS_COMPLETED: [],  # Sin transición ordinaria; usa reopen_task para reapertura
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
    def get_user_tasks(
        user_id: int,
        status_filter: str | None = None,
        sort_by: str | None = None,
        category_id: int | None = None,
        scope: str | None = None,
    ) -> list[Task]:
        """
        Lista las tareas activas del usuario autenticado (HU-02).
        Incluye tareas propias y asignadas (HU-10), excluyendo eliminadas (HU-05).
        Acepta filtros de estado (HU-02), categoría (HU-08) y prioridad (HU-07).
        `scope`: 'mine' (solo propias), 'assigned' (solo asignadas a mí); otro = ambas.
        """
        if scope == "mine":
            ownership = Task.user_id == user_id
        elif scope == "assigned":
            ownership = Task.assignee_id == user_id
        else:
            ownership = or_(Task.user_id == user_id, Task.assignee_id == user_id)

        query = Task.query.filter(ownership).filter(Task.deleted_at == None)  # noqa: E711

        if status_filter and status_filter in Task.ALLOWED_STATUSES:
            query = query.filter_by(status=status_filter)

        if category_id is not None:
            query = query.filter_by(category_id=category_id)

        tasks = query.order_by(Task.created_at.desc()).all()

        if sort_by == "priority":
            tasks = sorted(tasks, key=lambda t: Task.PRIORITY_SORT_KEY.get(t.priority, 99))

        return tasks
    @staticmethod
    def get_task_by_id(user_id: int, task_id: int) -> tuple[Task | None, str | None]:
        """
        Obtiene una tarea verificando que pertenezca al usuario (Principio VII).
        Rechaza tareas eliminadas lógicamente (HU-05).
        """
        task = db.session.get(Task, task_id)
        if not task:
            return None, "Tarea no encontrada."

        if task.user_id != user_id:
            return None, "No tiene permiso para acceder a esta tarea."

        if task.deleted_at is not None:
            return None, "La tarea ha sido eliminada y no se puede operar sobre ella."

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

    # -------------------------------------------------------------------------
    # Incremento 2 — HU-05: Eliminación lógica (Soft Delete)
    # -------------------------------------------------------------------------

    @staticmethod
    def delete_task(user_id: int, task_id: int) -> tuple[Task | None, str | None]:
        """
        Elimina lógicamente una tarea propia estampando deleted_at (HU-05).
        La tarea deja de aparecer en el listado por defecto.
        Audita el evento con TASK_DELETED (Principio VIII).
        """
        # Verificar propiedad (get_task_by_id ya rechaza eliminadas)
        task = db.session.get(Task, task_id)
        if not task:
            return None, "Tarea no encontrada."
        if task.user_id != user_id:
            return None, "No tiene permiso para acceder a esta tarea."
        if task.deleted_at is not None:
            return None, "La tarea ya fue eliminada."

        task.deleted_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            actor_id=user_id,
            action=AuditLog.ACTION_TASK_DELETED,
            entity_type="Task",
            entity_id=task.id,
            details={"title": task.title, "deleted_at": task.deleted_at.isoformat()},
        )

        return task, None

    # -------------------------------------------------------------------------
    # Incremento 2 — HU-06: Reapertura de tareas completadas
    # -------------------------------------------------------------------------

    @staticmethod
    def reopen_task(user_id: int, task_id: int) -> tuple[Task | None, str | None]:
        """
        Reabre una tarea completada devolviéndola a in_progress (HU-06).
        Registra un evento TASK_REOPENED (distinto de TASK_STATUS_CHANGED)
        para que el historial de auditoría permita distinguir la reapertura.
        """
        task, error = TaskService.get_task_by_id(user_id, task_id)
        if error:
            return None, error

        if task.status != Task.STATUS_COMPLETED:
            return None, "Solo se pueden reabrir tareas completadas."

        old_status = task.status
        task.status = Task.STATUS_IN_PROGRESS
        db.session.commit()

        AuditService.log_event(
            actor_id=user_id,
            action=AuditLog.ACTION_TASK_REOPENED,
            entity_type="Task",
            entity_id=task.id,
            details={"old_status": old_status, "new_status": task.status},
        )

        return task, None

    # -------------------------------------------------------------------------
    # Incremento 3 — HU-07: Prioridad de tareas
    # -------------------------------------------------------------------------

    @staticmethod
    def update_task_priority(
        user_id: int,
        task_id: int,
        priority: str,
    ) -> tuple:
        """
        Cambia la prioridad de una tarea propia (HU-07).
        Registra auditoría con TASK_PRIORITY_CHANGED (Principio VIII).
        """
        if priority not in Task.VALID_PRIORITIES:
            return None, (
                f"Prioridad inválida '{priority}'. "
                f"Valores permitidos: {', '.join(Task.VALID_PRIORITIES)}."
            )

        task, error = TaskService.get_task_by_id(user_id, task_id)
        if error:
            return None, error

        old_priority = task.priority
        task.priority = priority
        db.session.commit()

        AuditService.log_event(
            actor_id=user_id,
            action=AuditLog.ACTION_TASK_PRIORITY_CHANGED,
            entity_type='Task',
            entity_id=task.id,
            details={'old_priority': old_priority, 'new_priority': priority},
        )

        return task, None

    # -------------------------------------------------------------------------
    # Incremento 3 — HU-08: Categorías de tareas
    # -------------------------------------------------------------------------

    @staticmethod
    def assign_category(
        user_id: int,
        task_id: int,
        category_id: int | None,
    ) -> tuple:
        """
        Asigna o desasigna una categoría a una tarea propia (HU-08).
        Si category_id es None, desasigna la categoría actual.
        Verifica que la categoría pertenezca al mismo usuario (Principio VII).
        """
        task, error = TaskService.get_task_by_id(user_id, task_id)
        if error:
            return None, error

        if category_id is not None:
            from src.models import Category
            cat = db.session.get(Category, category_id)
            if not cat or cat.user_id != user_id:
                return None, 'Categoría no válida o no pertenece al usuario.'

        task.category_id = category_id
        db.session.commit()
        return task, None
