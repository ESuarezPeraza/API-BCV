import requests
from bs4 import BeautifulSoup
import csv
import re
import os
import io # Necesario para leer la última línea eficientemente

# --- Configuración Clave ---
URL = "https://www.bcv.org.ve/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
CSV_FILE = 'historial_bcv.csv'

# Los IDs de los <div> que contienen cada tasa
TARGET_IDS = {
    'eur': 'euro',
    'cny': 'yuan',
    'try': 'lira',
    'rub': 'rublo',
    'usd': 'dolar'
}

# Las cabeceras que esperamos en el CSV
FIELDNAMES = ['fecha_valor', 'eur', 'cny', 'try', 'rub', 'usd']

# --- Funciones Auxiliares ---

def _limpiar_tasa(div_tag):
    """Extrae y limpia el texto de la tasa de un <div> dado."""
    try:
        tasa_strong = div_tag.find('strong')
        tasa_cruda = tasa_strong.text.strip()
        
        match = re.search(r'(\d+,\d+)', tasa_cruda)
        if not match:
            print(f"Error: Formato no esperado en '{tasa_cruda}'")
            return None
            
        tasa_limpia_str = match.group(1).replace(',', '.')
        return float(tasa_limpia_str)
    except Exception as e:
        print(f"Error al limpiar tasa: {e}")
        return None

def _extraer_fecha_valor(soup):
    """
    Extrae la 'Fecha Valor' de la página, usando el selector de alta precisión.
    """
    try:
        # MÉTODO 1 (v2.2 - El más robusto)
        # Buscamos <span class="date-display-single" property="dc:date" ...>
        # Usamos attrs={} para la búsqueda más precisa y fiable
        fecha_tag = soup.find('span', attrs={
            'class': 'date-display-single',
            'property': 'dc:date'
        })
        
        if fecha_tag:
            fecha_str = fecha_tag.text.strip()
            if fecha_str:
                print(f"Fecha Valor (Método 1: attrs{{...}}): {fecha_str}")
                return fecha_str
        
        # PLAN B (Si el BCV cambia el selector principal)
        fecha_tag = soup.find('div', string=re.compile(r'Fecha Valor:'))
        if fecha_tag:
            texto_completo = fecha_tag.text.strip()
            fecha_str = texto_completo.replace('Fecha Valor:', '').strip()
            if fecha_str:
                print(f"Fecha Valor (Método 2: Texto 'Fecha Valor:'): {fecha_str}")
                return fecha_str

        # PLAN C (Respaldo final)
        fecha_tag = soup.find('span', class_='bcv-fecha-valor')
        if fecha_tag:
            fecha_str = fecha_tag.text.strip()
            if fecha_str:
                print(f"Fecha Valor (Método 3: span.bcv-fecha-valor): {fecha_str}")
                return fecha_str
        
        # Si todos fallan
        print("Error Crítico: No se pudo encontrar la 'Fecha Valor' con ninguno de los métodos.")
        return None
        
    except Exception as e:
        print(f"Error al extraer fecha: {e}")
        return None

def _leer_ultima_fila(filepath):
    """Lee la última fila de un CSV para evitar duplicados."""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return None # Archivo no existe o está vacío
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Leemos las últimas líneas (forma eficiente)
            q = io.StringIO()
            q.write(f.readline()) # Escribir cabecera
            for line in f:
                q.write(line)
            q.seek(0)
            
            reader = csv.DictReader(q)
            last_row = None
            for row in reader:
                last_row = row
            return last_row
            
    except Exception as e:
        print(f"Error leyendo última fila: {e}")
        return None

# --- Función Principal ---

def run_scraper():
    """
    Scraper multimoneda. Obtiene todas las tasas y la fecha valor.
    """
    print("Iniciando scraper del BCV (Multimoneda v2.2)...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 1. Extraer todas las tasas
        tasas = {}
        for key, target_id in TARGET_IDS.items():
            tasa_div = soup.find('div', id=target_id)
            if not tasa_div:
                print(f"Error Crítico: No se encontró <div> con id='{target_id}'")
                return
            
            tasa_valor = _limpiar_tasa(tasa_div)
            if tasa_valor is None:
                print(f"Error Crítico: No se pudo limpiar la tasa para '{key}'")
                return
            
            tasas[key] = tasa_valor
            print(f"Tasa encontrada: {key.upper()} = {tasa_valor}")

        # 2. Extraer la Fecha Valor
        fecha_valor = _extraer_fecha_valor(soup)
        if fecha_valor is None:
            return # El error ya se imprimió en la función auxiliar
            
        print(f"Fecha Valor encontrada: {fecha_valor}")

        # 3. Comprobar duplicados
        ultima_fila = _leer_ultima_fila(CSV_FILE)
        if ultima_fila and ultima_fila.get('fecha_valor') == fecha_valor:
            print("Datos ya están actualizados. No se requiere escritura.")
            return

        # 4. Guardar los nuevos datos
        nueva_fila = {'fecha_valor': fecha_valor, **tasas}
        
        file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0
        
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(nueva_fila)
            
        print(f"Datos guardados exitosamente en {CSV_FILE}")

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al intentar acceder a {URL}: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == '__main__':
    run_scraper()