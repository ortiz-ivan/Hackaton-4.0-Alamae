import os
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, current_user
from models import db, User, Producto, Categoria
from cart_utils import cart_items, cart_total  # no dependemos de cart_qty para evitar errores

def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    # === Config Admin por email (podés moverlo a config.py si preferís) ===
    app.config.setdefault("ADMIN_EMAILS", {"admin@faigothy.com"})

    # === Subida de imágenes (admin) ===
    app.config.setdefault("UPLOAD_FOLDER", os.path.join(app.root_path, "static", "img"))
    app.config.setdefault("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp", "avif"})
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # === DB ===
    db.init_app(app)

    # === Login manager ===
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # === Variables disponibles en todos los templates ===
    @app.context_processor
    def inject_globals():
        # Cantidad de ítems del carrito desde sesión (server-side)
        try:
            items = cart_items()  # dict {product_id: {name, price, qty}}
            cart_qty = sum((v.get("qty", 0) for v in items.values()))
        except Exception:
            cart_qty = 0

        admin_emails = app.config.get("ADMIN_EMAILS", set())
        is_admin = bool(current_user.is_authenticated and current_user.email in admin_emails)

        return {
            "SITE_TITLE": "FAIGOTHY ✶ accesorios hechos a mano",
            "CART_QTY": cart_qty,
            "IS_ADMIN": is_admin,
        }

    # === Blueprints ===
    from routes.cart import cart_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    app.register_blueprint(cart_bp, url_prefix="/carrito")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # === Rutas ===
    @app.route("/", endpoint="index")
    def index():
        # Novedades (24 últimos activos)
        latest_products = (
            Producto.query.filter_by(activo=True)
            .order_by(Producto.id.desc())
            .limit(24)
            .all()
        )

        # Carruseles por categoría (12 por categoría)
        slugs = ["accesorios-pelo", "aros", "anillos", "cinturones", "collares", "prendas"]
        cats = {c.slug: c for c in Categoria.query.filter(Categoria.slug.in_(slugs)).all()}
        productos_by_cat = {}
        for slug in slugs:
            cat = cats.get(slug)
            productos_by_cat[slug] = (
                Producto.query.filter_by(categoria_id=cat.id, activo=True)
                .order_by(Producto.id.desc())
                .limit(12)
                .all()
                if cat else []
            )

        return render_template(
            "index.html",
            latest_products=latest_products,
            productos_by_cat=productos_by_cat,
        )

    @app.route("/checkout")
    def checkout():
        if not current_user.is_authenticated:
            if request.args.get("partial"):
                return render_template("partials/login_form.html")
            return redirect(url_for("auth.login"))
        items = cart_items()
        total = cart_total()
        return render_template("checkout.html", items=items, total=total)

    # Aliases por conveniencia
    @app.route("/login")
    def login_alias():
        return redirect(url_for("auth.login"))

    @app.route("/register")
    def register_alias():
        return redirect(url_for("auth.register"))

    return app


# Ejecutable directo de desarrollo
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)