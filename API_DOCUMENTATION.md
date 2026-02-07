# API de Tasas del BCV (Banco Central de Venezuela)

Esta API proporciona acceso a las tasas de cambio oficiales del Banco Central de Venezuela (BCV) para múltiples monedas. Los datos se obtienen automáticamente del sitio web oficial del BCV y se almacenan en un repositorio de GitHub para acceso rápido.

## Base URL
```
https://api-bcv-five.vercel.app
```

## Monedas Disponibles
- `usd` - Dólar estadounidense
- `eur` - Euro
- `cny` - Yuan chino
- `try` - Lira turca
- `rub` - Rublo ruso

## Endpoints

### 1. Información General de la API
**GET** `/`

Devuelve información general sobre la API, incluyendo todos los endpoints disponibles y las monedas soportadas.

**Ejemplo de respuesta:**
```json
{
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
  "monedas_validas": ["eur", "cny", "try", "rub", "usd"]
}
```

### 2. Tasas Actuales
**GET** `/api/tasa/actual`

Devuelve las tasas de cambio actuales (última fecha disponible) para todas las monedas.

**Ejemplo de respuesta:**
```json
{
  "fecha_iso": "2024-11-02",
  "fecha_valor": "Sábado, 02 de noviembre de 2024",
  "eur": 45.6789,
  "cny": 6.7890,
  "try": 1.2345,
  "rub": 0.5678,
  "usd": 41.2345
}
```

### 3. Tasas Actuales con Diferencias
**GET** `/api/tasa/actual/diff`

Devuelve las tasas actuales junto con sus diferencias porcentuales respecto al día anterior.

**Ejemplo de respuesta:**
```json
{
  "fecha_actual": "2024-11-02",
  "fecha_anterior": "2024-11-01",
  "diferencias": {
    "usd": {
      "tasa_actual": 41.2345,
      "tasa_anterior": 41.1234,
      "diferencia_porcentual": 0.2701,
      "fecha_actual": "2024-11-02",
      "fecha_anterior": "2024-11-01"
    },
    "eur": {
      "tasa_actual": 45.6789,
      "tasa_anterior": 45.5678,
      "diferencia_porcentual": 0.2438,
      "fecha_actual": "2024-11-02",
      "fecha_anterior": "2024-11-01"
    }
  }
}
```

### 4. Historial Completo
**GET** `/api/tasa/historial`

Devuelve todo el historial de tasas de cambio disponible, ordenado por fecha descendente (más reciente primero).

**Ejemplo de respuesta:**
```json
[
  {
    "fecha_iso": "2024-11-02",
    "fecha_valor": "Sábado, 02 de noviembre de 2024",
    "eur": 45.6789,
    "cny": 6.7890,
    "try": 1.2345,
    "rub": 0.5678,
    "usd": 41.2345
  },
  {
    "fecha_iso": "2024-11-01",
    "fecha_valor": "Viernes, 01 de noviembre de 2024",
    "eur": 45.5678,
    "cny": 6.7654,
    "try": 1.2222,
    "rub": 0.5555,
    "usd": 41.1234
  }
]
```

### 5. Tasas por Fecha Específica
**GET** `/api/tasa/{fecha_iso}`

Devuelve las tasas de cambio para una fecha específica en formato YYYY-MM-DD.

**Parámetros:**
- `fecha_iso` (string): Fecha en formato YYYY-MM-DD

**Ejemplo:**
```
GET /api/tasa/2024-11-01
```

**Ejemplo de respuesta:**
```json
{
  "fecha_iso": "2024-11-01",
  "fecha_valor": "Viernes, 01 de noviembre de 2024",
  "eur": 45.5678,
  "cny": 6.7654,
  "try": 1.2222,
  "rub": 0.5555,
  "usd": 41.1234
}
```

**Códigos de error:**
- `400`: Formato de fecha inválido (esperado: YYYY-MM-DD)
- `404`: Fecha no encontrada

### 6. Tasa de Moneda Específica por Fecha
**GET** `/api/tasa/{moneda}/{fecha_iso}`

Devuelve la tasa de una moneda específica en una fecha específica.

**Parámetros:**
- `moneda` (string): Código de la moneda (usd, eur, cny, try, rub)
- `fecha_iso` (string): Fecha en formato YYYY-MM-DD

**Ejemplo:**
```
GET /api/tasa/usd/2024-11-01
```

**Ejemplo de respuesta:**
```json
{
  "fecha_iso": "2024-11-01",
  "moneda": "usd",
  "tasa": 41.1234,
  "fecha_valor_publicada": "Viernes, 01 de noviembre de 2024"
}
```

**Códigos de error:**
- `400`: Moneda no válida o formato de fecha inválido
- `404`: Fecha no encontrada o dato no disponible

### 7. Histórico Trimestral por Moneda
**GET** `/api/tasa/{moneda}/trimestre`

Devuelve el histórico de tasas de una moneda específica de los últimos 90 días (trimestre), desde hoy hacia atrás.

**Parámetros:**
- `moneda` (string): Código de la moneda (usd, eur, cny, try, rub)

**Ejemplo:**
```
GET /api/tasa/usd/trimestre
```

**Ejemplo de respuesta:**
```json
{
  "moneda": "usd",
  "periodo": "trimestre",
  "dias": 90,
  "desde": "2024-08-04",
  "hasta": "2024-11-02",
  "datos": [
    {
      "fecha_iso": "2024-11-02",
      "moneda": "usd",
      "tasa": 41.2345,
      "fecha_valor_publicada": "Sábado, 02 de noviembre de 2024"
    },
    {
      "fecha_iso": "2024-11-01",
      "moneda": "usd",
      "tasa": 41.1234,
      "fecha_valor_publicada": "Viernes, 01 de noviembre de 2024"
    }
  ]
}
```

### 8. Histórico Semestral por Moneda
**GET** `/api/tasa/{moneda}/semestre`

Devuelve el histórico de tasas de una moneda específica de los últimos 180 días (semestre), desde hoy hacia atrás.

**Parámetros:**
- `moneda` (string): Código de la moneda (usd, eur, cny, try, rub)

**Ejemplo:**
```
GET /api/tasa/usd/semestre
```

**Ejemplo de respuesta:**
```json
{
  "moneda": "usd",
  "periodo": "semestre",
  "dias": 180,
  "desde": "2024-05-06",
  "hasta": "2024-11-02",
  "datos": [
    {
      "fecha_iso": "2024-11-02",
      "moneda": "usd",
      "tasa": 41.2345,
      "fecha_valor_publicada": "Sábado, 02 de noviembre de 2024"
    },
    {
      "fecha_iso": "2024-11-01",
      "moneda": "usd",
      "tasa": 41.1234,
      "fecha_valor_publicada": "Viernes, 01 de noviembre de 2024"
    }
  ]
}
```

## Códigos de Estado HTTP

- `200`: Solicitud exitosa
- `400`: Solicitud incorrecta (parámetros inválidos)
- `404`: Recurso no encontrado
- `500`: Error interno del servidor

## Características Técnicas

- **CORS**: Habilitado para aplicaciones web y móviles
- **Cache**: Implementado con duración de 15 minutos para optimizar rendimiento
- **Formato JSON**: Todas las respuestas están en formato JSON
- **Orden JSON**: Las claves se mantienen en el orden original (no ordenadas alfabéticamente)
- **Actualización automática**: Los datos se actualizan automáticamente desde el sitio oficial del BCV

## Uso en Diferentes Lenguajes

### JavaScript/Fetch
```javascript
// Tasas actuales
fetch('https://api-bcv-five.vercel.app/api/tasa/actual')
  .then(response => response.json())
  .then(data => console.log(data));

// Histórico trimestral del USD
fetch('https://api-bcv-five.vercel.app/api/tasa/usd/trimestre')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Python/Requests
```python
import requests

# Tasas actuales con diferencias
response = requests.get('https://api-bcv-five.vercel.app/api/tasa/actual/diff')
data = response.json()
print(data)

# Histórico semestral del EUR
response = requests.get('https://api-bcv-five.vercel.app/api/tasa/eur/semestre')
data = response.json()
print(data)
```

### cURL
```bash
# Información general
curl https://api-bcv-five.vercel.app/

# Tasas por fecha específica
curl https://api-bcv-five.vercel.app/api/tasa/2024-11-01

# Histórico trimestral
curl https://api-bcv-five.vercel.app/api/tasa/usd/trimestre
```

## Notas Importantes

- Las fechas se manejan en formato ISO 8601 (YYYY-MM-DD)
- Los datos históricos comienzan desde octubre de 2021
- Las tasas se expresan en bolívares venezolanos por unidad de moneda extranjera
- El sistema de cache asegura respuestas rápidas sin sobrecargar el sitio del BCV
- Los fines de semana y días festivos pueden no tener actualizaciones

## Soporte

Para reportar problemas o solicitar nuevas funcionalidades, por favor crea un issue en el repositorio del proyecto.