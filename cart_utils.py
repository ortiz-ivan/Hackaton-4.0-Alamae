from flask import session

def _get_cart():
    cart = session.get("cart")
    if cart is None:
        cart = {}
        session["cart"] = cart
    return cart

def cart_items():
    return _get_cart()

def add_to_cart(product_id, name, price, qty=1):
    cart = _get_cart()
    product_id = str(product_id)
    if product_id in cart:
        cart[product_id]["qty"] += int(qty)
    else:
        cart[product_id] = {"name": name, "price": float(price), "qty": int(qty)}
    session["cart"] = cart

def remove_from_cart(product_id):
    cart = _get_cart()
    product_id = str(product_id)
    if product_id in cart:
        del cart[product_id]
        session["cart"] = cart

def update_quantity(product_id, qty):
    cart = _get_cart()
    product_id = str(product_id)
    if product_id in cart:
        qty = int(qty)
        if qty <= 0:
            del cart[product_id]
        else:
            cart[product_id]["qty"] = qty
        session["cart"] = cart

def cart_total():
    cart = _get_cart()
    total = 0.0
    for _, item in cart.items():
        total += float(item["price"]) * int(item["qty"])
    return total

def cart_qty():
    return sum(int(v.get("qty", 0)) for v in _get_cart().values())

def clear_cart():
    session["cart"] = {}
