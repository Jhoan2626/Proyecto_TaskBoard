from datetime import datetime, timezone
from src.models import db


def get_utc_now():
    return datetime.now(timezone.utc)


class Notification(db.Model):
    """Notificación interna de la aplicación (HU-11).

    Pertenece al usuario destinatario (`user_id`), referencia la tarea que la
    originó y persiste tras leerse (solo cambia `is_read`).
    """

    __tablename__ = "notifications"

    TYPE_TASK_ASSIGNED = "TASK_ASSIGNED"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(30), nullable=False, default=TYPE_TASK_ASSIGNED)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    task = db.relationship("Task", foreign_keys=[task_id])
    actor = db.relationship("User", foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return f"<Notification {self.id} user={self.user_id} task={self.task_id} read={self.is_read}>"
