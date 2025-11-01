import requests
import csv
import io
import datetime
from flask import Flask, jsonify
from flask_cors import CORS

# --- Configuración ---
app = Flask(__name__)
# No ordenamos las claves JSON para mantener el orden del CSV
app.config['JSON_SORT_KEYS'] = False
CORS(app) # Habilitamos CORS para apps web/móviles

# REEMPLAZA ESTO con la URL 'Raw' de tu historial_bcv.csv en GitHub
CSV_URL = "URL_DEL_CSV_RAW_EN_GITHUB"

# --- Lógica de Caching (Esencial) ---
cache = {
    'datos': None,
    'timestamp': None
}
CACHE_DURATION = datetime.timedelta(minutes=15)

# --- Funciones Auxiliares ---
def _convertir_fila_a_float(fila):
    tasas_keys = ['eur', 'cny', 'try', 'rub', 'usd']
    for key in tasas_keys:
        if key in fila:
            try:
                fila[key] = float(fila[key])
            except (ValueError, TypeError):
                fila[key] = None
    return fila

def get_data_from_github():
    ahora = datetime.datetime.now()
    
    if (cache['datos'] and cache['timestamp'] and
        (ahora - cache['timestamp'] < CACHE_DURATION)):
        print("Sirviendo desde el caché...")
        return cache['datos'], None

    print("Caché expirado. Descargando desde GitHub...")
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()
        
        csv_text = response.content.decode('utf-8')
        csv_file = io.StringIO(csv_text)
        
        reader = csv.DictReader(csv_file)
        
        historial = []
        for fila in reader:
            historial.append(_convertir_fila_a_float(fila))
            
        cache['datos'] = historial
        cache['timestamp'] = ahora
        
        return historial, None
        
    except Exception as e:
        print(f"Error al descargar o procesar CSV: {e}")
        return None, "Error al contactar la base de datos."

# --- Endpoints de la API ---

@app.route('/')
def index():
    return jsonify({
        "mensaje": "Bienvenido a la API de Tasas del BCV (Multimoneda)",
        "endpoints": {
            "actual": "/api/tasa/actual",
            "historial": "/api/tasa/historial",
            "por_fecha": "/api/tasa/YYYY-MM-DD"
        }
    })

@app.route('/api/tasa/actual')
def get_tasa_actual():
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404
    
    return jsonify(historial[-1]) # El último registro

@app.route('/api/tasa/historial')
def get_tasa_historial():
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    return jsonify(historial)

# --- ¡NUEVO ENDPOINT! ---
@app.route('/api/tasa/<string:fecha_iso>')
def get_tasa_por_fecha(fecha_iso):
    """
    Devuelve las tasas para una fecha específica en formato YYYY-MM-DD.
    """
    # Validar formato básico
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_iso):
        return jsonify({
            "error": "Formato de fecha inválido.",
            "formato_esperado": "YYYY-MM-DD"
        }), 400

    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404

    # Buscar en el historial la fecha_iso
    for fila in historial:
        if fila.get('fecha_iso') == fecha_iso:
            return jsonify(fila)
    
    return jsonify({"error": "Fecha no encontrada."}), 404

# --- Corre la aplicación ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)