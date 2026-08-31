import os
import pandas as pd
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask import send_file, request, jsonify
import pandas as pd
from io import BytesIO
from db import get_db_connection
import unicodedata

# Importación de tus módulos de consulta y rutas
from routes.api_prestamos import api_prestamos_bp
from utils.queries_auth import validar_usuario_db
from utils.queries_admin import (
    cargar_libros_masivo, 
    obtener_todos_los_libros, 
    obtener_deudores_y_multas,
    procesar_devolucion_db  # <--- AGREGA ESTA LÍNEA AQUÍ
)

app = Flask(__name__)

# =========================================================
# CONFIGURACIÓN DE SEGURIDAD
# =========================================================
app.secret_key = 'undac_biblioteca_2026_key_final'

# Registro de la API (Búsqueda de DNI y Libros para el bibliotecario)
app.register_blueprint(api_prestamos_bp)

# =========================================================
# RUTAS DE ACCESO (LOGIN / LOGOUT)
# =========================================================

@app.route('/login')
def login_view():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/auth/login', methods=['POST'])
def procesar_login_sistema():
    user_input = request.form.get('username')
    pass_input = request.form.get('password')

    user_db = validar_usuario_db(user_input, pass_input)

    if user_db:
        session['user_id'] = user_db['id']
        session['user_name'] = user_db['nombre']
        session['user_rol'] = user_db['rol']
        
        # Redirección por Rol
        if user_db['rol'] == 'Administrador':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    else:
        return "<h1>Error: Usuario o contraseña incorrectos</h1><a href='/login'>Volver</a>", 401

@app.route('/logout')
def cerrar_sesion():
    session.clear()
    return redirect(url_for('login_view'))

# =========================================================
# MÓDULO DE PRÉSTAMOS (BIBLIOTECARIO / VOUCHER)
# =========================================================

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login_view'))
    
    return render_template('prestamos.html', 
                           usuario_sistema=session.get('user_name'),
                           rol_sistema=session.get('user_rol'))

# =========================================================
# MÓDULO ADMINISTRATIVO (PANEL DE CONTROL)
# =========================================================

@app.route('/admin')
def admin_dashboard():
    """Pantalla principal de Admin: Carga de Excel"""
    if session.get('user_rol') != 'Administrador':
        return redirect(url_for('index'))
    
    return render_template('admin/dashboard.html', usuario=session.get('user_name'))

@app.route('/admin/inventario')
def admin_inventario():
    """Ver todos los libros cargados"""
    if session.get('user_rol') != 'Administrador':
        return redirect(url_for('index'))
    
    libros = obtener_todos_los_libros()
    return render_template('admin/inventario.html', libros=libros)

import unicodedata # <--- Asegúrate de tener este import arriba

@app.route('/admin/libros/upload_excel', methods=['POST'])
def upload_excel():
    # Ajustamos a 'user_rol' que es como lo tenías antes
    # Si quieres saltar la seguridad para probar, comenta estas dos líneas:
    if session.get('user_rol') != 'Administrador': 
        return jsonify({'error': f"Acceso denegado. Tu rol actual es: {session.get('user_rol')}"}), 403

    file = request.files.get('file')
    if not file or file.filename == '':
        return "No seleccionó ningún archivo", 400

    try:
        # 1. Leer el Excel
        df = pd.read_excel(file)
        
        # 2. Función para quitar tildes y dejar limpio el nombre de la columna
        def normalizar_nombre(txt):
            txt = str(txt).strip().lower()
            # Elimina tildes (ej: Título -> titulo)
            txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
            return txt

        # Aplicamos la normalización a todas las cabeceras del Excel
        df.columns = [normalizar_nombre(c) for c in df.columns]
        
        # 3. Limpiar filas totalmente vacías
        df.dropna(how='all', inplace=True)

        # 4. Convertir a lista de diccionarios
        lista_libros = df.to_dict(orient='records')

        # 5. Llamar a la función de inserción masiva
        exito, mensaje = cargar_libros_masivo(lista_libros)

        if exito:
            return f"""
            <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
            <script>
                window.onload = function() {{
                    Swal.fire({{
                        title: '¡Excelente!',
                        text: '{mensaje}',
                        icon: 'success',
                        confirmButtonText: 'Ir al Inventario',
                        confirmButtonColor: '#10b981'
                    }}).then(() => {{ window.location.href = '/admin/inventario'; }});
                }};
            </script>
            """
        else:
            return f"""
            <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
            <script>
                window.onload = function() {{
                    Swal.fire({{
                        title: 'Atención',
                        text: '{mensaje}',
                        icon: 'warning',
                        confirmButtonText: 'Reintentar'
                    }}).then(() => {{ window.location.href = '/admin'; }});
                }};
            </script>
            """

    except Exception as e:
        return f"""
        <div style="font-family:sans-serif; padding:50px; text-align:center;">
            <h1 style="color:#ef4444;">❌ Error Crítico</h1>
            <p>No se pudo procesar el archivo Excel.</p>
            <code style="background:#f1f5f9; padding:10px; display:block;">{str(e)}</code>
            <br>
            <a href="/admin" style="color:#0284c7;">Volver al panel</a>
        </div>
        """

@app.route('/admin/reportes')
def admin_reportes():
    """Vista de Deudores y Multas"""
    if session.get('user_rol') != 'Administrador':
        return redirect(url_for('index'))
    
    deudores = obtener_deudores_y_multas()
    # Calculamos la multa: S/. 1.00 por cada día de retraso
    for d in deudores:
        d['multa_total'] = d['DiasRetraso'] * 1.0 if d['DiasRetraso'] > 0 else 0
        
    return render_template('admin/reportes.html', deudores=deudores)




@app.route('/admin/libros/limpiar', methods=['POST'])
def admin_limpiar_libros():
    if session.get('user_rol') != 'Administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    from utils.queries_admin import limpiar_tabla_libros
    exito, msg = limpiar_tabla_libros()
    
    # Retornamos un script para que mande una alerta y regrese al dashboard
    return f"<script>alert('{msg}'); window.location.href='/admin';</script>"



@app.route('/admin/api/buscar_inventario')
def api_buscar_inventario():
    if session.get('user_rol') != 'Administrador':
        return jsonify([]), 403
    
    query = request.args.get('q', '')
    from utils.queries_admin import buscar_libros_inventario_admin
    
    if len(query) < 3: # No buscamos hasta que escriba al menos 3 letras
        from utils.queries_admin import obtener_todos_los_libros
        return jsonify(obtener_todos_los_libros())
        
    resultados = buscar_libros_inventario_admin(query)
    return jsonify(resultados)



@app.route('/admin/devolver/<int:p_id>/<int:l_id>', methods=['POST'])
def admin_devolver_libro(p_id, l_id):
    if session.get('user_rol') != 'Administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    from utils.queries_admin import procesar_devolucion_db
    exito, msg = procesar_devolucion_db(p_id, l_id)
    
    if exito:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 500

@app.route('/api/confirmar_prestamo', methods=['POST'])
def confirmar_prestamo():
    data = request.get_json()
    usuario = data.get('usuario') # Aquí ya viene el celular desde tu JS
    libro = data.get('libro')
    
    if not usuario or not libro:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400

    from utils.queries_prestamos import registrar_prestamo_db
    # Pasamos los diccionarios completos
    exito, msg = registrar_prestamo_db(usuario, libro)
    
    if exito:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 500

# =========================================================
# excel
# =========================================================

@app.route('/admin/exportar_excel')
def exportar_excel():
    # Capturamos las fechas que vienen del formulario HTML
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    
    if not fecha_inicio or not fecha_fin:
        return "Faltan las fechas para el reporte", 400

    from utils.queries_admin import obtener_reporte_excel_db
    datos = obtener_reporte_excel_db(fecha_inicio, fecha_fin)
    
    if not datos:
        return f"No se encontraron préstamos entre {fecha_inicio} y {fecha_fin}", 404

    # Creamos el Excel en memoria
    df = pd.DataFrame(datos)
    
    # Renombramos las columnas para el reporte oficial de la UNDAC
    df.columns = [
        'ID Registro', 'Nombre del Lector', 'DNI', 'Celular de Contacto', 
        'Título del Libro', 'Código Secuencial', 'Fecha de Préstamo', 
        'Vencimiento Estimado', 'Fecha Real de Entrega', 'Estado Actual'
    ]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Historial de Préstamos')
    
    output.seek(0)
    
    nombre_archivo = f"Reporte_Biblioteca_UNDAC_{fecha_inicio}_al_{fecha_fin}.xlsx"
    
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, 
        download_name=nombre_archivo
    )



@app.route('/admin/usuarios', methods=['GET', 'POST'])
def gestionar_usuarios():
    from utils.queries_admin import crear_usuario_sistema_db, obtener_usuarios_sistema
    
    if request.method == 'POST':
        # Captura los datos del formulario (los "name" del HTML)
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        email = request.form.get('email')
        rol = request.form.get('rol')
        sede = request.form.get('sede')
        
        # Llama a la función que encripta y guarda en SQL Server
        exito, msg = crear_usuario_sistema_db(usuario, password, email, rol, sede)
        
        # Redirige para limpiar el formulario y ver al nuevo usuario en la lista
        return redirect('/admin/usuarios')

    # Si es GET, solo muestra la página con la lista de usuarios
    usuarios = obtener_usuarios_sistema()
    return render_template('admin/gestion_usuarios.html', usuarios=usuarios)


@app.route('/prestamos')
def modulo_prestamos():
    # Esta es la página donde está el lector de barras y se busca al alumno
    return render_template('prestamos.html')



@app.route('/devoluciones', methods=['GET', 'POST'])
def modulo_devoluciones():
    # Esta página será la interfaz para el bibliotecario
    return render_template('devoluciones.html', active_page='devoluciones')

@app.route('/api/buscar_prestamo_por_libro/<string:codigo_libro>')
def buscar_prestamo_por_libro(codigo_libro):
    """Busca quién tiene el libro actualmente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT TOP 1
            p.PrestamoID, p.UsuarioNombre, p.UsuarioDNI, p.Celular,
            l.LibroID, l.Titulo, l.Secuenc, p.FechaDevolucionEstimada
        FROM Prestamos p
        JOIN Libros l ON p.LibroID = l.LibroID
        WHERE l.Secuenc = ? AND p.EstadoPrestamo = 'Activo'
    """
    cursor.execute(query, (codigo_libro,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            'success': True,
            'data': {
                'prestamo_id': row[0], 'nombre': row[1], 'dni': row[2],
                'celular': row[3], 'libro_id': row[4], 'titulo': row[5],
                'codigo': row[6], 'vencimiento': row[7].strftime('%d/%m/%Y')
            }
        })
    return jsonify({'success': False, 'message': 'Este libro no figura como prestado.'})



@app.route('/api/procesar_devolucion/<int:prestamo_id>/<int:libro_id>', methods=['POST'])
def ejecutar_devolucion_ruta(prestamo_id, libro_id):
    from utils.queries_admin import procesar_devolucion_db
    exito, msg = procesar_devolucion_db(prestamo_id, libro_id)
    if exito:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': str(msg)}), 500

# =========================================================
# LANZAMIENTO DEL SERVIDOR
# =========================================================
if __name__ == '__main__':
    # host='0.0.0.0' para acceso desde otras PCs en la red local
    app.run(host='0.0.0.0', port=5001, debug=True)