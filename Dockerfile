FROM python:3.11-slim-bullseye

# 1. Solución al error 100: Aceptar el cambio de release en Debian 11
RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends curl apt-transport-https gnupg2 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. Agregar llave de Microsoft a la carpeta de confianza y configurar el repositorio
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl -fsSL https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 3. Instalar el driver ODBC 17 (también aceptando el cambio por si acaso)
RUN apt-get update --allow-releaseinfo-change && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# 4. Configurar el directorio de trabajo
WORKDIR /app

# 5. Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el código de la aplicación
COPY . .

# 7. Iniciar la aplicación
CMD gunicorn --bind 0.0.0.0:$PORT app_prestamos:app