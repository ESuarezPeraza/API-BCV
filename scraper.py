import requests
from bs4 import BeautifulSoup
import csv
import re
import os
import io
import datetime # Aún lo usamos para formatear, pero no para parsear texto

# --- Configuración Clave ---
URL = "https://www.bcv.org.ve/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
CSV_FILE = 'historial_bcv.csv'

TARGET_IDS = {
    'eur': 'euro',
    'cny': 'yuan',
    'try': 'lira',
    'rub': 'rublo',
    'usd': 'dolar'
}

FIELDNAMES = ['fecha_iso', 'fecha_valor', 'eur', 'cny', 'try', 'rub', 'usd']

# --- NUEVO: Diccionario de meses para parseo manual ---
# Esto elimina la dependencia de 'locale'
MESES_ES = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

# --- Funciones Auxiliares ---

def _limpiar_tasa(div_tag):
    try:
        tasa_strong = div_tag.find('strong')
        tasa_cruda = tasa_strong.text.strip()
        match = re.search(r'(\d+,\d+)', tasa_cruda)
        if not match: return None
        return float(match.group(1).replace(',', '.'))
    except Exception:
        return None

def _extraer_fecha_valor(soup):
    try:
        fecha_tag = soup.find('span', attrs={'class': 'date-display-single', 'property': 'dc:date'})
        if fecha_tag and fecha_tag.text.strip():
            print(f"Fecha Valor (Método 1: attrs{{...}}): {fecha_tag.text.strip()}")
            return fecha_tag.text.strip()
        
        fecha_tag = soup.find('div', string=re.compile(r'Fecha Valor:'))
        if fecha_tag:
            texto = fecha_tag.text.strip().replace('Fecha Valor:', '').strip()
            if texto:
                print(f"Fecha Valor (Método 2: Texto 'Fecha Valor:'): {texto}")
                return texto
        
        print("Error Crítico: No se pudo encontrar la 'Fecha Valor'.")
        return None
    except Exception as e:
        print(f"Error al extraer fecha: {e}")
        return None

def _parsear_fecha_iso(fecha_valor_str):
    """
    NUEVA FUNCIÓN v2.4: Parseo manual de fecha sin 'locale'.
    """
    try:
        # Limpiar: "Lunes, 03 Noviembre  2025" -> "lunes, 03 noviembre  2025"
        texto_limpio = fecha_valor_str.lower().strip()
        
        # Extraer las partes con regex
        # Ignora el día de la semana, busca "dd mes yyyy"
        match = re.search(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', texto_limpio) # Formato "03 de Noviembre de 2025"
        if not match:
            # Plan B: "Lunes, 03 Noviembre 2025"
            match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', texto_limpio)
        
        if not match:
            print(f"Error parseando fecha: Regex no encontró patrón en '{texto_limpio}'")
            return None

        dia_str = match.group(1).zfill(2) # "03"
        mes_str = match.group(2)          # "noviembre"
        ano_str = match.group(3)          # "2025"
        
        # Traducir el mes
        if mes_str not in MESES_ES:
            print(f"Error parseando fecha: Mes desconocido '{mes_str}'")
            return None
            
        mes_num = MESES_ES[mes_str] # "11"
        
        fecha_iso = f"{ano_str}-{mes_num}-{dia_str}" # "2025-11-03"
        return fecha_iso
        
    except Exception as e:
        print(f"Error fatal al parsear fecha ISO: {e}")
        return None

def _leer_ultima_fila(filepath):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            q = io.StringIO()
            q.write(f.readline())
            for line in f: q.write(line)
            q.seek(0)
            reader = csv.DictReader(q)
            last_row = None
            for row in reader: last_row = row
            return last_row
    except Exception:
        return None

# --- Función Principal (sin cambios desde 2.3) ---

def run_scraper():
    print("Iniciando scraper del BCV (Multimoneda v2.4 - Sin Locale)...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        tasas = {}
        for key, target_id in TARGET_IDS.items():
            tasa_div = soup.find('div', id=target_id)
            tasa_valor = _limpiar_tasa(tasa_div) if tasa_div else None
            if tasa_valor is None:
                print(f"Error Crítico: No se pudo limpiar la tasa para '{key}'")
                return
            tasas[key] = tasa_valor
            print(f"Tasa encontrada: {key.upper()} = {tasa_valor}")

        fecha_valor = _extraer_fecha_valor(soup)
        if fecha_valor is None: return

        fecha_iso = _parsear_fecha_iso(fecha_valor) # <--- USA LA NUEVA FUNCIÓN
        if fecha_iso is None:
            print("Error Crítico: No se pudo parsear la fecha ISO. Abortando.")
            return
            
        print(f"Fecha Valor: {fecha_valor} | Fecha ISO: {fecha_iso}")

        ultima_fila = _leer_ultima_fila(CSV_FILE)
        if ultima_fila and ultima_fila.get('fecha_iso') == fecha_iso:
            print("Datos ya están actualizados (por fecha_iso). No se requiere escritura.")
            return

        nueva_fila = {'fecha_iso': fecha_iso, 'fecha_valor': fecha_valor, **tasas}
        
        file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0
        
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(nueva_fila)
            
        print(f"Datos guardados exitosamente en {CSV_FILE}")

    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == '__main__':
    run_scraper()