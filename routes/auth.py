from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from models import db, User

auth_bp = Blueprint("auth", __name__, template_folder="../templates")

@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("¡Bienvenido/a!", "success")
            return redirect(url_for("index"))
        flash("Email o contraseña inválidos", "danger")
    if request.args.get("partial"):
        return render_template("partials/login_form.html")
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if not nombre or not email or not password:
            return render_template("register.html", error="Completa todos los campos.")
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="Ese email ya está registrado.")
        user = User(nombre=nombre, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("index"))
    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
