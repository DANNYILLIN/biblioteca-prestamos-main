import pandas as pd
from db import get_db_connection

def verificar():
    conn = get_db_connection()
    if not conn:
        print("No se pudo conectar a la base de datos.")
        return

    cursor = conn.cursor()
    
    # 1. Contar el total de registros
    cursor.execute("SELECT COUNT(*) FROM Prestamos")
    total = cursor.fetchone()[0]
    print(f"Total de registros actuales en 'Prestamos': {total}")

    # 2. Ver una muestra de los últimos 5 registros
    if total > 0:
        print("\n--- Últimos 5 préstamos registrados ---")
        # Usando las columnas reales de tu base de datos
        query = """
        SELECT TOP 5 UsuarioNombre, LibroID, FechaPrestamo, EstadoPrestamo 
        FROM Prestamos 
        ORDER BY PrestamoID DESC
        """
        df = pd.read_sql(query, conn)
        print(df.to_string(index=False))
        
    conn.close()

if __name__ == "__main__":
    verificar()