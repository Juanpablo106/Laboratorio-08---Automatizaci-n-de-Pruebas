# Laboratorio 8 · Pruebas automatizadas con pytest y Playwright

| | |
|---|---|
| **Unidad** | 8 · Pruebas de Software |
| **Tipo de material** | Laboratorio práctico (guía del estudiante) |
| **Tiempo estimado** | 90 min en clase + 15 min de preparación previa |
| **Modalidad** | Parejas o tríos |
| **Herramientas** | Python 3.10+, pytest, Playwright (todo gratuito) |

## Objetivos

Al terminar podrás:

1. Probar el mismo sistema en tres niveles: unitario, integración (API) y sistema (E2E).
2. Diseñar casos con partición de equivalencia y valores límite, usando la especificación como oráculo.
3. Comparar con datos el costo, la velocidad y la fragilidad de cada nivel, y justificar una estrategia en forma de pirámide.

## Contexto

*Inventario IS1* es un sistema web de inventario que el equipo de desarrollo quiere liberar esta semana. Ustedes son el equipo de QA. Desarrollo asegura que "todo funciona", pero no escribió pruebas automatizadas. Su trabajo es construir la suite de pruebas y **encontrar los defectos antes de que lleguen a producción**.

**Reglas del juego**

- **No modifiques nada dentro de `app/`.** Tu trabajo es probar, no corregir.
- El oráculo es la **especificación** de esta guía (sección "Especificación"). Si la app se comporta distinto a lo especificado, encontraste un defecto.
- Cuando una prueba detecte un defecto, **déjala fallando**. No cambies la aserción para que pase: eso sería ocultar el defecto.
- Una prueba que falla sobre un comportamiento correcto es un **falso positivo** y resta puntos.

## Preparación (antes de la clase, ~15 min)

### Opción A · Instalación local en Windows (recomendada)

Abre PowerShell en la carpeta del laboratorio:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
pytest
```

> Si PowerShell bloquea la activación del entorno, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

En macOS o Linux cambia las dos primeras líneas por `python3 -m venv .venv` y `source .venv/bin/activate`.

Debes ver **`3 passed`**. Si lo ves, estás listo.

### Opción B · Docker (si la opción A falla)

```powershell
docker build -t lab08-pruebas .
docker run --rm -v "${PWD}:/lab" lab08-pruebas
```

Con Docker no podrás ver el navegador (`--headed`) ni usar `codegen`; por eso la opción A es la recomendada.

## La aplicación

Levántala para explorarla (no es obligatorio para correr las pruebas: si no está corriendo, pytest la levanta solo):

```powershell
python run.py
```

Abre http://127.0.0.1:5000 · usuario **admin** · contraseña **Admin123**

```
app/
  validaciones.py     <- reglas de validación (funciones puras)
  __init__.py         <- rutas web y API
  templates/          <- pantallas HTML
tests/
  conftest.py         <- fixtures compartidas (no modificar)
  unitarias/          <- NIVEL 1: pytest puro
  api/                <- NIVEL 2: Playwright, solo HTTP
  e2e/                <- NIVEL 3: Playwright con navegador
INFORME.md            <- plantilla del informe
```

## Especificación (el oráculo)

### Reglas de validación

| Campo | Regla |
|---|---|
| Usuario (login) | Obligatorio (no vacío ni solo espacios) |
| Contraseña (login) | Mínimo 6 caracteres |
| Nombre de producto | Entre 3 y 50 caracteres, ambos incluidos (sin contar espacios al inicio o final) |
| Precio | Número **mayor que 0** y como máximo 100,000 |
| Stock | Entero mayor o igual a 0 |

Las funciones `validar_credenciales(usuario, password)` y `validar_producto(nombre, precio, stock)` devuelven una **lista de mensajes de error**: lista vacía significa datos válidos.

### Contrato de la API

Todas las rutas de `/api/productos` requieren la cabecera `Authorization: Bearer <token>`. Sin token válido responden **401**.

| Método y ruta | Caso | Respuesta |
|---|---|---|
| `POST /api/login` | Credenciales correctas | 200 + `{"token": "..."}` |
| | Credenciales incorrectas | 401 |
| | Formato inválido | 400 + `{"errores": [...]}` |
| `GET /api/productos` | | 200 + lista de productos |
| `POST /api/productos` | Datos válidos | 201 + producto creado (con `id`) |
| | Datos inválidos | 400 + `{"errores": [...]}` |
| `GET /api/productos/<id>` | Existe | 200 + producto |
| | No existe | **404** |
| `PUT /api/productos/<id>` | Datos válidos | 200 + producto actualizado |
| | Datos inválidos / no existe | 400 / 404 |
| `DELETE /api/productos/<id>` | Existe | 204 |
| | No existe | 404 |

### Comportamiento de la interfaz web

1. Sin sesión, cualquier página de productos redirige a `/login`.
2. Login correcto: lleva a la lista de productos y muestra "Bienvenido, admin".
3. Login incorrecto: muestra "Usuario o contraseña incorrectos".
4. "Nuevo producto" abre un formulario; al guardar, muestra "Producto creado" y el producto aparece en la tabla.
5. "Editar" permite modificar el producto; al guardar, muestra "Producto actualizado".
6. "Eliminar" borra **ese** producto, muestra "Producto eliminado" y los demás productos no cambian.

**Datos iniciales** (se restauran antes de cada prueba de API y E2E):

| ID | Nombre | Precio (Q) | Stock |
|---|---|---|---|
| 1 | Teclado | 250.00 | 10 |
| 2 | Mouse | 95.50 | 25 |
| 3 | Monitor | 1450.00 | 5 |

## Desarrollo (90 min)

### Parte 1 · Reconocimiento (10 min)

1. Corre `pytest -v` y observa los 3 ejemplos (uno por nivel).
2. Levanta la app con `python run.py` y recórrela como usuario: login, crear, editar, eliminar.
3. Lee la especificación y anota qué comportamientos merecen una prueba.

### Parte 2 · Pruebas unitarias con pytest (15 min)

Archivo: `tests/unitarias/test_unitarias.py`

1. Para cada regla de validación identifica las **particiones** (válida e inválidas).
2. Para cada límite escribe el **último valor inválido y el primer valor válido** (por ejemplo, stock −1 y 0).
3. Usa `@pytest.mark.parametrize` para no repetir código.
4. Corre `pytest tests/unitarias -v`. Anota el tiempo.

### Parte 3 · Pruebas de API con Playwright (15 min)

Archivo: `tests/api/test_api.py`

1. Usa la fixture `api` (sin token) y `api_autenticada` (con token).
2. Prueba el login, el acceso sin token, el CRUD completo y los casos negativos de la tabla del contrato.
3. Verifica el **código de estado exacto**, no solo que "respondió".
4. Corre `pytest tests/api -v`. Anota el tiempo.

### Parte 4 · Pruebas E2E con Playwright (20 min)

Archivo: `tests/e2e/test_e2e.py`

1. Graba un flujo con `playwright codegen http://127.0.0.1:5000` (con la app corriendo) y úsalo como borrador. **Limpia** el código generado: nombres claros, localizadores por rol o etiqueta, aserciones con `expect`.
2. Automatiza: login exitoso, login fallido, crear producto y eliminar producto.
3. No uses `time.sleep()`. `expect(...)` espera automáticamente (*auto-waiting*). Compruébalo con el mensaje de bienvenida, que aparece con retraso.
4. Mira tus pruebas correr: `pytest tests/e2e --headed --slowmo 500`.
5. Corre `pytest tests/e2e -v`. Anota el tiempo.

### Parte 5 · Análisis e informe (25 min)

1. Corre la suite completa: `pytest -v --durations=0`.
2. Llena `INFORME.md`: defectos encontrados, tabla comparativa y recomendación.
3. Discute en equipo: ¿qué nivel encontró cada defecto? ¿Pudo encontrarlo un nivel más bajo y más barato?

### Parte 6 · Entrega (5 min)

Comprime en `equipoXX.zip` (XX = número de equipo):

```
equipoXX.zip
  tests/
    unitarias/test_unitarias.py
    api/test_api.py
    e2e/test_e2e.py
  INFORME.md
```

Puedes agregar más archivos `test_*.py` dentro de cada carpeta. Sube el zip a la plataforma antes de terminar la clase.

## Evaluación (100 pts)

**Calificación automática (80 pts).** Tus pruebas se ejecutarán contra una versión **correcta** de la app y contra versiones con defectos sembrados (como en las pruebas de mutación: "rompe a propósito").

| Criterio | Pts | Cómo se mide |
|---|---|---|
| Validez | 20 | Proporción de tus pruebas que pasan en la versión correcta (sin falsos positivos) |
| Cobertura de niveles | 15 | Al menos 2 pruebas válidas en cada nivel (5 pts por nivel) |
| Detección de defectos | 45 | Cada defecto sembrado que alguna de tus pruebas válidas detecta |

**Informe (20 pts), calificado por el catedrático.**

| Criterio | Pts |
|---|---|
| Reportes de defectos completos y reproducibles | 6 |
| Tabla comparativa con datos medidos (no supuestos) | 6 |
| Recomendación justificada con la pirámide de pruebas | 8 |

## Referencias

- Playwright para Python: https://playwright.dev/python/docs/intro
- pytest: https://docs.pytest.org
- ISTQB CTFL v4.0, capítulo 4 (técnicas de prueba)
- Fowler, M. / Vocke, H. *The Practical Test Pyramid*
