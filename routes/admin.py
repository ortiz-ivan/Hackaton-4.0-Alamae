import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Producto, Categoria

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

# ----------------- Helpers / Guards -----------------
def admin_required():
    if not current_user.is_authenticated:
        abort(401)
    admins = current_app.config.get("ADMIN_EMAILS", {"admin@faigothy.com"})
    if current_user.email not in admins:
        abort(403)

@admin_bp.before_request
def gate():
    # Solo filtra las rutas del blueprint admin
    if request.endpoint and request.endpoint.startswith("admin."):
        admin_required()

def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    allowed = current_app.config.get("ALLOWED_EXTENSIONS") or {"png","jpg","jpeg","gif","webp","avif"}
    return ext in allowed

# ----------------- Dashboard -----------------
@admin_bp.route("/", endpoint="dashboard")
@login_required
def dashboard():
    prod_count = db.session.query(Producto).count()
    cat_count = db.session.query(Categoria).count()
    return render_template("admin/dashboard.html", prod_count=prod_count, cat_count=cat_count)

# ----------------- Productos -----------------
# Listado (endpoint: admin.products)
@admin_bp.route("/product", endpoint="products")
@login_required
def product_list():
    productos = Producto.query.order_by(Producto.id.desc()).all()
    cats = {c.id: c for c in Categoria.query.all()}
    return render_template("admin/product_list.html", productos=productos, cats=cats)

# Nuevo (endpoint: admin.product_new)
@admin_bp.route("/product/new", methods=["GET", "POST"], endpoint="product_new")
@login_required
def product_new():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", "0").strip()
        categoria_id = int(request.form.get("categoria_id", "0") or 0)
        activo = bool(request.form.get("activo"))
        imagen_file = request.files.get("imagen")

        filename = ""
        if imagen_file and imagen_file.filename:
            if not allowed_file(imagen_file.filename):
                flash("Formato de imagen no permitido.", "danger")
                return render_template("admin/product_form.html", categorias=categorias, product=None, form=request.form)
            filename = secure_filename(imagen_file.filename)
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # Evitar sobrescribir
            base, ext = os.path.splitext(filename)
            i = 1
            while os.path.exists(save_path):
                filename = f"{base}-{i}{ext}"
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                i += 1
            imagen_file.save(save_path)

        p = Producto(
            nombre=nombre,
            descripcion=descripcion,
            imagen=filename,
            precio=precio,
            categoria_id=categoria_id,
            activo=activo,
        )
        db.session.add(p)
        db.session.commit()
        flash("Producto creado.", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", categorias=categorias, product=None)

# Editar (endpoint: admin.product_edit) => usa product_id (no pid)
@admin_bp.route("/product/<int:product_id>/edit", methods=["GET", "POST"], endpoint="product_edit")
@login_required
def product_edit(product_id):
    p = Producto.query.get_or_404(product_id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    if request.method == "POST":
        p.nombre = request.form.get("nombre", "").strip()
        p.descripcion = request.form.get("descripcion", "").strip()
        p.precio = request.form.get("precio", "0").strip()
        p.categoria_id = int(request.form.get("categoria_id", "0") or 0)
        p.activo = bool(request.form.get("activo"))

        imagen_file = request.files.get("imagen")
        if imagen_file and imagen_file.filename:
            if not allowed_file(imagen_file.filename):
                flash("Formato de imagen no permitido.", "danger")
                return render_template("admin/product_form.html", categorias=categorias, product=p, p=p)
            filename = secure_filename(imagen_file.filename)
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            base, ext = os.path.splitext(filename)
            i = 1
            while os.path.exists(save_path):
                filename = f"{base}-{i}{ext}"
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                i += 1
            imagen_file.save(save_path)
            p.imagen = filename  # actualiza referencia

        db.session.commit()
        flash("Producto actualizado.", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", categorias=categorias, product=p, p=p)

# Eliminar (endpoint: admin.product_delete) => usa product_id (no pid)
@admin_bp.route("/product/<int:product_id>/delete", methods=["POST"], endpoint="product_delete")
@login_required
def product_delete(product_id):
    p = Producto.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    flash("Producto eliminado.", "success")
    return redirect(url_for("admin.products"))

# ----------------- Categorías -----------------
# Listado (endpoint: admin.categories)
@admin_bp.route("/category", endpoint="categories")
@login_required
def category_list():
    categorias = Categoria.query.order_by(Categoria.id).all()
    return render_template("admin/category_list.html", categorias=categorias)

# Nueva
@admin_bp.route("/category/new", methods=["GET", "POST"], endpoint="category_new")
@login_required
def category_new():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        slug = request.form.get("slug", "").strip()
        if not nombre or not slug:
            flash("Nombre y slug son obligatorios.", "danger")
            return render_template("admin/category_form.html", form=request.form)
        if Categoria.query.filter_by(slug=slug).first():
            flash("Ese slug ya existe.", "danger")
            return render_template("admin/category_form.html", form=request.form)
        db.session.add(Categoria(nombre=nombre, slug=slug))
        db.session.commit()
        flash("Categoría creada.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html")

# Editar
@admin_bp.route("/category/<int:category_id>/edit", methods=["GET", "POST"], endpoint="category_edit")
@login_required
def category_edit(category_id):
    c = Categoria.query.get_or_404(category_id)
    if request.method == "POST":
        c.nombre = request.form.get("nombre", "").strip()
        c.slug = request.form.get("slug", "").strip()
        db.session.commit()
        flash("Categoría actualizada.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", c=c)

# Eliminar
@admin_bp.route("/category/<int:category_id>/delete", methods=["POST"], endpoint="category_delete")
@login_required
def category_delete(category_id):
    c = Categoria.query.get_or_404(category_id)
    db.session.delete(c)
    db.session.commit()
    flash("Categoría eliminada.", "success")
    return redirect(url_for("admin.categories"))