FROM python:3.11-slim-bullseye

# Instalar herramientas del sistema
RUN apt-get update && apt-get install -y curl apt-transport-https gnupg2 unixodbc-dev

# Agregar llave de Microsoft a la carpeta de confianza y configurar el repositorio
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl -fsSL https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Instalar el driver ODBC 17
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Configurar el directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Iniciar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app_prestamos:app"]