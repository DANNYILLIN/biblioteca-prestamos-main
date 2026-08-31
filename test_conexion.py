import os
import pyodbc
from dotenv import load_dotenv

# 1. Cargar el archivo .env
print("-> Cargando el archivo .env...")
load_dotenv()

def probar_conexion():
    print("-> Intentando conectar a SQL Server...")
    
    try:
        # Armar la llave de acceso usando tu .env
        conn_str = (
            f"DRIVER={os.getenv('DB_DRIVER')};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_DATABASE')};"
            f"Trusted_Connection={os.getenv('DB_TRUSTED_CONNECTION')};"
        )
        print(f"-> Tu cadena de conexion es: {conn_str}")

        # Intentar abrir la puerta
        conn = pyodbc.connect(conn_str)
        print("\n[EXITO] ¡Conexion establecida correctamente con SQL Server!")

        # Hacer una consulta rápida para comprobar que podemos leer datos
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Libros")
        cantidad_libros = cursor.fetchone()[0]

        print(f"[EXITO] Logre leer la base de datos. Tienes {cantidad_libros} libros registrados.")

        # Cerrar la puerta
        conn.close()
        print("-> Conexion cerrada. Tu configuracion es perfecta.\n")

    except Exception as e:
        print(f"\n[ERROR] Algo fallo al intentar conectar:\n{e}\n")

if __name__ == '__main__':
    probar_conexion()