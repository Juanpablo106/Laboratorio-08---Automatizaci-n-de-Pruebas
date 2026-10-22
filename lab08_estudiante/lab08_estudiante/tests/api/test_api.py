"""NIVEL DE INTEGRACIÓN (API) — Playwright APIRequestContext.

Objeto de prueba: el contrato HTTP de /api/... (rutas, códigos de estado, JSON).
Fixtures disponibles (ver tests/conftest.py):
    api               -> cliente sin token
    api_autenticada   -> cliente con token válido
Los datos se reinician antes de cada prueba (3 productos iniciales, ids 1, 2 y 3).

ORÁCULO: la tabla "Contrato de la API" de la guía (README.md).

    POST   /api/login          -> 200 + {"token": ...} | 401 credenciales incorrectas
                                | 400 + {"errores": [...]} formato inválido
    GET    /api/productos      -> 200 + lista de productos
    POST   /api/productos      -> 201 + producto creado (con id) | 400 + {"errores": [...]}
    GET    /api/productos/<id> -> 200 + producto | 404 no existe
    PUT    /api/productos/<id> -> 200 + producto actualizado | 400 datos inválidos
                                | 404 no existe
    DELETE /api/productos/<id> -> 204 | 404 no existe
    Cualquier ruta de /api/productos sin token válido -> 401

Reglas de validación (especificación):
    nombre -> 3 a 50 caracteres (sin contar espacios extremos)
    precio -> número mayor que 0 y como máximo 100,000
    stock  -> entero mayor o igual a 0

Cuando la aplicación se aparta de ese contrato, la prueba SE DEJA FALLANDO:
el defecto se documenta en INFORME.md, no se oculta ni se maquilla la aserción.

Ejecuta solo este nivel:   pytest tests/api -v
"""
import pytest

# ------------------------------------------------------------------ Constantes
USUARIO = "admin"
PASSWORD = "Admin123"

# Datos iniciales restaurados antes de cada prueba (ids 1, 2 y 3).
PRODUCTOS_INICIALES = {
    "Teclado": {"id": 1, "precio": 250.00, "stock": 10},
    "Mouse": {"id": 2, "precio": 95.50, "stock": 25},
    "Monitor": {"id": 3, "precio": 1450.00, "stock": 5},
}

# Identificador que nunca existe (los datos se reinician en cada prueba).
ID_INEXISTENTE = 9999


# ------------------------------------------------------------------- Utilidades
def _peticion(cliente, metodo, ruta, cuerpo=None):
    """Ejecuta una petición HTTP con el cliente de Playwright."""
    if cuerpo is None:
        return getattr(cliente, metodo)(ruta)
    return getattr(cliente, metodo)(ruta, data=cuerpo)


def _obtener_token(cliente):
    """Obtiene un token válido usando el mecanismo real de la app (POST /api/login)."""
    respuesta = cliente.post("/api/login", data={"usuario": USUARIO, "password": PASSWORD})
    assert respuesta.status == 200, (
        f"El login no devolvió 200: {respuesta.status} {respuesta.text()}"
    )
    return respuesta.json()["token"]


def _crear_producto(cliente, nombre="Producto de prueba", precio=99.90, stock=7):
    """Crea un producto de prueba y devuelve su JSON (id incluido)."""
    respuesta = cliente.post(
        "/api/productos", data={"nombre": nombre, "precio": precio, "stock": stock}
    )
    assert respuesta.status == 201, (
        f"No se pudo crear el producto de prueba: {respuesta.status} {respuesta.text()}"
    )
    return respuesta.json()


@pytest.fixture
def producto_de_prueba(api_autenticada):
    """Producto de prueba creado para las operaciones destructivas (PUT/DELETE).

    Nunca se opera sobre los productos iniciales: así la suite es repetible
    y respeta el aislamiento de datos del laboratorio.
    """
    return _crear_producto(api_autenticada)


# --------------------------------------------------------------- A. Autenticación
class TestAutenticacion:
    def test_login_con_credenciales_correctas_devuelve_200_y_un_token(self, api):
        respuesta = api.post("/api/login", data={"usuario": USUARIO, "password": PASSWORD})

        assert respuesta.status == 200, (
            f"Se esperaba 200 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        cuerpo = respuesta.json()
        assert "token" in cuerpo, f"La respuesta no contiene 'token': {cuerpo}"
        assert isinstance(cuerpo["token"], str)
        assert cuerpo["token"].strip() != "", "El token viene vacío"

    def test_el_token_creado_permite_usar_las_rutas_protegidas(self, api):
        token = _obtener_token(api)

        respuesta = api.get(
            "/api/productos", headers={"Authorization": f"Bearer {token}"}
        )

        assert respuesta.status == 200, (
            f"El token no fue aceptado: {respuesta.status} {respuesta.text()}"
        )

    @pytest.mark.parametrize(
        "credenciales",
        [
            pytest.param(
                {"usuario": "admin", "password": "ClaveIncorrecta"},
                id="password-incorrecta",
            ),
            pytest.param(
                {"usuario": "usuario_inexistente", "password": "Admin123"},
                id="usuario-inexistente",
            ),
        ],
    )
    def test_login_con_credenciales_incorrectas_devuelve_401(
        self, api, credenciales
    ):
        respuesta = api.post("/api/login", data=credenciales)

        assert respuesta.status == 401, (
            f"Se esperaba 401 y se recibió {respuesta.status}: {respuesta.text()}"
        )

    @pytest.mark.parametrize(
        "credenciales",
        [
            pytest.param({"password": "Admin123"}, id="falta-usuario"),
            pytest.param({"usuario": "admin"}, id="falta-password"),
            pytest.param({}, id="cuerpo-vacio"),
            pytest.param({"usuario": "", "password": "Admin123"}, id="usuario-vacio"),
            pytest.param(
                {"usuario": "   ", "password": "Admin123"}, id="usuario-solo-espacios"
            ),
            pytest.param({"usuario": "admin", "password": ""}, id="password-vacia"),
            pytest.param(
                {"usuario": "admin", "password": "12345"}, id="password-corta-5-caracteres"
            ),
            pytest.param(
                {"usuario": 123, "password": "Admin123"}, id="usuario-no-texto"
            ),
            pytest.param(
                {"usuario": "admin", "password": 123456}, id="password-no-texto"
            ),
        ],
    )
    def test_login_con_formato_invalido_devuelve_400_con_lista_de_errores(
        self, api, credenciales
    ):
        respuesta = api.post("/api/login", data=credenciales)

        assert respuesta.status == 400, (
            f"Se esperaba 400 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        cuerpo = respuesta.json()
        assert "errores" in cuerpo, f"La respuesta no contiene 'errores': {cuerpo}"
        assert isinstance(cuerpo["errores"], list), (
            f"'errores' no es una lista: {cuerpo['errores']!r}"
        )
        assert len(cuerpo["errores"]) >= 1, "La lista de errores viene vacía"


# -------------------------------------------------------------- B. Autorización
class TestAutorizacion:
    @pytest.mark.parametrize(
        "metodo, ruta, cuerpo",
        [
            pytest.param("get", "/api/productos", None, id="listar"),
            pytest.param(
                "post",
                "/api/productos",
                {"nombre": "Intruso", "precio": 10.0, "stock": 1},
                id="crear",
            ),
            pytest.param("get", "/api/productos/1", None, id="consultar-uno"),
            pytest.param(
                "put",
                "/api/productos/1",
                {"nombre": "Intruso", "precio": 10.0, "stock": 1},
                id="actualizar",
            ),
            pytest.param("delete", "/api/productos/1", None, id="eliminar"),
        ],
    )
    def test_ruta_protegida_sin_token_devuelve_401(self, api, metodo, ruta, cuerpo):
        respuesta = _peticion(api, metodo, ruta, cuerpo)

        assert respuesta.status == 401, (
            f"{metodo.upper()} {ruta} sin token debía responder 401 y respondió "
            f"{respuesta.status}: {respuesta.text()}"
        )

    @pytest.mark.parametrize(
        "cabecera",
        [
            pytest.param("Bearer token-inexistente", id="token-falso"),
            pytest.param("token-inexistente", id="sin-prefijo-bearer"),
            pytest.param("Bearer ", id="token-vacio"),
        ],
    )
    def test_ruta_protegida_con_token_invalido_devuelve_401(self, api, cabecera):
        respuesta = api.get("/api/productos", headers={"Authorization": cabecera})

        assert respuesta.status == 401, (
            f"Un token inválido debía responder 401 y respondió {respuesta.status}: "
            f"{respuesta.text()}"
        )


# ----------------------------------------------------------- C. Consulta de productos
class TestConsultaDeProductos:
    def test_listar_productos_devuelve_200_y_una_lista(self, api_autenticada):
        respuesta = api_autenticada.get("/api/productos")

        assert respuesta.status == 200, (
            f"Se esperaba 200 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        cuerpo = respuesta.json()
        assert isinstance(cuerpo, list), f"La respuesta no es una lista: {cuerpo!r}"
        assert len(cuerpo) == 3, (
            f"Se esperaban los 3 productos iniciales y llegaron {len(cuerpo)}: {cuerpo}"
        )

    def test_listar_productos_incluye_los_datos_iniciales(self, api_autenticada):
        respuesta = api_autenticada.get("/api/productos")
        assert respuesta.status == 200

        productos = {p["nombre"]: p for p in respuesta.json()}

        assert set(productos) == set(PRODUCTOS_INICIALES), (
            f"Los productos listados no son los iniciales: {sorted(productos)}"
        )
        for nombre, esperado in PRODUCTOS_INICIALES.items():
            producto = productos[nombre]
            assert producto["id"] == esperado["id"]
            assert producto["precio"] == pytest.approx(esperado["precio"])
            assert producto["stock"] == esperado["stock"]

    def test_consultar_producto_existente_devuelve_200_con_sus_datos(
        self, api_autenticada
    ):
        respuesta = api_autenticada.get("/api/productos/1")

        assert respuesta.status == 200, (
            f"Se esperaba 200 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        producto = respuesta.json()
        assert producto["id"] == 1
        assert producto["nombre"] == "Teclado"
        assert producto["precio"] == pytest.approx(250.00)
        assert producto["stock"] == 10

    def test_consultar_producto_inexistente_devuelve_404(self, api_autenticada):
        respuesta = api_autenticada.get(f"/api/productos/{ID_INEXISTENTE}")

        assert respuesta.status == 404, (
            f"El contrato exige 404 para un id inexistente y se recibió "
            f"{respuesta.status}: {respuesta.text()}"
        )


# ----------------------------------------------------------- D. Creación de productos
class TestCreacionDeProductos:
    def test_crear_producto_valido_devuelve_201_con_id_y_los_datos_enviados(
        self, api_autenticada
    ):
        datos = {"nombre": "Audífonos", "precio": 199.99, "stock": 3}

        respuesta = api_autenticada.post("/api/productos", data=datos)

        assert respuesta.status == 201, (
            f"Se esperaba 201 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        producto = respuesta.json()
        assert "id" in producto, f"El producto creado no trae 'id': {producto}"
        assert isinstance(producto["id"], int)
        assert producto["id"] > 3, (
            f"El id nuevo debe ser distinto de los iniciales (1, 2, 3): {producto['id']}"
        )
        assert producto["nombre"] == datos["nombre"]
        assert producto["precio"] == pytest.approx(datos["precio"])
        assert producto["stock"] == datos["stock"]

    def test_el_producto_creado_se_puede_recuperar_por_su_id(self, api_autenticada):
        creado = _crear_producto(api_autenticada)

        respuesta = api_autenticada.get(f"/api/productos/{creado['id']}")

        assert respuesta.status == 200, (
            f"Se esperaba 200 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        recuperado = respuesta.json()
        assert recuperado["id"] == creado["id"]
        assert recuperado["nombre"] == creado["nombre"]
        assert recuperado["precio"] == pytest.approx(creado["precio"])
        assert recuperado["stock"] == creado["stock"]

    def test_el_producto_creado_aparece_en_el_listado(self, api_autenticada):
        creado = _crear_producto(api_autenticada)

        respuesta = api_autenticada.get("/api/productos")
        assert respuesta.status == 200
        ids = [p["id"] for p in respuesta.json()]

        assert creado["id"] in ids, (
            f"El producto creado (id={creado['id']}) no aparece en el listado: {ids}"
        )

    @pytest.mark.parametrize(
        "datos",
        [
            pytest.param(
                {"nombre": "Ab", "precio": 10.0, "stock": 1}, id="nombre-demasiado-corto"
            ),
            pytest.param(
                {"nombre": "A" * 51, "precio": 10.0, "stock": 1},
                id="nombre-demasiado-largo",
            ),
            pytest.param({"precio": 10.0, "stock": 1}, id="falta-nombre"),
            pytest.param({"nombre": "SinPrecio", "stock": 1}, id="falta-precio"),
            pytest.param({"nombre": "SinStock", "precio": 10.0}, id="falta-stock"),
            pytest.param(
                {"nombre": 123, "precio": 10.0, "stock": 1}, id="nombre-no-texto"
            ),
            pytest.param(
                {"nombre": "PrecioTexto", "precio": "10", "stock": 1},
                id="precio-no-numerico",
            ),
            pytest.param(
                {"nombre": "StockTexto", "precio": 10.0, "stock": "1"},
                id="stock-no-entero",
            ),
            pytest.param(
                {"nombre": "StockDecimal", "precio": 10.0, "stock": 1.5},
                id="stock-decimal",
            ),
        ],
    )
    def test_crear_producto_con_datos_invalidos_devuelve_400_con_errores(
        self, api_autenticada, datos
    ):
        respuesta = api_autenticada.post("/api/productos", data=datos)

        assert respuesta.status == 400, (
            f"Se esperaba 400 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        cuerpo = respuesta.json()
        assert "errores" in cuerpo, f"La respuesta no contiene 'errores': {cuerpo}"
        assert isinstance(cuerpo["errores"], list)
        assert len(cuerpo["errores"]) >= 1

    @pytest.mark.parametrize(
        "precio",
        [
            pytest.param(0, id="precio-cero-entero"),
            pytest.param(0.0, id="precio-cero-decimal"),
        ],
    )
    def test_crear_producto_con_precio_cero_devuelve_400(self, api_autenticada, precio):
        """El precio debe ser MAYOR que 0: el cero es inválido (400)."""
        respuesta = api_autenticada.post(
            "/api/productos", data={"nombre": "Precio Cero", "precio": precio, "stock": 1}
        )

        assert respuesta.status == 400, (
            f"El precio {precio!r} viola la regla 'mayor que 0' y debía devolver 400; "
            f"se recibió {respuesta.status}: {respuesta.text()}"
        )
        cuerpo = respuesta.json()
        assert "errores" in cuerpo, f"La respuesta no contiene 'errores': {cuerpo}"
        assert isinstance(cuerpo["errores"], list)

    @pytest.mark.parametrize(
        "precio",
        [
            pytest.param(-1, id="precio-negativo-entero"),
            pytest.param(-0.01, id="precio-negativo-decimal"),
            pytest.param(100000.01, id="precio-sobre-el-maximo"),
            pytest.param(100001, id="precio-muy-sobre-el-maximo"),
        ],
    )
    def test_crear_producto_con_precio_fuera_de_rango_devuelve_400(
        self, api_autenticada, precio
    ):
        respuesta = api_autenticada.post(
            "/api/productos", data={"nombre": "Precio Fuera", "precio": precio, "stock": 1}
        )

        assert respuesta.status == 400, (
            f"El precio {precio!r} está fuera del rango (0, 100000] y debía devolver "
            f"400; se recibió {respuesta.status}: {respuesta.text()}"
        )
        assert isinstance(respuesta.json()["errores"], list)

    @pytest.mark.parametrize(
        "stock",
        [
            pytest.param(-1, id="stock-menos-uno"),
            pytest.param(-10, id="stock-muy-negativo"),
        ],
    )
    def test_crear_producto_con_stock_negativo_devuelve_400(
        self, api_autenticada, stock
    ):
        respuesta = api_autenticada.post(
            "/api/productos", data={"nombre": "Stock Negativo", "precio": 10.0, "stock": stock}
        )

        assert respuesta.status == 400, (
            f"El stock {stock!r} es negativo y debía devolver 400; se recibió "
            f"{respuesta.status}: {respuesta.text()}"
        )
        assert isinstance(respuesta.json()["errores"], list)

    @pytest.mark.parametrize(
        "nombre, precio, stock",
        [
            pytest.param("Abc", 0.01, 0, id="nombre-minimo-precio-minimo-stock-minimo"),
            pytest.param("A" * 50, 100000, 0, id="nombre-maximo-precio-maximo"),
        ],
    )
    def test_crear_producto_en_los_limites_validos_devuelve_201(
        self, api_autenticada, nombre, precio, stock
    ):
        respuesta = api_autenticada.post(
            "/api/productos", data={"nombre": nombre, "precio": precio, "stock": stock}
        )

        assert respuesta.status == 201, (
            f"Los límites válidos debían devolver 201 y devolvieron "
            f"{respuesta.status}: {respuesta.text()}"
        )

    def test_crear_producto_cuyo_nombre_tiene_espacios_extremos_usa_el_largo_real(
        self, api_autenticada
    ):
        """El largo del nombre se cuenta sin espacios al inicio o al final."""
        respuesta = api_autenticada.post(
            "/api/productos", data={"nombre": "  Abc  ", "precio": 10.0, "stock": 1}
        )

        assert respuesta.status == 201, (
            f"'Abc' tiene 3 caracteres válidos y debía devolver 201; se recibió "
            f"{respuesta.status}: {respuesta.text()}"
        )

    def test_crear_producto_cuyo_nombre_solo_tiene_dos_letras_devuelve_400(
        self, api_autenticada
    ):
        """'  Ab  ' tiene 2 caracteres reales: es inválido aunque ocupe 6 espacios."""
        respuesta = api_autenticada.post(
            "/api/productos", data={"nombre": "  Ab  ", "precio": 10.0, "stock": 1}
        )

        assert respuesta.status == 400, (
            f"Se esperaba 400 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        assert isinstance(respuesta.json()["errores"], list)


# -------------------------------------------------------- E. Actualización de productos
class TestActualizacionDeProductos:
    def test_actualizar_producto_existente_devuelve_200_con_los_cambios(
        self, producto_de_prueba, api_autenticada
    ):
        cambios = {"nombre": "Producto actualizado", "precio": 123.45, "stock": 42}

        respuesta = api_autenticada.put(
            f"/api/productos/{producto_de_prueba['id']}", data=cambios
        )

        assert respuesta.status == 200, (
            f"Se esperaba 200 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        producto = respuesta.json()
        assert producto["id"] == producto_de_prueba["id"]
        assert producto["nombre"] == cambios["nombre"]
        assert producto["precio"] == pytest.approx(cambios["precio"])
        assert producto["stock"] == cambios["stock"]

    def test_los_cambios_de_un_update_persisten_en_la_consulta_posterior(
        self, producto_de_prueba, api_autenticada
    ):
        cambios = {"nombre": "Nombre persistido", "precio": 55.50, "stock": 9}

        actualizacion = api_autenticada.put(
            f"/api/productos/{producto_de_prueba['id']}", data=cambios
        )
        assert actualizacion.status == 200

        consulta = api_autenticada.get(f"/api/productos/{producto_de_prueba['id']}")
        assert consulta.status == 200
        guardado = consulta.json()
        assert guardado["nombre"] == cambios["nombre"]
        assert guardado["precio"] == pytest.approx(cambios["precio"])
        assert guardado["stock"] == cambios["stock"]

    def test_actualizar_producto_inexistente_devuelve_404(self, api_autenticada):
        respuesta = api_autenticada.put(
            f"/api/productos/{ID_INEXISTENTE}",
            data={"nombre": "No existe", "precio": 10.0, "stock": 1},
        )

        assert respuesta.status == 404, (
            f"Se esperaba 404 y se recibió {respuesta.status}: {respuesta.text()}"
        )

    @pytest.mark.parametrize(
        "datos",
        [
            pytest.param(
                {"nombre": "Ab", "precio": 10.0, "stock": 1}, id="nombre-demasiado-corto"
            ),
            pytest.param(
                {"nombre": "A" * 51, "precio": 10.0, "stock": 1},
                id="nombre-demasiado-largo",
            ),
            pytest.param(
                {"nombre": "PrecioNeg", "precio": -5, "stock": 1}, id="precio-negativo"
            ),
            pytest.param(
                {"nombre": "PrecioCaro", "precio": 100001, "stock": 1},
                id="precio-sobre-el-maximo",
            ),
            pytest.param(
                {"nombre": "StockNeg", "precio": 10.0, "stock": -1}, id="stock-negativo"
            ),
            pytest.param({"precio": 10.0, "stock": 1}, id="falta-nombre"),
            pytest.param({}, id="cuerpo-vacio"),
        ],
    )
    def test_actualizar_producto_con_datos_invalidos_devuelve_400(
        self, producto_de_prueba, api_autenticada, datos
    ):
        respuesta = api_autenticada.put(
            f"/api/productos/{producto_de_prueba['id']}", data=datos
        )

        assert respuesta.status == 400, (
            f"Se esperaba 400 y se recibió {respuesta.status}: {respuesta.text()}"
        )
        cuerpo = respuesta.json()
        assert "errores" in cuerpo, f"La respuesta no contiene 'errores': {cuerpo}"
        assert isinstance(cuerpo["errores"], list)

    def test_actualizar_producto_con_precio_cero_devuelve_400(
        self, producto_de_prueba, api_autenticada
    ):
        """El precio debe ser MAYOR que 0: el cero es inválido (400)."""
        respuesta = api_autenticada.put(
            f"/api/productos/{producto_de_prueba['id']}",
            data={"nombre": "Precio Cero", "precio": 0, "stock": 1},
        )

        assert respuesta.status == 400, (
            f"El precio 0 viola la regla 'mayor que 0' y debía devolver 400; se recibió "
            f"{respuesta.status}: {respuesta.text()}"
        )
        assert isinstance(respuesta.json()["errores"], list)


# --------------------------------------------------------- F. Eliminación de productos
class TestEliminacionDeProductos:
    def test_eliminar_producto_de_prueba_devuelve_204(self, producto_de_prueba, api_autenticada):
        respuesta = api_autenticada.delete(f"/api/productos/{producto_de_prueba['id']}")

        assert respuesta.status == 204, (
            f"Se esperaba 204 y se recibió {respuesta.status}: {respuesta.text()}"
        )

    def test_eliminar_producto_lo_quita_del_listado_y_conserva_los_demas(
        self, producto_de_prueba, api_autenticada
    ):
        respuesta = api_autenticada.delete(f"/api/productos/{producto_de_prueba['id']}")
        assert respuesta.status == 204

        listado = api_autenticada.get("/api/productos")
        assert listado.status == 200
        productos = listado.json()
        ids = [p["id"] for p in productos]

        assert producto_de_prueba["id"] not in ids, (
            f"El producto eliminado (id={producto_de_prueba['id']}) sigue en el "
            f"listado: {ids}"
        )
        assert ids == [1, 2, 3], (
            f"Los productos iniciales debieron quedar intactos, el listado es {ids}"
        )

    def test_consultar_un_producto_eliminado_devuelve_404(
        self, producto_de_prueba, api_autenticada
    ):
        eliminacion = api_autenticada.delete(f"/api/productos/{producto_de_prueba['id']}")
        assert eliminacion.status == 204

        respuesta = api_autenticada.get(f"/api/productos/{producto_de_prueba['id']}")

        assert respuesta.status == 404, (
            f"Un producto eliminado ya no existe: el contrato exige 404 y se recibió "
            f"{respuesta.status}: {respuesta.text()}"
        )

    def test_eliminar_producto_inexistente_devuelve_404(self, api_autenticada):
        respuesta = api_autenticada.delete(f"/api/productos/{ID_INEXISTENTE}")

        assert respuesta.status == 404, (
            f"Se esperaba 404 y se recibió {respuesta.status}: {respuesta.text()}"
        )

    def test_eliminar_dos_veces_el_mismo_producto_devuelve_404_la_segunda(
        self, producto_de_prueba, api_autenticada
    ):
        primera = api_autenticada.delete(f"/api/productos/{producto_de_prueba['id']}")
        assert primera.status == 204

        segunda = api_autenticada.delete(f"/api/productos/{producto_de_prueba['id']}")

        assert segunda.status == 404, (
            f"Se esperaba 404 y se recibió {segunda.status}: {segunda.text()}"
        )
