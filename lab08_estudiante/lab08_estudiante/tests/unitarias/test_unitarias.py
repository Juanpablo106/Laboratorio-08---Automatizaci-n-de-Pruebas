"""NIVEL UNITARIO (componente) — pytest puro.

Objeto de prueba: app/validaciones.py (funciones puras, sin servidor ni navegador).
Técnicas sugeridas: partición de equivalencia y análisis de valores límite.

Ejecuta solo este nivel:   pytest tests/unitarias -v
"""
import pytest

from app.validaciones import validar_credenciales, validar_producto


# ---------------------------------------------------------------- EJEMPLO
def test_credenciales_con_formato_valido_no_tienen_errores():
    assert validar_credenciales("admin", "Admin123") == []


# ------------------------------------------------------------------ TODO
# 1. validar_credenciales: usuario vacío, contraseña en el límite (5 y 6 caracteres).
# 2. validar_producto: un producto válido no tiene errores.
# 3. validar_producto: aplica VALORES LÍMITE a cada regla de la especificación
#    (nombre, precio y stock). Pregúntate: ¿cuál es el último valor inválido
#    y el primer valor válido de cada regla?
#
# Pista: @pytest.mark.parametrize evita repetir la misma prueba con datos distintos.
#
# @pytest.mark.parametrize("stock, valido", [(-1, False), (0, True)])
# def test_limites_de_stock(stock, valido):
#     errores = validar_producto("Teclado", 100.0, stock)
#     assert (errores == []) == valido
