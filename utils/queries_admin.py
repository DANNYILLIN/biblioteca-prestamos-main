from db import get_db_connection
import pandas as pd
from werkzeug.security import generate_password_hash
from db import get_db_connection

def ejecutar_consulta(query, params=None, fetch=False, commit=True):
    """Función auxiliar para reducir la repetición de código y manejar errores"""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            columnas = [c[0] for c in cursor.description]
            resultado = [dict(zip(columnas, r)) for r in cursor.fetchall()]
            return resultado
        
        if commit:
            conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error SQL: {e}")
        return None
    finally:
        if conn: conn.close()

# --- FUNCIONES DE INVENTARIO ---

def obtener_todos_los_libros():
    """Carga inicial rápida del inventario (Top 500 para no saturar)"""
    query = """
        SELECT TOP 500 
            LibroID, Titulo, Autor, Secuenc, Materia, EstadoLibro 
        FROM Libros WITH (NOLOCK)
        ORDER BY LibroID DESC
    """
    return ejecutar_consulta(query, fetch=True) or []

def buscar_libros_inventario_admin(termino):
    """Búsqueda ultra rápida en los 12k+ registros"""
    termino = f"%{termino.strip()}%"
    query = """
        SELECT TOP 100 
            LibroID, Titulo, Autor, Secuenc, Materia, EstadoLibro 
        FROM Libros WITH (NOLOCK)
        WHERE Titulo LIKE ? OR Autor LIKE ? OR Secuenc LIKE ?
        ORDER BY Titulo ASC
    """
    return ejecutar_consulta(query, (termino, termino, termino), fetch=True) or []

# --- FUNCIONES DE CONTROL ---

def limpiar_tabla_libros():
    """Borrado total seguro reiniciando contadores"""
    conn = get_db_connection()
    if not conn: return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        # Borrar primero la tabla hija para evitar error de FK
        cursor.execute("DELETE FROM Prestamos")
        # Borrar la tabla padre
        cursor.execute("DELETE FROM Libros")
        # Reiniciar el ID Autoincrementable a 0 (el sig. será 1)
        cursor.execute("DBCC CHECKIDENT ('Libros', RESEED, 0)")
        conn.commit()
        return True, "✅ Base de datos vaciada con éxito."
    except Exception as e:
        if conn: conn.rollback()
        return False, f"Error al limpiar: {str(e)}"
    finally:
        if conn: conn.close()

# --- FUNCIONES DE REPORTES (DEUDORES) ---

def obtener_deudores_y_multas():
    """Reporte de préstamos activos incluyendo el número de celular"""
    # Agregamos p.Celular a la lista de selección
    query = """
        SELECT 
            p.PrestamoID, 
            p.LibroID,
            p.UsuarioNombre, 
            p.UsuarioDNI, 
            p.Celular, -- <--- Agregamos esta columna
            l.Titulo AS LibroTitulo, 
            p.FechaDevolucionEstimada,
            -- Calculamos los días de retraso (positivo es mora, negativo es a tiempo)
            DATEDIFF(day, p.FechaDevolucionEstimada, GETDATE()) AS DiasRetraso
        FROM Prestamos p WITH (NOLOCK)
        JOIN Libros l ON p.LibroID = l.LibroID
        WHERE p.EstadoPrestamo = 'Activo'
        ORDER BY p.FechaDevolucionEstimada ASC
    """
    return ejecutar_consulta(query, fetch=True) or []


def cargar_libros_masivo(lista_libros):
    conn = get_db_connection()
    if not conn: return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        datos_preparados = []

        for libro in lista_libros:
            # MAPEADOR INTELIGENTE: Busca la columna correcta aunque cambie el nombre
            # Intentará con 'titulo', 'libro', 'nombre' o 'descripcion'
            titulo = libro.get('titulo') or libro.get('libro') or libro.get('nombre') or libro.get('descripcion')
            autor = libro.get('autor') or libro.get('escritor') or "Desconocido"
            secuenc = libro.get('secuenc') or libro.get('codigo') or libro.get('barcode')
            
            # Los demás campos (pueden ser nulos)
            local = libro.get('local')
            conocim = libro.get('codigoconocimiento') or libro.get('conocimiento')
            notin = libro.get('notacioninterna') or libro.get('notacion')
            tema = libro.get('tema')
            materia = libro.get('materia')

            # VALIDACIÓN: Solo si hay un título real lo procesamos
            if titulo and str(titulo).strip().lower() != 'nan':
                params = (
                    local, conocim, notin, 
                    str(titulo).strip(), 
                    str(autor).strip(), 
                    tema, materia, secuenc
                )
                
                # Convertir NaNs a None para SQL Server
                fila_limpia = tuple((None if pd.isna(v) else v) for v in params)
                datos_preparados.append(fila_limpia)

        if not datos_preparados:
            # Si falla, te dirá qué columnas SÍ detectó para que sepas el error
            columnas = list(lista_libros[0].keys()) if lista_libros else "Vacío"
            return False, f"No se hallaron títulos. Columnas detectadas: {columnas}"

        query = """
            INSERT INTO Libros (
                Local, CodigoConocimiento, NotacionInterna, 
                Titulo, Autor, Tema, Materia, Secuenc, EstadoLibro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Disponible')
        """
        
        cursor.executemany(query, datos_preparados)
        conn.commit()
        return True, f"¡Éxito! Se cargaron {len(datos_preparados)} libros."

    except Exception as e:
        if conn: conn.rollback()
        return False, f"Error SQL: {str(e)}"
    finally:
        if conn: conn.close()

def procesar_devolucion_db(prestamo_id, libro_id):
    """Registra la devolución y libera el libro en una sola operación"""
    conn = get_db_connection()
    if not conn: return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        
        # 1. Actualizar el préstamo con la fecha real de entrega
        cursor.execute("""
            UPDATE Prestamos 
            SET EstadoPrestamo = 'Devuelto', FechaDevolucionReal = GETDATE() 
            WHERE PrestamoID = ?
        """, (prestamo_id,))
        
        # 2. Liberar el libro para que otros puedan usarlo
        cursor.execute("""
            UPDATE Libros 
            SET EstadoLibro = 'Disponible' 
            WHERE LibroID = ?
        """, (libro_id,))
        
        conn.commit()
        return True, "Libro devuelto correctamente."
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()


def obtener_historial_completo():
    query = """
        SELECT 
            p.PrestamoID,
            p.UsuarioNombre,
            p.UsuarioDNI,
            p.Celular,
            l.Titulo AS Libro,
            l.Secuenc AS CodigoLibro,
            p.FechaPrestamo,
            p.FechaDevolucionEstimada,
            p.FechaDevolucionReal,
            p.EstadoPrestamo,
            -- Cálculo de mora si es que hubo
            CASE 
                WHEN p.FechaDevolucionReal > p.FechaDevolucionEstimada 
                THEN DATEDIFF(day, p.FechaDevolucionEstimada, p.FechaDevolucionReal)
                ELSE 0 
            END AS DiasMora
        FROM Prestamos p
        JOIN Libros l ON p.LibroID = l.LibroID
        ORDER BY p.FechaPrestamo DESC
    """
    return ejecutar_consulta(query, fetch=True)


def obtener_reporte_excel_db(fecha_inicio, fecha_fin):
    """Consulta el historial de préstamos entre dos fechas"""
    query = """
        SELECT 
            p.PrestamoID,
            p.UsuarioNombre,
            p.UsuarioDNI,
            p.Celular,
            l.Titulo AS Libro,
            l.Secuenc AS CodigoLibro,
            p.FechaPrestamo,
            p.FechaDevolucionEstimada,
            p.FechaDevolucionReal,
            p.EstadoPrestamo
        FROM Prestamos p WITH (NOLOCK)
        JOIN Libros l ON p.LibroID = l.LibroID
        WHERE CAST(p.FechaPrestamo AS DATE) BETWEEN ? AND ?
        ORDER BY p.FechaPrestamo DESC
    """
    # Pasamos las fechas como tupla de parámetros
    return ejecutar_consulta(query, (fecha_inicio, fecha_fin), fetch=True) or []




def crear_usuario_sistema_db(usuario, password, email, rol, sede):
    """Crea un usuario con contraseña encriptada según tu tabla"""
    conn = get_db_connection()
    if not conn: return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        # Encriptamos la clave antes de que toque la base de datos
        pass_hash = generate_password_hash(password)
        
        query = """
            INSERT INTO UsuariosSistema 
            (Usuario, PasswordHash, Email, Rol, Activo, CreadoEn, SedeAsignada)
            VALUES (?, ?, ?, ?, 1, GETDATE(), ?)
        """
        cursor.execute(query, (usuario, pass_hash, email, rol, sede))
        conn.commit()
        return True, "Usuario registrado correctamente."
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        return False, str(e)
    finally:
        conn.close()

def obtener_usuarios_sistema():
    """Lista todos los bibliotecarios y administradores"""
    query = "SELECT UsuarioID, Usuario, Email, Rol, SedeAsignada, Activo FROM UsuariosSistema"
    # Usamos tu motor de ejecución centralizado
    return ejecutar_consulta(query, fetch=True) or []