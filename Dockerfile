# Usa una imagen base de Python oficial
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos al directorio de trabajo
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el contenido del directorio actual al directorio de trabajo
COPY . .

# Expone el puerto 3000
EXPOSE 3000

# Ejecuta el comando "python" cuando se inicie el contenedor
CMD ["gunicorn", "-b", "0.0.0.0:3000", "app:app"]
