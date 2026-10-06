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
    # Incremento 4 (HU-10): usuario asignado. user_id sigue siendo el propietario/creador.
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    user = db.relationship("User", back_populates="tasks", foreign_keys=[user_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id])

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.title} [{self.status}]>"
