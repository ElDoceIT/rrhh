FROM python:3.11-slim

WORKDIR /app

# Instalar FastAPI y Uvicorn
RUN pip install --no-cache-dir fastapi uvicorn

COPY app/main.py .

# Ejecutar en el puerto 8051 definido para RRHH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8051"]