import os
import sqlite3
from urllib.parse import quote
from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

productos = [
    {"id": 1, "nombre": "Miel de abeja 250 g", "precio": 15.00},
    {"id": 2, "nombre": "Miel de abeja 500 g", "precio": 28.00},
    {"id": 3, "nombre": "Miel de abeja 1 kg", "precio": 50.00}
]

carrito = []

NUMERO_WHATSAPP = "51940849095"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "ventas.db")


def conectar_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()

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
    return render_template("index.html", productos=productos)


@app.route("/comprar/<int:id>")
def comprar(id):
    for producto in productos:
        if producto["id"] == id:
            carrito.append(producto)
            break
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


if __name__ == "__main__":
    app.run(debug=True)