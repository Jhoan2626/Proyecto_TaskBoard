from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash, g
from src.models import db, User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"error": "Autenticación requerida"}), 401
            flash("Debe iniciar sesión para acceder a este recurso.", "warning")
            return redirect(url_for("auth.login", next=request.path))

        user = db.session.get(User, user_id)
        if not user:
            session.clear()
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"error": "Sesión inválida"}), 401
            flash("Sesión no válida. Inicie sesión nuevamente.", "warning")
            return redirect(url_for("auth.login"))

        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function
