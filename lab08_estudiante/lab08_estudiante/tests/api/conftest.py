import pytest


@pytest.fixture(autouse=True)
def _datos_limpios_api(datos_limpios):
    """Cada prueba de API empieza con los 3 productos iniciales."""
