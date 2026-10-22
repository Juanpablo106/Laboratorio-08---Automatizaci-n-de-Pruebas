# Informe · Laboratorio 8 · Pruebas automatizadas

**Equipo:** (número)
**Integrantes:** (nombres y carnés)

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
| Número de pruebas | 98 | 1 | 1 |
| Tiempo total de ejecución (s) | 0.15 | 0.37 | 2.13 |
| Tiempo promedio por prueba (s) | 0.0014 | 0.37 | 2.13 |
| Defectos detectados (IDs) | DEF-01 | OBS-01 (por revisión de código, no por las pruebas) | — |
| ¿Qué cambio en la app rompería estas pruebas sin que haya un defecto? | Reescribir el texto de los mensajes de error, o devolver los errores en otro formato (p. ej. objetos en vez de cadenas) | Cambiar la estructura del JSON (`{"errores": [...]}`) o el formato de la cabecera `Authorization` | Cambiar textos, roles o la estructura del HTML de las plantillas, o alargar la carga de la página |
| Costo de mantenimiento (Alto / Medio / Bajo) y por qué | **Bajo**: funciones puras, sin red ni navegador; se ejecutan en milisegundos y no se rompen por cambios de interfaz | **Medio**: depende del servidor pero no del navegador; requiere levantar la app | **Alto**: depende del navegador, del servidor y del HTML; es la capa que más se rompe por refactors cosméticos |

**Advertencia sobre la comparativa:** las cifras de API y E2E corresponden a **un solo test de ejemplo
por nivel** (los que trae la guía); no son el resultado de un desarrollo completo de esos niveles, por
lo que la comparación de tiempos entre niveles es indicativa y no concluyente. Los 98 tests
unitarios cubren las cinco reglas de `app/validaciones.py` (cada una con sus particiones válidas,
inválidas y sus valores límite); no se afirma cobertura de líneas o de código medida por
herramienta, solo cobertura de las reglas especificadas.

### 5.3 Suite completa

| Ejecución | Cantidad de pruebas | Pruebas aprobadas | Pruebas fallidas | Pruebas omitidas | Duración medida | Observaciones |
|---|---:|---:|---:|---:|---|---|
| `pytest -q` (los tres niveles) | 100 | 100 | 0 | 0 | **2.25 s** (pytest) · 2.79 s (reloj de pared) | Incluye el arranque automático del servidor en el que se ejecutan los niveles API y E2E. En una ejecución posterior con el sistema ocupado se midió 3.82 s (pytest): la variación es del entorno, no de las pruebas |

---

## 6. Recomendaciones

### 6.1 Prioridad alta

1. **Mantener la corrección de DEF-01 y su prueba de regresión.**
   `app/validaciones.py::validar_producto` ya no acepta `precio = 0`. La prueba
   `test_regresion_def_01_precio_cero_debe_rechazarse` debe permanecer en la suite: es la que
   detecta la regresión si alguien vuelve a escribir `precio < 0`.
2. **Cerrar OBS-01 (`GET /api/productos/<id>` de un id inexistente responde 200 en vez de 404).**
   La corrección mínima es devolver `jsonify({"error": "Producto no encontrado"}), 404`, igual que
   ya hacen `api_actualizar` y `api_eliminar`, y agregar el caso al nivel API
   (`GET /api/productos/999` → 404).

### 6.2 Prioridad media

3. **Validar el precio en la capa de entrada, no solo en el dominio.** El defecto DEF-01 llegó hasta
   la base de datos y se expuso por la API con `201 Created`. Conviene repetir la comprobación de
   `0 < precio <= 100,000` en la ruta (o garantizar que `validar_producto` sea la única puerta de
   entrada, con una prueba de API que lo demuestre).
4. **Rechazar valores no finitos en el precio.** Por RIESGO-01, `float("nan")` se guarda como
   precio válido. Recomendación: en `_es_numero`, usar `math.isfinite(valor)` y agregar la partición
   correspondiente al conjunto de pruebas.
5. **Cerrar la ambigüedad de la contraseña en blanco (RIESGO-02).** Definir en la especificación si
   una contraseña de 6 espacios es aceptable y, si no lo es, reflejarlo en la regla y en la prueba.

### 6.3 Prioridad baja

6. **Centralizar los mensajes de error.** Hoy son cadenas literales dentro de `validar_producto`; si
   se mueven a constantes o a un catálogo, las pruebas podrán referenciarlas y dejar de depender de
   fragmentos de texto.
7. **Extender la pirámide de pruebas.** Este entregable cubre las cinco reglas de
   `app/validaciones.py` en el nivel unitario, pero los niveles API y E2E siguen con un único test de
   ejemplo: los casos negativos del contrato de la API (400/401/404) y los flujos de la interfaz
   (login, alta, edición y borrado) siguen sin cubrirse.

### 6.4 Qué pruebas correr en el pipeline de CI (pirámide de pruebas)

- **En cada commit:** `pytest tests/unitarias -v`. Son 0.16 s y 98 aserciones sobre las reglas de
  negocio; no dependen de servidor ni de navegador, así que son la capa más barata y con menos
  falsos positivos.
- **En cada pull request:** `pytest tests/unitarias tests/api -v` (≈ 0.5 s). El nivel API verifica
  que la validación se respeta también en el contrato HTTP (autenticación, códigos de estado), que es
  donde se materializó el impacto de DEF-01.
- **Antes de liberar a producción:** la suite completa (`pytest -v --durations=0`, ≈ 2.3 s) más E2E,
  porque son las pruebas que detectan roturas de la interfaz que el usuario ve.

**Justificación con la pirámide:** la base (unitarias) es amplia y barata, el medio (API) cubre la
integración y la cima (E2E) cubre unos pocos flujos críticos. Con los datos medidos, las unitarias
detectaron el único defecto confirmado por pruebas (DEF-01) en 0.14–0.16 s de ejecución, mientras que
E2E consumió 2.13 s para una sola aserción.

**¿Qué defecto NO habría detectado una suite solo de E2E, o solo de unitarias?**
Una suite **solo E2E** no habría detectado DEF-01 de forma fiable: el flujo de la interfaz no tiene un
paso dedicado a "crear un producto con precio 0" y, si el formulario lo limitara, el defecto quedaría
oculto; además, un fallo de validación unitario se manifestaría en E2E como un mensaje en pantalla
difícil de distinguir de un error de negocio. Una suite **solo unitarias** no habría detectado
OBS-01 (el `200` en vez de `404` de `GET /api/productos/<id>`), porque `api_obtener` es una ruta de
Flask y ningún test de `validar_producto` la alcanza; sí lo detecta el nivel API.

---

## 7. Conclusión

Se verificaron las **cinco reglas de validación** de la especificación (usuario obligatorio,
contraseña de mínimo 6 caracteres, nombre de producto entre 3 y 50 caracteres sin contar espacios
extremos, precio numérico mayor que 0 y como máximo 100,000, y stock entero mayor o igual a 0)
mediante **partición de equivalencia** y **análisis de valores límite**, con `@pytest.mark.parametrize`
para agrupar los casos que comparten lógica y con identificadores descriptivos (`ids`) que identifican
cada partición y cada valor límite.

El análisis de particiones de equivalencia y valores límite detectó **un defecto confirmado
(DEF-01)**: la aplicación aceptaba
un precio de `0` pese a que la especificación exige un precio mayor que 0, lo que además se
materializaba en la API con un `201 Created`. Se aplicó el cambio mínimo en
`app/validaciones.py::validar_producto` (`precio < 0` → `precio <= 0`) y se conservó la prueba de
regresión que lo demuestra. Aparte de DEF-01, se documentó **OBS-01** (`GET /api/productos/<id>`
responde 200 en vez de 404) como observación pendiente, detectada por revisión de código y verificada
con el cliente de prueba de Flask, fuera del alcance de las pruebas unitarias.

**Estado final:** `pytest tests/unitarias -v` → **98 pruebas, 98 aprobadas, 0 fallidas, 0 omitidas,
en 0.14–0.16 s** según la ejecución (0.62–0.76 s de reloj de pared); la suite completa `pytest -q` →
100 aprobadas en 2.25 s.

**Límites de lo afirmado:** no se afirma cobertura completa de la aplicación. Lo verificado son las
cinco reglas de `app/validaciones.py` (cada una con particiones válidas, inválidas y valores límite),
pero los niveles API y E2E siguen conteniendo únicamente el test de ejemplo de la guía, y las
particiones no numéricas (tipo de dato, presencia de texto) no admiten un "valor límite" numérico, por
lo que en esas filas de la tabla de límites se documenta el criterio en lugar de un valor. Tampoco se
afirma nada sobre comportamientos que la especificación no define (precio `NaN`, contraseña solo con
espacios), que quedan registrados como riesgos y no como defectos.
