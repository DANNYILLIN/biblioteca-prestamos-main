import random
from datetime import datetime, timedelta

# Asegúrate de importar tu conexión a la base de datos exactamente como la usas en Flask
from db import get_db_connection 

def inyectar_datos_bd():
    print("🔌 Conectando a la base de datos...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("📖 Leyendo Alumnos y Libros reales...")
    cursor.execute("SELECT DNI, NombreCompleto FROM Alumnos")
    alumnos = cursor.fetchall()
    
    cursor.execute("SELECT LibroID FROM Libros")
    libros = cursor.fetchall()
    
    if not alumnos or not libros:
        print("❌ Error: La base de datos está vacía. Necesitas al menos 1 alumno y 1 libro.")
        return

    estados = ['Devuelto', 'Activo', 'Retrasado']
    cantidad_a_inyectar = 2000
    
    print(f"💉 Inyectando {cantidad_a_inyectar} préstamos aleatorios...")
    
    for _ in range(cantidad_a_inyectar):
        alumno = random.choice(alumnos)
        libro = random.choice(libros)
        
        # Generar fechas al azar dentro del último año
        dias_atras = random.randint(1, 365)
        fecha_prestamo = datetime.now() - timedelta(days=dias_atras)
        dias_prestamo = random.randint(3, 15)
        fecha_devolucion = fecha_prestamo + timedelta(days=dias_prestamo)
        
        estado = random.choice(estados)
        
        cursor.execute("""
            INSERT INTO Prestamos (LibroID, UsuarioNombre, UsuarioDNI, FechaPrestamo, FechaDevolucionEstimada, EstadoPrestamo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            libro.LibroID, 
            alumno.NombreCompleto, 
            alumno.DNI, 
            fecha_prestamo.strftime('%Y-%m-%d'), 
            fecha_devolucion.strftime('%Y-%m-%d'), 
            estado
        ))
        
    conn.commit()
    conn.close()
    print("✅ ¡Inyección completada! Revisa tu tabla de Préstamos en SQL Server.")

if __name__ == '__main__':
    inyectar_datos_bd()