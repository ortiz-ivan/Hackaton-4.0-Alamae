
from app import create_app
from models import db, Categoria, Producto, User
from werkzeug.security import generate_password_hash
from decimal import Decimal

app = create_app()

EXAMPLE_CATEGORIES = [
    ("Accesorios para el pelo","accesorios-pelo"),
    ("Aros","aros"),
    ("Anillos","anillos"),
    ("Cinturones","cinturones"),
    ("Collares","collares"),
    ("Prendas de vestir","prendas"),
]

EXAMPLE_PRODUCTS = {
    "accesorios-pelo":[
        ("Diadema Punk Faigothy", "Accesorio artesanal", "25000"),
        ("Coletero Satén", "Coletero suave", "8000"),
        ("Pinza Perla", "Pinza con perlas", "7000"),
    ],
    "aros":[
        ("Aros Dorados", "Par de aros dorados", "12000"),
        ("Aros Plata", "Par de aros plata", "11000"),
        ("Aros Cruz Gótica", "Aros con cruz", "14000"),
    ],
    "anillos":[
        ("Anillo Rosa", "Anillo artesanal", "14000"),
        ("Anillo Luna Negra", "Anillo con luna", "15000"),
        ("Anillo Estrella", "Anillo estrella", "14500"),
    ],
    "cinturones":[
        ("Cinturón Cuero", "Cinturón de cuero", "20000"),
        ("Cinturón Gótico", "Con tachas", "22000"),
        ("Cinturón Doble Cadena", "Doble cadena", "23000"),
    ],
    "collares":[
        ("Collar Perla", "Collar delicado", "18000"),
        ("Collar Cruz", "Cruz gótica", "17500"),
        ("Collar Corazón Oscuro", "Corazón oscuro", "18500"),
    ],
    "prendas":[
        ("Top Encaje", "Top de encaje", "22000"),
        ("Corset Negro", "Corset clásico", "26000"),
        ("Falda Volados", "Falda con volados", "25000"),
    ]
}

ADMIN_EMAIL = "admin@faigothy.com"
ADMIN_NAME  = "Admin"
ADMIN_PASS  = "admin123"  # cámbialo luego

with app.app_context():
    db.create_all()

    # Categorías
    slug_to_cat = {}
    for nombre, slug in EXAMPLE_CATEGORIES:
        cat = Categoria.query.filter_by(slug=slug).first()
        if not cat:
            cat = Categoria(nombre=nombre, slug=slug)
            db.session.add(cat)
            db.session.flush()
        slug_to_cat[slug] = cat
    db.session.commit()

    # Productos
    for slug, items in EXAMPLE_PRODUCTS.items():
        cat = slug_to_cat.get(slug)
        if not cat:
            continue
        for nombre, descripcion, precio in items:
            exists = Producto.query.filter_by(nombre=nombre, categoria_id=cat.id).first()
            if not exists:
                db.session.add(Producto(
                    nombre=nombre,
                    descripcion=descripcion,
                    imagen="",  # sin imagen por ahora
                    precio=Decimal(precio),
                    categoria_id=cat.id,
                    activo=True
                ))
    db.session.commit()

    # Usuario admin
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        admin = User(nombre=ADMIN_NAME, email=ADMIN_EMAIL, password_hash=generate_password_hash(ADMIN_PASS))
        db.session.add(admin)
        db.session.commit()
        print(f"[OK] Admin creado: {ADMIN_EMAIL} / {ADMIN_PASS} (cámbialo)")
    else:
        print("[OK] Admin ya existía:", ADMIN_EMAIL)

    print("[OK] Seed completo.")
