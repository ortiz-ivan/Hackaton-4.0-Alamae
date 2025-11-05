from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import Producto
from cart_utils import add_to_cart, cart_items, update_quantity, remove_from_cart, cart_total, clear_cart, cart_qty

cart_bp = Blueprint("cart", __name__, template_folder="../templates")

@cart_bp.route("/", methods=["GET"], endpoint="index")
def index():
    items = cart_items()
    total = cart_total()
    return render_template("carrito.html", items=items, total=total)

@cart_bp.route("/panel", methods=["GET"], endpoint="panel")
def panel():
    items = cart_items()
    total = cart_total()
    return render_template("partials/cart_panel.html", items=items, total=total)

@cart_bp.route("/qty", methods=["GET"], endpoint="qty")
def qty():
    return jsonify({"qty": cart_qty()})

@cart_bp.route("/add/<int:product_id>", methods=["POST"], endpoint="add")
def add(product_id):
    prod = Producto.query.get_or_404(product_id)
    add_to_cart(prod.id, prod.nombre, float(prod.precio), qty=int(request.form.get("qty", 1)))
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"ok": True, "qty": cart_qty()})
    return redirect(request.referrer or url_for("index"))

@cart_bp.route("/update/<int:product_id>", methods=["POST"], endpoint="update")
def update(product_id):
    qty = int(request.form.get("qty", 1))
    update_quantity(product_id, qty)
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"ok": True, "qty": cart_qty()})
    return redirect(url_for("cart.index"))

@cart_bp.route("/remove/<int:product_id>", methods=["POST"], endpoint="remove")
def remove(product_id):
    remove_from_cart(product_id)
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"ok": True, "qty": cart_qty()})
    return redirect(url_for("cart.index"))

@cart_bp.route("/clear", methods=["POST"], endpoint="clear")
def clear():
    clear_cart()
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"ok": True, "qty": cart_qty()})
    return redirect(url_for("cart.index"))
