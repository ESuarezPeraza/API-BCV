import requests
import csv
import io
import datetime
import re # Necesitamos re para validar la fecha
from flask import Flask, jsonify
from flask_cors import CORS

# --- Configuración ---
app = Flask(__name__)
# No ordenamos las claves JSON para mantener el orden del CSV
app.config['JSON_SORT_KEYS'] = False
CORS(app) # Habilitamos CORS para apps web/móviles

# REEMPLAZA ESTO con la URL 'Raw' de tu historial_bcv.csv en GitHub
CSV_URL = "https://raw.githubusercontent.com/ESuarezPeraza/API-BCV/refs/heads/main/historial_bcv.csv"

# Lista de monedas válidas (claves de nuestro CSV)
VALID_MONEDAS = ['eur', 'cny', 'try', 'rub', 'usd']

# --- Lógica de Caching (Esencial) ---
cache = {
    'datos': None,
    'timestamp': None
}
CACHE_DURATION = datetime.timedelta(minutes=15)

# --- Funciones Auxiliares ---
def _convertir_fila_a_float(fila):
    for key in VALID_MONEDAS:
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
            "actual_con_diferencias": "/api/tasa/actual/diff",
            "historial": "/api/tasa/historial",
            "por_fecha": "/api/tasa/YYYY-MM-DD",
            "por_moneda_y_fecha": "/api/tasa/[moneda]/YYYY-MM-DD",
            "trimestre_por_moneda": "/api/tasa/[moneda]/trimestre",
            "semestre_por_moneda": "/api/tasa/[moneda]/semestre"
        },
        "monedas_validas": VALID_MONEDAS
    })

@app.route('/api/tasa/actual')
def get_tasa_actual():
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404
    
    return jsonify(historial[-1])

@app.route('/api/tasa/historial')
def get_tasa_historial():
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    return jsonify(historial)

@app.route('/api/tasa/<string:fecha_iso>')
def get_tasa_por_fecha(fecha_iso):
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_iso):
        return jsonify({"error": "Formato de fecha inválido.", "formato_esperado": "YYYY-MM-DD"}), 400

    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404

    for fila in historial:
        if fila.get('fecha_iso') == fecha_iso:
            return jsonify(fila)
    
    return jsonify({"error": "Fecha no encontrada."}), 404

# --- ¡NUEVO ENDPOINT! ---
@app.route('/api/tasa/<string:moneda>/<string:fecha_iso>')
def get_tasa_moneda_fecha(moneda, fecha_iso):
    """
    Devuelve la tasa de una MONEDA específica en una FECHA específica.
    """
    # 1. Validar Moneda
    moneda_limpia = moneda.lower()
    if moneda_limpia not in VALID_MONEDAS:
        return jsonify({
            "error": "Moneda no válida.",
            "monedas_validas": VALID_MONEDAS
        }), 400

    # 2. Validar Fecha
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_iso):
        return jsonify({
            "error": "Formato de fecha inválido.",
            "formato_esperado": "YYYY-MM-DD"
        }), 400

    # 3. Buscar los datos
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404

    for fila in historial:
        if fila.get('fecha_iso') == fecha_iso:
            # Encontramos la fecha. Ahora devolvemos solo la moneda.
            tasa_valor = fila.get(moneda_limpia)

            if tasa_valor is None:
                return jsonify({"error": f"Dato no disponible para '{moneda_limpia}' en esta fecha."}), 404

            # Devolvemos un JSON simple y útil
            return jsonify({
                "fecha_iso": fecha_iso,
                "moneda": moneda_limpia,
                "tasa": tasa_valor,
                "fecha_valor_publicada": fila.get('fecha_valor')
            })

    # 4. Si no se encontró la fecha
    return jsonify({"error": "Fecha no encontrada."}), 404

# --- NUEVOS ENDPOINTS ---

@app.route('/api/tasa/<string:moneda>/trimestre')
def get_tasa_moneda_trimestre(moneda):
    """
    Devuelve el histórico de una MONEDA específica desde hoy hasta hace 90 días (trimestre).
    """
    # 1. Validar Moneda
    moneda_limpia = moneda.lower()
    if moneda_limpia not in VALID_MONEDAS:
        return jsonify({
            "error": "Moneda no válida.",
            "monedas_validas": VALID_MONEDAS
        }), 400

    # 2. Obtener datos
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404

    # 3. Calcular fechas
    hoy = datetime.datetime.now().date()
    fecha_limite = hoy - datetime.timedelta(days=90)

    # 4. Filtrar datos del trimestre
    trimestre_data = []
    for fila in historial:
        fecha_fila = datetime.datetime.fromisoformat(fila['fecha_iso']).date()
        if fecha_limite <= fecha_fila <= hoy:
            tasa_valor = fila.get(moneda_limpia)
            if tasa_valor is not None:
                trimestre_data.append({
                    "fecha_iso": fila['fecha_iso'],
                    "moneda": moneda_limpia,
                    "tasa": tasa_valor,
                    "fecha_valor_publicada": fila.get('fecha_valor')
                })

    # 5. Ordenar por fecha descendente (más reciente primero)
    trimestre_data.sort(key=lambda x: x['fecha_iso'], reverse=True)

    return jsonify({
        "moneda": moneda_limpia,
        "periodo": "trimestre",
        "dias": 90,
        "desde": fecha_limite.isoformat(),
        "hasta": hoy.isoformat(),
        "datos": trimestre_data
    })

@app.route('/api/tasa/<string:moneda>/semestre')
def get_tasa_moneda_semestre(moneda):
    """
    Devuelve el histórico de una MONEDA específica desde hoy hasta hace 180 días (semestre).
    """
    # 1. Validar Moneda
    moneda_limpia = moneda.lower()
    if moneda_limpia not in VALID_MONEDAS:
        return jsonify({
            "error": "Moneda no válida.",
            "monedas_validas": VALID_MONEDAS
        }), 400

    # 2. Obtener datos
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404

    # 3. Calcular fechas
    hoy = datetime.datetime.now().date()
    fecha_limite = hoy - datetime.timedelta(days=180)

    # 4. Filtrar datos del semestre
    semestre_data = []
    for fila in historial:
        fecha_fila = datetime.datetime.fromisoformat(fila['fecha_iso']).date()
        if fecha_limite <= fecha_fila <= hoy:
            tasa_valor = fila.get(moneda_limpia)
            if tasa_valor is not None:
                semestre_data.append({
                    "fecha_iso": fila['fecha_iso'],
                    "moneda": moneda_limpia,
                    "tasa": tasa_valor,
                    "fecha_valor_publicada": fila.get('fecha_valor')
                })

    # 5. Ordenar por fecha descendente (más reciente primero)
    semestre_data.sort(key=lambda x: x['fecha_iso'], reverse=True)

    return jsonify({
        "moneda": moneda_limpia,
        "periodo": "semestre",
        "dias": 180,
        "desde": fecha_limite.isoformat(),
        "hasta": hoy.isoformat(),
        "datos": semestre_data
    })

@app.route('/api/tasa/actual/diff')
def get_tasa_actual_diff():
    """
    Devuelve las tasas actuales con su diferencia porcentual respecto al día anterior.
    """
    # 1. Obtener datos
    historial, error = get_data_from_github()
    if error: return jsonify({"error": error}), 500
    if not historial: return jsonify({"error": "No se encontraron datos"}), 404

    # 2. Obtener las dos últimas entradas (hoy y ayer)
    if len(historial) < 2:
        return jsonify({"error": "No hay suficientes datos para calcular diferencias."}), 404

    hoy = historial[-1]  # Última entrada (más reciente)
    ayer = historial[-2]  # Penúltima entrada

    # 3. Calcular diferencias porcentuales
    diferencias = {}
    for moneda in VALID_MONEDAS:
        tasa_hoy = hoy.get(moneda)
        tasa_ayer = ayer.get(moneda)

        if tasa_hoy is not None and tasa_ayer is not None and tasa_ayer != 0:
            diff_porcentual = ((tasa_hoy - tasa_ayer) / tasa_ayer) * 100
            diferencias[moneda] = {
                "tasa_actual": tasa_hoy,
                "tasa_anterior": tasa_ayer,
                "diferencia_porcentual": round(diff_porcentual, 4),
                "fecha_actual": hoy['fecha_iso'],
                "fecha_anterior": ayer['fecha_iso']
            }
        else:
            diferencias[moneda] = {
                "error": f"Datos insuficientes para calcular diferencia en {moneda}"
            }

    return jsonify({
        "fecha_actual": hoy['fecha_iso'],
        "fecha_anterior": ayer['fecha_iso'],
        "diferencias": diferencias
    })

# --- Corre la aplicación ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)