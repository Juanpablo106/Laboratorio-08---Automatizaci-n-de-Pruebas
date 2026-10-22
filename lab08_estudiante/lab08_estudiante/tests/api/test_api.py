"""NIVEL DE INTEGRACIÓN (API) — Playwright APIRequestContext.

Objeto de prueba: el contrato HTTP de /api/... (rutas, códigos de estado, JSON).
Fixtures disponibles (ver tests/conftest.py):
    api               -> cliente sin token
    api_autenticada   -> cliente con token válido
Los datos se reinician antes de cada prueba (3 productos iniciales, ids 1, 2 y 3).

Ejecuta solo este nivel:   pytest tests/api -v
"""


# ---------------------------------------------------------------- EJEMPLO
def test_listar_productos_devuelve_los_tres_iniciales(api_autenticada):
    respuesta = api_autenticada.get("/api/productos")
    assert respuesta.status == 200
    assert len(respuesta.json()) == 3


# ------------------------------------------------------------------ TODO
# Usa la tabla "Contrato de la API" de la guía como ORÁCULO.
# 1. Login: credenciales correctas (200 + token) e incorrectas (401).
# 2. Seguridad mínima: sin token -> 401.
# 3. CRUD: crear (201), consultar, actualizar y eliminar (204).
# 4. Casos negativos: datos inválidos (400) y recursos que NO existen.
#    Verifica el código de estado exacto que exige el contrato.
#
# Ejemplo de POST con JSON:
#     r = api_autenticada.post("/api/productos",
#                              data={"nombre": "Audífonos", "precio": 199.99, "stock": 3})
#     assert r.status == 201
