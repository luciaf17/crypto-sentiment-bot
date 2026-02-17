# Fuentes de Datos

## Binance (Precios)

### Qué datos obtenemos

Velas OHLCV (Open, High, Low, Close, Volume) del par **BTC/USDT**:

| Campo | Descripción | Ejemplo |
|---|---|---|
| Open | Precio al inicio de la vela | $68,100.00 |
| High | Precio máximo durante la vela | $68,350.72 |
| Low | Precio mínimo durante la vela | $67,950.40 |
| Close | Precio al cierre de la vela | $68,200.00 |
| Volume | Volumen de BTC negociado | 8.11 BTC |
| Timestamp | Momento del dato | 2026-02-16T22:55:00Z |

### Configuración

- **Frecuencia:** Cada 5 minutos
- **Timeframe:** Velas de 5 minutos
- **Librería:** `ccxt` (wrapper universal para exchanges)
- **No requiere API key** para datos públicos de precios

### Por qué velas de 5 minutos

- Suficiente granularidad para detectar movimientos rápidos
- No sobrecarga la base de datos (~288 registros por día)
- Permite calcular indicadores técnicos con buena resolución
- El Stop Loss/Take Profit se chequea cada 5 minutos, así que tiene sentido recolectar al mismo ritmo

### Rate limits

Binance permite ~1200 peticiones por minuto para datos públicos. Nosotros hacemos 1 petición cada 5 minutos, así que estamos muy lejos del límite.

## CryptoPanic (Noticias Cripto + Sentimiento)

### Qué proporciona

CryptoPanic es un **agregador de noticias cripto** donde la comunidad vota si las noticias son positivas o negativas.

### Cómo calculamos el sentimiento

```python
# Para cada noticia:
vader_score = VADER.analyze(titulo_noticia)      # -1 a +1
vote_score  = (votos_positivos - votos_negativos) / total_votos  # -1 a +1
combined    = (vader_score + vote_score) / 2.0    # Promedio de ambos
```

**Ejemplo:**
```
Noticia: "Bitcoin ETF sees record $500M inflows"
  VADER score:  +0.65
  Votos: 45 positivos, 5 negativos → vote_score = 0.80
  Combined: (0.65 + 0.80) / 2 = 0.725
```

### Configuración

- **Frecuencia:** Cada 15 minutos
- **API Key:** Requerida (gratis en https://cryptopanic.com/developers/api/)
- **Filtro:** Noticias sobre la moneda especificada (BTC)
- **Reintentos:** Backoff exponencial en caso de error

## NewsAPI (Titulares Financieros)

### Qué obtenemos

Titulares recientes de medios financieros globales buscando "BTC cryptocurrency".

### Cómo analizamos el sentimiento

```python
# Para cada artículo:
text  = titulo + " " + descripcion
score = VADER.analyze(text)  # -1 a +1
```

**Ejemplos de análisis VADER:**

| Titular | Score VADER |
|---|---|
| "Bitcoin breaks $70k as institutional demand surges" | +0.72 |
| "Crypto market steady amid mixed economic signals" | +0.05 |
| "Bitcoin crashes 10% amid regulatory crackdown fears" | -0.68 |
| "SEC approves new Bitcoin ETF application" | +0.34 |

### Configuración

- **Frecuencia:** Cada 15 minutos
- **API Key:** Requerida (gratis en https://newsapi.org/)
- **Query:** `"{SYMBOL} cryptocurrency"`
- **Reintentos:** Backoff exponencial

### Limitaciones

- Plan gratuito: 100 peticiones por día
- Solo noticias en inglés (VADER funciona mejor en inglés)
- Puede tener delay de algunas horas en noticias

## Fear & Greed Index (Índice de Miedo y Codicia)

### Qué mide

El Crypto Fear & Greed Index combina múltiples factores para medir el sentimiento general del mercado cripto:

| Factor | Peso | Descripción |
|---|---|---|
| Volatilidad | 25% | Comparada con promedios de 30 y 90 días |
| Momentum | 25% | Volumen comparado con promedios |
| Redes sociales | 15% | Menciones y engagement en Twitter/Reddit |
| Encuestas | 15% | Encuestas semanales a traders |
| Dominancia BTC | 10% | % del mercado que es Bitcoin |
| Google Trends | 10% | Búsquedas relacionadas con crypto |

### Escala

| Rango | Clasificación | Significado |
|---|---|---|
| 0-24 | Miedo Extremo | El mercado está asustado. Posible oportunidad de compra. |
| 25-49 | Miedo | Precaución general en el mercado. |
| 50 | Neutral | Equilibrio entre miedo y codicia. |
| 51-74 | Codicia | Optimismo creciente. |
| 75-100 | Codicia Extrema | Euforia. Posible sobrevaloración. |

### Normalización

El bot normaliza el índice de 0-100 a escala -1 a +1:

```python
normalized = (valor - 50) / 50
# Ejemplos:
#   valor=25 (miedo) → (25-50)/50 = -0.50
#   valor=50 (neutral) → (50-50)/50 = 0.00
#   valor=75 (codicia) → (75-50)/50 = +0.50
```

### Configuración

- **Frecuencia:** Cada 15 minutos
- **API:** https://api.alternative.me/fng/ (gratis, sin key)
- **Actualización real:** El índice se actualiza 1 vez por día, pero lo consultamos cada 15 min para tener siempre el dato más reciente

## Pesos de las fuentes

```
Sentimiento Final = CP × 0.40 + NA × 0.40 + FG × 0.20
```

| Fuente | Peso | Justificación |
|---|---|---|
| CryptoPanic | **40%** | Específico para cripto + votos de comunidad = alta relevancia |
| NewsAPI | **40%** | Cobertura más amplia de medios financieros |
| Fear & Greed | **20%** | Índice compuesto pero se actualiza solo 1x/día, menor granularidad |

### Manejo de fuentes faltantes

Si una fuente no devuelve datos (error de API, rate limit, etc.), se **redistribuye el peso** entre las fuentes disponibles:

```python
# Ejemplo: CryptoPanic falla
# Solo tenemos NewsAPI (0.40) + Fear&Greed (0.20) = 0.60 total
# Se normaliza:
#   NewsAPI: 0.40/0.60 = 66.7%
#   F&G:    0.20/0.60 = 33.3%
```

El Fear & Greed Index siempre contribuye porque su API es gratuita y sin key.
