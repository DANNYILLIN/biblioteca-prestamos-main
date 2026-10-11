import datetime
import random
from db import get_db_connection

def poblar_prestamos(n_registros=1200):
    conn = get_db_connection()
    if not conn:
        print("No se pudo conectar a la base de datos remota.")
        return

    cursor = conn.cursor()
    print(f"Generando {n_registros} registros para la tabla Prestamos en SmarterASP...")

    # Datos falsos para rellenar
    nombres = ["Juan", "Maria", "Carlos", "Ana", "Luis", "Elena", "Pedro", "Lucia", "Jorge", "Marta", "Diego", "Sofia"]
    apellidos = ["Gomez", "Perez", "Rodriguez", "Fernandez", "Lopez", "Martinez", "Sanchez", "Diaz", "Torres", "Ramirez"]

    fecha_base = datetime.datetime(2025, 1, 1)
    registros = []

    for _ in range(n_registros):
        libro_id = random.randint(1, 50) # Suponemos que tienes unos 50 libros registrados
        nombre = f"{random.choice(nombres)} {random.choice(apellidos)}"
        dni = str(random.randint(40000000, 79999999))
        celular = f"9{random.randint(10000000, 99999999)}"

        # Lógica de fechas
        dias_offset = random.randint(0, 500)
        fecha_prestamo = fecha_base + datetime.timedelta(days=dias_offset)
        dias_prestamo = random.randint(3, 14)
        fecha_estimada = fecha_prestamo + datetime.timedelta(days=dias_prestamo)

        # Determinar el estado y la fecha real de devolución
        rand_estado = random.random()

        if rand_estado < 0.10:
            # 10% Activos (Aún no devuelven el libro)
            estado = "Activo"
            fecha_real = None  # Queda en NULL en SQL Server
        elif rand_estado < 0.70:
            # 60% Devueltos a tiempo
            estado = "Devuelto"
            dias_uso = random.randint(1, dias_prestamo)
            fecha_real = fecha_prestamo + datetime.timedelta(days=dias_uso)
        else:
            # 30% Retrasados (Morosos)
            estado = "Retrasado"
            dias_retraso = random.randint(1, 20)
            fecha_real = fecha_estimada + datetime.timedelta(days=dias_retraso)

        registros.append((
            libro_id, nombre, dni, fecha_prestamo, 
            fecha_estimada, estado, celular, fecha_real
        ))

    # Insertar usando los nombres exactos de tu imagen
    query = """
    INSERT INTO Prestamos (
        LibroID, UsuarioNombre, UsuarioDNI, FechaPrestamo, 
        FechaDevolucionEstimada, EstadoPrestamo, Celular, FechaDevolucionReal
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        cursor.executemany(query, registros)
        conn.commit()
        print(f"¡Éxito! Se insertaron {len(registros)} registros correctamente.")
    except Exception as e:
        conn.rollback()
        print("Error durante la inserción:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    poblar_prestamos(1200)