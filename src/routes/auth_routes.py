from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from src.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("tasks.list_tasks"))

    if request.method == "POST":
        email = request.form.get("email") if request.form else None
        password = request.form.get("password") if request.form else None

        if request.is_json:
            data = request.get_json() or {}
            email = data.get("email")
            password = data.get("password")

        user, error = AuthService.register_user(email=email, password=password)

        if error:
            if request.is_json:
                status_code = 409 if "ya está registrado" in error else 400
                return jsonify({"error": error}), status_code
            flash(error, "danger")
            return render_template("auth/register.html", email=email), 400

        if request.is_json:
            return jsonify({"message": "Usuario registrado exitosamente", "user_id": user.id}), 201

        flash("Registro exitoso. Por favor inicie sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("tasks.list_tasks"))

    if request.method == "POST":
        email = request.form.get("email") if request.form else None
        password = request.form.get("password") if request.form else None

        if request.is_json:
            data = request.get_json() or {}
            email = data.get("email")
            password = data.get("password")

        user, error = AuthService.authenticate_user(email=email, password=password)

        if error:
            if request.is_json:
                return jsonify({"error": error}), 401
            flash(error, "danger")
            return render_template("auth/login.html", email=email), 401

        session.clear()
        session["user_id"] = user.id

        if request.is_json:
            return jsonify({"message": "Inicio de sesión exitoso", "user_id": user.id}), 200

        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("tasks.list_tasks")

        return redirect(next_page)

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


# =============================================================================
# Incremento 2 — HU-14: Recuperación de contraseña
# =============================================================================

@auth_bp.route("/auth/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Muestra y procesa el formulario de solicitud de restablecimiento (HU-14)."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email or "@" not in email:
            flash("Por favor ingrese un correo electrónico válido.", "danger")
            return render_template("auth/forgot_password.html", email=email), 200

        # Siempre responde neutral (Principio VII — no revela si el email existe)
        AuthService.request_password_reset(email)
        flash(
            "Si ese correo está registrado, recibirás un enlace en breve. "
            "Revisa también tu carpeta de spam.",
            "info",
        )
        return render_template("auth/forgot_password.html"), 200

    return render_template("auth/forgot_password.html")


@auth_bp.route("/auth/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Muestra y procesa el formulario para establecer nueva contraseña (HU-14)."""
    from src.models import PasswordResetToken

    # Pre-validar token antes de mostrar el formulario
    token_obj = PasswordResetToken.query.filter_by(token=token).first()
    if not token_obj or not token_obj.is_valid():
        flash("El enlace de restablecimiento es inválido o ha expirado.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("auth/reset_password.html", token=token), 200

        success, error = AuthService.reset_password(token, password)

        if error:
            flash(error, "danger")
            if "inválido" in error or "expirado" in error:
                return redirect(url_for("auth.forgot_password"))
            return render_template("auth/reset_password.html", token=token), 200

        flash("Contraseña actualizada. Por favor inicia sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
