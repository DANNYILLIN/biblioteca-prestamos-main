# Módulo GIS - Biblioteca UNDAC

acá le paso el módulo GIS para ver el mapa con las sedes y filiales de la UNDAC. 

Lo armé usando **Flask (con Blueprints)** para que sea un módulo totalmente aparte, y para el mapa usé **Leaflet con OpenStreetMap** (así es gratis y no nos pide tarjeta de crédito como Google Maps).

1. ¿Qué tiene este módulo?
* Una API propia: Si entra a `/gis/api/sedes`, le va a botar los datos de las sedes en formato GeoJSON.
* El Mapa: Es la vista principal donde se ven los marcadores de la universidad.
* Todo separado: Como es un Blueprint, se puede probar solito sin necesidad de que usted tenga todo el sistema de la biblioteca de mi compu.

2. Archivos del Módulo
Todo está dentro de esta carpeta:
```text
modulo_gis/
├── __init__.py
├── routes_gis.py          # Las rutas y la API
├── run_standalone.py      # El archivo para que usted lo pruebe directo
└── templates/
    └── gis/
        └── mapa_sedes.html # El diseño del mapa
```

osea con el zip que le estoy pasasndo ya sobra y basta

3. ¿Cómo probarlo en su compu?
Solo necesita tener Flask instalado (`pip install Flask`). 

Como usted no tiene mi base de datos de SQL Server ni mi archivo `db.py`, le puse un "truco" al archivo `run_standalone.py` para que simule la conexión (usando un mock) y el código no se rompa al buscar los datos.

Para levantar el servidor, solo abra la terminal en esta carpeta y corra:
```bash
python run_standalone.py
```
Va a levantar en el puerto 5000. **Ojo:** Como está usando la simulación para que usted lo pueda correr, los "Préstamos Activos" al hacer clic en las sedes siempre van a salir en 0 por ahora.

4. ¿Cómo lo unimos al sistema principal después?
Cuando ya lo pongamos en producción con la base de datos real, solo hay que importar el Blueprint en el `app_prestamos.py` principal, agregando estas dos líneas:

```python
from modulo_gis.routes_gis import gis_bp
app.register_blueprint(gis_bp)
```

Y listo, ya con eso jalará los datos reales de SQL.