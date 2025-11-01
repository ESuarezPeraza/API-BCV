import requests
import csv
import io
import datetime
from flask import Flask, jsonify
from flask_cors import CORS  # Importamos la librería de permisos

# --- Configuración ---
app = Flask(__name__)
# Habilitamos CORS para todos los dominios.
# Esto permite que tu app web (JS) llame a esta API.
CORS(app)

# REEMPLAZA ESTO con la URL 'Raw' de tu historial_bcv.csv en GitHub
CSV_URL = "https://raw.githubusercontent.com/ESuarezPeraza/API-BCV/refs/heads/main/historial_bcv.csv"

# --- Lógica de Caching (Esencial) ---
# No queremos descargar el CSV de GitHub en CADA llamada a la API.
# GitHub nos bloquearía. Guardamos los datos en memoria por un tiempo.
cache = {
    'datos': None,
    'timestamp': None
}
CACHE_DURATION = datetime.timedelta(minutes=15)

# --- Funciones Auxiliares ---

def _convertir_fila_a_float(fila):
    """Toma una fila del CSV y convierte las tasas a números (float)."""
    tasas_keys = ['eur', 'cny', 'try', 'rub', 'usd']
    for key in tasas_keys:
        if key in fila:
            try:
                fila[key] = float(fila[key])
            except (ValueError, TypeError):
                # Si un dato está malformado, lo dejamos como None
                fila[key] = None
    return fila

def get_data_from_github():
    """
    Obtiene los datos del CSV desde GitHub, usando el caché.
    """
    ahora = datetime.datetime.now()
    
    # 1. Revisar si el caché es válido
    if (cache['datos'] and cache['timestamp'] and
        (ahora - cache['timestamp'] < CACHE_DURATION)):
        print("Sirviendo desde el caché...")
        return cache['datos'], None  # Devuelve (datos, error)

    print("Caché expirado. Descargando desde GitHub...")
    # 2. Si el caché no es válido, descargar
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()  # Lanza error si no lo puede descargar
        
        csv_text = response.content.decode('utf-8')
        csv_file = io.StringIO(csv_text)
        
        reader = csv.DictReader(csv_file)
        
        historial = []
        for fila in reader:
            historial.append(_convertir_fila_a_float(fila))
            
        # 3. Actualizar el caché
        cache['datos'] = historial
        cache['timestamp'] = ahora
        
        return historial, None  # Devuelve (datos, error)
        
    except requests.exceptions.RequestException as e:
        print(f"Error descargando CSV desde GitHub: {e}")
        return None, "Error al contactar la base de datos en GitHub."
    except Exception as e:
        print(f"Error procesando el CSV: {e}")
        return None, "Error interno al procesar los datos."

# --- Endpoints de la API ---

@app.route('/')
def index():
    """Endpoint raíz de bienvenida."""
    return jsonify({
        "mensaje": "Bienvenido a la API de Tasas del BCV (Multimoneda)",
        "desarrollador": "Tu Nombre Aquí",
        "fuente": "Datos scrapeados de bcv.org.ve",
        "endpoints": {
            "actual": "/api/tasa/actual",
            "historial": "/api/tasa/historial"
        }
    })

@app.route('/api/tasa/actual')
def get_tasa_actual():
    """Devuelve solo el último registro (el más reciente)."""
    historial, error = get_data_from_github()
    
    if error:
        return jsonify({"error": error}), 500
        
    if not historial:
        return jsonify({"error": "No se encontraron datos"}), 404
    
    # La tasa actual es el ÚLTIMO elemento en la lista
    tasa_actual = historial[-1]
    
    return jsonify(tasa_actual)

@app.route('/api/tasa/historial')
def get_tasa_historial():
    """Devuelve todo el historial de tasas."""
    historial, error = get_data_from_github()
    
    if error:
        return jsonify({"error": error}), 500

    return jsonify(historial)

# --- Corre la aplicación ---
if __name__ == '__main__':
    # 'host="0.0.0.0"' es importante para despliegue
    app.run(host='0.0.0.0', port=5000, debug=True)