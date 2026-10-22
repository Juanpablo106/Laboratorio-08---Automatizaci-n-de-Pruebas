"""NIVEL DE SISTEMA (E2E) — Playwright en un navegador real.

Objeto de prueba: los flujos del usuario en la interfaz web.
La fixture `page` la provee pytest-playwright; las rutas relativas usan base_url.
Los datos se reinician antes de cada prueba (3 productos iniciales: ids 1, 2, 3).

Oráculo de verdad: la sección "Especificación" de la guía del laboratorio.

Ejecuta solo este nivel:          pytest tests/e2e -v
Para VER el navegador:            pytest tests/e2e --headed --slowmo 500
Para grabar interacciones:        playwright codegen http://127.0.0.1:5000
                                   (con la app corriendo: python run.py)

Nota sobre las esperas: NO se usa time.sleep(). `expect(...)` reintenta solo
hasta que la condición se cumple, por eso funciona con el mensaje de
bienvenida, que la app muestra con 800 ms de retraso.
"""
import re

import pytest
from playwright.sync_api import Page, expect

USUARIO = "admin"
PASSWORD = "Admin123"

# Datos iniciales documentados en la especificación.
PRODUCTOS_INICIALES = {"Teclado": "250.00", "Mouse": "95.50", "Monitor": "1450.00"}


# ---------------------------------------------------------------- HELPERS
def _iniciar_sesion(page: Page, usuario: str = USUARIO, password: str = PASSWORD) -> None:
    """Recorre el formulario de login y espera a llegar a la lista de productos."""
    page.goto("/login")
    page.get_by_label("Usuario").fill(usuario)
    page.get_by_label("Contraseña").fill(password)
    page.get_by_role("button", name="Ingresar").click()
    expect(page).to_have_url(re.compile(r"/productos$"))


def _fila_de(page: Page, nombre: str):
    """Fila de la tabla que contiene el producto indicado (por nombre, no por posición)."""
    return page.get_by_role("row").filter(has_text=nombre)


def _productos_en_la_tabla(page: Page) -> dict:
    """Instantánea de la tabla: {nombre: {id, precio, stock}} (sin la fila de encabezado)."""
    productos = {}
    for fila in page.get_by_role("row").filter(has=page.get_by_role("cell")).all():
        celdas = fila.get_by_role("cell")
        productos[celdas.nth(1).inner_text().strip()] = {
            "id": celdas.nth(0).inner_text().strip(),
            "precio": celdas.nth(2).inner_text().strip(),
            "stock": celdas.nth(3).inner_text().strip(),
        }
    return productos


# ---------------------------------------------------------------- EJEMPLO
def test_pagina_de_login_carga(page: Page):
    page.goto("/login")
    expect(page.get_by_role("heading", name="Iniciar sesión")).to_be_visible()


# ----------------------------------------------- Escenario 1 · Login exitoso
def test_login_exitoso_muestra_bienvenido_y_lista_de_productos(page: Page):
    """Spec: "Login correcto: lleva a la lista de productos y muestra 'Bienvenido, admin'"."""
    _iniciar_sesion(page)

    # El saludo se inserta con 800 ms de retraso: expect() espera sin time.sleep().
    expect(page.get_by_text("Bienvenido, admin")).to_be_visible()
    expect(page.get_by_role("heading", name="Productos")).to_be_visible()

    # La tabla protegida muestra los 3 productos iniciales con sus datos.
    expect(page.get_by_role("row").filter(has=page.get_by_role("cell"))).to_have_count(
        len(PRODUCTOS_INICIALES)
    )
    for nombre, precio in PRODUCTOS_INICIALES.items():
        fila = _fila_de(page, nombre)
        expect(fila).to_have_count(1)
        expect(fila.get_by_role("cell").nth(2)).to_have_text(precio)


# ---------------------------------------------- Escenario 2 · Login fallido
def test_login_fallido_muestra_error_y_no_accede_a_la_lista_de_productos(page: Page):
    """Spec: "Login incorrecto: muestra 'Usuario o contraseña incorrectos'".

    La contraseña es incorrecta pero con formato válido (>= 6 caracteres), así que
    la app llega a la comprobación de credenciales y no a la de formato.
    """
    page.goto("/login")
    page.get_by_label("Usuario").fill(USUARIO)
    page.get_by_label("Contraseña").fill("ClaveIncorrecta")
    page.get_by_role("button", name="Ingresar").click()

    expect(page.get_by_role("alert")).to_contain_text("Usuario o contraseña incorrectos")

    # Sigue en el login: no se accede a la lista protegida de productos.
    expect(page).to_have_url(re.compile(r"/login$"))
    expect(page.get_by_role("heading", name="Productos")).to_have_count(0)
    expect(page.get_by_text("Bienvenido, admin")).to_have_count(0)


@pytest.mark.parametrize("ruta", ["/productos", "/productos/nuevo", "/productos/1/editar"])
def test_sin_sesion_las_paginas_de_productos_redirigen_al_login(page: Page, ruta: str):
    """Spec: "Sin sesión, cualquier página de productos redirige a /login"."""
    page.goto(ruta)
    expect(page).to_have_url(re.compile(r"/login$"))
    expect(page.get_by_role("heading", name="Iniciar sesión")).to_be_visible()


# ---------------------------------------------- Escenario 3 · Crear producto
def test_crear_producto_desde_el_formulario_aparece_en_la_tabla(page: Page):
    """Spec: "'Nuevo producto' abre un formulario; al guardar, muestra 'Producto creado'
    y el producto aparece en la tabla"."""
    _iniciar_sesion(page)

    page.get_by_role("link", name="Nuevo producto").click()
    expect(page.get_by_role("heading", name="Nuevo producto")).to_be_visible()

    page.get_by_label("Nombre").fill("Audífonos")
    page.get_by_label("Precio").fill("199.99")
    page.get_by_label("Stock").fill("3")
    page.get_by_role("button", name="Guardar").click()

    expect(page.get_by_text("Producto creado")).to_be_visible()

    fila = _fila_de(page, "Audífonos")
    expect(fila).to_have_count(1)
    celdas = fila.get_by_role("cell")
    expect(celdas.nth(0)).to_have_text(re.compile(r"^\d+$"))  # recibe un id
    expect(celdas.nth(1)).to_have_text("Audífonos")
    expect(celdas.nth(2)).to_have_text("199.99")
    expect(celdas.nth(3)).to_have_text("3")

    # Los productos anteriores siguen intactos.
    expect(page.get_by_role("row").filter(has=page.get_by_role("cell"))).to_have_count(
        len(PRODUCTOS_INICIALES) + 1
    )


# ---------------------------------------------- Escenario 4 · Eliminar producto
def test_eliminar_producto_borra_solo_ese_producto_y_no_afecta_a_los_demas(page: Page):
    """Spec: "'Eliminar' borra **ese** producto, muestra 'Producto eliminado' y los
    demás productos no cambian"."""
    _iniciar_sesion(page)

    estado_inicial = _productos_en_la_tabla(page)
    assert set(estado_inicial) == set(PRODUCTOS_INICIALES), (
        f"Se esperaban los productos iniciales de la especificación, se obtuvo: {estado_inicial}"
    )

    # Se identifica el producto por su nombre (no por la posición en la tabla) y se
    # elimina únicamente ese producto.
    fila = _fila_de(page, "Mouse")
    expect(fila).to_have_count(1)
    fila.get_by_role("button", name="Eliminar").click()

    expect(page.get_by_text("Producto eliminado")).to_be_visible()

    # 1) Instantánea completa de la tabla: solo debe faltar el producto eliminado.
    #    Se compara el snapshot completo para que el fallo muestre qué producto
    #    se borró de más y cuál sobrevivió.
    esperado = {n: d for n, d in estado_inicial.items() if n != "Mouse"}
    obtenido = _productos_en_la_tabla(page)
    assert obtenido == esperado, (
        "La tabla no quedó como exige la especificación "
        "(solo debe desaparecer el producto eliminado):\n"
        f"  esperado: {esperado}\n"
        f"  obtenido: {obtenido}"
    )

    # 2) El producto eliminado ya no aparece en la tabla.
    expect(_fila_de(page, "Mouse")).to_have_count(0)

    # 3) Los demás productos siguen presentes y con exactamente los mismos datos.
    for nombre in ("Teclado", "Monitor"):
        fila_otros = _fila_de(page, nombre)
        expect(fila_otros).to_have_count(1)
        celdas = fila_otros.get_by_role("cell")
        expect(celdas.nth(0)).to_have_text(estado_inicial[nombre]["id"])
        expect(celdas.nth(2)).to_have_text(estado_inicial[nombre]["precio"])
        expect(celdas.nth(3)).to_have_text(estado_inicial[nombre]["stock"])


# ---------------------------------------------- Extra · Editar producto
def test_editar_producto_actualiza_sus_datos_en_la_tabla(page: Page):
    """Spec: "'Editar' permite modificar el producto; al guardar, muestra
    'Producto actualizado'"."""
    _iniciar_sesion(page)

    _fila_de(page, "Monitor").get_by_role("link", name="Editar").click()
    expect(page.get_by_role("heading", name="Editar producto")).to_be_visible()

    # El formulario llega con los datos del producto que se está editando.
    expect(page.get_by_label("Nombre")).to_have_value("Monitor")
    expect(page.get_by_label("Precio")).to_have_value(re.compile(r"1450(\.0+)?"))
    expect(page.get_by_label("Stock")).to_have_value("5")

    page.get_by_label("Precio").fill("1399.50")
    page.get_by_role("button", name="Guardar").click()

    expect(page.get_by_text("Producto actualizado")).to_be_visible()

    fila = _fila_de(page, "Monitor")
    expect(fila).to_have_count(1)
    expect(fila.get_by_role("cell").nth(2)).to_have_text("1399.50")
    expect(fila.get_by_role("cell").nth(3)).to_have_text("5")


# ---------------------------------------------- Extra · Validación del formulario
def test_formulario_rechaza_nombre_con_menos_de_3_caracteres(page: Page):
    """Spec: "Nombre de producto: entre 3 y 50 caracteres" -> el formulario debe rechazarlo."""
    _iniciar_sesion(page)

    page.get_by_role("link", name="Nuevo producto").click()
    page.get_by_label("Nombre").fill("Ab")
    page.get_by_label("Precio").fill("10")
    page.get_by_label("Stock").fill("1")
    page.get_by_role("button", name="Guardar").click()

    expect(page.get_by_role("alert")).to_be_visible()
    expect(page.get_by_role("heading", name="Nuevo producto")).to_be_visible()  # sigue en el formulario
    expect(page.get_by_text("Producto creado")).to_have_count(0)


def test_formulario_rechaza_precio_cero(page: Page):
    """Spec: "Precio: número **mayor que 0**" -> el formulario debe rechazar el precio 0."""
    _iniciar_sesion(page)

    page.get_by_role("link", name="Nuevo producto").click()
    page.get_by_label("Nombre").fill("Producto Sin Costo")
    page.get_by_label("Precio").fill("0")
    page.get_by_label("Stock").fill("1")
    page.get_by_role("button", name="Guardar").click()

    # Debe informar el error y NO crear el producto.
    expect(page.get_by_role("alert")).to_be_visible()
    expect(page.get_by_text("Producto creado")).to_have_count(0)
    expect(_fila_de(page, "Producto Sin Costo")).to_have_count(0)
