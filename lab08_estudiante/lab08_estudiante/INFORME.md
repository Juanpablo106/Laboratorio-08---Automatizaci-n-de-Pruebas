# Informe · Laboratorio 8 · Pruebas automatizadas

**Equipo:** 01
**Integrantes:**
- Paula Nicolle West Ortiz — 1245524 *(parte 3 · nivel API)*
- Juan Pablo Estrada Rodriguez — 1056124 *(parte 2 · nivel unitario)*
- Christopher Conrado Lopez Vicente — 1053824 *(parte 4 · nivel E2E)*

> Los datos de identificación del equipo provienen de la rama `origin/Nicky` (`INFORME.md`), la única
> de las tres ramas de los integrantes que los consigna. Si el número de equipo o algún carné
> estuviera mal, este encabezado debe ajustarse antes de la entrega.

**Sistema bajo prueba:** *Inventario IS1* — aplicación Flask (`app/`) con interfaz web (login + CRUD de
productos en HTML renderizado por el servidor) y API REST JSON (`/api/...`), con datos en memoria.
**Oráculo de verdad:** la sección "Especificación" de la guía del laboratorio (`README.md`).
**Alcance de este informe:** las tres partes del laboratorio (2 · unitarias, 3 · API, 4 · E2E) y el
análisis comparativo de la parte 5.

> Este informe consolida las entregas por partes (2, 3 y 4) en un solo documento. Se conserva el
> contenido útil de cada entrega —análisis de particiones y valores límite del nivel unitario,
> fichas de los defectos de API y E2E, observaciones sin prueba— y se reorganiza con una
> numeración única, sin contradicciones entre secciones.

---

## 1. Objetivo y contexto

El equipo de desarrollo de *Inventario IS1* afirma que "todo funciona", pero no escribió pruebas
automatizadas. El trabajo del equipo de QA fue construir una suite de tres niveles sobre el mismo
sistema y **encontrar los defectos antes de que lleguen a producción**.

El objetivo concreto de esta parte final del laboratorio fue:

1. Consolidar la suite automatizada de los tres niveles (unitario, API y E2E) en un único repositorio
   ejecutable con `pytest`.
2. Ejecutar la suite completa con el comando de la guía (`pytest -v --durations=0`) y registrar los
   resultados reales, con su evidencia.
3. Documentar los defectos confirmados, distinguiendo claramente los **defectos de la aplicación** de
   los **errores de las pruebas** y de los **problemas del entorno**.
4. Comparar los tres niveles con datos medidos y fundar una recomendación de estrategia de pruebas
   en pirámide.

La regla de juego del laboratorio se respetó como criterio de diseño de las pruebas: **la
especificación es el oráculo**, no el comportamiento actual del código. Cuando la app se aparta de lo
especificado, la prueba se deja fallando como evidencia y el defecto se reporta; no se maquilla la
aserción, no se usa `skip`/`xfail` y no se corrige `app/`.

### 1.1 Fuentes de la información y cómo se leen las cifras

Este informe consolida el trabajo de las tres ramas del equipo. Cada rama entregó su nivel y su
propio `INFORME.md`; los tres archivos de prueba (`tests/unitarias/test_unitarias.py`,
`tests/api/test_api.py`, `tests/e2e/test_e2e.py`) son **byte a byte idénticos** a sus equivalentes en
`main` (verificado con `git diff`), por lo que la suite que se midió en §3 es exactamente la suma de
las tres entregas.

| Fuente | Alcance | Archivo de origen | Entorno declarado por el integrante | Qué aportó a este informe |
|---|---|---|---|---|
| Rama `origin/JuanPablo` | Parte 2 · nivel **unitario** | `lab08_estudiante/lab08_estudiante/INFORME.md` (274 líneas) | Windows · Python **3.13.3** · pytest 9.1.1 · pytest-playwright 0.10.0 · `.venv` del proyecto | Diseño de particiones y valores límite de las 5 reglas; **DEF-01** (precio 0) con su prueba de regresión; **OBS-01**; riesgos RIESGO-01..03; recomendaciones de desarrollo y de pipeline; línea base de API/E2E (solo el test de ejemplo) |
| Rama `origin/Nicky` | Parte 3 · nivel **API** | `lab08_estudiante/lab08_estudiante/INFORME.md` (158 líneas) | Windows (win32) · Python **3.14.8** · pytest 9.1.1 · pytest-playwright 0.10.0 · playwright 1.64.0 · Flask 3.1.3 | Alcance por bloques del contrato HTTP; **API-001** y **API-002** con evidencia literal; 12 ejecuciones de tiempo del nivel API; datos de identificación del equipo |
| Rama `origin/Chris` | Parte 4 · nivel **E2E** | `lab08_estudiante/lab08_estudiante/INFORME.md` (151 líneas) | Python **3.14.6** · pytest 9.1.1 · pytest-playwright 0.10.0 · Chromium de Playwright | Los 9 flujos E2E; **E2E-001** y **E2E-002** con traza del servidor y verificación en el DOM; tiempos del nivel E2E; observación independiente de `GET /api/productos/999` → 200 |
| Rama `origin/main` (estado actual) | Suite completa integrada | `lab08_estudiante/lab08_estudiante/INFORME.md` (este documento) | Linux · Python **3.14.6** · pytest 9.1.1 · pytest-playwright 0.10.0 | Ejecución de `pytest -v --durations=0` y mediciones repetidas por nivel (§3); tabla comparativa; análisis de detección y recomendación en pirámide |

**Regla de lectura aplicada en todo el documento.** Cada cifra se etiqueta según de dónde sale:

| Etiqueta | Significado |
|---|---|
| **Medido aquí** | Ejecutado y registrado en esta entrega, con el comando y la fecha de la corrida |
| **Reportado por el equipo** | Cifra de una rama o de un integrante, reproducida solo como *reportada*; no se volvió a medir en esta máquina |
| **Derivado** | Conclusión o cálculo hecho en este informe a partir de datos medidos |
| **Pendiente de confirmar** | Dato en conflicto entre fuentes, que requiere una decisión del equipo |

Cuando una cifra reportada y una medida no coinciden (niveles API y E2E, §3.6), **se conservan ambas**
con su procedencia en lugar de elegir una.

---

## 2. Estrategia de pruebas y niveles utilizados

Se aplicó una estrategia de tres niveles, cada uno con un objeto de prueba distinto y un costo
creciente:

| Nivel | Objeto de prueba | Herramienta | Dependencias | Archivo |
|---|---|---|---|---|
| 1 · Unitario (componente) | `app/validaciones.py`: reglas de validación puras | pytest puro | ninguna | `tests/unitarias/test_unitarias.py` |
| 2 · API (integración) | Contrato HTTP de `/api/...`: autenticación, autorización, CRUD, códigos de estado | Playwright `APIRequestContext` | servidor Flask en `127.0.0.1:5000`, sin navegador | `tests/api/test_api.py` |
| 3 · E2E (sistema) | Flujos de usuario en la interfaz web (HTML + JS) | Playwright + Chromium | servidor Flask + navegador gráfico | `tests/e2e/test_e2e.py` |

### 2.1 Aislamiento de datos

La fixture compartida `datos_limpios` (`tests/conftest.py`) hace `POST /api/reset` antes de cada
prueba, por lo que **toda** la suite parte del mismo estado conocido: los tres productos iniciales
(Teclado id 1 · Mouse id 2 · Monitor id 3). Las operaciones destructivas del nivel API se ejecutan
sobre un producto de prueba creado por la fixture local `producto_de_prueba`, nunca sobre los
productos iniciales. Ninguna prueba depende del orden de ejecución de las demás.

### 2.2 Nivel unitario: reglas, particiones y valores límite

*Procedencia: diseño y tabla de valores límite de `origin/JuanPablo` (§2 y §3), contrastado con la
suite medida en §3.*

Las cinco reglas verificadas son las de la tabla "Reglas de validación" de la guía. Los límites se
transcriben **de la especificación** (no de las constantes del módulo), para que la prueba falle si la
implementación cambia un límite.

| Regla o campo | Condición verificada | Particiones válidas | Particiones inválidas | Pruebas implementadas |
|---|---|---|---|---|
| Usuario (login) | Texto no vacío ni solo espacios | 1 carácter, texto normal, con espacios al rededor, con números o acentos | `""`, `"   "`, `"\t\n"`, `None`, `123`, `["admin"]` | `test_usuario_no_vacio_no_reporta_error_de_usuario` (6) · `test_usuario_invalido_reporta_error_de_usuario` (6) |
| Contraseña (login) | `str` con largo ≥ 6 (medido sobre la contraseña tal cual) | 6, 7 y 8 caracteres, 6 con espacios | `""`, 1 carácter, 5 caracteres, 5 espacios, `None`, `123456` | `test_contrasena_valida_no_reporta_error_de_contrasena` (4) · `test_contrasena_invalida_reporta_error_de_contrasena` (6) · `test_limite_minimo_contrasena` (3) |
| Nombre de producto | `str` con `3 <= len(strip()) <= 50` | 3, 4, 7, 49 y 50 caracteres; 3 y 50 rodeados de espacios | 1 y 2 caracteres; `""`; `"   "`; 51 caracteres (con y sin espacios); `None`; `12345`; `b"ABC"` | `test_nombre_valido_no_reporta_error_de_nombre` (8) · `test_nombre_invalido_reporta_error_de_nombre` (10) · `test_limite_longitud_nombre` (6) |
| Precio | Número (sin booleanos) con `0 < precio <= 100,000` | `0.001`, `0.01`, `1`, `99.99`, `250.00`, `1450.00`, `99,999.99`, `100,000` | Rango: `0`, `0.0`, `-1`, `-0.01`, `100,000.01`, `100,001`. Tipo: `"100"`, `"250.00"`, `None`, `True`, `False`, `[100]` | `test_precio_valido_no_reporta_error_de_precio` (8) · `test_precio_fuera_de_rango_reporta_error_de_rango` (6) · `test_precio_no_numerico_reporta_error_de_numero` (6) · `test_limite_rango_precio` (6) |
| Stock | `int` no booleano con `stock >= 0` | `0`, `1`, `5`, `10`, `1,000,000` | Rango: `-1`, `-2`, `-100`. Tipo: `5.0`, `0.0`, `"5"`, `None`, `True`, `False` | `test_stock_valido_no_reporta_error_de_stock` (5) · `test_stock_negativo_reporta_error_de_negativo` (3) · `test_stock_no_entero_reporta_error_de_entero` (6) · `test_limite_rango_stock` (3) |
| Combinación de reglas | Cada regla incumplida aporta **su propio** mensaje | Producto que cumple las 5 reglas → lista vacía | Producto con 3 reglas incumplidas → 3 mensajes; credenciales con 2 → 2 mensajes | `test_producto_valido_no_sesiona_ningun_error` · `test_producto_invalido_reporta_un_error_por_regla_incumplida` · `test_credenciales_invalidas_reportan_un_error_por_regla_incumplida` |
| Regresión | El precio `0` debe rechazarse (límite inferior **exclusivo**) | — | `precio = 0` | `test_regresion_def_01_precio_cero_debe_rechazarse` |

**Criterio de aserción.** Las funciones devuelven una *lista de mensajes* (vacía = válido). Las
pruebas comprueban (a) lista vacía en los casos válidos, (b) un mensaje por regla incumplida en los
inválidos y (c) que el mensaje corresponde al campo y al tipo de fallo. El punto (c) se valida por
**fragmentos normalizados** (sin acentos y en minúsculas: "precio" + "numer", "stock" + "enter", …)
en vez de por el texto literal: un cambio de redacción del mensaje no produce falsos positivos, pero
un mensaje sobre el campo equivocado sí se detecta.

### 2.3 Tabla de valores límite

| Regla o campo | Límite analizado | Último valor inválido | Primer valor válido | Resultado esperado | Resultado observado en la ejecución actual |
|---|---|---|---|---|---|
| Usuario (login) | Sin límite numérico; la regla es "no vacío ni solo espacios" | `""` (y `"   "`, que queda vacío al recortar) | `"a"` (1 carácter) | Vacío o solo espacios → rechazado; 1 carácter → aceptado | Correcto: `""`, `"   "`, `"\t\n"`, `None` → 1 error de usuario; `"a"` → sin error |
| Contraseña (login) | Mínimo 6 caracteres, **inclusivo** | `"12345"` (5) | `"123456"` (6) · siguiente: `"1234567"` (7) | 5 → rechazado; 6 y 7 → aceptados | Correcto: 5 → 1 error de contraseña; 6 y 7 → sin error |
| Nombre de producto | Mínimo 3 caracteres, **inclusivo** (sin espacios extremos) | `"Ab"` (2) | `"ABC"` (3) · siguiente: `"ABCD"` (4) | 2 → rechazado; 3 y 4 → aceptados | Correcto: 2 → 1 error de nombre; 3 y 4 → sin error |
| Nombre de producto | Máximo 50 caracteres, **inclusivo** (sin espacios extremos) | `"A" * 51` | `"A" * 50` · anterior: `"A" * 49` | 51 → rechazado; 50 y 49 → aceptados | Correcto: 51 → 1 error de nombre; 50 y 49 → sin error (también `"  " + "A"*50 + "  "`) |
| Precio | Límite inferior **exclusivo**: `precio > 0` | `0` (y `0.0`) | `0.001` · siguiente: `0.01` | 0 → rechazado; cualquier positivo → aceptado | **Defectuoso en el código original:** `0` y `0.0` eran aceptados. **En el código actual ya está corregido** (`precio <= 0`): `0` y `0.0` → 1 error de rango; `0.001` y `0.01` → aceptados (ver §4.6) |
| Precio | Límite superior **inclusivo**: `precio <= 100,000` | `100,000.01` | `100,000` · anterior: `99,999.99` | 100,000.01 → rechazado; 100,000 y 99,999.99 → aceptados | Correcto: 100,000.01 y 100,001 → 1 error de rango; 100,000 y 99,999.99 → sin error |
| Stock | Mínimo 0, **inclusivo**: `stock >= 0` | `-1` | `0` · siguiente: `1` | -1 → rechazado; 0 y 1 → aceptados | Correcto: -1, -2, -100 → 1 error de stock negativo; 0 y 1 → sin error |
| Stock | Límite de **tipo de dato**: debe ser `int` y no `bool` | N/A — la regla no es numérica | N/A — el primer entero válido es `0` (o `5`) | `5.0`, `"5"`, `None`, `True` → rechazados; `5` → aceptado | Correcto: `5.0`, `0.0`, `"5"`, `None`, `True`, `False` → 1 error "debe ser un número entero"; `5` → sin error |

*Nota*: en la fila de "Stock · límite de tipo de dato" no se usa N/A por falta de datos, sino porque
la regla no es numérica (partición válida: "int no booleano"; inválida: "cualquier otro tipo"), por lo
que las columnas de último inválido / primer válido se expresan en términos de tipo.

### 2.4 Nivel API: alcance cubierto

*Procedencia: `origin/Nicky` §4.1.*

| Bloque | Endpoints | Qué se verifica |
|---|---|---|
| A. Autenticación | `POST /api/login` | 200 + `token` utilizable; 401 con credenciales incorrectas; 400 + `errores` (lista) con formato inválido |
| B. Autorización | `GET/POST /api/productos`, `GET/PUT/DELETE /api/productos/1` | 401 exacto sin token y con token inválido |
| C. Consulta | `GET /api/productos`, `GET /api/productos/<id>` | 200 + lista y datos iniciales; 404 para id inexistente |
| D. Creación | `POST /api/productos` | 201 + `id` + datos devueltos, recuperabilidad por `GET`, 400 + `errores` en casos negativos, límites válidos |
| E. Actualización | `PUT /api/productos/<id>` | 200 + cambios, persistencia verificada con un `GET` posterior, 404 inexistente, 400 datos inválidos |
| F. Eliminación | `DELETE /api/productos/<id>` | 204 exacto, ausencia en el listado, 404 inexistente y en el segundo borrado |

### 2.5 Nivel E2E: alcance cubierto

*Procedencia: `origin/Chris` §1 (flujos) y §2 (tabla comparativa de su entrega).*

| Prueba | Flujo verificado | Aspecto de la especificación |
|---|---|---|
| `test_pagina_de_login_carga` | La pantalla de login carga | Smoke test de la pantalla inicial |
| `test_login_exitoso_muestra_bienvenido_y_lista_de_productos` | Login con `admin`/`Admin123` | "Login correcto: lleva a la lista de productos y muestra 'Bienvenido, admin'" (el saludo aparece con 800 ms de retraso; `expect()` espera sola, sin `time.sleep`) |
| `test_login_fallido_muestra_error_y_no_accede_a_la_lista_de_productos` | Credenciales incorrectas | "Login incorrecto: muestra 'Usuario o contraseña incorrectos'" + no acceso a la lista protegida |
| `test_sin_sesion_las_paginas_de_productos_redirigen_al_login` | `/productos`, `/productos/nuevo`, `/productos/1/editar` sin sesión | "Sin sesión, cualquier página de productos redirige a `/login`" |
| `test_crear_producto_desde_el_formulario_aparece_en_la_tabla` | "Nuevo producto" → guardar | "'Nuevo producto' abre un formulario; al guardar, muestra 'Producto creado' y el producto aparece en la tabla" |
| `test_eliminar_producto_borra_solo_ese_producto_y_no_afecta_a_los_demas` | "Eliminar" en la fila de *Mouse* | "'Eliminar' borra **ese** producto, muestra 'Producto eliminado' y los demás productos no cambian" |
| `test_editar_producto_actualiza_sus_datos_en_la_tabla` | "Editar" → guardar | "'Editar' permite modificar el producto; al guardar, muestra 'Producto actualizado'" |
| `test_formulario_rechaza_nombre_con_menos_de_3_caracteres` | Nombre de 2 caracteres | Regla "Nombre de producto: entre 3 y 50 caracteres" |
| `test_formulario_rechaza_precio_cero` | Precio `0` | Regla "Precio: número **mayor que 0**" |

Los localizadores son accesibles (`get_by_role`, `get_by_label`, `get_by_text`), el producto a
eliminar se identifica **por nombre** (nunca por posición en la tabla) y cada prueba es
independiente.

---

## 3. Resumen de ejecución de la suite completa

### 3.1 Comando y resultado

Comando ejecutado desde la raíz del proyecto (`lab08_estudiante/lab08_estudiante/`), tal como lo pide
la guía:

```
pytest -v --durations=0
```

| Métrica | Valor observado |
|---|---|
| Casos de prueba collected | **174** |
| Pruebas aprobadas | **171** |
| Pruebas fallidas | **3** |
| Pruebas omitidas (`skip`) | **0** |
| Pruebas marcadas como `xfail` | **0** |
| Errores de colección o de infraestructura (`error`) | **0** |
| Duración total reportada por pytest | **14.12 s** (ejecución de referencia; rango observado 5.64 – 15.71 s en 10 ejecuciones, ver §3.4) |
| Defectos únicos que explican los 3 fallos | **2** (API-001 y E2E-001) |
| Fallos pendientes de diagnóstico | **0** |

Los 3 fallos son **defectos reales de la aplicación**, confirmados con evidencia reproducible (§4).
Ninguna prueba se marcó como omitida ni se relajó una aserción para obtener un resultado verde.

### 3.2 Desglose por nivel (misma ejecución de la suite completa)

| Nivel | Funciones de prueba | Casos ejecutados | Aprobadas | Fallidas | Omitidas |
|---|---:|---:|---:|---:|---:|
| Unitario (`tests/unitarias`) | 22 | 98 | 98 | 0 | 0 |
| API (`tests/api`) | 30 | 65 | 63 | 2 | 0 |
| E2E (`tests/e2e`) | 9 | 11 | 10 | 1 | 0 |
| **Total** | **61** | **174** | **171** | **3** | **0** |

> La diferencia entre funciones y casos se debe a `@pytest.mark.parametrize`: el nivel unitario
> genera 98 casos a partir de 22 funciones, el nivel API 65 a partir de 30, y el nivel E2E 11 a partir
> de 9 (una de ellas parametrizada con 3 rutas). "174 pruebas" y "61 funciones" no son la misma cifra.

### 3.3 Pruebas más lentas (`--durations=0`)

| Duración | Prueba | Explicación |
|---:|---|---|
| 1.48 s (call) | `tests/e2e/test_e2e.py::test_login_exitoso_muestra_bienvenido_y_lista_de_productos` | Espera el mensaje "Bienvenido, admin", que la app inserta con 800 ms de retraso (auto-waiting de `expect`) |
| 1.01 s (call) | `tests/e2e/...::test_editar_producto_actualiza_sus_datos_en_la_tabla` | Navegación + formulario + confirmación en la tabla |
| 0.92 s (call) | `tests/e2e/...::test_crear_producto_desde_el_formulario_aparece_en_la_tabla` | Navegación + formulario + confirmación en la tabla |
| 0.92 s (call) | `tests/e2e/...::test_formulario_rechaza_precio_cero` | Navegación + envío del formulario |
| 0.91 s (call) | `tests/e2e/...::test_eliminar_producto_borra_solo_ese_producto_y_no_afecta_a_los_demas` | Login + borrado + lectura de la tabla |
| 0.82 s (call) | `tests/e2e/...::test_formulario_rechaza_nombre_con_menos_de_3_caracteres` | Navegación + envío del formulario |
| 0.65 s (setup) | `tests/api/...::test_login_con_credenciales_correctas_devuelve_200_y_un_token` | Arranque de Playwright en el primer caso que lo usa |
| 0.26 s (setup) | `tests/e2e/...::test_pagina_de_login_carga` | Arranque del contexto de navegador |
| < 0.005 s (cada una) | Las 98 pruebas unitarias | Funciones puras, sin I/O: prácticamente todos los casos (entre 380 y 430 duraciones ocultas bajo ese umbral, según la carga de la máquina) quedaron por debajo de 0.005 s |

**Advertencia sobre los valores absolutos.** Las duraciones de esta tabla corresponden a la ejecución
de referencia (máquina con *load average* ≈ 4.8). Repetida la misma suite con la máquina descargada
(suite completa en 5.64 s), los mismos casos bajaron a 0.94 s (login), 0.46 s (editar), 0.42 s
(crear), 0.40 s (eliminar), 0.39 s (precio cero) y 0.35 s (nombre corto). **El orden de las pruebas
por lentitud se mantuvo en todas las ejecuciones**; lo que cambia es la escala. Por eso las
comparaciones de §5 usan la mediana de ejecuciones independientes y no un único cronómetro.

### 3.4 Tiempos medidos por nivel (ejecuciones independientes)

Además de la ejecución completa, se midió cada nivel por separado con `pytest tests/<nivel> -q`,
cinco veces cada uno. Son **mediciones independientes**, no partes de la corrida anterior:

| Nivel | 5 ejecuciones independientes (s) | Mediana | Promedio | Casos | Tiempo promedio por caso |
|---|---|---:|---:|---:|---:|
| Unitario | 0.15 · 0.15 · 0.15 · 0.18 · 0.22 | **0.15 s** | 0.17 s | 98 | ≈ 0.0017 s |
| API | 5.00 · 5.18 · 5.75 · 6.34 · 6.45 | **5.75 s** | 5.74 s | 65 | ≈ 0.088 s |
| E2E | 6.08 · 6.94 · 9.73 · 9.98 · 10.52 | **9.73 s** | 8.65 s | 11 | ≈ 0.79 s |

La suma de las medianas por nivel (0.15 + 5.75 + 9.73 = 15.63 s) es coherente con el tiempo de la
suite completa en la máquina cargada (13.2 – 15.7 s), lo que confirma que el costo total es la suma de
los tres niveles y no hay una penalización por ejecutarlos juntos.

**Sobre la dispersión de los tiempos:** la máquina compartida tenía *load average* ≈ 4.8 durante las
mediciones, lo que explica que una misma suite fluctuara entre 5.6 s y 15.7 s. La comparación
*entre niveles* es concluyente en cualquier caso (diferencias de uno y dos órdenes de magnitud);
las cifras absolutas deben leerse como dependientes del entorno. Como referencia, las entregas
previas del nivel API se midieron en otro equipo (Windows, Python 3.14.8) y dieron 2.02 – 3.35 s:
el orden de magnitud se mantiene; el valor absoluto depende de la máquina.

### 3.5 Entorno de ejecución

| Elemento | Valor |
|---|---|
| Sistema operativo | Linux (Debian/Ubuntu) |
| Python | 3.14.6 |
| pytest | 9.1.1 |
| pytest-playwright | 0.10.0 |
| Navegador | Chromium (Playwright), modo headless por defecto |
| Servidor de la app | Werkzeug `make_server` en `http://127.0.0.1:5000`, levantado automáticamente por la fixture `base_url` de `tests/conftest.py` |
| Comando de referencia | `pytest -v --durations=0` desde la raíz del proyecto |

No hubo errores de dependencias ni de infraestructura: la suite se ejecutó completa en todas las
corridas, sin pruebas ignoradas por falta de navegador.

### 3.6 Resultados reportados por el equipo en sus ramas (ejecuciones históricas)

Las cifras de esta tabla **no** son de la ejecución actual: son las que cada integrante registró en su
propia entrega, con su propio entorno y con el estado del código de su momento. Se conservan para
trazar la historia del proyecto, y **no sustituyen** los datos de §3.1–§3.4.

| Fuente | Nivel | Pruebas | Aprobadas | Fallidas | Tiempo reportado | Entorno |
|---|---|---:|---:|---:|---|---|
| `origin/JuanPablo` | Unitario (ejecución **inicial**, antes de corregir el defecto) | 98 | 94 | 4 | **0.24 s** (pytest) · 0.78 s (reloj de pared) | Windows · Python 3.13.3 |
| `origin/JuanPablo` | Unitario (ejecución **final**, después de la corrección) | 98 | 98 | 0 | **0.16 s** (pytest) · 0.76 s (reloj de pared); 5 repeticiones entre 0.14 s y 0.16 s | Windows · Python 3.13.3 |
| `origin/JuanPablo` | Unitario (confirmación con `--durations=5`) | 98 | 98 | 0 | **0.14 s**; las 98 pruebas por debajo de 0.005 s (≈ 0.0014 s por prueba) | Windows · Python 3.13.3 |
| `origin/JuanPablo` | Suite completa de su momento (`pytest -q`) | 100 | 100 | 0 | **2.25 s** (pytest) · 2.79 s (reloj de pared); 3.82 s en una corrida con el sistema ocupado | Windows · Python 3.13.3 |
| `origin/JuanPablo` | Línea base API y E2E de su momento (solo el test de ejemplo) | 1 y 1 | 1 y 1 | 0 | 0.37 s (API) y 2.13 s (E2E) | Windows · Python 3.13.3 |
| `origin/Nicky` | API | 65 | 60 | 5 | **2.02 – 3.35 s** (12 ejecuciones: 3.35, 3.19, 3.14, 3.11, 3.07, 2.82, 2.55, 2.41, 2.24, 2.23, 2.23, 2.02 s); mediana ≈ 2.69 s, promedio ≈ 2.70 s (0.042 s por prueba) | Windows (win32) · Python 3.14.8 · playwright 1.64.0 · Flask 3.1.3 |
| `origin/Nicky` | Suite completa de su momento | — | — | — | No reportada en esa entrega | Windows (win32) · Python 3.14.8 |
| `origin/Chris` | E2E | 11 | 9 | 2 | **9.8 s** (mediana de 3 corridas: 9.86 / 9.75 / 9.50 s); 14.6 s en la primera corrida con navegador en frío; 9.54 s con `--durations=0 -q`; 37.39 s con `--headed --slowmo 500` | Python 3.14.6 · Chromium |
| `origin/Chris` | Línea base unitaria y API de su momento (solo el test de ejemplo) | 1 y 1 | 1 y 1 | 0 | 0.03 s (unitarias) y 0.83 s (API) | Python 3.14.6 |
| `origin/Chris` | Suite completa de su momento (`pytest -v`, antes de su entrega) | 3 | 3 | 0 | **1.07 s** | Python 3.14.6 |

**Cómo se leen estas cifras frente a las de §3.**

1. **Los conteos de fallos de API y E2E no contradicen los actuales: son de otro estado del código.**
   Nicky reporta 5 fallos de API y Chris 2 fallos de E2E; hoy la suite registra 2 y 1
   respectivamente. La diferencia no está en las pruebas: el commit `82dd920` (rama `origin/JuanPablo`)
   cambió `app/validaciones.py` de `precio < 0` a `precio <= 0`, y con ello las 3 pruebas de
   `API-002` (precio 0) y la de `E2E-002` (precio 0 en el formulario) pasaron a verde. Chris y Nicky
   trabajan sobre ramas creadas **antes** de ese cambio (su `app/validaciones.py` conserva
   `precio < 0`, verificado con `git show`), por lo que sus informes describen la app **antes** de la
   corrección. En el estado actual de `main` sus cifras de fallos ya no son reproducibles.
2. **Los conteos de pruebas totales tampoco son comparables**: las 100 pruebas de Juan Pablo
   (= 98 unitarias + 1 API + 1 E2E, las dos últimas siendo el test de ejemplo de la plantilla) y las 3
   de Chris (= 1 por nivel) eran el estado de la suite en su momento; la suite completa actual tiene
   174 casos.
3. **Los tiempos sí son comparables por nivel, con matices.** El nivel unitario coincide en las tres
   fuentes (0.14–0.16 s reportados por Juan Pablo; 0.15 s medido aquí). El nivel E2E también coincide
   (9.8 s reportados por Chris; 9.73 s medido aquí, en el mismo tipo de entorno: Python 3.14.6).
   El nivel API es el caso distinto: 2.02–3.35 s en el equipo de Nicky (Windows) frente a 5.00–6.45 s
   medidos aquí (Linux, máquina compartida con *load average* ≈ 4.8). **Son dos máquinas distintas**
   (Windows frente a Linux, y con distinta carga), por lo que el orden de magnitud del nivel API
   (segundos) es comparable, pero la cifra absoluta no. Es importante precisar que **el stack de
   software es idéntico** en ambos casos (pytest 9.1.1, pytest-playwright 0.10.0, playwright 1.64.0 y
   Flask 3.1.3): la diferencia de 2.02–3.35 s frente a 5.00–6.45 s proviene del sistema operativo, del
   hardware y de la carga de la máquina, no de las versiones de las librerías. Es el ejemplo más claro
   de que un mismo conjunto de pruebas rinde distinto en cada equipo.
4. **El reporte de Chris sobre su propio conteo** —"11 collected (10 pruebas propias + el ejemplo de la
   plantilla)"— no coincide con el contenido de su rama: `tests/e2e/test_e2e.py` en `origin/Chris`
   tiene 9 funciones (una parametrizada con 3 rutas), que generan 11 casos. El total de 11 es
   correcto; la explicación "10 propias + el ejemplo" no lo es: no quedó ningún test de ejemplo en el
   archivo E2E (el ejemplo sí estaba en los archivos unitario y API de su rama).

### 3.7 Problemas del entorno y diferencias entre máquinas

| Aspecto | Equipo (`origin/JuanPablo`) | Equipo (`origin/Nicky`) | Equipo (`origin/Chris`) | Medición de esta entrega |
|---|---|---|---|---|
| Sistema operativo | Windows | Windows (win32) | no declarado en su informe | Linux |
| Versión de Python | 3.13.3 | 3.14.8 | 3.14.6 | 3.14.6 |
| pytest / pytest-playwright | 9.1.1 / 0.10.0 | 9.1.1 / 0.10.0 | 9.1.1 / 0.10.0 | 9.1.1 / 0.10.0 |
| playwright / Flask | no declarados | 1.64.0 / 3.1.3 | no declarados | **1.64.0 / 3.1.3** (idénticos a los de `origin/Nicky`) |
| Entorno Python | `.venv` del proyecto | `.venv` del proyecto | el del laboratorio | `/usr/bin/python3` (el `.venv` del proyecto solo tiene `pip`; no se usó) |
| Navegador | no aplica | no aplica (nivel API sin navegador) | Chromium de Playwright | Chromium de Playwright (`DISPLAY=:1`) |
| Carga de la máquina durante las mediciones | no declarada | no declarada | no declarada | *load average* ≈ 4.8 (máquina compartida) |

Problemas de entorno registrados por el equipo, sin impacto en los resultados:

- **La suite se levanta sola.** En las tres ramas, la fixture `base_url` de `tests/conftest.py` levanta
  la app con `werkzeug.serving.make_server` en `http://127.0.0.1:5000`; no se requiere un servidor
  manual ni existe el riesgo de que el puerto esté ocupado por una ejecución anterior.
- **Navegador en frío.** Chris reporta una primera corrida de 14.6 s frente a una mediana de 9.8 s: el
  arranque en frío de Chromium encarece la primera ejecución. Es el motivo por el que las mediciones
  de este informe usan medianas de varias corridas y no un único cronómetro.
- **Sin residuos entre corridas.** Nicky verificó que dos ejecuciones consecutivas de `pytest tests/api
  -q` dieron exactamente el mismo resultado (5 fallidas, 60 aprobadas).
- **Ausencia de dependencias del `.venv` en Linux.** En esta máquina, el entorno virtual del proyecto
  no tiene pytest ni Playwright instalados; se ejecutó con el intérprete del sistema. No afecta a los
  resultados, pero explica por qué las cifras de esta entrega no son directamente comparables con las
  de las ramas Windows, que sí usaron el `.venv` del proyecto.

---

## 4. Defectos encontrados y evidencia reproducible

### 4.1 Registro de defectos

| ID consolidado | Nivel que lo detectó | Funcionalidad afectada | Prueba (archivo::función) | Alias en las ramas del equipo | Estado |
|---|---|---|---|---|---|
| **UNIT-001** | Unitario (primero en detectarlo); también API y E2E | Validación del precio: se aceptaba `0` | `tests/unitarias/test_unitarias.py::test_regresion_def_01_precio_cero_debe_rechazarse` · `test_precio_fuera_de_rango_reporta_error_de_rango[cero_int\|cero_float]` · `test_limite_rango_precio[ultimo_invalido_cero]` | `DEF-01` (`origin/JuanPablo`) · `API-002` / `DEF-02` (`origin/Nicky`) · `E2E-002` (`origin/Chris`) | **Corregido** en `app/validaciones.py` (commit `82dd920`); ya no reproduce (§4.6) |
| **API-001** | API | `GET /api/productos/<id>` con id inexistente responde 200 `{}` en vez de 404 | `tests/api/test_api.py::TestConsultaDeProductos::test_consultar_producto_inexistente_devuelve_404` · `::TestEliminacionDeProductos::test_consultar_un_producto_eliminado_devuelve_404` | `OBS-01` (`origin/JuanPablo`) · `DEF-01` / `API-001` (`origin/Nicky`) · observación §1.3 de `origin/Chris` | **Pendiente de corrección por desarrollo** |
| **E2E-001** | E2E | El botón "Eliminar" borra siempre el **primer** producto de la tabla | `tests/e2e/test_e2e.py::test_eliminar_producto_borra_solo_ese_producto_y_no_afecta_a_los_demas` | `E2E-001` (`origin/Chris`) | **Pendiente de corrección por desarrollo** |

> **Consolidación de identificadores.** Cada integrante numeró sus hallazgos desde su propia entrega:
> `DEF-01`/`OBS-01` (Juan Pablo), `DEF-01`/`DEF-02`/`API-001`/`API-002` (Nicky) y `E2E-001`/`E2E-002`
> (Chris). Al cruzar los tres informes aparece que **el precio `0` aceptado es un único defecto
> reportado con tres nombres distintos** (`DEF-01` de Juan Pablo = `API-002`/`DEF-02` de Nicky =
> `E2E-002` de Chris), y que **el `200` en vez de `404` en `GET /api/productos/<id>` es un único
> defecto con dos nombres** (`OBS-01` de Juan Pablo = `DEF-01`/`API-001` de Nicky; Chris lo detectó
> por revisión del contrato y lo dejó como observación, porque lo reporta el nivel API y no el E2E).
> El inventario final es de **3 entradas, sin duplicados**: 2 defectos vigentes (API-001, E2E-001) y
> 1 ya corregido (UNIT-001). Nicky dejó además una fila explícita `DEF-03` con "no se confirmó un
> tercer defecto en el nivel de API", y Chris dejó una fila reservada equivalente: no son defectos,
> son afirmaciones de no-hay-más-hallazgos, y por eso no figuran en el inventario.
>
> **Nota sobre la numeración original de Nicky:** su tabla de defectos llama `DEF-01` a lo que aquí es
> **API-001** (el `200` en vez de `404`) y `DEF-02` a lo que aquí es **UNIT-001** (el precio `0`), pero
> en la sección 4.3 de su propio informe asigna los mismos identificadores a `API-001` y `API-002`.
> Se adoptó la numeración por nivel (`API-xxx`, `E2E-xxx`, `UNIT-xxx`) por ser la que usa el equipo
> completo, y se deja constancia de la equivalencia.

### 4.1.1 Evidencia aportada por cada rama

| Defecto | Evidencia consolidada | Procedencia |
|---|---|---|
| **UNIT-001** | `AssertionError: El precio 0 viola la regla 'mayor que 0' y debía devolver 400; se recibió 201: {"id":4,"nombre":"Precio Cero","precio":0,"stock":1}` → `assert 201 == 400` (API)<br>`AssertionError: El precio 0.0 viola la regla 'mayor que 0' y debía devolver 400; se recibió 201: {"id":4,"nombre":"Precio Cero","precio":0.0,"stock":1}` → `assert 201 == 400` (API, variante decimal)<br>`AssertionError: El precio 0 viola la regla 'mayor que 0' y debía devolver 400; se recibió 200: {"id":4,"nombre":"Precio Cero","precio":0,"stock":1}` → `assert 200 == 400` (API, variante `PUT`)<br>`AssertionError: El precio 0 debe rechazarse: la regla dice 'mayor que 0'` (unitario)<br>`AssertionError: Locator expected to be visible / Actual value: None / Error: element(s) not found` (E2E: no aparece el `role="alert"`; la tabla muestra `4 Producto Sin Costo 0.00 1 Editar Eliminar`) | API: `origin/Nicky` §4.3 · unitario: `origin/JuanPablo` §4.1 · E2E: `origin/Chris` §E2E-002 |
| **API-001** | `AssertionError: El contrato exige 404 para un id inexistente y se recibió 200: {}` → `assert 200 == 404`, con `status=200 status_text='OK'` en `http://127.0.0.1:5000/api/productos/9999`<br>`AssertionError: Un producto eliminado ya no existe: el contrato exige 404 y se recibió 200: {}` → `assert 200 == 404`, sobre `http://127.0.0.1:5000/api/productos/4`<br>Respuesta recibida: `HTTP/1.1 200 OK` con cuerpo `{}`.<br>Verificación independiente por código y cliente de Flask de Juan Pablo: `GET /api/productos/999` → `200 {}`, frente a `PUT`/`DELETE` sobre un id inexistente, que sí devuelven `404` | API: `origin/Nicky` §4.3 (evidencia literal) · unitario: `origin/JuanPablo` §4.2 (OBS-01, verificado con el cliente de prueba de Flask) · E2E: `origin/Chris` §1.3 (verificación con petición real, sin dejar prueba E2E fallando) |
| **E2E-001** | `AssertionError: La tabla no quedó como exige la especificación (solo debe desaparecer el producto eliminado):`<br>`  esperado: {'Teclado': {'id': '1', 'precio': '250.00', 'stock': '10'}, 'Monitor': {'id': '3', 'precio': '1450.00', 'stock': '5'}}`<br>`  obtenido: {'Mouse': {'id': '2', 'precio': '95.50', 'stock': '25'}, 'Monitor': {'id': '3', 'precio': '1450.00', 'stock': '5'}}`<br>Traza del servidor durante la prueba: `POST /productos/1/eliminar HTTP/1.1" 302` (la fila pulsada era la de Mouse, id 2). Verificación en el DOM: las 3 filas iniciales tenían `action="/productos/1/eliminar"` | E2E: `origin/Chris` §E2E-001 (traza y DOM) · reproducido en la medición de esta entrega |

### 4.2 UNIT-001 · El precio `0` se aceptaba como válido (ya corregido)

| Campo | Detalle |
|---|---|
| **Identificador** | UNIT-001 (referenciado como DEF-01 / API-002 / E2E-002 en entregas previas) |
| **Nivel que lo detectó primero** | Unitario |
| **Funcionalidad afectada** | Regla de validación del precio: "Número **mayor que 0** y como máximo 100,000" |
| **Causa raíz** | `app/validaciones.py`, rama de rango del precio: se comparaba `precio < 0`, de modo que el `0` pasaba la validación. El propio mensaje de error de la app ("debe ser mayor que 0") contradecía la condición implementada |
| **Pasos para reproducirlo (versión original del código)** | 1. `from app.validaciones import validar_producto`. 2. `validar_producto("Teclado", 0, 10)` → devuelve `[]` (producto válido). 3. Consecuencia observable en la API: `POST /api/productos` con `{"nombre": "Precio Cero", "precio": 0, "stock": 1}` respondía **201 Created** y almacenaba el producto |
| **Resultado esperado** | Lista de errores no vacía, con el mensaje de precio fuera de rango; en la API, 400 + `{"errores": [...]}` |
| **Resultado real (en el código original)** | Lista de errores vacía; la API respondía 201 y persistía el producto con precio 0 |
| **Pruebas que lo detectaban** | 1 unitaria (`test_regresion_def_01_precio_cero_debe_rechazarse`) + 3 del nivel API (`test_crear_producto_con_precio_cero_devuelve_400[precio-cero-entero|precio-cero-decimal]`, `test_actualizar_producto_con_precio_cero_devuelve_400`) + 1 E2E (`test_formulario_rechaza_precio_cero`) = **5 pruebas** |
| **Evidencia** | `AssertionError: El precio 0 viola la regla 'mayor que 0' y debía devolver 400; se recibió 201: {"id":4,"nombre":"Precio Cero","precio":0,"stock":1}` → `assert 201 == 400` (API) · `AssertionError: El precio 0 debe rechazarse: la regla dice 'mayor que 0'` (unitario) · `AssertionError: Locator expected to be visible / Actual value: None / Error: element(s) not found` (E2E) |
| **Severidad sugerida** | **Discrepancia entre integrantes (pendiente de acordar).** En `origin/JuanPablo` se clasifica como **Alta** ("permite registrar y vender productos con precio 0; afecta la integridad de los datos y el cálculo de ventas; el caso llega hasta la base de datos en memoria y se expone por la API con 201"). En esta consolidación se propone **Media**: permite persistir productos con precio 0, pero no hay pérdida de datos, brecha de seguridad ni caída del servicio, y la corrección es de una línea. El argumento de la severidad Alta (impacto en el cálculo de ventas) depende del contexto de negocio, que la especificación del laboratorio no define |
| **Estado** | **Corregido** en `app/validaciones.py` por el commit `82dd920` ("feat: Pruebas Unitarias"), que cambió `precio < 0` por `precio <= 0`. En la ejecución actual **las 5 pruebas pasan**; el defecto no reproduce |

### 4.3 API-001 · `GET /api/productos/<id>` responde 200 en lugar de 404

| Campo | Detalle |
|---|---|
| **Identificador** | API-001 (referenciado como OBS-01 en entregas previas) |
| **Nivel que lo detectó** | API |
| **Funcionalidad afectada** | Contrato HTTP de la API: `GET /api/productos/<id>` · No existe → **404** |
| **Causa raíz** | `app/__init__.py:216`, ruta `api_obtener`: la rama de producto inexistente devuelve `jsonify({}), 200` |
| **Pasos para reproducirlo** | 1) `POST /api/login` con `{"usuario": "admin", "password": "Admin123"}` → 200 con token. 2) `GET /api/productos/9999` con la cabecera `Authorization: Bearer <token>`. 3) Observar el código y el cuerpo de la respuesta. (Variante: crear un producto, borrarlo con `DELETE /api/productos/<id>` y volver a hacer `GET` sobre ese id.) |
| **Resultado esperado** | **404** con un cuerpo de error, como sí hacen `PUT` y `DELETE` sobre un id inexistente |
| **Resultado real** | **200 OK** con el cuerpo JSON vacío `{}`. La diferencia es doble: el código de estado (200 en lugar de 404) y el cuerpo (un objeto vacío, no un cuerpo de error). El cliente que solo comprueba el código de estado no puede distinguir "el producto existe y está vacío" de "el producto no existe"; en consecuencia, el flujo `DELETE` tampoco puede confirmarse por `GET` (la prueba `test_eliminar_producto_lo_quita_del_listado_y_conserva_los_demas` sí lo confirma por el listado, y esa parte sí pasa) |
| **Pruebas que lo detectan** | `tests/api/test_api.py::TestConsultaDeProductos::test_consultar_producto_inexistente_devuelve_404`<br>`tests/api/test_api.py::TestEliminacionDeProductos::test_consultar_un_producto_eliminado_devuelve_404` |
| **Evidencia (salida de `pytest -v --durations=0`)** | `AssertionError: El contrato exige 404 para un id inexistente y se recibió 200: {}` → `assert 200 == 404`, con `status=200 status_text='OK'` en `http://127.0.0.1:5000/api/productos/9999`<br>`AssertionError: Un producto eliminado ya no existe: el contrato exige 404 y se recibió 200: {}` → `assert 200 == 404`, sobre `http://127.0.0.1:5000/api/productos/4` |
| **Severidad sugerida** | **Media** (coincide con la calificación de `origin/Nicky` §4.3). No hay corrupción de datos ni riesgo de seguridad, y un cliente atento puede deducir la ausencia por el cuerpo `{}`; sin embargo, rompe el contrato documentado y hace que un `DELETE` no sea verificable por `GET`, lo que puede inducir lógica de cliente defectuosa (marcar "eliminado" solo si el `GET` devuelve 404) |
| **Estado** | **Pendiente de corrección por desarrollo.** La prueba se conserva fallando en la entrega |

### 4.4 E2E-001 · "Eliminar" borra siempre el primer producto de la tabla

| Campo | Detalle |
|---|---|
| **Identificador** | E2E-001 |
| **Nivel que lo detectó** | E2E (navegador real) |
| **Funcionalidad afectada** | Interfaz web: "'Eliminar' borra **ese** producto, muestra 'Producto eliminado' y los demás productos no cambian" |
| **Causa raíz** | `app/templates/productos.html:25`: el formulario de borrado se construye con `url_for('eliminar_producto', pid=productos[0].id)`, es decir, **siempre el id del primer producto de la lista**, en lugar del `p.id` de la fila. Verificado en el DOM: las tres filas iniciales apuntaban a `action="/productos/1/eliminar"` |
| **Pasos para reproducirlo** | 1) `python run.py` (o dejar que pytest levante la app) y abrir `http://127.0.0.1:5000/login`. 2) Iniciar sesión con `admin` / `Admin123`. 3) En la tabla (Teclado id 1, Mouse id 2, Monitor id 3) pulsar **Eliminar** en la fila de **Mouse**. 4) La página muestra "Producto eliminado", pero la tabla queda con `Mouse (2)` y `Monitor (3)`: se borró `Teclado (1)`. El log del servidor registra `POST /productos/1/eliminar` |
| **Resultado esperado** | Desaparece Mouse (id 2); Teclado (1) y Monitor (3) permanecen idénticos (250.00/10 y 1450.00/5) |
| **Resultado real** | El mensaje "Producto eliminado" sí aparece, pero el registro borrado es el primero de la tabla (Teclado, id 1); el producto sobre el que se hizo clic (Mouse, id 2) permanece en la tabla. El mensaje de éxito es engañoso: comunica que se borró el producto equivocado |
| **Prueba que lo detecta** | `tests/e2e/test_e2e.py::test_eliminar_producto_borra_solo_ese_producto_y_no_afecta_a_los_demas` (se conserva **fallando**) |
| **Evidencia (salida de `pytest -v --durations=0`)** | `AssertionError: La tabla no quedó como exige la especificación (solo debe desaparecer el producto eliminado):`<br>`  esperado: {'Teclado': {'id': '1', 'precio': '250.00', 'stock': '10'}, 'Monitor': {'id': '3', 'precio': '1450.00', 'stock': '5'}}`<br>`  obtenido: {'Mouse': {'id': '2', 'precio': '95.50', 'stock': '25'}, 'Monitor': {'id': '3', 'precio': '1450.00', 'stock': '5'}}` |
| **Severidad sugerida** | **Alta** (coincide con la calificación de `origin/Chris` §E2E-001). Destrucción silenciosa de un registro que el usuario no eligió (pérdida de datos del inventario) y mensaje de éxito falso. Ocurre en todos los borrados desde la interfaz web salvo que el producto sea el primero de la lista |
| **Estado** | **Pendiente de corrección por desarrollo.** La prueba se conserva fallando en la entrega |

### 4.5 Observaciones sin prueba asociada (fuera del alcance de la especificación)

No son defectos confirmados contra el oráculo, pero conviene que desarrollo las considere:

| ID | Observación | Evidencia | Impacto |
|---|---|---|---|
| RIESGO-01 | Un precio `float("nan")` se acepta como válido: en Python toda comparación con `NaN` es `False`, así que ni `precio <= 0` ni `precio > 100000` se cumplen | `validar_producto("Teclado", float("nan"), 1)` → `[]` | Un `NaN` entrante por la API se guarda como precio y contamina cálculos. La especificación no lo menciona, por lo que **no** se escribió una prueba que lo prohíba |
| RIESGO-02 | Una contraseña de 6 espacios (`"      "`) se considera válida: el largo se mide sin recortar y la especificación solo exige "mínimo 6 caracteres" | `validar_credenciales("admin", "      ")` → `[]` | Conviene aclarar en la especificación si una contraseña solo con espacios debe rechazarse |
| RIESGO-03 | El stock se valida con `isinstance(stock, int)`, por lo que un `5.0` (float) se rechaza aunque sea un valor entero | `validar_producto("Teclado", 100.0, 5.0)` → 1 error "El stock debe ser un número entero" | Cumple la especificación ("Entero"), pero un cliente JSON que envíe `5.0` recibe 400. Conviene documentarlo en el contrato de la API |

> Los tres riesgos proceden de `origin/JuanPablo` §4.4 y fueron **verificados de nuevo en esta
> entrega** (mismos resultados), por lo que se mantienen con la etiqueta *medido aquí*.


### 4.7 Verificación cruzada de los hallazgos del equipo

Cada defecto reportado por un integrante fue contrastado con la evidencia de los otros dos niveles y
con la medición de esta entrega:

| Hallazgo del equipo | Contrastado con | Veredicto |
|---|---|---|
| `DEF-01` (Juan Pablo) y `API-002`/`DEF-02` (Nicky) y `E2E-002` (Chris): el precio `0` se acepta | La función `validar_producto` (causa raíz común), la API (`201`) y la interfaz web (fila con precio `0.00`) | **Mismo defecto, tres nombres.** Corregido en `82dd920`; sus 5 pruebas pasan hoy |
| `OBS-01` (Juan Pablo) y `DEF-01`/`API-001` (Nicky): `GET /api/productos/<id>` de un id inexistente devuelve `200 {}` | `app/__init__.py:216` (`return jsonify({}), 200`), la observación §1.3 de Chris (`GET /api/productos/999` → `200`) y las 2 pruebas de API que fallan hoy | **Mismo defecto, dos nombres.** Sigue vigente |
| `E2E-001` (Chris): "Eliminar" borra el primer producto | `app/templates/productos.html:25` (`pid=productos[0].id`), la traza `POST /productos/1/eliminar` de Chris y la reproducción de esta entrega | **Defecto propio del nivel E2E**, sin equivalente en API ni unitario |
| Filas `DEF-03` (Nicky) y "fila reservada" (Chris): no se confirmó un tercer defecto | — | No son defectos: son afirmaciones de no-hay-más-hallazgos, con 2 y 2 fallos respectivamente explicados |
| Juan Pablo §5.2: cifras de API y E2E de su momento (1 Fallos pendientes de diagnóstico

**Ninguno.** Los 3 fallos de la ejecución se explican íntegramente por los dos defectos confirmados
(2 pruebas para API-001 y 1 para E2E-001). No hubo errores de pruebas, no hubo problemas de entorno
(la suite se ejecutó completa en todas las corridas) y no quedaron fallos sin causa identificada.
Ninguna prueba se marcó con `skip`/`xfail` ni se relajó para obtener un resultado verde.


## 5. Tabla comparativa de los tres niveles

Los datos de la columna "medido" provienen de §3. Las valoraciones cualitativas se marcan como tales.

| Aspecto | Unitarias (pytest) | API (Playwright HTTP) | E2E (Playwright navegador) |
|---|---|---|---|
| **Qué verifican** | Las reglas de validación puras de `app/validaciones.py`: usuario, contraseña, nombre, precio y stock, con particiones de equivalencia y valores límite (98 casos) | El contrato HTTP de `/api/...`: autenticación (200/401/400), autorización (401 sin o con token inválido), CRUD completo con códigos de estado exactos, persistencia y casos de "no existe" (65 casos) | Los flujos del usuario en la interfaz web: login exitoso y fallido, redirección sin sesión, alta, edición y baja de productos, y mensajes en pantalla (11 casos) |
| **Cantidad de pruebas ejecutadas** | **Medido:** 98 casos (22 funciones parametrizadas) | **Medido:** 65 casos (30 funciones parametrizadas) | **Medido:** 11 casos (9 funciones parametrizadas) |
| **Pruebas aprobadas y fallidas** | **Medido:** 98 aprobadas, 0 fallidas | **Medido:** 63 aprobadas, 2 fallidas (API-001) | **Medido:** 10 aprobadas, 1 fallida (E2E-001) |
| **Tiempo medido** | **Medido:** 0.15 s (mediana de 5 ejecuciones independientes; rango 0.15 – 0.22 s) | **Medido:** 5.75 s (mediana de 5 ejecuciones independientes; rango 5.00 – 6.45 s) | **Medido:** 9.73 s (mediana de 5 ejecuciones independientes; rango 6.08 – 10.52 s) |
| **Dependencia de la interfaz gráfica** | **Ninguna:** funciones puras, sin servidor, sin navegador | **Ninguna:** solo HTTP; no se abre ningún navegador (usa `APIRequestContext`) | **Total:** Chromium real, con renderizado de HTML y ejecución del JavaScript de la página |
| **Velocidad observada** | **Medido:** ≈ 0.0017 s por caso; prácticamente todos los casos por debajo de 0.005 s (entre 380 y 430 duraciones ocultas según la carga de la máquina) | **Medido:** ≈ 0.088 s por caso; dominada por el arranque de Playwright (0.65 s en el primer caso de la ejecución de referencia, 0.32 s con la máquina descargada) | **Medido:** ≈ 0.79 s por caso; el caso más lento (1.48 s en la ejecución de referencia; 0.94 s con la máquina descargada) espera el mensaje de bienvenida con 800 ms de retraso |
| **Costo de ejecución y mantenimiento** | **Bajo.** Sin dependencias externas; se ejecuta en cualquier entorno con Python. Mantenimiento bajo: el oráculo son las reglas del spec, no la implementación | **Medio.** Necesita el servidor de la app levantado (la fixture lo hace sola) y Playwright instalado. Mantenimiento medio: depende del contrato HTTP y de la forma del JSON, no de selectores de UI, pero un renombrado de campo o de ruta rompe muchas aserciones a la vez | **Alto.** Necesita servidor + navegador + drivers. Mantenimiento alto: depende del texto en pantalla, del orden de las columnas y del HTML; es el nivel que más se resiente con los cambios de maquetación |
| **Fragilidad observada** | **Baja observada.** 98/98 estables en todas las corridas. Fragilidad potencial: si se reescribiera el *formato* de los mensajes de error (no su significado), las aserciones por fragmentos normalizados lo absorberían | **Baja observada.** Los 2 fallos son deterministas y están causados por la app, no por la prueba. Fragilidad potencial: cambios en nombres de ruta, en el JSON o en el mecanismo del token | **Media observada.** 1 de 11 casos falla por un defecto real de la app. Fragilidad potencial: un cambio de *copy* ("Ingresar", "Guardar", "Producto creado", "Bienvenido, admin"), un reordenamiento de columnas o un retardo mayor en el saludo romperían pruebas sin que haya un defecto de negocio |
| **Defectos detectados** | **Medido:** 1 (UNIT-001, ya corregido). Ninguno vigente | **Medido:** 1 vigente (API-001) + 1 ya corregido (API-002 = UNIT-001) | **Medido:** 1 vigente (E2E-001) + 1 ya corregido (E2E-002 = UNIT-001) |

**Lectura de los datos.** Con 11 casos, el nivel E2E consume ≈ 9.7 s: **63 veces** el tiempo del
nivel unitario y **1.7 veces** el del nivel API, y su costo por caso es ≈ **465 veces** el de una
prueba unitaria (0.79 s frente a 0.0017 s). El nivel unitario, con 98 casos, es el que aporta mayor
cobertura de reglas en menos de un segundo. El nivel API es el punto intermedio: sin navegador, pero
con el costo de levantar el servidor y el cliente HTTP.

### 5.1 Cifras reportadas por el equipo (otras ramas, otras máquinas)

Esta tabla **complementa** la anterior y no la sustituye: recoge lo que cada integrante midió en su
propio nivel y en su propio entorno. Las cifras de tiempo **no son comparables entre filas** cuando
cambia la máquina (§3.6).

| Criterio | Unitarias | API | E2E |
|---|---|---|---|
| **Procedencia** | `origin/JuanPablo` | `origin/Nicky` | `origin/Chris` |
| **Número de pruebas** | **Reportado:** 98 (22 funciones) | **Reportado:** 65 (30 funciones) | **Reportado:** 11 casos (9 funciones, una parametrizada con 3 rutas) |
| **Pruebas aprobadas y fallidas** | **Reportado:** 98 / 0 tras la corrección de UNIT-001 (94 / 4 en la ejecución inicial, con los 4 fallos del mismo defecto) | **Reportado:** 60 / 5 (2 de API-001 + 3 de API-002), **antes** de la corrección de `app/validaciones.py` | **Reportado:** 9 / 2 (E2E-001 + E2E-002), **antes** de la corrección de `app/validaciones.py` |
| **Tiempo total de ejecución (s)** | **Reportado:** 0.14 – 0.16 s (5 ejecuciones) | **Reportado:** 2.02 – 3.35 s (12 ejecuciones; mediana ≈ 2.69 s) | **Reportado:** 9.8 s (mediana de 3 ejecuciones; 14.6 s en frío) |
| **Tiempo promedio por prueba (s)** | **Reportado:** ≈ 0.0014 s | **Reportado:** ≈ 0.042 s | **Reportado:** ≈ 0.89 s |
| **Defectos detectados (IDs de la rama)** | **Reportado:** DEF-01 (precio 0) + OBS-01 (por revisión de código, no por las pruebas) | **Reportado:** API-001, API-002 | **Reportado:** E2E-001, E2E-002 |
| **¿Qué cambio en la app rompería estas pruebas sin que haya un defecto?** | Reescribir el texto de los mensajes de error, o devolver los errores en otro formato (p. ej. objetos en vez de cadenas) | Cambiar el contrato HTTP: códigos de estado, forma del JSON (`{"token"}` / `{"errores"}`), nombres de rutas, mecanismo de autenticación (`Authorization: Bearer <token>`) o los datos iniciales que restaura `POST /api/reset` | Cambios de *copy* o de maquetación: renombrar "Ingresar"/"Guardar"/"Eliminar", cambiar "Bienvenido, admin" o "Producto creado", o reordenar las columnas de la tabla (las pruebas comprueban la celda por posición) |
| **Costo de mantenimiento** | **Bajo**: funciones puras, sin red ni navegador; se ejecutan en milisegundos y no se rompen por cambios de interfaz | **Medio**: depende del contrato HTTP estable, no de selectores de UI, pero un renombrado de campo o de ruta rompe muchas aserciones a la vez | **Alto** en esta consolidación; Chris lo calificó de **Medio** ("no depende de la base de datos ni del backend, pero sí del texto de la interfaz, del orden de las columnas y de la existencia del navegador; además cada corrida paga el arranque de Chromium, ~3-5 s"). **Discrepancia menor pendiente**: el nivel E2E es el único que depende de Chromium y de la maquetación, y en la medición de esta entrega fue el más caro y el más frágil |

**Sobre la última fila:** la calificación del costo de mantenimiento del nivel E2E no coincide entre
el equipo (Medio, `origin/Chris`) y esta consolidación (Alto). Se conservan ambas posturas con su
procedencia; el factor objetivo en el que ambos coinciden es que **es el único nivel que depende del
navegador y del texto de la interfaz**, y es el único que aporta un defecto que ningún otro nivel
puede detectar (E2E-001).

---

## 6. Análisis de detección de defectos

### 6.1 ¿Qué nivel detectó cada defecto?

| Defecto | ¿Qué nivel lo detectó? | ¿Quién lo reportó? | ¿Qué aspecto verificó esa prueba? |
|---|---|---|---|
| **UNIT-001** (precio `0` aceptado) | **Primero el nivel unitario** (partición de rango y límite inferior del precio); después lo detectaron también API (2 pruebas) y E2E (1 prueba) — ver la coincidencia en §6.2 | `origin/JuanPablo` (`DEF-01`), `origin/Nicky` (`API-002`/`DEF-02`), `origin/Chris` (`E2E-002`) | La regla "Precio: número mayor que 0" en la función pura `validar_producto`, con el límite inferior exclusivo verificado como valor límite |
| **API-001** (`GET` de id inexistente devuelve 200) | **Solo el nivel API** | `origin/Nicky` (`API-001`/`DEF-01`); `origin/JuanPablo` lo detectó por revisión de código (`OBS-01`); `origin/Chris` lo verificó con una petición real (§1.3) | El código de estado HTTP exacto de `GET /api/productos/<id>` frente al contrato de la guía, y la verificación posterior a un `DELETE` |
| **E2E-001** ("Eliminar" borra el primer producto) | **Solo el nivel E2E** | `origin/Chris` (`E2E-001`) | La identidad del registro borrado y la integridad del resto de la tabla tras pulsar el botón "Eliminar" de una fila concreta, en un navegador real |

> **Sobre el alcance de cada hallazgo.** Nicky y Juan Pablo no "descubrieron" por separado los mismos
> tres defectos: cada uno vio el que le tocaba en su nivel, y la coincidencia se produce porque los
> tres niveles ejercitan la **misma función de validación** `validar_producto` a través de capas
> distintas. La única coincidencia real entre niveles es UNIT-001 (detectado por los tres). API-001 y
> E2E-001 son hallazgos independientes, aunque Juan Pablo y Chris los mencionaran como observaciones
> al revisar el contrato de la API y el flujo web respectivamente: por eso el nivel API y el E2E
> **sí** aportan verificación sobre un mismo defecto, y el nivel unitario no puede llegar a ninguno
> de los dos.

### 6.2 Coincidencias entre niveles y su valor

**UNIT-001 fue detectado por los tres niveles.** Es el único defecto con redundancia de detección, y
la redundancia resultó útil:

- El nivel **unitario** lo detectó primero, en milisegundos y sin necesidad de servidor ni
  navegador, localizando la causa raíz exacta (`app/validaciones.py`).
- El nivel **API** confirmó que el defecto no era un artefacto de la función aislada sino que se
  propagaba al contrato público: la API devolvía `201 Created` y almacenaba un producto con precio
  0.
- El nivel **E2E** confirmó que también se propagaba a la interfaz web: el formulario aceptaba el
  precio 0, mostraba "Producto creado" y el producto quedaba listado con precio `0.00`.

Es decir, los tres niveles cuentan **la misma historia con detalle creciente**: la función está mal,
el contrato público está mal y la experiencia del usuario está mal. La redundancia no es un defecto
del diseño de la suite: es la confirmación de que el defecto tiene impacto real en las tres capas.
Una vez corregido el código, las 5 pruebas que lo detectaban pasaron a la vez, lo que confirma que
ninguna de ellas dependía de un detalle accidental de la implementación.

Los otros dos defectos **no** presentan redundancia, y eso también es información útil: API-001
afecta solo a la capa HTTP (la interfaz web nunca usa `GET /api/productos/<id>`), y E2E-001 afecta
solo a la capa de presentación (la API borra correctamente el producto que se le pide). Ninguno de
los dos habría sido encontrado por los niveles inferiores, por lo que la pirámide completa está
justificada.

### 6.3 ¿Por qué sigue siendo útil la prueba del nivel que lo detectó?

- **E2E-001 (nivel E2E).** La prueba verifica el resultado observable por el usuario (qué registro
  desaparece de la tabla y qué mensaje aparece). Un test unitario o de API que solo comprobara "el
  endpoint de borrado elimina el id que recibe" pasaría en verde aunque la interfaz enviara el id
  equivocado: el defecto está en el **enlace entre la fila y la acción del formulario**, no en la
  ruta HTTP. La prueba E2E sigue siendo útil además como documentación ejecutable del requisito
  "borrar *ese* producto", y porque es la única que verifica el texto "Producto eliminado" que el
  usuario lee.
- **API-001 (nivel API).** Verifica códigos de estado exactos, algo que no existe en la interfaz web
  ni en las funciones puras. Sigue siendo útil porque el contrato documentado es parte de la
  especificación y los clientes de la API dependen de él.
- **UNIT-001 (nivel unitario).** Sigue siendo la prueba más barata y precisa para vigilar la regla
  del precio: si desarrollo reintroduce `precio < 0`, falla en milisegundos y señala la línea exacta.

---

## 7. Evaluación de si podía detectarse en un nivel inferior

| Defecto | ¿Podía detectarse en un nivel más barato? | ¿Qué prueba lo habría detectado antes? | ¿Por qué no? / ¿Por qué sí? |
|---|---|---|---|
| **UNIT-001** (precio `0`) | **Sí, y de hecho así se detectó** | Una prueba unitaria de `validar_producto("Teclado", 0, 10)` que exija lista de errores no vacía. Ya existe: `test_regresion_def_01_precio_cero_debe_rechazarse` | No depende de integración, rutas HTTP, sesión ni HTML: es lógica de negocio pura. Es el candidato ideal al nivel unitario |
| **API-001** (`GET` de id inexistente → 200) | **Sí, en el nivel API** (ya es el nivel más barato posible para este defecto) | `GET /api/productos/9999` esperando 404. Ya existe: `test_consultar_producto_inexistente_devuelve_404` | Es un comportamiento del contrato HTTP. Una prueba unitaria no puede observarlo: depende de la ruta, del decorador `requiere_token` y de la serialización JSON. El nivel API es el más barato que puede detectarlo |
| **E2E-001** ("Eliminar" borra el primero) | **No, no con los niveles inferiores** | No existe una prueba unitaria ni de API que lo detecte | El defecto está en la **plantilla HTML**: el `action` del formulario se construye con `productos[0].id`. La ruta `POST /productos/<id>/eliminar` funciona perfectamente (la API borra el id que recibe y devuelve 204), y `validar_producto` no interviene. Solo una prueba que renderice la página, lea el formulario y envíe la petición reproduce el enlace roto entre la fila y la acción. Un test de API que borrara `/api/productos/2` daría verde con el bug presente |

**Conclusión de esta sección.** Dos de los tres defectos (UNIT-001 y API-001) eran detectables en un
nivel más barato que el que terminó reportándolos, y en el caso de UNIT-001 el nivel unitario los
detectó primero. El tercero (E2E-001) es genuinamente un defecto de la capa de presentación: no es
redundante con los niveles inferiores, y la prueba E2E que lo detecta es la única forma razonable de
certificarlo. Esto es exactamente el argumento a favor de una pirámide: **cada nivel cubre lo que
los niveles inferiores no alcanzan**, y ninguno es innecesario.

### 7.1 Contraste con lo que concluyó cada integrante

| Pregunta | Conclusión de esta consolidación (medida aquí) | Conclusión del equipo en sus ramas | Veredicto |
|---|---|---|---|
| ¿Un E2E solo detectaría el precio `0`? | Sí, pero de forma tardía y confusa: el fallo se manifiesta como un `role="alert"` que no aparece | Chris (`origin/Chris`, ficha de E2E-002): "este defecto también es detectable con una prueba unitaria de `validar_producto` (Parte 2), que es más barata y rápida que la prueba E2E" | **Coinciden**: el nivel unitario lo detecta antes y mejor |
| ¿Una suite solo de unitarias detectaría el `200` en vez de `404`? | No: es una ruta de Flask, ningún test de `validar_producto` la alcanza | Juan Pablo (`origin/JuanPablo`, §6.4): "Una suite **solo unitarias** no habría detectado OBS-01… porque `api_obtener` es una ruta de Flask y ningún test de `validar_producto` la alcanza; sí lo detecta el nivel API" | **Coinciden** |
| ¿Qué nivel detecta el borrado del producto equivocado? | Solo E2E: el defecto está en la plantilla (`productos[0].id`), y tanto la API como las funciones puras funcionan correctamente por separado | Chris: nadie de los otros niveles lo detectó | **Coinciden** (no hay discrepancia: cada integrante, desde su nivel, solo lo ve en E2E) |

---

## 8. Recomendación fundamentada en la pirámide de pruebas

### 8.1 Qué correr en cada momento del pipeline

| Momento | Suite recomendada | Justificación con los datos medidos |
|---|---|---|
| **En cada commit** | **Unitarias** (98 casos, 0.15 s) + **API** (65 casos, 5.75 s) | Ambas detectan defectos de contrato y de reglas de negocio sin necesidad de navegador, y juntas tardan ≈ 5.9 s. Son las que aportan volumen de casos (163 de 174) a un costo despreciable. Detectarían UNIT-001 en milisegundos y API-001 en el mismo commit en que se introdujo |
| **En cada pull request** | **Unitarias + API + E2E** (suite completa, 174 casos, ≈ 14 s) | El PR es el último punto antes de integrar código de varios autores: un fallo de integración (p. ej. E2E-001, que rompe el flujo de borrado completo) solo se ve con navegador. 14 s es un costo aceptable para esa garantía, y los datos muestran que el nivel E2E aporta ≈ 0.79 s por caso, muy por debajo de los segundos que tardan los pipelines reales |
| **Antes de liberar a producción** | **Suite completa + revisión manual de los flujos críticos** (login, alta y baja de productos) | Los flujos E2E son los que el usuario final vive; el resto de la pirámide garantiza que las reglas se mantienen. Es también el momento de revisar que no quede ningún defecto abierto de severidad alta (E2E-001 lo es) |

Adicionalmente, conviene **dejar el nivel E2E en modo *nightly*** (una corrida por noche o antes de
cada publicación), porque es el más sensible a cambios de maquetación: es el único que se rompe por
un cambio de *copy* o de orden de columnas que no es un defecto.

### 8.2 Justificación con la pirámide de pruebas

La pirámide de pruebas (Fowler & Vocke, *The Practical Test Pyramid*) recomienda muchos tests rápidos
en la base y pocos tests lentos y de alto costo en la cima. Los datos de este laboratorio respaldan la
recomendación con números medidos:

1. **Base amplia y barata (unitarias).** 98 casos en 0.15 s, sin servidor ni navegador: el 56 % de
   los casos de la suite se ejecuta en el 1 % del tiempo total. Es donde conviene concentrar la
   cobertura de reglas y de valores límite, porque el costo marginal de un caso es despreciable y
   el diagnóstico es inmediato (la función está a un stack de un salto).
2. **Nivel intermedio (API).** 65 casos en 5.75 s sin navegador: cubre autenticación, autorización,
   códigos de estado y el contrato JSON, que son la superficie de integración real entre la app y
   sus clientes. Aquí se detectan los defectos de contrato (API-001) que ni las funciones puras ni
   la interfaz web pueden ver, y sin pagar el costo de un navegador.
3. **Cima estrecha y valiosa (E2E).** 11 casos en 9.73 s: no intenta revalidar todas las
   combinaciones de validación (eso ya lo hacen los dos niveles inferiores), sino comprobar los
   **flujos críticos** — iniciar sesión, crear, editar y eliminar un producto — y la coherencia
   entre lo que el usuario ve y lo que la app hace. Es el único nivel que detectó E2E-001.

El resultado práctico: **detectar un defecto en el nivel más bajo posible reduce el costo de
diagnóstico**. Para UNIT-001, la prueba unitaria señaló el archivo y la línea en milisegundos; para
API-001, la prueba de API muestra el código de estado y el cuerpo exactos en 5.75 s; solo E2E-001
exige abrir un navegador. Y a la inversa: un E2E que detecta un defecto de reglas puras obliga a
recorrer la pirámide hacia abajo para encontrar la causa, gastando tiempo en lo que la suite unitaria
la habría detectado a tiempo.

### 8.3 Respuestas a las preguntas de la guía

- **¿Qué defecto NO habría detectado una suite solo de pruebas E2E?** API-001: la interfaz web nunca
  llama a `GET /api/productos/<id>`, así que un E2E verde no dice nada sobre ese código de estado.
  Y en general, una suite solo E2E no cubre ni el contrato JSON ni los códigos de estado exactos.
  Consecuencia práctica: un cliente de la API que dependa del 404 se rompería sin que la suite
  E2E se enterara.
- **¿Qué defecto NO habría detectado una suite solo de pruebas unitarias?** E2E-001: es un defecto
  de la plantilla HTML, no de una función. Y aunque existiera una suite unitaria y de API completa,
  seguiría sin detectar que el botón "Eliminar" de la fila de *Mouse* borra *Teclado*, porque ambas
  capas inferiores funcionan correctamente por separado: la API borra el id que recibe y las funciones
  de validación no participan en el borrado.

### 8.4 Recomendaciones del equipo para el desarrollo (respaldadas por la evidencia)

Estas recomendaciones proceden de `origin/JuanPablo` §6.1–§6.3 y se recogen aquí porque están
**respaldadas por la evidencia reunida en §4**; las que no se pudieron verificar con la evidencia
disponible se marcan como *pendiente de confirmar*.

| Prioridad | Recomendación | Evidencia que la respalda | Estado |
|---|---|---|---|
| **Alta** | Mantener la corrección de UNIT-001 y su prueba de regresión `test_regresion_def_01_precio_cero_debe_rechazarse` | §4.2: si alguien vuelve a escribir `precio < 0`, la prueba falla en milisegundos | Aplicada (commit `82dd920`) y verificada |
| **Alta** | Cerrar API-001: devolver `jsonify({"error": "Producto no encontrado"}), 404` en la rama de producto inexistente de `api_obtener`, igual que ya hacen `api_actualizar` y `api_eliminar` | §4.3: 2 pruebas fallan por esto; `app/__init__.py:216` | **Pendiente de desarrollo** |
| **Alta** | Corregir E2E-001: el `action` del formulario de borrado debe usar el id de la fila (`p.id`) y no `productos[0].id` | §4.4: pérdida silenciosa de datos; `app/templates/productos.html:25` | **Pendiente de desarrollo** |
| **Media** | Validar el precio en la capa de entrada (ruta), o garantizar que `validar_producto` sea la única puerta de entrada, con una prueba de API que lo demuestre | §4.2: el defecto llegó hasta el almacén y se expuso por la API con `201` | Pendiente de desarrollo |
| **Media** | Rechazar valores no finitos en el precio (usar `math.isfinite` en `_es_numero`) y agregar la partición correspondiente al conjunto de pruebas | RIESGO-01 (§4.5): `float("nan")` se guarda como precio válido | Pendiente: la especificación no lo exige, por lo que **no** se escribió una prueba que lo prohíba |
| **Media** | Definir en la especificación si una contraseña de solo espacios es aceptable y, si no lo es, reflejarlo en la regla y en la prueba | RIESGO-02 (§4.5) | Pendiente de definir por el equipo |
| **Baja** | Centralizar los mensajes de error en constantes o en un catálogo, para que las pruebas dejen de depender de fragmentos de texto | §2.2: las aserciones por fragmentos normalizados absorben cambios de redacción, pero no un cambio de estructura | Pendiente de desarrollo |
| **Baja** | Documentar en el contrato de la API que el stock debe enviarse como entero (`5.0` se rechaza) | RIESGO-03 (§4.5) | Pendiente de desarrollo |

> Las recomendaciones 1 a 3 del equipo (prioridades alta) se derivan directamente de los tres
> defectos consolidados en §4; las de prioridad media y baja se apoyan en los riesgos RIESGO-01..03,
> que son observaciones **fuera del alcance de la especificación** y por lo que no se dejó ninguna
> prueba fallando que las imponga.

---

## 9. Conclusiones

1. La suite automatizada de los tres niveles quedó construida y es ejecutable con un solo comando:
   **174 casos (61 funciones), 171 aprobados, 3 fallidos, 0 omitidos, 0 errores de infraestructura**,
   en ≈ 14 s.
2. Se confirmaron **2 defectos vigentes** de la aplicación, ambos con evidencia reproducible y con su
   prueba fallando en la entrega: **API-001** (`GET /api/productos/<id>` de un id inexistente
   devuelve 200 `{}` en vez de 404 — severidad media) y **E2E-001** (el botón "Eliminar" borra siempre
   el primer producto de la tabla — severidad alta, con pérdida silenciosa de datos). Un tercer
   defecto histórico, **UNIT-001** (el precio `0` se aceptaba), ya fue corregido en
   `app/validaciones.py` por un commit previo y sus 5 pruebas pasan.
3. Ninguno de los 3 fallos se atribuye a un error de las pruebas ni a un problema del entorno: en
   todos los casos la causa raíz está identificada en el código de `app/` (líneas `app/__init__.py:216`
   y `app/templates/productos.html:25`). No hay fallos pendientes de diagnóstico.
4. La comparación entre niveles muestra con datos medidos una diferencia de **dos órdenes de
   magnitud** entre la base y la cima: 98 casos unitarios en 0.15 s frente a 11 casos E2E en 9.73 s
   (≈ 465 veces más caro por caso). Cada nivel tiene un alcance propio: las reglas de negocio, el
   contrato HTTP y la interacción real con la interfaz web.
5. El análisis de detección confirma que la estrategia en pirámide no es una recomendación de
   manual: UNIT-001 se detectó primero con una prueba unitaria de milisegundos y API-001 con una
   prueba de API de 5.75 s, mientras que E2E-001 solo es observable en el navegador y por eso la
   cima de la pirámide es indispensable en este proyecto.
6. **Pendiente para el equipo de desarrollo:** corregir `app/__init__.py` (rama de producto
   inexistente en `api_obtener`) y `app/templates/productos.html` (el `action` del formulario de
   borrado debe usar el id de la fila). Ambas correcciones son de una línea y, al aplicarlas, las
   3 pruebas que hoy fallan pasarán a verde sin tocar las aserciones.
7. **Observación de proceso:** la entrega anterior modificó `app/validaciones.py` para corregir
   UNIT-001 (§4.6), lo que contraviene la regla del laboratorio de no tocar `app/`. En esta entrega
   **no se modificó ningún archivo de `app/`** ni de `tests/`; solo `INFORME.md`. Si se requiere
   evaluar la suite contra la app original, basta revertir ese commit de un carácter.
8. **El trabajo de las tres ramas es coherente y complementario.** Al cruzar `origin/JuanPablo`
   (unitario), `origin/Nicky` (API) y `origin/Chris` (E2E) con la medición de esta entrega, los tres
   niveles detectan defectos **distintos y complementarios**, los tres hallazgos del equipo se
   consolidan en **3 defectos únicos** (2 vigentes + 1 ya corregido), y las conclusiones de cada
   integrante sobre qué nivel detecta qué coinciden con las de esta consolidación (§7.1). Ninguna
   rama introduce un hallazgo que contradiga a otro, y ninguna cifra reportada resultó ser un error
   de medición: las diferencias entre los conteos de fallos se explican por el cambio de
   `app/validaciones.py` del commit `82dd920`.
9. **Los datos del equipo y los datos de esta entrega son complementarios, no intercambiables.** Los
   conteos y tiempos reportados por cada integrante se conservan en §3.6 y §5.1 con su procedencia
   (rama, archivo, entorno y estado del código). Las únicas cifras que deben leerse como
   equivalentes son las del nivel unitario (0.14–0.16 s reportados / 0.15 s medidos) y las del
   nivel E2E (9.8 s reportados / 9.73 s medidos); las del nivel API corresponden a máquinas distintas
   y no deben compararse directamente.
10. **Discrepancias abiertas (pendientes de que el equipo las resuelva):** (a) la severidad de
   UNIT-001, **Alta** según `origin/JuanPablo` frente a **Media** según esta consolidación;
   (b) el costo de mantenimiento del nivel E2E, **Medio** según `origin/Chris` frente a **Alto**
   según esta consolidación; (c) la explicación del conteo de 11 casos E2E en el informe de Chris
   ("10 propias + el ejemplo de la plantilla"), cuando su archivo contiene 9 funciones que
   parametrizan a 11 casos. Ninguna de las tres afecta a los resultados de la suite.

---

### Anexo · Comandos ejecutados y registro de mediciones

| Comando | Resultado | Tiempo reportado por pytest |
|---|---|---|
| `pytest -v --durations=0` (ejecución de referencia de la guía) | 171 passed, 3 failed | **14.12 s** |
| `pytest -q` (10 ejecuciones de control) | 171 passed, 3 failed | 5.64 · 6.58 · 13.21 · 14.12 · 14.80 · 15.23 · 15.29 · 15.31 · 15.47 · 15.71 s |
| `pytest tests/unitarias -q` (5 ejecuciones independientes) | 98 passed | 0.15 · 0.15 · 0.15 · 0.18 · 0.22 s (mediana 0.15 s) |
| `pytest tests/api -q` (5 ejecuciones independientes) | 63 passed, 2 failed | 5.00 · 5.18 · 5.75 · 6.34 · 6.45 s (mediana 5.75 s) |
| `pytest tests/e2e -q` (5 ejecuciones independientes) | 10 passed, 1 failed | 6.08 · 6.94 · 9.73 · 9.98 · 10.52 s (mediana 9.73 s) |
| `pytest tests/e2e --headed --slowmo 500` | 10 passed, 1 failed | 31.58 s (navegador visible y pasos ralentizados, para revisión manual del flujo) |

Todos los comandos se ejecutaron desde la raíz del proyecto (`lab08_estudiante/lab08_estudiante/`).

### Anexo B · Ramas inspeccionadas y procedimiento seguido

Comandos usados (ninguno alteró el estado del repositorio):

```bash
git fetch --all --prune                       # solo actualiza referencias remotas
git branch -a && git branch -r                # inventario de ramas locales y remotas
git log --graph --oneline --all               # historia y merges
git ls-tree -r --name-only origin/<rama>     # archivos de cada rama
git show origin/<rama>:lab08_estudiante/lab08_estudiante/INFORME.md   # informe de cada rama
git diff --stat origin/main origin/<rama> -- lab08_estudiante/lab08_estudiante/{app,tests}
git show origin/<rama>:.../app/validaciones.py                        # estado del código en cada rama
```

No se ejecutó `git pull`, `git merge`, `git rebase`, `git reset`, `git checkout` ni `git switch`: los
informes de los compañeros se consultaron **en modo lectura**, con `git show` y `git diff`. No se
eliminó ninguna rama, no se hizo `push` y no se sobrescribió ningún archivo de los integrantes.

| Rama | Commit | Contenido del `INFORME.md` | Estado del `app/validaciones.py` | Archivos de prueba propios |
|---|---|---|---|---|
| `origin/main` | `3f3a7d4` (merge de los tres aportes) | 394 líneas — versión concatenada de las tres entregas | `precio <= 0` (con la corrección) | Los tres niveles completos |
| `origin/JuanPablo` | `82dd920` "feat: Pruebas Unitarias" | 274 líneas — nivel unitario | `precio <= 0` (con la corrección) | `tests/unitarias/test_unitarias.py` (22 funciones) |
| `origin/Nicky` | `44ab185` "api/test_api" | 158 líneas — nivel API | `precio < 0` (sin la corrección) | `tests/api/test_api.py` (30 funciones) |
| `origin/Chris` | `39e022c` "feat: test-2e2" | 151 líneas — nivel E2E | `precio < 0` (sin la corrección) | `tests/e2e/test_e2e.py` (9 funciones) |

Verificación de integridad: `git diff origin/main origin/<rama> -- tests/.../test_<nivel>.py` no
devuelve diferencias de código en ninguno de los tres archivos de prueba (solo `.pyc`), es decir, la
suite medida en §3 es exactamente la unión de las tres entregas.

### Anexo C · Procedencia de cada dato y discrepancias abiertas

| Dato | Procedencia | Tipo |
|---|---|---|
| 174 casos · 171 aprobados · 3 fallidos · 14.12 s (rango 5.64–15.71 s) | `pytest -v --durations=0` en esta entrega | **Medido aquí** |
| Desglose 98 / 65 / 11 casos por nivel | `pytest --collect-only` + ejecución por nivel en esta entrega | **Medido aquí** |
| Medianas por nivel: 0.15 s · 5.75 s · 9.73 s | 5 ejecuciones independientes por nivel en esta entrega | **Medido aquí** |
| Causa raíz de API-001 (`app/__init__.py:216`) | Inspección del código + reproducción en esta entrega | **Medido aquí** |
| Causa raíz de E2E-001 (`app/templates/productos.html:25`) | `origin/Chris` §E2E-001 (traza del servidor y DOM) + reproducción en esta entrega | **Reportado y reproducido aquí** |
| Texto literal de las aserciones de API-001 | `origin/Nicky` §4.3 | **Reportado** (reproducido aquí: mismo `assert 200 == 404`) |
| Texto literal de las aserciones de UNIT-001 en API | `origin/Nicky` §4.3 | **Reportado** (histórico: ya no se reproduce por la corrección) |
| Tiempos del nivel API en Windows (2.02–3.35 s) | `origin/Nicky` §4.2 | **Reportado** — otra máquina, no directamente comparable |
| Tiempos del nivel E2E (9.8 s de mediana) | `origin/Chris` §2.1 | **Reportado** — comparable con los 9.73 s medidos aquí |
| Tiempos del nivel unitario (0.14–0.16 s) | `origin/JuanPablo` §5.1 | **Reportado** — comparable con los 0.15 s medidos aquí |
| 65 API: 60 aprobadas / 5 fallidas | `origin/Nicky` §4.2 | **Reportado, histórico** (antes de la corrección de `app/validaciones.py`) |
| 11 E2E: 9 aprobadas / 2 fallidas | `origin/Chris` §2.1 | **Reportado, histórico** (ídem) |
| 100 casos / 100 aprobados / 2.25 s (suite completa del nivel unitario) | `origin/JuanPablo` §5.3 | **Reportado, histórico** — con solo 1 prueba de ejemplo en API y E2E |
| Severidad Alta de UNIT-001 | `origin/JuanPablo` §4.1 | **Reportado — discrepancia abierta** (esta consolidación propone Media) |
| Costo de mantenimiento Medio del nivel E2E | `origin/Chris` §2 | **Reportado — discrepancia abierta** (esta consolidación propone Alto) |
| "11 collected = 10 propias + el ejemplo de la plantilla" | `origin/Chris` §2 | **Reportado — discrepancia abierta** (su archivo tiene 9 funciones → 11 casos) |
| Datos de identificación del equipo (nombres y carnés) | `origin/Nicky` (encabezado) | **Reportado** — pendiente de que el equipo lo confirme |
| RIESGO-01..03 | `origin/JuanPablo` §4.4 | **Reportado y verificado aquí** (mismos resultados) |
| Recomendaciones de desarrollo por prioridad | `origin/JuanPablo` §6.1–§6.3 | **Reportado** — respaldado por la evidencia de §4 |
