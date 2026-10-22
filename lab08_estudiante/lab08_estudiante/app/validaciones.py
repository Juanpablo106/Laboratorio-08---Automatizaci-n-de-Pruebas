"""Reglas de validación del sistema de inventario.

Funciones puras (sin Flask, sin red, sin base de datos): se pueden probar
con pruebas unitarias en milisegundos.
"""

LONGITUD_MIN_PASSWORD = 6
NOMBRE_MIN = 3
NOMBRE_MAX = 50
PRECIO_MAX = 100_000


def validar_credenciales(usuario, password):
    """Valida el FORMATO de las credenciales (no si son correctas).

    Devuelve una lista de mensajes de error; lista vacía = formato válido.
    """
    errores = []
    if not isinstance(usuario, str) or not usuario.strip():
        errores.append("El usuario es obligatorio")
    if not isinstance(password, str) or len(password) < LONGITUD_MIN_PASSWORD:
        errores.append(
            f"La contraseña debe tener al menos {LONGITUD_MIN_PASSWORD} caracteres"
        )
    return errores


def _es_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_producto(nombre, precio, stock):
    """Valida los datos de un producto.

    Reglas (ver especificación):
      - nombre: texto de 3 a 50 caracteres (sin contar espacios extremos)
      - precio: número mayor que 0 y menor o igual a 100,000
      - stock: entero mayor o igual a 0

    Devuelve una lista de mensajes de error; lista vacía = producto válido.
    """
    errores = []

    if not isinstance(nombre, str) or not (
        NOMBRE_MIN <= len(nombre.strip()) <= NOMBRE_MAX
    ):
        errores.append(
            f"El nombre debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres"
        )

    if not _es_numero(precio):
        errores.append("El precio debe ser un número")
    elif precio < 0 or precio > PRECIO_MAX:
        errores.append("El precio debe ser mayor que 0 y como máximo 100,000")

    if not isinstance(stock, int) or isinstance(stock, bool):
        errores.append("El stock debe ser un número entero")
    elif stock < 0:
        errores.append("El stock no puede ser negativo")

    return errores
