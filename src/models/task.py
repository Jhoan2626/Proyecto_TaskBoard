from datetime import datetime, timezone
from src.models import db


def get_utc_now():
    return datetime.now(timezone.utc)


class Task(db.Model):
    __tablename__ = "tasks"

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"

    ALLOWED_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED]

    VALID_PRIORITIES = ['alta', 'media', 'baja']
    PRIORITY_SORT_KEY = {'alta': 1, 'media': 2, 'baja': 3}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    # Soft delete (HU-05): NULL = activa; timestamp = eliminada lógicamente
    deleted_at = db.Column(db.DateTime, nullable=True, default=None)
    priority = db.Column(db.String(10), nullable=False, default='media')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    # Incremento 4 (HU-10): usuario asignado. user_id sigue siendo el propietario/creador.
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    VALID_PRIORITIES = ['alta', 'media', 'baja']
    PRIORITY_SORT_KEY = {'alta': 1, 'media': 2, 'baja': 3}

    user = db.relationship("User", back_populates="tasks", foreign_keys=[user_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id])

    @property
    def is_overdue(self) -> bool:
        """Calcula si la tarea está vencida (HU-09).
        Nunca se persiste — es un campo derivado calculado en el backend.
        Una tarea está vencida si: tiene due_date, esa fecha ya pasó (< hoy),
        no está completada y no está eliminada.
        """
        if self.due_date is None:
            return False
        if self.status == self.STATUS_COMPLETED:
            return False
        if self.deleted_at is not None:
            return False
        from datetime import date
        return self.due_date < date.today()

    @property
    def is_overdue(self) -> bool:
        """Calcula si la tarea está vencida (HU-09).
        Nunca se persiste — es un campo derivado calculado en el backend.
        Una tarea está vencida si: tiene due_date, esa fecha ya pasó (< hoy),
        no está completada y no está eliminada.
        """
        if self.due_date is None:
            return False
        if self.status == self.STATUS_COMPLETED:
            return False
        if self.deleted_at is not None:
            return False
        from datetime import date
        return self.due_date < date.today()

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.title} [{self.status}]>"
