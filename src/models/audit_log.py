from datetime import datetime, timezone
from src.models import db


def get_utc_now():
    return datetime.now(timezone.utc)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    ACTION_TASK_CREATED = "TASK_CREATED"
    ACTION_TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    ACTION_TASK_UPDATED = "TASK_UPDATED"
    # Incremento 2
    ACTION_TASK_DELETED = "TASK_DELETED"      # HU-05: soft delete
    ACTION_TASK_REOPENED = "TASK_REOPENED"    # HU-06: reapertura explícita (distinto de STATUS_CHANGED)

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False, default="Task")
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by Actor:{self.actor_id}>"
