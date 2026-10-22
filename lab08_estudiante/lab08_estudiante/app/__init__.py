"""Inventario IS1: aplicación base del laboratorio de pruebas.

Aplicación Flask mínima con:
  - Interfaz web: login + CRUD de productos (HTML renderizado en servidor)
  - API REST JSON: login con token + CRUD de productos
  - Datos en memoria (se pierden al reiniciar; ideal para pruebas)

NO modifiques este código: tu trabajo es PROBARLO.
"""

import secrets
from functools import wraps

from flask import (
    Flask, flash, jsonify, redirect, render_template, request, session, url_for,
)

from .validaciones import validar_credenciales, validar_producto

USUARIOS = {"admin": "Admin123"}

DATOS_INICIALES = [
    {"nombre": "Teclado", "precio": 250.00, "stock": 10},
    {"nombre": "Mouse", "precio": 95.50, "stock": 25},
    {"nombre": "Monitor", "precio": 1450.00, "stock": 5},
]


def autenticar(usuario, password):
    return USUARIOS.get(usuario) == password


def _a_numero(texto, tipo):
    """Convierte el texto de un formulario a número; None si no se puede."""
    try:
        return tipo(texto)
    except (TypeError, ValueError):
        return None


def crear_app():
    app = Flask(__name__)
    app.secret_key = "lab-is1-solo-para-pruebas"

    estado = {"productos": {}, "siguiente_id": 1, "tokens": set()}

    def reiniciar_datos():
        estado["productos"].clear()
        estado["siguiente_id"] = 1
        estado["tokens"].clear()
        for p in DATOS_INICIALES:
            agregar(p["nombre"], p["precio"], p["stock"])

    def agregar(nombre, precio, stock):
        pid = estado["siguiente_id"]
        estado["productos"][pid] = {
            "id": pid, "nombre": nombre.strip(), "precio": precio, "stock": stock,
        }
        estado["siguiente_id"] += 1
        return estado["productos"][pid]

    def lista_productos():
        return [estado["productos"][k] for k in sorted(estado["productos"])]

    reiniciar_datos()

    # ------------------------------------------------------------------
    # Interfaz web
    # ------------------------------------------------------------------
    def requiere_sesion(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if "usuario" not in session:
                return redirect(url_for("login"))
            return vista(*args, **kwargs)
        return envoltura

    @app.get("/")
    def inicio():
        return redirect(url_for("listar_productos"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        errores = []
        if request.method == "POST":
            usuario = request.form.get("usuario", "")
            password = request.form.get("password", "")
            errores = validar_credenciales(usuario, password)
            if not errores:
                if autenticar(usuario, password):
                    session["usuario"] = usuario
                    return redirect(url_for("listar_productos"))
                errores = ["Usuario o contraseña incorrectos"]
        return render_template("login.html", errores=errores)

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/productos")
    @requiere_sesion
    def listar_productos():
        return render_template(
            "productos.html", productos=lista_productos(), usuario=session["usuario"]
        )

    def _leer_formulario():
        nombre = request.form.get("nombre", "")
        precio = _a_numero(request.form.get("precio"), float)
        stock = _a_numero(request.form.get("stock"), int)
        return nombre, precio, stock

    @app.route("/productos/nuevo", methods=["GET", "POST"])
    @requiere_sesion
    def nuevo_producto():
        errores, datos = [], {"nombre": "", "precio": "", "stock": ""}
        if request.method == "POST":
            nombre, precio, stock = _leer_formulario()
            datos = request.form
            errores = validar_producto(nombre, precio, stock)
            if not errores:
                agregar(nombre, precio, stock)
                flash("Producto creado")
                return redirect(url_for("listar_productos"))
        return render_template(
            "formulario.html", titulo="Nuevo producto", datos=datos, errores=errores
        )

    @app.route("/productos/<int:pid>/editar", methods=["GET", "POST"])
    @requiere_sesion
    def editar_producto(pid):
        producto = estado["productos"].get(pid)
        if producto is None:
            flash("Producto no encontrado")
            return redirect(url_for("listar_productos"))
        errores, datos = [], producto
        if request.method == "POST":
            nombre, precio, stock = _leer_formulario()
            datos = request.form
            errores = validar_producto(nombre, precio, stock)
            if not errores:
                producto.update(nombre=nombre.strip(), precio=precio, stock=stock)
                flash("Producto actualizado")
                return redirect(url_for("listar_productos"))
        return render_template(
            "formulario.html", titulo="Editar producto", datos=datos, errores=errores
        )

    @app.post("/productos/<int:pid>/eliminar")
    @requiere_sesion
    def eliminar_producto(pid):
        if estado["productos"].pop(pid, None) is not None:
            flash("Producto eliminado")
        else:
            flash("Producto no encontrado")
        return redirect(url_for("listar_productos"))

    # ------------------------------------------------------------------
    # API REST (JSON)
    # ------------------------------------------------------------------
    def requiere_token(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            cabecera = request.headers.get("Authorization", "")
            token = cabecera.removeprefix("Bearer ").strip()
            if token not in estado["tokens"]:
                return jsonify({"error": "No autorizado"}), 401
            return vista(*args, **kwargs)
        return envoltura

    @app.get("/api/salud")
    def salud():
        return jsonify({"estado": "ok"})

    @app.post("/api/reset")
    def reset():
        # Gancho SOLO para pruebas: deja los datos en su estado inicial.
        # En un sistema real NUNCA debe existir en producción (ver Unidad 10).
        reiniciar_datos()
        return jsonify({"estado": "reiniciado"})

    @app.post("/api/login")
    def api_login():
        cuerpo = request.get_json(silent=True) or {}
        usuario, password = cuerpo.get("usuario"), cuerpo.get("password")
        errores = validar_credenciales(usuario, password)
        if errores:
            return jsonify({"errores": errores}), 400
        if not autenticar(usuario, password):
            return jsonify({"error": "Credenciales inválidas"}), 401
        token = secrets.token_hex(16)
        estado["tokens"].add(token)
        return jsonify({"token": token})

    @app.get("/api/productos")
    @requiere_token
    def api_listar():
        return jsonify(lista_productos())

    @app.post("/api/productos")
    @requiere_token
    def api_crear():
        cuerpo = request.get_json(silent=True) or {}
        nombre, precio, stock = cuerpo.get("nombre"), cuerpo.get("precio"), cuerpo.get("stock")
        errores = validar_producto(nombre, precio, stock)
        if errores:
            return jsonify({"errores": errores}), 400
        return jsonify(agregar(nombre, precio, stock)), 201

    @app.get("/api/productos/<int:pid>")
    @requiere_token
    def api_obtener(pid):
        producto = estado["productos"].get(pid)
        if producto is None:
            return jsonify({}), 200
        return jsonify(producto)

    @app.put("/api/productos/<int:pid>")
    @requiere_token
    def api_actualizar(pid):
        producto = estado["productos"].get(pid)
        if producto is None:
            return jsonify({"error": "Producto no encontrado"}), 404
        cuerpo = request.get_json(silent=True) or {}
        nombre, precio, stock = cuerpo.get("nombre"), cuerpo.get("precio"), cuerpo.get("stock")
        errores = validar_producto(nombre, precio, stock)
        if errores:
            return jsonify({"errores": errores}), 400
        producto.update(nombre=nombre.strip(), precio=precio, stock=stock)
        return jsonify(producto)

    @app.delete("/api/productos/<int:pid>")
    @requiere_token
    def api_eliminar(pid):
        if estado["productos"].pop(pid, None) is None:
            return jsonify({"error": "Producto no encontrado"}), 404
        return "", 204

    return app
