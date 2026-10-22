# Informe · Laboratorio 8 · Pruebas automatizadas

**Equipo:** (número)
**Integrantes:** (nombres y carnés)

> Alcance de esta entrega: **Parte 4 · Pruebas E2E con Playwright** (`tests/e2e/test_e2e.py`).
> Las Partes 2 (unitarias) y 3 (API) siguen con la suite de ejemplo de la plantilla, por lo que
> sus columnas en la tabla comparativa se marcan como no medidas para esas partes.

**Alcance de este informe:** nivel UNITARIO (`tests/unitarias/test_unitarias.py`), aplicado sobre
`app/validaciones.py`. Los niveles API y E2E se midieron solo como línea base (conservan únicamente
el test de ejemplo de la guía), por lo que sus cifras no son comparables con el nivel unitario ya
desarrollado.

**Entorno de ejecución:** Windows · Python 3.13.3 · pytest 9.1.1 · pytest-playwright 0.10.0 ·
entorno virtual del proyecto (`lab08_estudiante/lab08_estudiante/.venv`).
**Comando de ejecución del nivel unitario:** `pytest tests/unitarias -v` ejecutado desde la raíz del
proyecto (donde están `pytest.ini` y `tests/`).

---

## 1. Objetivo

Verificar mediante pruebas unitarias con pytest las reglas de validación del sistema de inventario
(`app/validaciones.py`), usando dos técnicas de diseño de casos:

- **Partición de equivalencia:** identificar, para cada regla, las clases de entradas válidas e
  inválidas, y comprobar con un representante de cada partición relevante.
- **Análisis de valores límite:** para cada límite, comprobar explícitamente el último valor
  inválido, el primer valor válido y los valores inmediatamente adyacentes.

El oráculo es la sección **"Especificación → Reglas de validación"** del `README.md` del proyecto, no
el comportamiento actual del código: si la app se comporta distinto a lo especificado, eso es un
defecto. Las pruebas se diseñaron para distinguir un **defecto de la aplicación** de una prueba mal
construida, y cada defecto confirmado quedó cubierto por una prueba de regresión.

---

## 2. Reglas de validación y particiones

Las cinco reglas verificadas son las de la tabla "Reglas de validación" del `README.md`. Los
límites se transcriben **de la especificación** (no de las constantes del módulo), para que el test
falle si la implementación cambia un límite.

| Regla o campo | Condición de validación | Particiones válidas | Particiones inválidas | Casos de prueba implementados |
|---|---|---|---|---|
| Usuario (login) | Texto no vacío y no compuesto solo por espacios (`usuario.strip() != ""`) | Cualquier texto con al menos un carácter: 1 carácter, texto normal, con espacios al rededor, con números o acentos | Cadena vacía `""`; solo espacios `"   "`; solo blancos `"\t\n"`; `None`; entero `123`; lista `["admin"]` | `test_usuario_no_vacio_no_reporta_error_de_usuario` (6 casos válidos) · `test_usuario_invalido_reporta_error_de_usuario` (6 casos inválidos) |
| Contraseña (login) | `isinstance(password, str)` y `len(password) >= 6` (largo medido sobre la contraseña tal cual, sin recortar) | 6 caracteres (mínimo), 7 caracteres, 8 caracteres, 6 caracteres con espacios | Vacía `""`; 1 carácter; 5 caracteres; 5 espacios; `None`; entero `123456` | `test_contrasena_valida_no_reporta_error_de_contrasena` (4) · `test_contrasena_invalida_reporta_error_de_contrasena` (6) · `test_limite_minimo_contrasena` (3) |
| Nombre de producto | `isinstance(nombre, str)` y `3 <= len(nombre.strip()) <= 50` (los espacios extremos no cuentan) | 3, 4, 7, 49 y 50 caracteres; 3 y 50 caracteres rodeados de espacios | 1 y 2 caracteres; vacío `""`; solo espacios `"   "`; 51 caracteres (con y sin espacios alrededor); `None`; entero `12345`; bytes `b"ABC"` | `test_nombre_valido_no_reporta_error_de_nombre` (8) · `test_nombre_invalido_reporta_error_de_nombre` (10) · `test_limite_longitud_nombre` (6) |
| Precio | Número (entero o flotante, **sin** booleanos) con `0 < precio <= 100,000` | `0.001`, `0.01`, `1`, `99.99`, `250.00`, `1450.00`, `99,999.99` y `100,000` | Rango: `0`, `0.0`, `-1`, `-0.01`, `100,000.01`, `100,001`. Tipo: `"100"`, `"250.00"`, `None`, `True`, `False`, `[100]` | `test_precio_valido_no_reporta_error_de_precio` (8) · `test_precio_fuera_de_rango_reporta_error_de_rango` (6) · `test_precio_no_numerico_reporta_error_de_numero` (6) · `test_limite_rango_precio` (6) |
| Stock | `isinstance(stock, int)` y **no** booleano, con `stock >= 0` | `0`, `1`, `5`, `10`, `1,000,000` | Rango: `-1`, `-2`, `-100`. Tipo: `5.0`, `0.0`, `"5"`, `None`, `True`, `False` | `test_stock_valido_no_reporta_error_de_stock` (5) · `test_stock_negativo_reporta_error_de_negativo` (3) · `test_stock_no_entero_reporta_error_de_entero` (6) · `test_limite_rango_stock` (3) |
| Combinación de reglas | Todas las reglas a la vez; cada regla incumplida aporta **su propio** mensaje y no se tapan entre sí | Producto que cumple las 5 reglas → lista de errores vacía | Producto con 3 reglas incumplidas → 3 mensajes (nombre, precio, stock); credenciales con 2 reglas incumplidas → 2 mensajes | `test_producto_valido_no_reporta_errores` · `test_producto_valido_no_sesiona_ningun_error` · `test_producto_invalido_reporta_un_error_por_regla_incumplida` · `test_credenciales_invalidas_reportan_un_error_por_regla_incumplida` |
| Regresión | El precio `0` debe rechazarse (límite inferior **exclusivo**: "mayor que 0") | — | `precio = 0` | `test_regresion_def_01_precio_cero_debe_rechazarse` |

**Criterio de aserción usado.** Las funciones devuelven una *lista de mensajes de error*
(lista vacía = válido). Las pruebas comprueban (a) que la lista está vacía en los casos válidos,
(b) que tiene un mensaje por regla incumplida en los casos inválidos, y (c) que el mensaje
corresponde al campo y al tipo de fallo. El punto (c) se valida por **fragmentos normalizados**
(sin acentos y en minúsculas: "precio" + "numer", "stock" + "enter", …) en lugar de por el texto
literal, para que un cambio de redacción del mensaje no produzca un falso positivo, pero un mensaje
sobre el campo equivocado sí se detecte.

*Recuento:* el archivo tiene 22 funciones de prueba. Las 21 funciones nuevas generan 97 casos por el
mecanismo de parametrización y, sumadas al test de ejemplo que trae la guía
(`test_credenciales_con_formato_valido_no_tiene_errores`, conservado sin cambios), dan un total de
**98 pruebas** ejecutadas.

---

## 3. Tabla de valores límite

| Regla o campo | Límite analizado | Último valor inválido | Primer valor válido | Resultado esperado | Resultado observado |
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
| Usuario (login) | Sin límite numérico; la regla es "no vacío ni solo espacios" | `""` (y `"   "`, que queda vacío al recortar) | `"a"` (1 carácter) | Vacío o solo espacios → rechazado; 1 carácter → aceptado | Correcto: `""`, `"   "`, `"\t\n"`, `None` → 1 error de usuario; `"a"` → sin error |
| Contraseña (login) | Mínimo 6 caracteres, **inclusivo** | `"12345"` (5) | `"123456"` (6) · siguiente: `"1234567"` (7) | 5 → rechazado; 6 y 7 → aceptados | Correcto: 5 → 1 error de contraseña; 6 y 7 → sin error |
| Nombre de producto | Mínimo 3 caracteres, **inclusivo** (medido sin espacios extremos) | `"Ab"` (2) | `"ABC"` (3) · siguiente: `"ABCD"` (4) | 2 → rechazado; 3 y 4 → aceptados | Correcto: 2 → 1 error de nombre; 3 y 4 → sin error |
| Nombre de producto | Máximo 50 caracteres, **inclusivo** (medido sin espacios extremos) | `"A" * 51` (51) | `"A" * 50` (50) · anterior: `"A" * 49` (49) | 51 → rechazado; 50 y 49 → aceptados | Correcto: 51 → 1 error de nombre; 50 y 49 → sin error (también `"  " + "A"*50 + "  "`) |
| Precio | Límite inferior **exclusivo**: `precio > 0` | `0` (y `0.0`) | `0.001` · siguiente: `0.01` | 0 → rechazado; cualquier positivo → aceptado | **Inicial (defecto DEF-01): `0` y `0.0` fueron ACEPTADOS** (sin error). **Final (tras la corrección): `0` y `0.0` → 1 error de rango; `0.001` y `0.01` → aceptados** |
| Precio | Límite superior **inclusivo**: `precio <= 100,000` | `100,000.01` | `100,000` (máximo válido) · anterior: `99,999.99` | 100,000.01 → rechazado; 100,000 y 99,999.99 → aceptados | Correcto: 100,000.01 y 100,001 → 1 error de rango; 100,000 y 99,999.99 → sin error |
| Stock | Mínimo 0, **inclusivo**: `stock >= 0` | `-1` | `0` · siguiente: `1` | -1 → rechazado; 0 y 1 → aceptados | Correcto: -1, -2, -100 → 1 error de stock negativo; 0 y 1 → sin error |
| Stock | Límite de **tipo de dato** (no numérico): debe ser `int` y no `bool` | N/A — no aplica un límite numérico; el último valor "no entero" representable es `5.0` (float) | N/A — el primer entero válido es `5` (y `0`) | `5.0`, `"5"`, `None`, `True` → rechazados; `5` → aceptado | Correcto: `5.0`, `0.0`, `"5"`, `None`, `True`, `False` → 1 error "debe ser un número entero"; `5` → sin error |

*Nota sobre N/A*: en la fila de "Stock · límite de tipo de dato" no se usan N/A por falta de datos,
sino porque la regla no es numérica (la partición válida es "int no booleano" y la inválida es
"cualquier otro tipo"); por eso las columnas de último inválido / primer válido se expresan en
términos de tipo y no de magnitud.

---

## 4. Defectos encontrados

### 4.1 Defecto confirmado

| ID | Nivel que lo detectó | Defecto | Archivo o función afectada | Prueba (archivo::función) | Pasos para reproducir | Resultado esperado (según la especificación) | Resultado obtenido | Gravedad | Estado |
|---|---|---|---|---|---|---|---|---|---|
| DEF-01 | Unitario | El precio `0` se acepta como válido: la comprobación de rango rechaza solo los negativos (`precio < 0`), pero la especificación exige un precio **mayor que 0**. El propio mensaje de error de la app ("debe ser mayor que 0") contradice la condición implementada. | `app/validaciones.py` → `validar_producto` (rama de validación de `precio`) | `tests/unitarias/test_unitarias.py::test_regresion_def_01_precio_cero_debe_rechazarse` (también `test_precio_fuera_de_rango_reporta_error_de_rango[cero_int]`, `[cero_float]` y `test_limite_rango_precio[ultimo_invalido_cero]`) | 1. Abrir el intérprete con el entorno virtual del proyecto. 2. `from app.validaciones import validar_producto`. 3. `validar_producto("Teclado", 0, 10)` → devuelve `[]` (producto válido). 4. Consecuencia observable en la API: `POST /api/productos` con `{"nombre": "Gratis", "precio": 0, "stock": 1}` responde **201 Created** y crea un producto de precio 0. | Lista de errores **no vacía**, con el mensaje de precio fuera de rango: "El precio debe ser mayor que 0 y como máximo 100,000" | Lista de errores **vacía**: el producto con precio 0 se considera válido | **Alta** — permite registrar y vender productos con precio 0 (afecta la integridad de los datos y el cálculo de ventas; el caso llega hasta la base de datos en memoria y se expone por la API con 201) | **Corregido** (ver 4.3) |

**Evidencia adicional (no es un defecto, solo contexto):** en la ejecución inicial fallaron 4 de las
98 pruebas y **las 4 corresponden al mismo DEF-01** (los tres casos de partición/límite con `precio = 0`
y la prueba de regresión). Ninguna otra prueba falló, lo que descarta que el defecto esté en la
construcción de las pruebas.

### 4.2 Observación fuera del alcance de las pruebas unitarias

| ID | Defecto | Archivo o función afectada | Cómo se verificó | Resultado esperado | Resultado obtenido | Gravedad | Estado |
|---|---|---|---|---|---|---|---|
| OBS-01 | `GET /api/productos/<id>` de un producto inexistente responde **200** con `{}` en lugar de **404**, incumpliendo la tabla "Contrato de la API" del `README.md` | `app/__init__.py` → `api_obtener` | Revisión de código y ejecución puntual con el cliente de prueba de Flask (`GET /api/productos/999` → `200 {}`, frente a `GET /api/productos/1` → `200` con producto; `PUT` y `DELETE` sobre un id inexistente sí devuelven `404`) | 404 | 200 con cuerpo `{}` | **Media** — el cliente no puede distinguir "producto inexistente" de "producto vacío"; además la ruta documenta 404 para `PUT`/`DELETE`, así que el contrato quedó inconsistente | **Pendiente** (no se modifica: no es detectado por las pruebas unitarias y excede el alcance de este entregable) |

### 4.3 Cambio realizado en el código de producción

Para poder validar el comportamiento especificado se aplicó el **cambio mínimo** en
`app/validaciones.py`, un solo carácter, en la rama de rango del precio:

```diff
--- a/app/validaciones.py
+++ b/app/validaciones.py
@@ -50,7 +50,7 @@ def validar_producto(nombre, precio, stock):
     if not _es_numero(precio):
         errores.append("El precio debe ser un número")
-    elif precio < 0 or precio > PRECIO_MAX:
+    elif precio <= 0 or precio > PRECIO_MAX:
         errores.append("El precio debe ser mayor que 0 y como máximo 100,000")
```

- **Archivo:** `app/validaciones.py`, función `validar_producto` (línea 53).
- **Justificación:** la especificación (tabla "Reglas de validación"), el *docstring* de la función
  ("precio: número mayor que 0 y menor o igual a 100,000") y el mensaje de error emitido por la app
  ("debe ser mayor que 0 y como máximo 100,000") coinciden en exigir `precio > 0`; solo la condición
  implementada (`precio < 0`) era más laxa. El cambio alinea el código con el oráculo sin tocar
  ninguna regla de negocio.
- **Prueba que demuestra la corrección:** `test_regresion_def_01_precio_cero_debe_rechazarse` (se
  conserva en la suite final y pasa), junto con
  `test_precio_fuera_de_rango_reporta_error_de_rango[cero_int|cero_float]` y
  `test_limite_rango_precio[ultimo_invalido_cero]`.
- **Nota para el equipo:** la guía del laboratorio sugiere dejar el defecto **fallando** como
  evidencia. Aquí se corrigió el código de producción por indicación de la tarea; si se prefiere
  seguir la convención de la guía, basta con revertir ese cambio de un carácter (queda en
  `git diff`) y volver a ejecutar la suite: fallarán exactamente las 4 pruebas de DEF-01.

### 4.4 Riesgos y recomendaciones sin prueba asociada

| ID | Observación | Evidencia | Impacto |
|---|---|---|---|
| RIESGO-01 | Un precio `float("nan")` se acepta como válido: en Python toda comparación con `NaN` es `False`, por lo que `precio < 0` y `precio > 100000` nunca se cumplen | `validar_producto("Teclado", float("nan"), 1)` → `[]` | Un `NaN` entrante por la API se guarda como precio y contamina cálculos (sumas, comparaciones). La especificación no lo menciona, por lo que **no** se escribió una prueba que lo prohíba; se recomienda documentarlo y rechazarlo explícitamente |
| RIESGO-02 | Una contraseña de 6 espacios (`"      "`) se considera válida: el largo se mide sin recortar y la especificación solo exige "mínimo 6 caracteres" | `validar_credenciales("admin", "      ")` → `[]` | La especificación no exige contenido, por lo que no se generó prueba; conviene aclarar en la especificación si una contraseña solo con espacios debe rechazarse |
| RIESGO-03 | El stock se valida con `isinstance(stock, int)`, por lo que un `5.0` (float) se rechaza aunque sea un valor entero | `validar_producto("Teclado", 100.0, 5.0)` → 1 error "El stock debe ser un número entero" | Cumple la especificación ("Entero"), pero un cliente JSON que envíe `5.0` recibe 400. Conviene documentarlo en el contrato de la API |

---

## 5. Tabla comparativa de ejecución

### 5.1 Nivel unitario (`pytest tests/unitarias -v`)

| Ejecución | Cantidad de pruebas | Pruebas aprobadas | Pruebas fallidas | Pruebas omitidas | Duración medida | Observaciones |
|---|---:|---:|---:|---:|---|---|
| Inicial (antes de corregir DEF-01) | 98 | 94 | 4 | 0 | **0.24 s** (pytest) · 0.78 s (reloj de pared) | Los 4 fallos son el mismo defecto (DEF-01, precio 0). El resto de la suite quedó verde |
| Final (después de corregir DEF-01) | 98 | 98 | 0 | 0 | **0.16 s** (pytest) · 0.76 s (reloj de pared) | Suite completamente verde. En 5 ejecuciones repetidas el tiempo reportado por pytest osciló entre 0.14 s y 0.16 s (0.62–0.76 s de reloj de pared) |
| Repetida (confirmación, `pytest tests/unitarias -q --durations=5`) | 98 | 98 | 0 | 0 | **0.14 s** (pytest) | Las 98 pruebas individuales duran menos de 0.005 s cada una; promedio ≈ 0.0014 s por prueba |

### 5.2 Comparativa de niveles (línea base medida en esta entrega)

Comandos: `pytest tests/unitarias -q`, `pytest tests/api -q`, `pytest tests/e2e -q` y `pytest -q`
(tiempo reportado por pytest, sin warm-up).

| Criterio | Unitarias | API | E2E |
|---|---|---|---|
| Número de pruebas | | | |
| Tiempo total de ejecución (s) | | | |
| Tiempo promedio por prueba (s) | | | |
| Defectos detectados (IDs) | | | |
| ¿Qué cambio en la app rompería estas pruebas sin que haya un defecto? | | | |
| Costo de mantenimiento (Alto / Medio / Bajo) y por qué | | | |

## 3. Recomendación (máximo media página)

El equipo de Inventario IS1 tiene un pipeline de CI. Recomienda qué pruebas correr:

- en cada commit,
- en cada pull request,
- antes de liberar a producción.

Justifica con tus datos de la tabla y con la pirámide de pruebas.
Responde además: ¿qué defecto NO habría detectado una suite solo de pruebas E2E, o solo de pruebas unitarias?
