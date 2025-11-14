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
# Asegurarse de que entrypoint es ejecutable y usarlo para materializar secretos
RUN chmod +x /app/entrypoint.sh 2>/dev/null || true

# Usar el entrypoint para escribir CLIENT_SECRETS/TOKEN_JSON en archivos y luego
# arrancar gunicorn desde el script. Esto asegura que los secretos inyectados
# via Cloud Run / Secret Manager existan antes de que la app intente autenticarse.
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
