import requests
from bs4 import BeautifulSoup
import csv
import datetime
import re  # Para limpieza robusta de texto
import os  # Para verificar la ruta del archivo

# --- Configuración Clave ---
URL = "https://www.bcv.org.ve/"

# Simulamos ser un navegador. Esencial para evitar bloqueos.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Esta es la parte FRÁGIL. Es el 'id' del <div> que contiene el precio.
# Si la web del BCV cambia esto, el scraper fallará.
TARGET_ID = 'dolar'

# Nombre de nuestro archivo de base de datos
CSV_FILE = 'historial_bcv.csv'

# ----------------------------

def run_scraper():
    """
    Función principal que ejecuta el scraper.
    Contacta al BCV, parsea el HTML y guarda el dato en el CSV.
    """
    print("Iniciando scraper del BCV...")
    
    try:
        # 1. Obtener el HTML
        response = requests.get(URL, headers=HEADERS, timeout=10)
        # Lanza un error si la página no respondió bien (ej. 404, 500)
        response.raise_for_status()
        
        # 2. Parsear el HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 3. Encontrar el dato
        # Buscamos un <div> que tenga el id='dolar'
        tasa_div = soup.find('div', id=TARGET_ID)
        
        if not tasa_div:
            print(f"Error Crítico: No se encontró ningún <div> con id='{TARGET_ID}'.")
            print("Posible cambio en la estructura de la página del BCV.")
            return

        tasa_strong = tasa_div.find('strong')
        
        if not tasa_strong:
            print(f"Error Crítico: Se encontró el <div>, pero no la etiqueta <strong> dentro.")
            return

        # 4. Limpiar el texto
        tasa_cruda = tasa_strong.text.strip()  # Ej: "   35,9012    "
        
        # Usamos expresión regular para extraer solo el número (formato XX,XXXX)
        match = re.search(r'(\d+,\d+)', tasa_cruda)
        
        if not match:
            print(f"Error: El texto '{tasa_cruda}' no tiene el formato esperado (ej. 35,90).")
            return
            
        # Reemplazamos la coma por un punto para el formato decimal estándar
        tasa_limpia_str = match.group(1).replace(',', '.')
        tasa_final = float(tasa_limpia_str)
        fecha_hoy = datetime.date.today().isoformat()  # Formato AAAA-MM-DD
        
        print(f"Tasa encontrada: {tasa_final} | Fecha: {fecha_hoy}")

        # 5. Guardar en CSV
        # Usamos 'os.path.abspath' para asegurar que escribimos en el archivo correcto
        file_path = os.path.abspath(CSV_FILE)
        
        # 'a' significa 'append' (añadir al final)
        # 'newline=""' es vital para que 'csv.writer' no cree líneas extra
        with open(file_path, mode='a', newline='', encoding='utf-8') as f:
            escritor_csv = csv.writer(f)
            escritor_csv.writerow([fecha_hoy, tasa_final])
            
        print(f"Tasa guardada exitosamente en {file_path}")

    except requests.exceptions.Timeout:
        print(f"Error: La solicitud a {URL} tardó demasiado (Timeout).")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al intentar acceder a {URL}: {e}")
    except AttributeError as e:
        # Este error ocurre si 'tasa_div' es 'None' y tratamos de usar .find()
        print(f"Error de 'AttributeError': {e}. (Revisar TARGET_ID)")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

# --- Este bloque permite ejecutar el script directamente ---
if __name__ == '__main__':
    run_scraper()