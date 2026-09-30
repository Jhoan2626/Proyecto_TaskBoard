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
