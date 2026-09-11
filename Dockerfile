FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Ejecutar en el puerto 8051 definido para RRHH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8051", "--proxy-headers", "--forwarded-allow-ips=*"]
