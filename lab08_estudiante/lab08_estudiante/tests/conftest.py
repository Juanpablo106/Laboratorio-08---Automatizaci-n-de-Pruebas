"""Configuración compartida de las pruebas (NO es necesario modificarla).

- base_url: si la app no está corriendo en la URL configurada, la levanta
  automáticamente en segundo plano durante la ejecución de pytest.
- datos_limpios: reinicia los datos de la app antes de una prueba
  (aislamiento: cada prueba empieza desde el mismo estado conocido).
- api / api_autenticada: clientes HTTP de Playwright para probar la API.
"""
import threading
import urllib.request
from urllib.parse import urlparse

import pytest
from werkzeug.serving import make_server

USUARIO, PASSWORD = "admin", "Admin123"


def _responde(url):
    try:
        with urllib.request.urlopen(f"{url}/api/salud", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def base_url(pytestconfig):
    url = (pytestconfig.getoption("base_url") or "http://127.0.0.1:5000").rstrip("/")
    if _responde(url):
        yield url
        return
    from app import crear_app

    destino = urlparse(url)
    servidor = make_server(destino.hostname, destino.port, crear_app(), threaded=True)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield url
    servidor.shutdown()


@pytest.fixture
def datos_limpios(playwright, base_url):
    contexto = playwright.request.new_context(base_url=base_url)
    respuesta = contexto.post("/api/reset")
    assert respuesta.ok, "No se pudieron reiniciar los datos de la app"
    contexto.dispose()


@pytest.fixture
def api(playwright, base_url, datos_limpios):
    """Cliente HTTP SIN autenticar."""
    contexto = playwright.request.new_context(base_url=base_url)
    yield contexto
    contexto.dispose()


@pytest.fixture
def api_autenticada(playwright, base_url, datos_limpios):
    """Cliente HTTP con token válido (cabecera Authorization: Bearer ...)."""
    login = playwright.request.new_context(base_url=base_url)
    respuesta = login.post("/api/login", data={"usuario": USUARIO, "password": PASSWORD})
    assert respuesta.status == 200, "El login de la API falló en la fixture"
    token = respuesta.json()["token"]
    login.dispose()

    contexto = playwright.request.new_context(
        base_url=base_url, extra_http_headers={"Authorization": f"Bearer {token}"}
    )
    yield contexto
    contexto.dispose()
