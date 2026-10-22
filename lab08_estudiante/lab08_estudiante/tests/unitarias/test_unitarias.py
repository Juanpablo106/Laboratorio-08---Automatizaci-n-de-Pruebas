"""NIVEL UNITARIO (componente) — pytest puro.

Objeto de prueba: app/validaciones.py (funciones puras, sin servidor ni navegador).
Técnicas aplicadas: partición de equivalencia y análisis de valores límite.
Oráculo: tabla "Reglas de validación" de la sección "Especificación" del README.md.

    | Campo             | Regla                                                        |
    | Usuario (login)   | Obligatorio (no vacío ni solo espacios)                     |
    | Contraseña        | Mínimo 6 caracteres                                          |
    | Nombre producto   | Entre 3 y 50 caracteres, ambos incluidos (sin espacios       |
    |                   | externos)                                                    |
    | Precio            | Número mayor que 0 y como máximo 100,000                     |
    | Stock             | Entero mayor o igual a 0                                     |

Ambas funciones devuelven una lista de mensajes de error: lista vacía = válido.

Ejecuta solo este nivel:   pytest tests/unitarias -v
"""
import unicodedata

import pytest

from app.validaciones import validar_credenciales, validar_producto


# =============================================================================
# Límites tomados de la ESPECIFICACIÓN (no de las constantes del módulo):
# el oráculo es la especificación, no la implementación.
# =============================================================================
PASSWORD_MIN = 6  # Contraseña: "Mínimo 6 caracteres"
NOMBRE_MIN = 3  # Nombre: "Entre 3 y 50 caracteres, ambos incluidos"
NOMBRE_MAX = 50  # Nombre: "Entre 3 y 50 caracteres, ambos incluidos"
PRECIO_MAX = 100_000  # Precio: "como máximo 100,000"
STOCK_MIN = 0  # Stock: "Entero mayor o igual a 0"

# Fragmentos que debe contener el mensaje de error de cada regla.
# Se comparan en minúsculas y sin acentos, para no depender de la redacción
# exacta del mensaje sino de que este identifique el campo y el tipo de fallo.
MSG_USUARIO = ("usuario",)
MSG_CONTRASENA = ("contrase",)
MSG_NOMBRE = ("nombre",)
MSG_PRECIO_NUMERO = ("precio", "numer")  # "El precio debe ser un número"
MSG_PRECIO_RANGO = ("precio", "mayor")  # "El precio debe ser mayor que 0 y ..."
MSG_STOCK_ENTERO = ("stock", "enter")  # "El stock debe ser un número entero"
MSG_STOCK_NEGATIVO = ("stock", "negativ")  # "El stock no puede ser negativo"


# =============================================================================
# Utilidades de aserción
# =============================================================================
def _sin_acentos(texto):
    """Pasa el texto a minúsculas y le quita los acentos."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def _error_que_menciona(errores, *fragmentos):
    """Devuelve el primer mensaje que menciona todos los fragmentos, o None."""
    for error in errores:
        normalizado = _sin_acentos(error)
        if all(_sin_acentos(fragmento) in normalizado for fragmento in fragmentos):
            return error
    return None


def _assert_error_sobre(errores, *fragmentos):
    """Falla si ningún mensaje de error menciona el campo/tipo esperado."""
    assert errores, "Se esperaba al menos un mensaje de error y la lista llegó vacía"
    encontrado = _error_que_menciona(errores, *fragmentos)
    assert encontrado is not None, (
        f"Ningún mensaje menciona {fragmentos}; mensajes recibidos: {errores}"
    )
    return encontrado


# =============================================================================
# 1. validar_credenciales
# =============================================================================
# ---------------------------------------------------------------- EJEMPLO
def test_credenciales_con_formato_valido_no_tiene_errores():
    assert validar_credenciales("admin", "Admin123") == []


# ------------------------------------------------- Partición: usuario válido
# Regla: "Obligatorio (no vacío ni solo espacios)". Cualquier texto no vacío
# es un usuario con formato válido (la contraseña se valida aparte).
@pytest.mark.parametrize(
    "usuario",
    ["admin", "a", "usuario1", " usuario ", "ADMIN", "ñandú"],
    ids=["normal", "un_caracter", "con_numero", "con_espacios_al_rededor", "mayusculas", "con_acentos"],
)
def test_usuario_no_vacio_no_reporta_error_de_usuario(usuario):
    errores = validar_credenciales(usuario, "Admin123")
    assert _error_que_menciona(errores, *MSG_USUARIO) is None


# ----------------------------------------------- Partición: usuario inválido
@pytest.mark.parametrize(
    "usuario",
    ["", "   ", "\t\n", None, 123, ["admin"]],
    ids=["vacio", "solo_espacios", "solo_blancos", "none", "entero", "lista"],
)
def test_usuario_invalido_reporta_error_de_usuario(usuario):
    errores = validar_credenciales(usuario, "Admin123")
    assert len(errores) == 1
    _assert_error_sobre(errores, *MSG_USUARIO)


# ---------------------------------------------- Partición: contraseña válida
# Regla: "Mínimo 6 caracteres". El largo se cuenta sobre la contraseña tal cual.
@pytest.mark.parametrize(
    "password",
    ["123456", "Admin123", "abcdefgh", "  a   "],
    ids=["6_caracteres", "formato_admin", "8_caracteres", "6_con_espacios"],
)
def test_contrasena_valida_no_reporta_error_de_contrasena(password):
    errores = validar_credenciales("admin", password)
    assert _error_que_menciona(errores, *MSG_CONTRASENA) is None


# -------------------------------------------- Partición: contraseña inválida
@pytest.mark.parametrize(
    "password",
    ["", "a", "12345", "     ", None, 123456],
    ids=["vacia", "1_caracter", "5_caracteres", "5_espacios", "none", "entero"],
)
def test_contrasena_invalida_reporta_error_de_contrasena(password):
    errores = validar_credenciales("admin", password)
    assert len(errores) == 1
    _assert_error_sobre(errores, *MSG_CONTRASENA)


# ------------------------------------------- Límite: longitud de la contraseña
# Último inválido = 5, primer válido = 6, siguiente válido = 7.
@pytest.mark.parametrize(
    "password, es_valido",
    [
        pytest.param("1" * (PASSWORD_MIN - 1), False, id="ultimo_invalido_5_caracteres"),
        pytest.param("1" * PASSWORD_MIN, True, id="primer_valido_6_caracteres"),
        pytest.param("1" * (PASSWORD_MIN + 1), True, id="siguiente_valido_7_caracteres"),
    ],
)
def test_limite_minimo_contrasena(password, es_valido):
    errores = validar_credenciales("admin", password)
    assert (errores == []) is es_valido


# =============================================================================
# 2. validar_producto
# =============================================================================
# ------------------------------------------------- Partición: producto válido
def test_producto_valido_no_reporta_errores():
    assert validar_producto("Teclado", 250.00, 10) == []


# ------------------------------------------------ Partición: nombre válido
# Regla: 3 a 50 caracteres, sin contar los espacios extremos.
@pytest.mark.parametrize(
    "nombre",
    [
        "Teclado",
        "ABC",
        "ABCD",
        "Mouse",
        "A" * 49,
        "A" * 50,
        "  ABC  ",
        "  " + "A" * 50 + "  ",
    ],
    ids=[
        "normal",
        "minimo_3",
        "4_caracteres",
        "otro_normal",
        "49_caracteres",
        "maximo_50",
        "3_con_espacios_al_rededor",
        "50_con_espacios_al_rededor",
    ],
)
def test_nombre_valido_no_reporta_error_de_nombre(nombre):
    errores = validar_producto(nombre, 100.0, 1)
    assert _error_que_menciona(errores, *MSG_NOMBRE) is None


# ---------------------------------------------- Partición: nombre inválido
@pytest.mark.parametrize(
    "nombre",
    [
        "Ab",
        "A",
        "",
        "   ",
        "A" * 51,
        "  Ab  ",
        "  " + "A" * 51 + "  ",
        None,
        12345,
        b"ABC",
    ],
    ids=[
        "2_caracteres",
        "1_caracter",
        "vacio",
        "solo_espacios",
        "51_caracteres",
        "2_con_espacios_al_rededor",
        "51_con_espacios_al_rededor",
        "none",
        "entero",
        "bytes",
    ],
)
def test_nombre_invalido_reporta_error_de_nombre(nombre):
    errores = validar_producto(nombre, 100.0, 1)
    assert len(errores) == 1
    _assert_error_sobre(errores, *MSG_NOMBRE)


# ---------------------------------------------------- Límite: longitud nombre
# Límite inferior: último inválido = 2, primer válido = 3, siguiente = 4.
# Límite superior: último válido = 49, máximo válido = 50, primer inválido = 51.
@pytest.mark.parametrize(
    "nombre, es_valido",
    [
        pytest.param("A" * (NOMBRE_MIN - 1), False, id="ultimo_invalido_2_caracteres"),
        pytest.param("A" * NOMBRE_MIN, True, id="primer_valido_3_caracteres"),
        pytest.param("A" * (NOMBRE_MIN + 1), True, id="siguiente_valido_4_caracteres"),
        pytest.param("A" * (NOMBRE_MAX - 1), True, id="ultimo_valido_49_caracteres"),
        pytest.param("A" * NOMBRE_MAX, True, id="maximo_valido_50_caracteres"),
        pytest.param("A" * (NOMBRE_MAX + 1), False, id="primer_invalido_51_caracteres"),
    ],
)
def test_limite_longitud_nombre(nombre, es_valido):
    errores = validar_producto(nombre, 100.0, 1)
    assert (errores == []) is es_valido


# -------------------------------------------------- Partición: precio válido
# Regla: número mayor que 0 y como máximo 100,000.
@pytest.mark.parametrize(
    "precio",
    [0.001, 0.01, 1, 99.99, 250.00, 1450.00, 99999.99, 100_000],
    ids=[
        "positivo_minimo_3_decimales",
        "positivo_minimo_2_decimales",
        "entero",
        "decimal",
        "decimal_2",
        "decimal_3",
        "por_debajo_del_maximo",
        "maximo_100000",
    ],
)
def test_precio_valido_no_reporta_error_de_precio(precio):
    errores = validar_producto("Teclado", precio, 1)
    assert _error_que_menciona(errores, *MSG_PRECIO_NUMERO) is None
    assert _error_que_menciona(errores, *MSG_PRECIO_RANGO) is None


# ------------------------------- Partición: precio inválido por tipo de dato
# La regla exige un número: los booleanos NO cuentan como número (en Python
# bool es subclase de int, por eso la implementación los excluye).
@pytest.mark.parametrize(
    "precio",
    ["100", "250.00", None, True, False, [100]],
    ids=["str_numerico", "str_decimal", "none", "true", "false", "lista"],
)
def test_precio_no_numerico_reporta_error_de_numero(precio):
    errores = validar_producto("Teclado", precio, 1)
    assert len(errores) == 1
    _assert_error_sobre(errores, *MSG_PRECIO_NUMERO)


# ------------------------------- Partición: precio inválido por rango (límite)
# El límite inferior es EXCLUSIVO (precio > 0): 0 es inválido.
# El límite superior es INCLUSIVO (precio <= 100,000).
@pytest.mark.parametrize(
    "precio",
    [0, 0.0, -1, -0.01, 100_000.01, 100_001],
    ids=["cero_int", "cero_float", "negativo_int", "negativo_decimal", "sobre_maximo", "muy_sobre_maximo"],
)
def test_precio_fuera_de_rango_reporta_error_de_rango(precio):
    errores = validar_producto("Teclado", precio, 1)
    assert len(errores) == 1
    _assert_error_sobre(errores, *MSG_PRECIO_RANGO)


# ------------------------------------------------------ Límite: rango precio
# Límite inferior exclusivo: último inválido = 0, primer válido = 0.001
# (menor positivo que representa la app, que maneja precios con 2 decimales).
# Límite superior inclusivo: último válido = 100,000, primer inválido = 100,000.01.
@pytest.mark.parametrize(
    "precio, es_valido",
    [
        pytest.param(0, False, id="ultimo_invalido_cero"),
        pytest.param(0.001, True, id="primer_valido_0.001"),
        pytest.param(0.01, True, id="siguiente_valido_0.01"),
        pytest.param(PRECIO_MAX - 0.01, True, id="ultimo_valido_99999.99"),
        pytest.param(PRECIO_MAX, True, id="maximo_valido_100000"),
        pytest.param(PRECIO_MAX + 0.01, False, id="primer_invalido_100000.01"),
    ],
)
def test_limite_rango_precio(precio, es_valido):
    errores = validar_producto("Teclado", precio, 1)
    assert (errores == []) is es_valido


# ------------------------------------------------ Partición: stock válido
# Regla: entero mayor o igual a 0.
@pytest.mark.parametrize(
    "stock",
    [0, 1, 5, 10, 1_000_000],
    ids=["cero", "uno", "cinco", "diez", "un_millon"],
)
def test_stock_valido_no_reporta_error_de_stock(stock):
    errores = validar_producto("Teclado", 100.0, stock)
    assert _error_que_menciona(errores, *MSG_STOCK_ENTERO) is None
    assert _error_que_menciona(errores, *MSG_STOCK_NEGATIVO) is None


# ------------------------------- Partición: stock inválido por tipo de dato
# La regla exige un entero: los flotantes (5.0), las cadenas y los booleanos
# no son enteros válidos.
@pytest.mark.parametrize(
    "stock",
    [5.0, 0.0, "5", None, True, False],
    ids=["float", "float_cero", "str_numerico", "none", "true", "false"],
)
def test_stock_no_entero_reporta_error_de_entero(stock):
    errores = validar_producto("Teclado", 100.0, stock)
    assert len(errores) == 1
    _assert_error_sobre(errores, *MSG_STOCK_ENTERO)


# ------------------------------------- Partición: stock inválido por rango
@pytest.mark.parametrize(
    "stock",
    [-1, -2, -100],
    ids=["menos_uno", "menos_dos", "menos_cien"],
)
def test_stock_negativo_reporta_error_de_negativo(stock):
    errores = validar_producto("Teclado", 100.0, stock)
    assert len(errores) == 1
    _assert_error_sobre(errores, *MSG_STOCK_NEGATIVO)


# ------------------------------------------------------- Límite: rango stock
# Límite inferior inclusivo: último inválido = -1, primer válido = 0,
# siguiente válido = 1.
@pytest.mark.parametrize(
    "stock, es_valido",
    [
        pytest.param(STOCK_MIN - 1, False, id="ultimo_invalido_negativo"),
        pytest.param(STOCK_MIN, True, id="primer_valido_cero"),
        pytest.param(STOCK_MIN + 1, True, id="siguiente_valido_uno"),
    ],
)
def test_limite_rango_stock(stock, es_valido):
    errores = validar_producto("Teclado", 100.0, stock)
    assert (errores == []) is es_valido


# =============================================================================
# 3. Combinación de reglas
# =============================================================================
def test_producto_valido_no_sesiona_ningun_error():
    """Un producto que cumple las cinco reglas no produce mensajes."""
    errores = validar_producto("Teclado", 250.00, 10)
    assert errores == []
    assert len(errores) == 0


def test_producto_invalido_reporta_un_error_por_regla_incumplida():
    """Cada regla incumplida aporta su propio mensaje, sin taparse entre sí."""
    errores = validar_producto("A", -5, -1)
    assert len(errores) == 3
    _assert_error_sobre(errores, *MSG_NOMBRE)
    _assert_error_sobre(errores, *MSG_PRECIO_RANGO)
    _assert_error_sobre(errores, *MSG_STOCK_NEGATIVO)


def test_credenciales_invalidas_reportan_un_error_por_regla_incumplida():
    errores = validar_credenciales("", "123")
    assert len(errores) == 2
    _assert_error_sobre(errores, *MSG_USUARIO)
    _assert_error_sobre(errores, *MSG_CONTRASENA)


# =============================================================================
# 4. Pruebas de regresión de defectos
# =============================================================================
def test_regresion_def_01_precio_cero_debe_rechazarse():
    """DEF-01: la especificación exige "precio mayor que 0", pero la
    implementación solo rechazaba los negativos, por lo que un producto con
    precio 0 se daba por válido (y la API lo aceptaba con 201 Created)."""
    errores = validar_producto("Teclado", 0, 10)
    assert errores, "El precio 0 debe rechazarse: la regla dice 'mayor que 0'"
    _assert_error_sobre(errores, *MSG_PRECIO_RANGO)
