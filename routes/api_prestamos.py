from flask import Blueprint, request, jsonify
from utils.queries_prestamos import buscar_usuario_por_codigo, buscar_libro_bd
import os
import google.generativeai as genai

api_prestamos_bp = Blueprint('api_prestamos', __name__)

# Busca la función buscar_usuario y déjala así:
@api_prestamos_bp.route('/api/buscar_usuario', methods=['POST'])
def buscar_usuario():
    data = request.get_json()
    codigo = data.get('codigo')
    
    from utils.queries_prestamos import buscar_usuario_por_codigo
    datos, error = buscar_usuario_por_codigo(codigo) # IMPORTANTE: Capturar los dos
    
    if datos:
        return jsonify({'success': True, 'usuario': datos})
    
    return jsonify({'success': False, 'message': error or 'No encontrado'})

@api_prestamos_bp.route('/api/buscar_libro', methods=['POST'])
def buscar_libro():
    # 1. Obtenemos el código de barras del libro
    codigo_barras = request.json.get('codigo_barras', '').strip()
    
    if not codigo_barras:
        return jsonify({'error': 'El código de barras del libro está vacío'})

    # 2. Buscamos el libro en la base de datos
    libro, error = buscar_libro_bd(codigo_barras)

    # 3. Si hay error (Libro no encontrado)
    if error:
        return jsonify({'success': False, 'error': error})

    # 4. Enviamos los datos del libro
    return jsonify({
        'success': True,
        'libro': libro
    })


# Asegúrate de importar Blueprint, request, jsonify (ya los tienes)

@api_prestamos_bp.route('/api/resena_ia', methods=['POST'])
def generar_resena_ia():
    data = request.json
    titulo = data.get('titulo')
    autor = data.get('autor', 'Desconocido')
    
    if not titulo:
        return jsonify({'success': False, 'error': 'Falta el título del libro'})
        
    try:
        # Configurar la llave desde tu .env
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # Usamos el modelo más rápido
        model = genai.GenerativeModel('gemini-3.6-flash') 
        
        prompt = f"Actúa como un bibliotecario experto. Escribe una reseña muy breve (máximo 3 líneas) sobre el libro '{titulo}' de {autor}. Destaca de qué trata."
        response = model.generate_content(prompt)
        
        return jsonify({'success': True, 'resena': response.text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})