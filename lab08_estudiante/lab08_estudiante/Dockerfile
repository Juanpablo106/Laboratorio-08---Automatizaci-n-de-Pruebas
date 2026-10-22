# Alternativa a la instalación local (útil si Windows da problemas).
# Construir:   docker build -t lab08-pruebas .
# Probar:      docker run --rm -v "${PWD}:/lab" lab08-pruebas
# Ver la app:  docker run --rm -p 5000:5000 lab08-pruebas python run.py --host 0.0.0.0
#              (y abrir http://127.0.0.1:5000 en tu navegador)
FROM python:3.12-slim

WORKDIR /lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY . .
CMD ["pytest", "-v"]
