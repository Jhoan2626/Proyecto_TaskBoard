from email_validator import validate_email, EmailNotValidError
from src.models import db, User


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
