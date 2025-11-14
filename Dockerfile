# Imagen base
FROM python:3.11-slim

# Configuración
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8080/health || exit 1

# Comando: gunicorn para producción
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --timeout 120 main:app
