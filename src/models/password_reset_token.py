import secrets
from datetime import datetime, timezone, timedelta
from src.models import db


def get_utc_now():
    return datetime.now(timezone.utc)


class PasswordResetToken(db.Model):
    """Token de restablecimiento de contraseña de un solo uso con expiración (HU-14)."""

    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token = db.Column(db.String(64), unique=True, index=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True, default=None)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    user = db.relationship("User", backref=db.backref("reset_tokens", lazy="dynamic"))

    @staticmethod
    def generate(user_id: int, expires_in_hours: int = 1) -> "PasswordResetToken":
        """Crea un token seguro con tiempo de vida configurable (por defecto 1 hora)."""
        token_str = secrets.token_hex(32)  # 64 hex chars
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        token = PasswordResetToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at,
        )
        db.session.add(token)
        return token

    def is_valid(self) -> bool:
        """Devuelve True si el token no expiró y no ha sido usado."""
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        # Normalize timezone: SQLite stores naive datetimes
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return self.used_at is None and expires_at > now

    def mark_used(self) -> None:
        """Invalida el token marcándolo como consumido."""
        self.used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id} valid={self.is_valid()}>"
