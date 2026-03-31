import os
import sqlite3
from uuid import uuid4
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "apiario_quino_secret_key"

NUMERO_WHATSAPP = "51929204188"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "ventas.db")


def conectar_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            imagen TEXT
        )
    """)

    conexion.commit()
    conexion.close()


crear_tablas()


def obtener_productos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    conexion.close()
    return productos


def obtener_producto_por_id(producto_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    producto = cursor.fetchone()
    conexion.close()
    return producto


@app.route("/")
def inicio():
    return redirect(url_for("tienda_virtual"))


@app.route("/tienda-virtual")
def tienda_virtual():
    productos = obtener_productos()
    return render_template("tienda.html", productos=productos)


@app.route("/panel-de-control")
def panel_de_control():
    productos = obtener_productos()
    return render_template("admin.html", productos=productos)


@app.route("/panel-de-control/agregar", methods=["GET", "POST"])
def agregar_producto():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        precio = request.form["precio"].strip()
        imagen = request.files["imagen"]

        if not nombre or not precio:
            flash("Completa el nombre y el precio.")
            return redirect(url_for("agregar_producto"))

        nombre_imagen = None

        if imagen and imagen.filename:
            extension = os.path.splitext(imagen.filename)[1]
            nombre_imagen = f"{uuid4().hex}{extension}"
            ruta_imagen = os.path.join(UPLOAD_DIR, nombre_imagen)
            imagen.save(ruta_imagen)

        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, precio, imagen) VALUES (?, ?, ?)",
            (nombre, float(precio), nombre_imagen)
        )
        conexion.commit()
        conexion.close()

        flash("Producto agregado correctamente.")
        return redirect(url_for("panel_de_control"))

    return render_template("agregar_producto.html")


@app.route("/panel-de-control/eliminar/<int:id>")
def eliminar_producto(id):
    producto = obtener_producto_por_id(id)

    if producto:
        if producto["imagen"]:
            ruta_imagen = os.path.join(UPLOAD_DIR, producto["imagen"])
            if os.path.exists(ruta_imagen):
                os.remove(ruta_imagen)

        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
        conexion.commit()
        conexion.close()

        flash("Producto eliminado correctamente.")

    return redirect(url_for("panel_de_control"))


@app.route("/comprar/<int:id>")
def comprar(id):
    producto = obtener_producto_por_id(id)

    if not producto:
        return redirect(url_for("tienda_virtual"))

    carrito = session.get("carrito", [])

    carrito.append({
        "id": producto["id"],
        "nombre": producto["nombre"],
        "precio": float(producto["precio"]),
        "imagen": producto["imagen"]
    })

    session["carrito"] = carrito
    return redirect(url_for("ver_carrito"))


@app.route("/carrito")
def ver_carrito():
    carrito = session.get("carrito", [])
    total = sum(float(p["precio"]) for p in carrito)
    return render_template("carrito.html", carrito=carrito, total=total)


@app.route("/vaciar_carrito")
def vaciar_carrito():
    session["carrito"] = []
    return redirect(url_for("ver_carrito"))


@app.route("/enviar_whatsapp")
def enviar_whatsapp():
    carrito = session.get("carrito", [])

    if not carrito:
        return redirect(url_for("ver_carrito"))

    total = sum(float(p["precio"]) for p in carrito)

    mensaje = "Hola, quiero realizar un pedido en Apiario Quino:\n\n"
    for i, producto in enumerate(carrito, start=1):
        mensaje += f"{i}. {producto['nombre']} - S/ {float(producto['precio']):.2f}\n"

    mensaje += f"\nTotal: S/ {total:.2f}"
    mensaje += "\n\nPor favor, deseo confirmar mi pedido."

    mensaje_codificado = quote(mensaje)
    url_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={mensaje_codificado}"
    return redirect(url_whatsapp)


if __name__ == "__main__":
    app.run(debug=True)