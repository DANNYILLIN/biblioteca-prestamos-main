from flask import Blueprint, render_template, request, jsonify
import joblib
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from db import get_db_connection


ml_bp = Blueprint('ml', __name__)


# ¡Asegúrate de pegar tu API Key de Gemini aquí!
genai.configure(api_key="AQ.Ab8RN6J6iNMXfaF8-T54hsnPB9yaUICr-NElmovK8d8qo0kJYw")

modelo_llm = genai.GenerativeModel('gemini-3.6-flash')

# --- 1. RUTA PARA MOSTRAR LA PÁGINA WEB DEL CHAT ---
@ml_bp.route('/chat')
def pagina_chat():
    return render_template('chat.html')


# Cargar el modelo IA y la estructura exacta de las columnas que aprendió
modelo_ia = joblib.load('modelo_morosidad.joblib')
columnas_entrenamiento = joblib.load('columnas_modelo.joblib')

@ml_bp.route('/estadisticas')
def estadisticas():
    return render_template('estadisticas.html')

@ml_bp.route('/api/predecir_riesgo', methods=['POST'])
def predecir_riesgo():
    datos = request.json
    try:
        fecha_prestamo = datetime.strptime(datos['fecha_prestamo'], '%Y-%m-%d')
        fecha_estimada = datetime.strptime(datos['fecha_estimada'], '%Y-%m-%d')
        
        # 1. Crear un diccionario con todas las columnas en 0 por defecto
        entrada_dict = {col: 0 for col in columnas_entrenamiento}
        
        # 2. Asignar las fechas
        entrada_dict['DiasSolicitados'] = (fecha_estimada - fecha_prestamo).days
        entrada_dict['DiaSemana'] = fecha_prestamo.weekday()
        entrada_dict['Mes'] = fecha_prestamo.month
        
        # 3. Asignar Tipo de Usuario (Si es Alumno, Personal o Docente)
        tipo = datos.get('tipo_usuario', 'Alumno')
        col_tipo = f'TipoUsuario_{tipo}'
        if col_tipo in entrada_dict:
            entrada_dict[col_tipo] = 1
            
        # 4. Asignar Escuela (Solo si es alumno, sino 'No Aplica')
        if tipo == 'Alumno':
            escuela = datos.get('escuela', 'Agronomía')
            col_escuela = f'Escuela_{escuela}'
            if col_escuela in entrada_dict:
                entrada_dict[col_escuela] = 1
        else:
            if 'Escuela_No Aplica' in entrada_dict:
                entrada_dict['Escuela_No Aplica'] = 1
                
        # Convertir a formato Pandas para la IA
        entrada_df = pd.DataFrame([entrada_dict])
        
        # Obtener predicción
        probabilidad = modelo_ia.predict_proba(entrada_df)[0][1]
        
        return jsonify({
            "riesgo_porcentaje": round(probabilidad * 100, 2),
            "nivel_riesgo": "Alto" if probabilidad > 0.5 else "Bajo"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- 2. API DEL MULTIAGENTE ---
@ml_bp.route('/api/chat_agentes', methods=['POST'])
def chat_agentes():
    datos = request.json
    mensaje_usuario = datos.get('mensaje', '')
    
    try:
        # AGENTE 1: Coordinador (Clasifica la intención)
        prompt_coordinador = f"""
        Eres el Coordinador del sistema multiagente de una biblioteca universitaria. 
        Lee el mensaje del usuario y clasifícalo en una de estas dos áreas:
        - Escribe 'RIESGO' si el usuario pregunta sobre morosidad, estadísticas, carreras, comportamiento de los alumnos, o predicciones de retraso.
        - Escribe 'CATALOGO' si el usuario pregunta sobre libros, autores, resúmenes, inventario o temáticas de lectura.
        
        Mensaje del usuario: "{mensaje_usuario}"
        Responde ÚNICAMENTE con una palabra: RIESGO o CATALOGO.
        """
        clasificacion = modelo_llm.generate_content(prompt_coordinador).text.strip().upper()
        
        # AGENTE 2: El Especialista (Responde basado en la clasificación)
        if "RIESGO" in clasificacion:
            nombre_agente = "Agente Analista de Riesgos"
            prompt_especialista = f"""
            Eres el Analista de Riesgos de la Biblioteca UNDAC. Conoces el modelo Random Forest que predice la morosidad de los préstamos.
            Responde la siguiente consulta de manera profesional, técnica y amable. Si es relevante, menciona que nuestra IA evalúa la Escuela/Carrera y el Tipo de Usuario (Alumno, Docente, Personal) para calcular los riesgos.
            
            Consulta: "{mensaje_usuario}"
            """
        else:
            nombre_agente = "Agente Bibliotecario"
            prompt_especialista = f"""
            Eres el Bibliotecario Jefe de la Biblioteca UNDAC. Eres un experto en literatura y material académico.
            Responde la siguiente consulta recomendando libros, autores o explicando el funcionamiento del catálogo de manera muy amable e ilustrada.
            
            Consulta: "{mensaje_usuario}"
            """
            
        respuesta_final = modelo_llm.generate_content(prompt_especialista).text
        
        return jsonify({
            "agente": nombre_agente,
            "respuesta": respuesta_final
        })
    except Exception as e:
        print(f"❌ ERROR DE GEMINI: {str(e)}") # Esto nos dirá exactamente qué falló
        return jsonify({"error": str(e)}), 500


@ml_bp.route('/api/top_estadisticas', methods=['GET'])
def top_estadisticas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Top 5 Libros más prestados
        query_libros = """
            SELECT TOP 5 L.Titulo, COUNT(P.PrestamoID) as Total
            FROM Prestamos P
            JOIN Libros L ON P.LibroID = L.LibroID
            GROUP BY L.Titulo
            ORDER BY Total DESC
        """
        cursor.execute(query_libros)
        top_libros = [{"titulo": row.Titulo, "total": row.Total} for row in cursor.fetchall()]
        
        # Top 5 Alumnos con más préstamos
        query_alumnos = """
            SELECT TOP 5 A.NombreCompleto, A.Escuela, COUNT(P.PrestamoID) as Total
            FROM Prestamos P
            JOIN Alumnos A ON P.UsuarioDNI = A.DNI
            GROUP BY A.NombreCompleto, A.Escuela
            ORDER BY Total DESC
        """
        cursor.execute(query_alumnos)
        top_alumnos = [{"nombre": row.NombreCompleto, "escuela": row.Escuela, "total": row.Total} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "libros": top_libros,
            "alumnos": top_alumnos
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ml_bp.route('/api/datos_graficos', methods=['GET'])
def datos_graficos():
    try:
        from db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. ESTADOS (Dona) y KPI Morosidad
        cursor.execute("SELECT EstadoPrestamo, COUNT(PrestamoID) as Total FROM Prestamos GROUP BY EstadoPrestamo")
        estados_raw = {row.EstadoPrestamo: row.Total for row in cursor.fetchall()}
        devueltos = estados_raw.get('Devuelto', 0)
        activos = estados_raw.get('Activo', 0)
        retrasados = estados_raw.get('Retrasado', 0)
        total_prestamos = devueltos + activos + retrasados
        
        porcentaje_morosidad = 0
        if total_prestamos > 0:
            porcentaje_morosidad = round((retrasados / total_prestamos) * 100, 1)

        # 2. MESES (Gráfico de Línea)
        cursor.execute("SELECT MONTH(FechaPrestamo) as Mes, COUNT(PrestamoID) as Total FROM Prestamos GROUP BY MONTH(FechaPrestamo)")
        meses_dict = {row.Mes: row.Total for row in cursor.fetchall()}
        # Creamos un arreglo ordenado de Enero (1) a Diciembre (12)
        meses_array = [meses_dict.get(i, 0) for i in range(1, 13)]

        # 3. DÍAS DE LA SEMANA (Gráfico Polar)
        # DATEPART(dw) devuelve 1=Domingo, 2=Lunes, 3=Martes... hasta 7=Sábado
        cursor.execute("SELECT DATEPART(dw, FechaPrestamo) as Dia, COUNT(PrestamoID) as Total FROM Prestamos GROUP BY DATEPART(dw, FechaPrestamo)")
        dias_dict = {row.Dia: row.Total for row in cursor.fetchall()}
        dias_array = [
            dias_dict.get(2, 0), # Lunes
            dias_dict.get(3, 0), # Martes
            dias_dict.get(4, 0), # Miércoles
            dias_dict.get(5, 0), # Jueves
            dias_dict.get(6, 0), # Viernes
            dias_dict.get(7, 0)  # Sábado
        ]

        # 4. ESCUELAS (Gráfico de Barras Horizontales)
        cursor.execute("""
            SELECT A.Escuela, COUNT(P.PrestamoID) as Total 
            FROM Prestamos P 
            JOIN Alumnos A ON P.UsuarioDNI = A.DNI 
            GROUP BY A.Escuela
            ORDER BY Total DESC
        """)
        escuelas_raw = cursor.fetchall()
        escuelas_labels = [row.Escuela for row in escuelas_raw]
        escuelas_data = [row.Total for row in escuelas_raw]

        # 5. TIPOS DE USUARIOS (Gráfico de Pie)
        cursor.execute("""
            SELECT 'Alumnos' as Tipo, COUNT(P.PrestamoID) as Total FROM Prestamos P JOIN Alumnos A ON P.UsuarioDNI = A.DNI
            UNION ALL
            SELECT 'Docentes' as Tipo, COUNT(P.PrestamoID) FROM Prestamos P JOIN Docentes D ON P.UsuarioDNI = D.DNI
            UNION ALL
            SELECT 'Personal' as Tipo, COUNT(P.PrestamoID) FROM Prestamos P JOIN PersonalAdministrativo PA ON P.UsuarioDNI = PA.DNI
        """)
        usuarios_raw = {row.Tipo: row.Total for row in cursor.fetchall()}
        usuarios_array = [usuarios_raw.get('Alumnos', 0), usuarios_raw.get('Docentes', 0), usuarios_raw.get('Personal', 0)]

        conn.close()
        
        # Enviamos absolutamente toda la información al Frontend
        return jsonify({
            "estados": [devueltos, activos, retrasados],
            "total_prestamos": total_prestamos,
            "porcentaje_morosidad": porcentaje_morosidad,
            "meses": meses_array,
            "dias": dias_array,
            "escuelas_labels": escuelas_labels,
            "escuelas_data": escuelas_data,
            "usuarios": usuarios_array
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500