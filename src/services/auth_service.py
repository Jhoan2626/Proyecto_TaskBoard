from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timezone
from flask import current_app
from src.models import db, User
from src.models.password_reset_token import PasswordResetToken


class AuthService:
    @staticmethod
    def register_user(email: str, password: str) -> tuple[User | None, str | None]:
        """
        Registra un nuevo usuario validando formato y unicidad de correo,
        y almacenando la contraseña con hash seguro (HU-12).
        """
        if not email or not email.strip():
            return None, "El correo electrónico es obligatorio."

        cleaned_email = email.strip().lower()

        try:
            valid_info = validate_email(cleaned_email, check_deliverability=False)
            cleaned_email = valid_info.normalized
        except EmailNotValidError:
            return None, "Por favor ingrese un correo electrónico válido."

        if not password or len(password) < 6:
            return None, "La contraseña debe tener al menos 6 caracteres."

        existing_user = User.query.filter_by(email=cleaned_email).first()
        if existing_user:
            return None, "El correo electrónico ya está registrado."

        new_user = User(email=cleaned_email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return new_user, None

    @staticmethod
    def authenticate_user(email: str, password: str) -> tuple[User | None, str | None]:
        """
        Autentica credenciales de usuario contra hash seguro (HU-13).
        """
        if not email or not password:
            return None, "Credenciales inválidas."

        cleaned_email = email.strip().lower()
        user = User.query.filter_by(email=cleaned_email).first()

        if not user or not user.check_password(password):
            return None, "Credenciales inválidas."

        return user, None

    # -------------------------------------------------------------------------
    # Incremento 2 — HU-14: Recuperación de contraseña
    # -------------------------------------------------------------------------

    @staticmethod
    def request_password_reset(email: str) -> tuple[bool, str | None]:
        """
        Genera un token de restablecimiento de contraseña para el email dado (HU-14).
        La respuesta es SIEMPRE (True, None) para no revelar si el email existe
        (Principio VII — seguridad por defecto).
        En desarrollo, el enlace se imprime en el log de Flask.
        """
        if not email or not email.strip():
            return True, None

        cleaned_email = email.strip().lower()
        user = User.query.filter_by(email=cleaned_email).first()

        if user:
            token_obj = PasswordResetToken.generate(user.id)
            db.session.commit()
            # Simulación de correo en desarrollo (Principio V — sin SMTP real en alcance académico)
            try:
                current_app.logger.info(
                    f"[DEV] Password reset link for {cleaned_email}: "
                    f"/auth/reset-password/{token_obj.token}"
                )
            except RuntimeError:
                pass  # Fuera de contexto de app (ej. tests sin push_context)

        return True, None

    @staticmethod
    def reset_password(token_str: str, new_password: str) -> tuple[bool, str | None]:
        """
        Aplica una nueva contraseña usando el token de restablecimiento (HU-14).
        Valida: token existe, no expirado, no usado.
        Invalida el token estampando used_at tras el uso exitoso.
        """
        if not token_str:
            return False, "Token inválido."

        token_obj = PasswordResetToken.query.filter_by(token=token_str).first()
        if not token_obj or not token_obj.is_valid():
            return False, "El enlace de restablecimiento es inválido o ha expirado."

        if not new_password or len(new_password) < 8:
            return False, "La nueva contraseña debe tener al menos 8 caracteres."

        user = db.session.get(User, token_obj.user_id)
        if not user:
            return False, "Usuario no encontrado."

        user.set_password(new_password)
        token_obj.mark_used()
        db.session.commit()

        return True, None
