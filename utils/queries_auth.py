from db import get_db_connection

def validar_usuario_db(username, password):
    """
    Busca al bibliotecario en SQL Server por su usuario y clave.
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        # Buscamos que el usuario coincida, la clave coincida y esté ACTIVO (1)
        query = """
            SELECT UsuarioID, Usuario, Rol 
            FROM UsuariosSistema 
            WHERE Usuario = ? AND PasswordHash = ? AND Activo = 1
        """
        cursor.execute(query, (username, password))
        row = cursor.fetchone()
        
        if row:
            # Si lo encuentra, devolvemos sus datos en un diccionario
            return {
                "id": row[0],
                "nombre": row[1],
                "rol": row[2]
            }
        return None # Si no coincide nada, devuelve nada
        
    except Exception as e:
        print(f"❌ Error en la consulta de login: {e}")
        return None
    finally:
        conn.close()