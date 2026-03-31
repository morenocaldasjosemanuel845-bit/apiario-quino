import os
import sqlite3
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "apiario_quino_secret_key"

carrito = []
NUMERO_WHATSAPP = "51940849095"

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            producto_nombre TEXT NOT NULL,
            precio REAL NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


crear_tablas()


@app.route("/")
def inicio():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    conexion.close()
    return render_template("index.html", productos=productos)


@app.route("/comprar/<int:id>")
def comprar(id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (id,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        carrito.append({
            "id": producto["id"],
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "imagen": producto["imagen"]
        })

    return redirect(url_for("ver_carrito"))


@app.route("/carrito")
def ver_carrito():
    total = sum(p["precio"] for p in carrito)
    return render_template("carrito.html", carrito=carrito, total=total)


@app.route("/vaciar_carrito")
def vaciar_carrito():
    carrito.clear()
    return redirect(url_for("ver_carrito"))


@app.route("/enviar_whatsapp")
def enviar_whatsapp():
    if not carrito:
        return redirect(url_for("ver_carrito"))

    total = sum(p["precio"] for p in carrito)

    mensaje = "Hola, quiero realizar un pedido en Apiario Quino:\n\n"
    for i, producto in enumerate(carrito, start=1):
        mensaje += f"{i}. {producto['nombre']} - S/ {producto['precio']:.2f}\n"

    mensaje += f"\nTotal: S/ {total:.2f}"
    mensaje += "\n\nPor favor, deseo confirmar mi pedido."

    mensaje_codificado = quote(mensaje)
    url_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={mensaje_codificado}"
    return redirect(url_whatsapp)


@app.route("/admin/productos", methods=["GET", "POST"])
def admin_productos():
    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        imagen = request.files["imagen"]

        nombre_imagen = None

        if imagen and imagen.filename:
            nombre_imagen = imagen.filename
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

        flash("Producto agregado correctamente")
        return redirect(url_for("admin_productos"))

    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    conexion.close()

    return render_template("admin_productos.html", productos=productos)


if __name__ == "__main__":
    app.run(debug=True)