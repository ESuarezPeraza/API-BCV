# 1. La Imagen Base
# Cambiamos a 'bullseye', una versión de Debian OS completa
FROM python:3.10-bullseye

# 2. ACTUALIZACIÓN DE CERTIFICADOS DEL SISTEMA
# Esta es la nueva línea clave.
# Actualizamos los paquetes del OS y reinstalamos los certificados raíz.
RUN apt-get update && apt-get install -y --reinstall ca-certificates

# 3. Configuración del Entorno
WORKDIR /app

# 4. Copiar Requisitos
COPY requirements.txt .

# 5. Instalar Dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el Resto del Código
COPY . .