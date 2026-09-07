# 1. Cambiamos a Bookworm (Debian 12) que es la versión estable actual
FROM python:3.11-slim-bookworm

# 2. Instalamos dependencias del sistema (ya no fallará el update)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl apt-transport-https gnupg2 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# 3. Llave de Microsoft y repositorio apuntando a Debian 12
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 4. Instalar el driver ODBC 17
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# 5. Configurar el directorio de trabajo
WORKDIR /app

# 6. Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copiar el código de la aplicación
COPY . .

# 8. Iniciar la aplicación
CMD gunicorn --bind 0.0.0.0:$PORT app_prestamos:app