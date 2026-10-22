"""NIVEL DE SISTEMA (E2E) — Playwright en un navegador real.

Objeto de prueba: los flujos del usuario en la interfaz web.
La fixture `page` la provee pytest-playwright; las rutas relativas usan base_url.
Los datos se reinician antes de cada prueba.

Ejecuta solo este nivel:          pytest tests/e2e -v
Para VER el navegador:            pytest tests/e2e --headed --slowmo 500
Para grabar interacciones:        playwright codegen http://127.0.0.1:5000
                                  (con la app corriendo: python run.py)
"""
from playwright.sync_api import Page, expect


# ---------------------------------------------------------------- EJEMPLO
def test_pagina_de_login_carga(page: Page):
    page.goto("/login")
    expect(page.get_by_role("heading", name="Iniciar sesión")).to_be_visible()


# ------------------------------------------------------------------ TODO
# 1. Login exitoso: debe mostrarse "Bienvenido, admin".
#    (Ojo: aparece con retraso. NO uses time.sleep: expect() espera solo.)
# 2. Login fallido: se muestra un mensaje de error.
# 3. Crear un producto desde el formulario y verificar que aparece en la tabla.
# 4. Eliminar un producto desde la tabla.
#    Verifica el resultado esperado Y que no haya efectos colaterales
#    sobre los demás registros.
#
# Localizadores recomendados (por rol/etiqueta, como los ve el usuario):
#     page.get_by_label("Usuario").fill("admin")
#     page.get_by_role("button", name="Ingresar").click()
#     fila = page.get_by_role("row").filter(has_text="Teclado")
#     fila.get_by_role("button", name="Eliminar").click()
