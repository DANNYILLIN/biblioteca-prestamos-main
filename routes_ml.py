from flask import Blueprint, render_template, request, jsonify
import joblib
import pandas as pd
from datetime import datetime

ml_bp = Blueprint('ml', __name__)

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