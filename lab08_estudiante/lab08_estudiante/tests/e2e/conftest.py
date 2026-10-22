import pytest


@pytest.fixture(autouse=True)
def _datos_limpios_e2e(datos_limpios):
    """Cada prueba E2E empieza con los 3 productos iniciales."""
