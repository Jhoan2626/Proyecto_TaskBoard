import json
import logging
from src.models import db, AuditLog

logger = logging.getLogger("audit")


class AuditService:
    @staticmethod
    def log_event(
        actor_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        details: dict | str | None = None,
    ) -> AuditLog:
        """
        Registra un evento de auditoría de forma estructurada e inmutable
        según lo estipulado en el Principio VIII de la Constitución.
        """
        details_str = None
        if isinstance(details, dict):
            details_str = json.dumps(details)
        elif isinstance(details, str):
            details_str = details

        audit_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details_str,
        )

        db.session.add(audit_entry)
        db.session.commit()

        logger.info(
            "AUDIT_EVENT: actor=%s action=%s entity=%s:%s timestamp=%s",
            actor_id,
            action,
            entity_type,
            entity_id,
            audit_entry.timestamp.isoformat(),
        )

        return audit_entry
