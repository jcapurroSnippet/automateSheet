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

# Copiar entrypoint (si existe en la imagen) y asegurarse de permisos
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh || true

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8080/health || exit 1

# Comando: entrypoint que prepara credenciales y arranca gunicorn
CMD ["/entrypoint.sh"]
