# Usa una imagen base oficial de Python. Es buena práctica especificar la versión.
FROM python:3.12

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# Instala las dependencias. La bandera --no-cache-dir ahorra espacio.
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de tu aplicación al contenedor
COPY . .

# Expone el puerto si tu bot es un servidor web o escucha en algún puerto (ej. un bot de Discord que usa un webhook)
# Si tu bot no es un servidor, puedes omitir esta línea.
# EXPOSE 8000

# Define el comando para ejecutar tu aplicación cuando el contenedor se inicie
# Reemplaza 'tu_bot.py' con el nombre de tu archivo principal.
CMD ["python", "bot.py"]