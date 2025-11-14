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

# Copiar código y credenciales
COPY . .

# Asegurarse de que los archivos de credenciales existen y tienen permisos correctos
RUN chmod 600 credentials.json token.json 2>/dev/null || true

# Exponer puerto
EXPOSE 8080


# Comando: directo con gunicorn (sin entrypoint para simplificar debug)
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --timeout 120 main:app
