from flask import Flask
import sys
from unittest.mock import MagicMock

# 1. Simulamos el archivo db.py y forzamos a que la conexión devuelva "None"
mock_db = MagicMock()
mock_db.get_db_connection.return_value = None # ¡Esta es la línea mágica que arregla el error!
sys.modules['db'] = mock_db

# 2. Importamos las rutas directamente
from routes_gis import gis_bp

# 3. Configuramos Flask
app = Flask(__name__)
app.register_blueprint(gis_bp)

if __name__ == '__main__':
    print("=======================================")
    print(" INICIANDO MÓDULO GIS (MODO STANDALONE)")
    print("=======================================")
    print(" -> Mapa interactivo: http://127.0.0.1:5000/gis/")
    print(" -> API GeoJSON:      http://127.0.0.1:5000/gis/api/sedes")
    print("=======================================\n")
    app.run(debug=True, port=5000)