# 1) Imagen base
FROM python:3.11-slim

# 2) Crear directorio de trabajo
WORKDIR /app

# 3) Copiar requirements primero
COPY requirements.txt .

# 4) Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copiar TODO el código
COPY . .

# 6) Exponer el puerto que usa Cloud Run
EXPOSE 8080

# 7) Comando de arranque
CMD ["python", "main.py"]
