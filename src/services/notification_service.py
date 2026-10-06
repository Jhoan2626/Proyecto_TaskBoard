from src.models import db, Notification


class NotificationService:
    @staticmethod
    def list_for_user(user_id: int, unread_only: bool = False) -> list[Notification]:
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc(), Notification.id.desc()).all()

    @staticmethod
    def unread_count(user_id: int) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def mark_as_read(user_id: int, notification_id: int) -> tuple[Notification | None, str | None]:
        """Marca como leída (la notificación persiste). Solo su destinatario puede hacerlo."""
        notification = db.session.get(Notification, notification_id)
        if not notification:
            return None, "Notificación no encontrada."
        if notification.user_id != user_id:
            return None, "No tiene permiso para acceder a esta notificación."
        notification.is_read = True
        db.session.commit()
        return notification, None

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        count = Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
        db.session.commit()
        return count
