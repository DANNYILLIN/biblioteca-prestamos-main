from db import get_db_connection

def buscar_usuario_por_codigo(codigo):
    """Busca en Alumnos, Egresados, Administrativos y Visitantes"""
    conn = get_db_connection()
    if not conn: 
        return None, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Unificamos las 4 tablas en una sola búsqueda
        query = """
        SELECT NombreCompleto AS Nombre, DNI, 'Estudiante' AS Tipo FROM Alumnos 
        WHERE DNI = ? OR CodigoMatricula = ?
        UNION ALL
        SELECT NombreCompleto AS Nombre, DNI, 'Egresado' AS Tipo FROM Egresados 
        WHERE DNI = ? OR CodigoMatricula = ?
        UNION ALL
        SELECT ApellidosNombres AS Nombre, DNI, 'Administrativo' AS Tipo FROM PersonalAdministrativo 
        WHERE DNI = ?
        UNION ALL
        SELECT NombreCompleto AS Nombre, DNI, 'Visitante' AS Tipo FROM Visitantes 
        WHERE DNI = ?
        """
        
        # Pasamos los parámetros en el orden de los '?'
        params = (codigo, codigo, codigo, codigo, codigo, codigo)
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        if row:
            datos = {
                'nombre': row[0],
                'dni': row[1],
                'tipo': row[2]
            }
            return datos, None
        
        return None, "Persona no encontrada en ninguna categoría"

    except Exception as e:
        print(f"Error en búsqueda multitabla: {e}")
        return None, f"Error de base de datos: {str(e)}"
    finally:
        if conn: conn.close()

def buscar_libro_bd(termino):
    """Busca un libro por Secuenc, Titulo o Autor para el módulo de préstamos"""
    conn = get_db_connection()
    if not conn: return None, "Error de conexión"
    try:
        cursor = conn.cursor()
        # Usamos nombres exactos de tu SQL (Titulo, Autor, Secuenc, etc.)
        query = """
            SELECT 
                LibroID, Titulo, Autor, Secuenc, 
                CodigoConocimiento, NotacionInterna, Local, EstadoLibro 
            FROM Libros WITH (NOLOCK)
            WHERE (Secuenc = ? OR Titulo LIKE ? OR Autor LIKE ?)
              AND EstadoLibro = 'Disponible'
        """
        t = f'%{termino}%'
        cursor.execute(query, (termino, t, t))
        
        columnas = [c[0] for c in cursor.description]
        row = cursor.fetchone()
        
        if row:
            libro = dict(zip(columnas, row))
            return libro, None
        return None, "El libro no existe o ya está prestado"
    except Exception as e:
        print(f"Error buscando libro: {e}")
        return None, str(e)
    finally:
        conn.close()

def registrar_prestamo_db(usuario, libro):
    """Inserta el préstamo en SQL incluyendo el celular y libera el libro"""
    conn = get_db_connection()
    if not conn: return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Extraemos el celular que viene del JavaScript
        # Si por alguna razón no llega, ponemos 'S/N' (Sin Número)
        celular_contacto = usuario.get('celular', 'S/N')
        
        query_ins = """
            INSERT INTO Prestamos (
                LibroID, 
                UsuarioNombre, 
                UsuarioDNI, 
                Celular, -- Tu nueva columna
                FechaPrestamo, 
                FechaDevolucionEstimada, 
                EstadoPrestamo
            ) VALUES (?, ?, ?, ?, GETDATE(), DATEADD(day, 3, GETDATE()), 'Activo')
        """
        
        params = (
            libro['LibroID'], 
            usuario['nombre'], 
            usuario['dni'], 
            celular_contacto
        )
        
        cursor.execute(query_ins, params)
        
        # Actualizamos el estado del libro en el inventario
        cursor.execute("UPDATE Libros SET EstadoLibro = 'Prestado' WHERE LibroID = ?", (libro['LibroID'],))
        
        conn.commit()
        return True, "Préstamo guardado con celular."
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error registrando préstamo: {e}")
        return False, str(e)
    finally:
        conn.close()