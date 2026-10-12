from flask import Blueprint, render_template, request, jsonify
import joblib
import pandas as pd
from datetime import datetime
import google.generativeai as genai


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