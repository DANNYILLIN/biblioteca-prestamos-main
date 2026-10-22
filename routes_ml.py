from flask import Blueprint, render_template, request, jsonify
import joblib
import pandas as pd
from datetime import datetime
import os 
import requests 
from db import get_db_connection
from agentes import Orquestador

ml_bp = Blueprint('ml', __name__)

GEMINI_API_KEY = "AQ.Ab8RN6I5429F2H6zWHlcqszTZzMK3k_fXa2mW3GoW5nOAssXrw"

def llamar_ia_directo(prompt_texto):
    """Función maestra con enrutamiento de contingencia Multi-Modelo"""
    payload = {"contents": [{"parts": [{"text": prompt_texto}]}]}
    headers = {"Content-Type": "application/json"}
    
    # 1. Intento principal con gemini-3.6-flash
    url_principal = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    respuesta = requests.post(url_principal, json=payload, headers=headers)
    datos = respuesta.json()
    
    # Si hay un error, aplicamos Tolerancia a Fallos
    if "error" in datos:
        error_msg = datos['error']['message'].lower()
        if "high demand" in error_msg or "quota" in error_msg or "429" in error_msg or "overloaded" in error_msg:
            print("⚠️ [API] gemini-3.6-flash saturado. Enrutando a gemini-flash-lite-latest...")
            # 2. PLAN B: Modelo de contingencia ligero
            url_respaldo = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}"
            respuesta_b = requests.post(url_respaldo, json=payload, headers=headers)
            datos_b = respuesta_b.json()
            
            if "error" in datos_b:
                raise Exception(f"Saturación total en Google: {datos_b['error']['message']}")
            return datos_b["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise Exception(f"Error de Google: {datos['error']['message']}")
            
    return datos["candidates"][0]["content"]["parts"][0]["text"]


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
        
        entrada_dict = {col: 0 for col in columnas_entrenamiento}
        entrada_dict['DiasSolicitados'] = (fecha_estimada - fecha_prestamo).days
        entrada_dict['DiaSemana'] = fecha_prestamo.weekday()
        entrada_dict['Mes'] = fecha_prestamo.month
        
        tipo = datos.get('tipo_usuario', 'Alumno')
        col_tipo = f'TipoUsuario_{tipo}'
        if col_tipo in entrada_dict:
            entrada_dict[col_tipo] = 1
            
        if tipo == 'Alumno':
            escuela = datos.get('escuela', 'Agronomía')
            col_escuela = f'Escuela_{escuela}'
            if col_escuela in entrada_dict:
                entrada_dict[col_escuela] = 1
        else:
            if 'Escuela_No Aplica' in entrada_dict:
                entrada_dict['Escuela_No Aplica'] = 1
                
        entrada_df = pd.DataFrame([entrada_dict])
        probabilidad = modelo_ia.predict_proba(entrada_df)[0][1]
        
        return jsonify({
            "riesgo_porcentaje": round(probabilidad * 100, 2),
            "nivel_riesgo": "Alto" if probabilidad > 0.5 else "Bajo"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------
# SISTEMA MULTIAGENTE: ORQUESTADOR + 5 AGENTES (CON GEMINI)
# ---------------------------------------------------------
@ml_bp.route('/api/chat_automatico', methods=['POST'])
def chat_automatico():
    try:
        datos = request.json
        pregunta_usuario = datos.get('mensaje', '')

        # 1. EL ORQUESTADOR DECIDE ENTRE 5 ÁREAS
        prompt_coordinador = f"""
        Eres el Coordinador del sistema multiagente de la biblioteca UNDAC.
        Clasifica el mensaje en una de estas 5 áreas:
        - 'CATALOGO' (sobre libros, autores, recomendaciones)
        - 'RIESGO' (sobre morosidad, estadísticas, devoluciones, deudas)
        - 'ACADEMICO' (sobre investigación, tesis, estudio por facultades)
        - 'SOPORTE' (sobre reglas, horarios, cómo usar el sistema, ayuda)
        - 'NOVEDADES' (sobre noticias, eventos, comunicados de la universidad)
        Mensaje: "{pregunta_usuario}"
        Responde ÚNICAMENTE con una palabra de la lista.
        """
        clasificacion = llamar_ia_directo(prompt_coordinador).strip().upper()

        # 2. ENRUTAMIENTO A LOS 5 AGENTES
        if "RIESGO" in clasificacion:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT EstadoPrestamo, COUNT(PrestamoID) as Total FROM Prestamos GROUP BY EstadoPrestamo")
            estados = {row.EstadoPrestamo: row.Total for row in cursor.fetchall()}
            conn.close()
            retrasados = estados.get('Retrasado', 0)
            activos = estados.get('Activo', 0)
            devueltos = estados.get('Devuelto', 0)

            prompt = f"Eres el Analista de Riesgos de la UNDAC. Datos reales: {devueltos} devueltos, {activos} activos, {retrasados} con retraso. Responde la duda basándote en estos números con un tono profesional a esta pregunta: {pregunta_usuario}"
            agente_nombre = "Analista de Riesgos"
            tema_color = "azul"
            icono_clase = "fas fa-chart-line"

        elif "ACADEMICO" in clasificacion:
            prompt = f"Eres el Asesor Académico de la Biblioteca UNDAC. Ayudas a los estudiantes con consejos de investigación, redacción de tesis y recursos de estudio para sus escuelas (ej. Sistemas, Agronomía). Responde a la pregunta de forma académica y motivadora: {pregunta_usuario}"
            agente_nombre = "Asesor Académico"
            tema_color = "verde"
            icono_clase = "fas fa-user-graduate"

        elif "SOPORTE" in clasificacion:
            prompt = f"Eres el Agente de Soporte Técnico de la Biblioteca UNDAC. Ayudas con el uso de la plataforma web, consultas sobre horarios (L-V 8am a 6pm), reglas y multas. Responde de forma clara, paciente y servicial a esta duda: {pregunta_usuario}"
            agente_nombre = "Soporte Técnico"
            tema_color = "morado"
            icono_clase = "fas fa-headset"

        elif "NOVEDADES" in clasificacion:
            prompt = f"Eres el Agente de Novedades de la UNDAC. Informas sobre eventos culturales, ingresos de nuevos libros, y noticias de la universidad. Sé entusiasta y comunicativo al responder esto: {pregunta_usuario}"
            agente_nombre = "Agente de Novedades"
            tema_color = "naranja"
            icono_clase = "fas fa-bullhorn"

        else: # CATALOGO por defecto
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 5 Titulo, COUNT(PrestamoID) as VecesPrestado FROM Prestamos JOIN Libros ON Prestamos.LibroID = Libros.LibroID GROUP BY Titulo ORDER BY VecesPrestado DESC")
            top_libros = cursor.fetchall()
            conn.close()
            contexto_libros = ", ".join([f"{row.Titulo} ({row.VecesPrestado} préstamos)" for row in top_libros])

            prompt = f"Eres el Agente Bibliotecario de la UNDAC. Libros más prestados actualmente: {contexto_libros}. Responde la duda recomendando literatura de forma amable: {pregunta_usuario}"
            agente_nombre = "Agente Bibliotecario"
            tema_color = "rojo"
            icono_clase = "fas fa-book-reader"

        # 3. LLAMADA A GEMINI Y RESPUESTA FINAL
        respuesta_texto = llamar_ia_directo(prompt)

        return jsonify({
            "respuesta": respuesta_texto, 
            "agente": agente_nombre,
            "tema": tema_color,
            "icono": icono_clase
        })

    except Exception as e:
        print(f"❌ ERROR EN MULTIAGENTE: {str(e)}")
        error_msg = str(e).lower()
        # Si fallan todos los modelos, devolvemos un JSON válido para que el Frontend no colapse
        if "saturación" in error_msg or "high demand" in error_msg or "quota" in error_msg:
            return jsonify({
                "respuesta": "El asistente está procesando múltiples consultas en este momento. Por favor, espera unos segundos e intenta nuevamente.", 
                "agente": "Sistema de Contingencia",
                "tema": "gris",
                "icono": "fas fa-exclamation-triangle"
            })
        return jsonify({"error": str(e)}), 500

@ml_bp.route('/api/top_estadisticas', methods=['GET'])
def top_estadisticas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query_libros = "SELECT TOP 5 L.Titulo, COUNT(P.PrestamoID) as Total FROM Prestamos P JOIN Libros L ON P.LibroID = L.LibroID GROUP BY L.Titulo ORDER BY Total DESC"
        cursor.execute(query_libros)
        top_libros = [{"titulo": row.Titulo, "total": row.Total} for row in cursor.fetchall()]
        
        query_alumnos = "SELECT TOP 5 A.NombreCompleto, A.Escuela, COUNT(P.PrestamoID) as Total FROM Prestamos P JOIN Alumnos A ON P.UsuarioDNI = A.DNI GROUP BY A.NombreCompleto, A.Escuela ORDER BY Total DESC"
        cursor.execute(query_alumnos)
        top_alumnos = [{"nombre": row.NombreCompleto, "escuela": row.Escuela, "total": row.Total} for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({"libros": top_libros, "alumnos": top_alumnos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ml_bp.route('/api/datos_graficos', methods=['GET'])
def datos_graficos():
    try:
        from db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT EstadoPrestamo, COUNT(PrestamoID) as Total FROM Prestamos GROUP BY EstadoPrestamo")
        estados_raw = {row.EstadoPrestamo: row.Total for row in cursor.fetchall()}
        devueltos = estados_raw.get('Devuelto', 0)
        activos = estados_raw.get('Activo', 0)
        retrasados = estados_raw.get('Retrasado', 0)
        total_prestamos = devueltos + activos + retrasados
        
        porcentaje_morosidad = 0 if total_prestamos == 0 else round((retrasados / total_prestamos) * 100, 1)

        cursor.execute("SELECT MONTH(FechaPrestamo) as Mes, COUNT(PrestamoID) as Total FROM Prestamos GROUP BY MONTH(FechaPrestamo)")
        meses_dict = {row.Mes: row.Total for row in cursor.fetchall()}
        meses_array = [meses_dict.get(i, 0) for i in range(1, 13)]

        cursor.execute("SELECT DATEPART(dw, FechaPrestamo) as Dia, COUNT(PrestamoID) as Total FROM Prestamos GROUP BY DATEPART(dw, FechaPrestamo)")
        dias_dict = {row.Dia: row.Total for row in cursor.fetchall()}
        dias_array = [dias_dict.get(2, 0), dias_dict.get(3, 0), dias_dict.get(4, 0), dias_dict.get(5, 0), dias_dict.get(6, 0), dias_dict.get(7, 0)]

        cursor.execute("SELECT A.Escuela, COUNT(P.PrestamoID) as Total FROM Prestamos P JOIN Alumnos A ON P.UsuarioDNI = A.DNI GROUP BY A.Escuela ORDER BY Total DESC")
        escuelas_raw = cursor.fetchall()
        escuelas_labels = [row.Escuela for row in escuelas_raw]
        escuelas_data = [row.Total for row in escuelas_raw]

        cursor.execute("SELECT 'Alumnos' as Tipo, COUNT(P.PrestamoID) as Total FROM Prestamos P JOIN Alumnos A ON P.UsuarioDNI = A.DNI UNION ALL SELECT 'Docentes' as Tipo, COUNT(P.PrestamoID) FROM Prestamos P JOIN Docentes D ON P.UsuarioDNI = D.DNI UNION ALL SELECT 'Personal' as Tipo, COUNT(P.PrestamoID) FROM Prestamos P JOIN PersonalAdministrativo PA ON P.UsuarioDNI = PA.DNI")
        usuarios_raw = {row.Tipo: row.Total for row in cursor.fetchall()}
        usuarios_array = [usuarios_raw.get('Alumnos', 0), usuarios_raw.get('Docentes', 0), usuarios_raw.get('Personal', 0)]

        conn.close()
        
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


@ml_bp.route('/api/ejecutar_agentes', methods=['POST'])
def ejecutar_agentes():
    correo_ingeniero_o_admin = "d4ni3l482003@gmail.com" 
    gerente = Orquestador(correo_admin=correo_ingeniero_o_admin)
    resultado = gerente.iniciar_comite()
    return jsonify(resultado)