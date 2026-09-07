from flask import Blueprint, render_template, jsonify
from db import get_db_connection

# Creamos el Blueprint para el módulo aislado
gis_bp = Blueprint('modulo_gis', __name__, template_folder='templates', url_prefix='/gis')

# Coordenadas de las 6 Sedes y Filiales principales de la UNDAC
SEDES_UNDAC = [
    {
        "id": 1,
        "nombre": "Ciudad Universitaria San Juan Pampa",
        "codigo": "Central",
        "lat": -10.668205,
        "lng": -76.253137,
        "tipo": "Sede Principal"
    },
    {
        "id": 2,
        "nombre": "Filial Yanahuanca",
        "codigo": "Sede Yanahuanca",
        "lat": -10.491386,
        "lng": -76.513511,
        "tipo": "Filial Provincial"
    },
    {
        "id": 3,
        "nombre": "Filial Oxapampa",
        "codigo": "Sede Oxapampa",
        "lat": -10.59407,
        "lng": -75.38435,
        "tipo": "Filial Provincial"
    },
    {
        "id": 4,
        "nombre": "Filial Tarma",
        "codigo": "Sede Tarma",
        "lat": -11.415381233858549,
        "lng": -75.70877730823705,
        "tipo": "Filial Regional (Junín)"
    },
    {
        "id": 5,
        "nombre": "Filial La Merced (Chanchamayo)",
        "codigo": "Sede La Merced",
        "lat": -11.074643038646231,
        "lng": -75.33524993175864,
        "tipo": "Filial Regional (Junín)"
    },
    {
        "id": 6,
        "nombre": "Sede Paucartambo",
        "codigo": "Sede Paucartambo",
        "lat": -10.77043,
        "lng": -75.81503,
        "tipo": "Centro Experimental / Filial"
    }
]

@gis_bp.route('/')
def ver_mapa():
    """Ruta que muestra la interfaz del mapa."""
    return render_template('gis/mapa_sedes.html')

@gis_bp.route('/api/sedes', methods=['GET'])
def api_sedes_geojson():
    """API GIS interna que devuelve los puntos en formato GeoJSON."""
    conn = get_db_connection()
    prestamos_activos = 0
    
    # Consultamos cuántos préstamos hay activos (para darle interactividad al mapa)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Prestamos WHERE EstadoPrestamo = 'Activo'")
            row = cursor.fetchone()
            if row:
                prestamos_activos = row[0]
        except Exception as e:
            print(f"Error consultando préstamos para GIS: {e}")
        finally:
            conn.close()

    # Formateamos los datos al estándar GeoJSON
    features = []
    for sede in SEDES_UNDAC:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [sede["lng"], sede["lat"]] # GeoJSON requiere [Longitud, Latitud]
            },
            "properties": {
                "id": sede["id"],
                "nombre": sede["nombre"],
                "codigo": sede["codigo"],
                "tipo": sede["tipo"],
                "prestamos_activos": prestamos_activos if sede["codigo"] == "Central" else 0
            }
        })

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })