# Informe · Laboratorio 8 · Pruebas automatizadas

**Equipo:** (número)
**Integrantes:** (nombres y carnés)

> Alcance de esta entrega: **Parte 4 · Pruebas E2E con Playwright** (`tests/e2e/test_e2e.py`).
> Las Partes 2 (unitarias) y 3 (API) siguen con la suite de ejemplo de la plantilla, por lo que
> sus columnas en la tabla comparativa se marcan como no medidas para esas partes.

## 1. Defectos encontrados

Un reporte por defecto. Deja la prueba que lo detecta FALLANDO en tu entrega.

| ID | Nivel que lo detectó | Prueba (archivo::función) | Pasos para reproducir | Resultado esperado (según la especificación) | Resultado obtenido |
|---|---|---|---|---|---|
| E2E-001 | E2E (sistema, navegador real) | `tests/e2e/test_e2e.py::test_eliminar_producto_borra_solo_ese_producto_y_no_afecta_a_los_demas` | 1) Iniciar sesión con `admin` / `Admin123`. 2) En `/productos` (Teclado id 1, Mouse id 2, Monitor id 3) pulsar **Eliminar** en la fila de **Mouse**. 3) Observar la tabla. | El botón "Eliminar" borra **ese** producto: desaparece Mouse (id 2) y Teclado (1) y Monitor (3) siguen con 250.00/10 y 1450.00/5, sin cambios. | Se borró **Teclado** (id 1) y **Mouse siguió en la tabla** con sus datos intactos; Monitor no cambió. El log del servidor registra `POST /productos/1/eliminar` (el id del primer producto) en lugar de `/productos/2/eliminar`. |
| E2E-002 | E2E (sistema, navegador real) | `tests/e2e/test_e2e.py::test_formulario_rechaza_precio_cero` | 1) Iniciar sesión con `admin` / `Admin123`. 2) "Nuevo producto". 3) Nombre `Producto Sin Costo`, Precio `0`, Stock `1`. 4) Guardar. | La regla "Precio: número **mayor que 0**" se aplica: la app informa el error y **no** crea el producto. | La app **aceptó** el producto sin mostrar ningún error: redirigió a `/productos`, mostró el mensaje "Producto creado" y el producto aparece en la tabla con id 4 y precio `0.00`. |
| — | — | — | — | — | (fila reservada: no se confirmó un tercer defecto en el nivel E2E) |

### 1.1 Detalle de los defectos E2E

#### E2E-001 · "Eliminar" borra siempre el primer producto de la tabla

* **Escenario afectado:** Escenario D · Eliminar producto (y cualquier flujo de borrado de la interfaz web).
* **Causa raíz identificada:** `app/templates/productos.html:25` construye el `action` del formulario
  con `url_for('eliminar_producto', pid=productos[0].id)`, es decir, **siempre el id del primer
  producto de la lista**, en lugar del `p.id` de la fila. El resto de filas apuntan al mismo destino
  (verificado en el DOM: las 3 filas iniciales tenían `action="/productos/1/eliminar"`).
* **Pasos para reproducirlo:**
  1. `python run.py` (o dejar que pytest levante la app) y abrir `http://127.0.0.1:5000/login`.
  2. Iniciar sesión con `admin` / `Admin123`.
  3. En la tabla de productos pulsar el botón **Eliminar** de la fila **Mouse** (id 2).
  4. La página muestra "Producto eliminado", pero la tabla queda: `Mouse (2)`, `Monitor (3)`;
     se borró `Teclado (1)`.
* **Resultado esperado (según la especificación):** "Eliminar" borra **ese** producto, muestra
  "Producto eliminado" y los demás productos no cambian ⇒ debe desaparecer Mouse y Teclado y Monitor
  deben permanecer idénticos.
* **Resultado real observado:** el mensaje "Producto eliminado" sí aparece, pero el registro borrado
  es el primero de la tabla (Teclado, id 1); el producto sobre el que se hizo clic (Mouse, id 2)
  permanece en la tabla. El mensaje de éxito es engañoso: comunica que se borró el producto
  equivocado.
* **Prueba que lo detecta:** `tests/e2e/test_e2e.py::test_eliminar_producto_borra_solo_ese_producto_y_no_afecta_a_los_demas`
  (la prueba queda **fallando** en la entrega).
* **Mensaje de error / aserción fallida relevante:**
  ```
  AssertionError: La tabla no quedó como exige la especificación (solo debe desaparecer el producto eliminado):
    esperado: {'Teclado': {'id': '1', 'precio': '250.00', 'stock': '10'}, 'Monitor': {'id': '3', 'precio': '1450.00', 'stock': '5'}}
    obtenido: {'Mouse':  {'id': '2', 'precio': '95.50',  'stock': '25'}, 'Monitor': {'id': '3', 'precio': '1450.00', 'stock': '5'}}
  ```
  Traza del servidor durante la prueba:
  `POST /productos/1/eliminar HTTP/1.1" 302` (la fila pulsada era la de Mouse, id 2).
* **Severidad sugerida: ALTA.** Destrucción silenciosa de un registro que el usuario no eligió
  (pérdida de datos del inventario) y mensaje de éxito falso; ocurre en el 100 % de los borrados
  desde la interfaz web salvo que el producto borrado sea el primero de la lista.
* **Estado:** pendiente de corrección por el equipo de desarrollo.

#### E2E-002 · El formulario web acepta productos con precio 0

* **Escenario afectado:** Extra · validación del formulario web (regla de validación de la
  especificación: "Precio | Número **mayor que 0** y como máximo 100,000").
* **Causa raíz identificada:** `app/validaciones.py:54` evalúa `elif precio < 0`, por lo que el
  precio `0` pasa la validación (debería ser `precio <= 0`). El propio mensaje de error de la app
  ("El precio debe ser mayor que 0 y como máximo 100,000") contradice la comprobación realizada.
  El mismo defecto afecta a la API (`POST /api/productos` y `PUT /api/productos/<id>`).
* **Pasos para reproducirlo:**
  1. Iniciar sesión con `admin` / `Admin123`.
  2. "Nuevo producto" → Nombre `Producto Sin Costo`, Precio `0`, Stock `1` → **Guardar**.
  3. La app redirige a `/productos` con el mensaje "Producto creado" y el producto aparece en la
     tabla con precio `0.00`.
* **Resultado esperado (según la especificación):** la app informa el error y no crea el producto.
* **Resultado real observado:** no se muestra ningún mensaje de error; el producto se crea y queda
  registrado con precio 0.00 (id 4).
* **Prueba que lo detecta:** `tests/e2e/test_e2e.py::test_formulario_rechaza_precio_cero`
  (la prueba queda **fallando** en la entrega).
* **Mensaje de error / aserción fallida relevante:**
  ```
  >       expect(page.get_by_role("alert")).to_be_visible()
  E       AssertionError: Locator expected to be visible
  E       Actual value: None
  E       Error: element(s) not found
  ```
  (no existe el `role="alert"` con el error de validación; en la tabla aparece la fila
  `4 Producto Sin Costo 0.00 1 Editar Eliminar`).
* **Severidad sugerida: MEDIA.** Permite registrar en el inventario productos sin costo; no rompe
  el flujo ni corrompe otros datos, pero contradice la regla de negocio publicada.
* **Estado:** pendiente de corrección por el equipo de desarrollo.
  *Nota:* este defecto también es detectable con una prueba unitaria de `validar_producto`
  (Parte 2), que es más barata y rápida que la prueba E2E.

### 1.2 Problemas pendientes de diagnóstico

Ninguno. Los dos fallos de la suite E2E se investigaron y se confirmaron como defectos reales de
la aplicación (causa raíz identificada en `app/templates/productos.html:25` y
`app/validaciones.py:54`), no como errores de localizador, de preparación de datos ni de entorno.
No se reporta ningún defecto a partir de un simple fallo de prueba.

### 1.3 Observación fuera del alcance de la Parte 4 (API)

Detectado al revisar el contrato de la API (Parte 3, no implementada en esta entrega) y verificado
con una petición real: `GET /api/productos/999` (id inexistente) responde **200 `{}`**, cuando el
contrato de la guía exige **404**. Lo reporta el nivel API, no el E2E, por lo que **no** se incluye
en la tabla de defectos E2E ni se deja ninguna prueba E2E fallando por este punto.

## 2. Tabla comparativa de niveles

Tiempo: ejecuta `pytest tests/<nivel> -q` y anota el tiempo que reporta pytest.

| Criterio | Unitarias | API | E2E |
|---|---|---|---|
| Número de pruebas | 1 (solo el ejemplo de la plantilla; Parte 2 pendiente) | 1 (solo el ejemplo de la plantilla; Parte 3 pendiente) | 11 collected (10 pruebas propias + el ejemplo de la plantilla; una de ellas parametrizada con 3 rutas) |
| Tiempo total de ejecución (s) | 0.03 | 0.83 | 9.8 (mediana de 3 corridas: 9.86 / 9.75 / 9.50; 14.6 en la primera corrida con navegador en frío) |
| Tiempo promedio por prueba (s) | 0.03 | 0.83 | 0.89 |
| Defectos detectados (IDs) | n/d — Parte 2 pendiente | n/d — Parte 3 pendiente | E2E-001, E2E-002 |
| ¿Qué cambio en la app rompería estas pruebas sin que haya un defecto? | n/d — Parte 2 pendiente | n/d — Parte 3 pendiente | Cambios de *copy* o de maquetación que no son defectos: renombrar el botón "Ingresar"/"Guardar"/"Eliminar", cambiar el texto de "Bienvenido, admin" o de "Producto creado", o reordenar las columnas de la tabla (las pruebas comprueban la celda por posición: ID, Nombre, Precio, Stock). |
| Costo de mantenimiento (Alto / Medio / Bajo) y por qué | n/d — Parte 2 pendiente | n/d — Parte 3 pendiente | **Medio.** No depende de la base de datos ni del backend, pero sí del texto de la interfaz, del orden de las columnas y de la existencia del navegador; además cada corrida paga el arranque de Chromium (~3-5 s). |

### 2.1 Comandos ejecutados y tiempos reales

Ejecutados en el entorno del laboratorio (Python 3.14.6, pytest 9.1.1, pytest-playwright 0.10.0,
Chromium de Playwright):

| Comando | Resultado | Tiempo reportado por pytest |
|---|---|---|
| `pytest tests/e2e -v` | 9 passed, 2 failed | 9.8 s (mediana de 3 corridas) |
| `pytest tests/e2e --headed --slowmo 500` | 9 passed, 2 failed | 37.39 s |
| `pytest tests/e2e --durations=0 -q` | 9 passed, 2 failed | 9.54 s |
| `pytest tests/unitarias -q` | 1 passed | 0.03 s |
| `pytest tests/api -q` | 1 passed | 0.83 s |
| `pytest -v` (suite completa, antes de esta entrega) | 3 passed | 1.07 s |

Las 2 pruebas que fallan son, exactamente, las que detectan E2E-001 y E2E-002. Se dejan fallando a
propósito (no se marcaron como `skip` ni `xfail`).

Pruebas E2E slower más lentas por `--durations=0`: `test_formulario_rechaza_precio_cero` 5.32 s
(falla y agota el auto-waiting de `expect`), `test_login_exitoso...` 1.03 s (espera el mensaje de
bienvenida, que la app muestra con 800 ms de retraso), `test_crear_producto...` 0.49 s.

## 3. Recomendación (máximo media página)

*(Pendiente de la Parte 5 · Análisis e informe, con los datos definitivos de los tres niveles una
vez implementadas las Partes 2 y 3. Los datos medidos del nivel E2E ya están en la sección 2.)*

El equipo de Inventario IS1 tiene un pipeline de CI. Recomienda qué pruebas correr:

- en cada commit,
- en cada pull request,
- antes de liberar a producción.

Justifica con tus datos de la tabla y con la pirámide de pruebas.
Responde además: ¿qué defecto NO habría detectado una suite solo de pruebas E2E, o solo de pruebas
unitarias?
