# Informe · Laboratorio 8 · Pruebas automatizadas

**Equipo:** 01
**Integrantes:**
- Paula Nicolle West Ortiz - 1245524
- Juan Pablo Estrada Rodriguez - 1056124
- Christopher Conrado Lopez Vicente - 1053824

## 1. Defectos encontrados

Un reporte por defecto. Deja la prueba que lo detecta FALLANDO en tu entrega.

| ID | Nivel que lo detectó | Prueba (archivo::función) | Pasos para reproducir | Resultado esperado (según la especificación) | Resultado obtenido |
|---|---|---|---|---|---|
| DEF-01 | API (integración) → **API-001** | `tests/api/test_api.py::TestConsultaDeProductos::test_consultar_producto_inexistente_devuelve_404` y `tests/api/test_api.py::TestEliminacionDeProductos::test_consultar_un_producto_eliminado_devuelve_404` | 1) `POST /api/login` con `admin`/`Admin123` → 200 con token. 2) `GET /api/productos/9999` con `Authorization: Bearer <token>`. | **404** (el contrato dice: `GET /api/productos/<id>` · No existe → 404) | **200** con cuerpo `{}` |
| DEF-02 | API (integración) → **API-002** | `tests/api/test_api.py::TestCreacionDeProductos::test_crear_producto_con_precio_cero_devuelve_400[precio-cero-entero]`, `[precio-cero-decimal]` y `tests/api/test_api.py::TestActualizacionDeProductos::test_actualizar_producto_con_precio_cero_devuelve_400` | 1) `POST /api/login` con `admin`/`Admin123` → 200 con token. 2) `POST /api/productos` con `{"nombre": "Precio Cero", "precio": 0, "stock": 1}` (o `PUT /api/productos/<id>` con el mismo cuerpo). | **400 + `{"errores": [...]}`** (la especificación exige precio **mayor que 0**) | **201** con `{"id": 4, "nombre": "Precio Cero", "precio": 0, "stock": 1}` (en `PUT`: **200** con el producto ya actualizado) |
| DEF-03 | — | — | — | — | No se confirmó un tercer defecto en el nivel de API (65 pruebas ejecutadas, 5 fallos, todos atribuibles a API-001 y API-002) |

> Los reportes completos de **API-001** y **API-002** están en la sección 4.3.

## 2. Tabla comparativa de niveles

Tiempo: ejecuta `pytest tests/<nivel> -q` y anota el tiempo que reporta pytest.

| Criterio | Unitarias | API | E2E |
|---|---|---|---|
| Número de pruebas | no medido en esta entrega | **65** (60 aprobadas + 5 fallidas) | no medido en esta entrega |
| Tiempo total de ejecución (s) | no medido en esta entrega | **2.02 – 3.35 s** (12 ejecuciones; mediana ≈ 2.69 s, promedio ≈ 2.70 s) | no medido en esta entrega |
| Tiempo promedio por prueba (s) | no medido en esta entrega | **0.042 s** (2.70 s / 65 pruebas) | no medido en esta entrega |
| Defectos detectados (IDs) | no medido en esta entrega | **API-001, API-002** | no medido en esta entrega |
| ¿Qué cambio en la app rompería estas pruebas sin que haya un defecto? | no medido en esta entrega | Cambiar el contrato HTTP (códigos de estado, forma del JSON `{"token"}` / `{"errores"}`), el nombre de las rutas, el mecanismo de autenticación (`Authorization: Bearer <token>`) o los datos iniciales restaurados por `POST /api/reset` | no medido en esta entrega |
| Costo de mantenimiento (Alto / Medio / Bajo) y por qué | no medido en esta entrega | **Medio**: depende del contrato HTTP estable, no de selectores de UI, pero cualquier renombrada de campo o de ruta rompe muchas aserciones a la vez | no medido en esta entrega |

## 3. Recomendación (máximo media página)

El equipo de Inventario IS1 tiene un pipeline de CI. Recomienda qué pruebas correr:

- en cada commit,
- en cada pull request,
- antes de liberar a producción.

Justifica con tus datos de la tabla y con la pirámide de pruebas.
Responde además: ¿qué defecto NO habría detectado una suite solo de pruebas E2E, o solo de pruebas unitarias?

## 4. Pruebas de API (nivel de integración) — detalle de esta entrega

Esta sección documenta únicamente lo ejecutado y observado en el nivel de integración (API).
Las secciones 1 y 2 reciben los datos medidos de este nivel; los niveles unitario y E2E no
forman parte de esta entrega, por lo que sus columnas quedan sin medir (no se inventan datos).

### 4.1 Alcance cubierto

Archivo: `tests/api/test_api.py` (único archivo de código modificado).
Pruebas HTTP puras con `playwright.request` (sin navegador, sin esperas fijas).

| Bloque | Endpoints | Qué se verifica |
|---|---|---|
| A. Autenticación | `POST /api/login` | 200 + `token` utilizable; 401 con credenciales incorrectas; 400 + `errores` (lista) con formato inválido |
| B. Autorización | `GET/POST /api/productos`, `GET/PUT/DELETE /api/productos/1` | 401 exacto sin token y con token inválido |
| C. Consulta | `GET /api/productos`, `GET /api/productos/<id>` | 200 + lista, datos iniciales (Teclado/Mouse/Monitor), 404 para id inexistente |
| D. Creación | `POST /api/productos` | 201 + `id` + datos devueltos, recuperabilidad por `GET`, 400 + `errores` en casos negativos, límites válidos |
| E. Actualización | `PUT /api/productos/<id>` | 200 + cambios, persistencia verificada con un `GET` posterior, 404 inexistente, 400 datos inválidos |
| F. Eliminación | `DELETE /api/productos/<id>` | 204 exacto, ausencia en el listado, 404 inexistente y en el segundo borrado |

Datos de prueba: todas las operaciones destructivas (`PUT`, `DELETE`) se ejecutan sobre un
producto de prueba creado por la fixture local `producto_de_prueba`. Los tres productos
iniciales nunca se modifican ni se borran; la fixture compartida `datos_limpios` (POST `/api/reset`)
restaura el estado inicial antes de cada prueba.

### 4.2 Resultado de la ejecución (medido)

| Métrica | Valor observado |
|---|---|
| Pruebas ejecutadas | **65** |
| Pruebas aprobadas | **60** |
| Pruebas fallidas | **5** |
| Pruebas omitidas / marcadas (skip, xfail) | **0** |
| Defectos confirmados que explican los 5 fallos | **2** (API-001, API-002) |
| Fallos pendientes de diagnóstico | **0** |
| Tiempo total reportado por pytest | **2.02 – 3.35 s** (12 ejecuciones: 3.35, 3.19, 3.14, 3.11, 3.07, 2.82, 2.55, 2.41, 2.24, 2.23, 2.23, 2.02 s) |
| Promedio por prueba | **0.042 s** (2.70 s / 65) |
| Prueba más lenta | `TestAutenticacion::test_login_con_credenciales_correctas_devuelve_200_y_un_token` — 0.29 s de *setup* (arranque de Playwright); el resto de *setup* ≤ 0.09 s |

Comandos utilizados (desde la carpeta del proyecto, con el entorno virtual `.venv`):

```powershell
pytest tests/api -v                 # ejecución principal
pytest tests/api -v --durations=0   # medición de duraciones
pytest tests/api -q                 # 2 ejecuciones de control de repetibilidad
```

Entorno: Windows (win32), Python 3.14.8, pytest 9.1.1, pytest-playwright 0.10.0,
playwright 1.64.0, Flask 3.1.3. La aplicación de prueba la levanta automáticamente la
fixture `base_url` (Werkzeug) en `http://127.0.0.1:5000`; no se usó navegador gráfico.

Las ejecuciones son repetibles: dos corridas consecutivas de `pytest tests/api -q` dieron
exactamente el mismo resultado (5 fallidas, 60 aprobadas), sin residuos de ejecuciones anteriores.

### 4.3 Defectos confirmados de la API

#### API-001 · `GET /api/productos/<id>` responde 200 en lugar de 404

| Campo | Detalle |
|---|---|
| **Identificador** | API-001 (registrado también como DEF-01 en la sección 1) |
| **Endpoint y método** | `GET /api/productos/<id>` (también afecta a la verificación posterior a `DELETE`) |
| **Escenario probado** | Consultar un producto con un identificador que no existe en el inventario; y consultar un producto que acaba de ser eliminado. |
| **Datos enviados** | `Authorization: Bearer <token>` obtenido de `POST /api/login` con `usuario=admin`, `password=Admin123`. Para el caso del producto eliminado: id devuelto por `POST /api/productos` con `{"nombre": "Producto de prueba", "precio": 99.90, "stock": 7}`. Para el id inexistente: `9999`. |
| **Pasos para reproducirlo** | 1) `POST /api/login` con `{"usuario": "admin", "password": "Admin123"}` → `200` con token. 2) `GET /api/productos/9999` con la cabecera `Authorization: Bearer <token>`. 3) Observar el código y el cuerpo de la respuesta. (Variante: crear un producto, borrarlo con `DELETE /api/productos/<id>` y volver a hacer `GET` sobre ese id.) |
| **Código HTTP esperado** | `404` |
| **Código HTTP real** | `200` |
| **Resultado esperado según la especificación** | La tabla "Contrato de la API" de la guía exige `GET /api/productos/<id>` · No existe → **404**. Un recurso inexistente debe reportarse como tal. |
| **Resultado real y diferencias observadas** | La API responde `200 OK` con el cuerpo JSON vacío `{}`. La diferencia es doble: el código de estado (200 en lugar de 404) y el cuerpo (un objeto vacío, no un cuerpo de error). El cliente que solo comprueba el código de estado no puede distinguir "el producto existe y está vacío" de "el producto no existe"; en consecuencia, el flujo `DELETE` tampoco puede confirmarse por `GET` (la prueba `test_eliminar_producto_lo_quita_del_listado_y_conserva_los_demas` sí lo confirma por el listado, y esa parte sí pasa). |
| **Pruebas que lo detectaron** | `tests/api/test_api.py::TestConsultaDeProductos::test_consultar_producto_inexistente_devuelve_404`<br>`tests/api/test_api.py::TestEliminacionDeProductos::test_consultar_un_producto_eliminado_devuelve_404` |
| **Evidencia** | `AssertionError: El contrato exige 404 para un id inexistente y se recibió 200: {}` → `assert 200 == 404`<br>`AssertionError: Un producto eliminado ya no existe: el contrato exige 404 y se recibió 200: {}` → `assert 200 == 404`<br>Respuesta recibida: `HTTP/1.1 200 OK` con cuerpo `{}`. |
| **Ubicación sospechosa en el código** | `app/__init__.py`, ruta `api_obtener`: la rama de producto inexistente devuelve `jsonify({}), 200`. (No se modificó: la corrección es de desarrollo.) |
| **Severidad sugerida** | **Media.** No hay corrupción de datos ni riesgo de seguridad, y un cliente atento puede deducir la ausencia por el cuerpo `{}`; sin embargo, rompe el contrato documentado y hace que el resultado de un `DELETE` no sea verificable por `GET`, lo que puede llevar a lógica de cliente defectuosa (p. ej. marcar como "eliminado" solo si el `GET` devuelve 404). |
| **Estado** | Pendiente de corrección por desarrollo |

#### API-002 · La validación de precio acepta el valor 0 (debe ser mayor que 0)

| Campo | Detalle |
|---|---|
| **Identificador** | API-002 (registrado también como DEF-02 en la sección 1) |
| **Endpoint y método** | `POST /api/productos` y `PUT /api/productos/<id>` |
| **Escenario probado** | Crear y actualizar un producto cuyo precio es exactamente 0 (inválido según la regla "precio mayor que 0"). |
| **Datos enviados** | `POST /api/productos` → `{"nombre": "Precio Cero", "precio": 0, "stock": 1}` y la variante `{"nombre": "Precio Cero", "precio": 0.0, "stock": 1}`.<br>`PUT /api/productos/4` → `{"nombre": "Precio Cero", "precio": 0, "stock": 1}` (id 4 = producto de prueba creado en la misma prueba). |
| **Pasos para reproducirlo** | 1) `POST /api/login` con `{"usuario": "admin", "password": "Admin123"}` → `200` con token. 2) `POST /api/productos` con `{"nombre": "Precio Cero", "precio": 0, "stock": 1}`. 3) Observar el código y el cuerpo de la respuesta. (Variante `PUT`: actualizar un producto existente con el mismo cuerpo.) |
| **Código HTTP esperado** | `400` con `{"errores": [...]}` |
| **Código HTTP real** | `201` en `POST` y `200` en `PUT`, ambos con el producto persistido |
| **Resultado esperado según la especificación** | La tabla de reglas de validación exige: *Precio → Número **mayor que 0** y como máximo 100,000*. El 0 no cumple la regla, así que la API debe rechazarlo con `400` y una lista `errores` (igual que ya hace con los precios negativos y con los mayores a 100,000). |
| **Resultado real y diferencias observadas** | El precio `0` (y `0.0`) se acepta y queda **almacenado** en el inventario: la API devuelve `201 {"id": 4, "nombre": "Precio Cero", "precio": 0, "stock": 1}`; en `PUT` devuelve `200 {"id": 4, "nombre": "Precio Cero", "precio": 0, "stock": 1}`. La diferencia observable es doble: falta el `400` y falta la lista `errores`. Nótese que el propio mensaje de error del producto ("El precio debe ser mayor que 0 y como máximo 100,000") contradice el comportamiento: la regla implementada solo descarta los negativos, no el cero. |
| **Pruebas que lo detectaron** | `tests/api/test_api.py::TestCreacionDeProductos::test_crear_producto_con_precio_cero_devuelve_400[precio-cero-entero]`<br>`tests/api/test_api.py::TestCreacionDeProductos::test_crear_producto_con_precio_cero_devuelve_400[precio-cero-decimal]`<br>`tests/api/test_api.py::TestActualizacionDeProductos::test_actualizar_producto_con_precio_cero_devuelve_400` |
| **Evidencia** | `AssertionError: El precio 0 viola la regla 'mayor que 0' y debía devolver 400; se recibió 201: {"id":4,"nombre":"Precio Cero","precio":0,"stock":1}` → `assert 201 == 400`<br>`AssertionError: El precio 0.0 viola la regla 'mayor que 0' y debía devolver 400; se recibió 201: {"id":4,"nombre":"Precio Cero","precio":0.0,"stock":1}` → `assert 201 == 400`<br>`AssertionError: El precio 0 viola la regla 'mayor que 0' y debía devolver 400; se recibió 200: {"id":4,"nombre":"Precio Cero","precio":0,"stock":1}` → `assert 200 == 400` |
| **Ubicación sospechosa en el código** | `app/validaciones.py`, función `validar_producto`: la condición `precio < 0 or precio > PRECIO_MAX` acepta el cero, aunque el texto del error exija "mayor que 0". (No se modificó: la corrección es de desarrollo.) |
| **Severidad sugerida** | **Media.** Permite persistir en el inventario productos con precio 0, un dato de negocio inválido que afecta la valorización del stock y que queda almacenado sin ninguna advertencia (el resto de la validación sí es consistente). No hay pérdida de datos, brecha de seguridad ni caída del servicio, y la corrección es de una línea, por lo que no se considera alta. |
| **Estado** | Pendiente de corrección por desarrollo |

### 4.4 Fallos pendientes de diagnóstico

**Ninguno.** Los 5 fallos de la ejecución se explican íntegramente por los dos defectos
confirmados arriba (3 pruebas detectan API-002 y 2 pruebas detectan API-001). No quedaron
fallos sin causa identificada, ni pruebas marcadas con `skip`/`xfail`, ni aserciones
relajadas para hacerlas pasar.

### 4.5 Notas de método

- No se modificó ningún archivo de `app/`, ni `tests/conftest.py`, ni `tests/api/conftest.py`,
  ni las pruebas unitarias o E2E. Solo se modificaron `tests/api/test_api.py` y este `INFORME.md`.
- Las 5 pruebas que fallan se dejan fallando a propósito: son la evidencia de los defectos.
  No se usaron `skip`, `xfail` ni captura de excepciones para ocultarlas.
- Todas las solicitudes se hicieron con las fixtures existentes `api` y `api_autenticada`;
  el token manual se obtuvo por el mecanismo real de la aplicación (`POST /api/login`).
- Los casos repetitivos negativos usan `@pytest.mark.parametrize` con `pytest.param(..., id=...)`
  para que el reporte identifique cada partición de equivalencia y cada valor límite.
- Cobertura por valores límite comprobada: nombre 3 / 50 caracteres (válidos) y 2 / 51
  (inválidos); precio 0.01 / 100,000 (válidos) y 0 / negativo / 100,000.01 / 100,001;
  stock 0 (válido) y negativos (inválidos); contraseña de 5 caracteres (inválida) y 6 (válida).
