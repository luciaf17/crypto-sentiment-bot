# Cómo Funciona el Bot

Esta guía explica paso a paso la lógica de trading del bot: desde los indicadores técnicos hasta la ejecución de operaciones.

## Indicadores técnicos

El bot usa 3 indicadores técnicos principales:

### RSI (Relative Strength Index)

El RSI mide la **velocidad y magnitud** de los cambios de precio recientes. Escala de 0 a 100.

**Cómo se calcula (período de 14 velas):**

```
1. Calcular los cambios de precio entre velas consecutivas
2. Separar ganancias (cambios positivos) y pérdidas (cambios negativos)
3. Promediar ganancias y pérdidas con suavizado exponencial (Wilder)
4. RS = promedio_ganancias / promedio_pérdidas
5. RSI = 100 - (100 / (1 + RS))
```

**Interpretación:**

| RSI | Significado | Acción |
|---|---|---|
| < 30 | **Sobrevendido** - El precio bajó mucho, posible rebote | Señal de compra |
| 30-70 | Zona neutral | Sin señal clara |
| > 70 | **Sobrecomprado** - El precio subió mucho, posible corrección | Señal de venta |

> **Nota:** Los umbrales exactos dependen de la estrategia activa. Una estrategia conservadora usa 25/75, una agresiva usa 45/55.

### MACD (Moving Average Convergence Divergence)

El MACD mide el **momentum** (impulso) de la tendencia usando medias móviles exponenciales.

**Componentes:**

```
Línea MACD   = EMA(12 períodos) - EMA(26 períodos)
Línea Signal = EMA(9 períodos de la línea MACD)
Histograma   = Línea MACD - Línea Signal
```

**Interpretación:**

- **Histograma positivo (verde):** Tendencia alcista, el momentum comprador es más fuerte
- **Histograma negativo (rojo):** Tendencia bajista, el momentum vendedor es más fuerte
- **Cruce MACD sobre signal:** Señal alcista
- **Cruce MACD debajo de signal:** Señal bajista

> En el bot, el MACD se usa como información complementaria (aparece en las razones de la señal) pero no es una condición obligatoria para comprar o vender.

### Medias Móviles (MA)

Las medias móviles suavizan el precio para ver la tendencia general.

| Media | Período | Uso |
|---|---|---|
| MA(20) | 20 velas | Tendencia corto plazo (~1.5 días con velas de 5min) |
| MA(50) | 50 velas | Tendencia mediano plazo (~4 días) |
| MA(200) | 200 velas | Tendencia largo plazo (~17 días) |

**Regla clave del bot:** Se usa **MA(50)** como referencia:
- Precio **debajo** de MA(50) → Condición para COMPRAR (el precio está "barato")
- Precio **arriba** de MA(50) → Condición para VENDER (el precio está "caro")

## Análisis de sentimiento

El bot mide cómo se "siente" el mercado analizando noticias y otros indicadores.

### Fuentes y pesos

```
Sentimiento Final = (CryptoPanic × 0.40) + (NewsAPI × 0.40) + (Fear&Greed × 0.20)
```

| Fuente | Peso | Qué analiza |
|---|---|---|
| CryptoPanic | 40% | Noticias cripto + votos de la comunidad |
| NewsAPI | 40% | Titulares financieros generales |
| Fear & Greed Index | 20% | Índice de miedo/codicia del mercado |

### Cómo se calcula

1. **CryptoPanic:** Se obtienen noticias recientes. Cada noticia tiene votos (positivos/negativos) de la comunidad. Además se analiza el título con VADER NLP. Se promedian ambos scores.

2. **NewsAPI:** Se buscan noticias sobre "BTC cryptocurrency". Se analiza título + descripción con VADER NLP.

3. **Fear & Greed Index:** Se obtiene el índice actual (0-100) y se normaliza a escala -1 a +1.

**VADER NLP** analiza texto en inglés y devuelve un score compuesto:
- +1.0 = Extremadamente positivo
- 0.0 = Neutral
- -1.0 = Extremadamente negativo

**Ejemplo:**
```
"Bitcoin breaks $70k milestone as institutional demand surges"
→ VADER score: +0.72 (muy positivo)

"Crypto market crashes amid regulatory fears"
→ VADER score: -0.65 (negativo)
```

## Cómo se generan las señales

Cada hora, el bot evalúa **3 condiciones para comprar** y **3 condiciones para vender**. Se necesitan las **3 condiciones cumplidas** para generar señal.

### Condiciones de COMPRA

| # | Condición | Ejemplo (conservador) | Ejemplo (agresivo) |
|---|---|---|---|
| 1 | RSI < umbral_compra | RSI < 25 | RSI < 45 |
| 2 | Sentimiento > mínimo | Sentimiento > 0.30 | Sentimiento > -0.20 |
| 3 | Precio < MA(50) | Precio debajo de la media | Precio debajo de la media |

### Condiciones de VENTA

| # | Condición | Ejemplo (conservador) | Ejemplo (agresivo) |
|---|---|---|---|
| 1 | RSI > umbral_venta | RSI > 75 | RSI > 55 |
| 2 | Sentimiento < 0 | Sentimiento negativo | Sentimiento negativo |
| 3 | Precio > MA(50) | Precio arriba de la media | Precio arriba de la media |

### Cuándo el bot MANTIENE (HOLD)

Si no se cumplen las 3 condiciones de compra NI las 3 de venta, el bot emite HOLD. Esto pasa la mayoría del tiempo (~78% de señales típicamente).

**Confianza de la señal:**
- BUY o SELL (3/3 condiciones) → Confianza = 1.0
- HOLD → Confianza = 1.0 - (condiciones_cumplidas / 3)

## Ejemplo completo paso a paso

### Escenario: Señal de COMPRA exitosa

```
═══════════════════════════════════════════════════════
  10:00 AM - El bot analiza el mercado
═══════════════════════════════════════════════════════

  Precio BTC: $68,000
  MA(50):     $69,200 (precio está POR DEBAJO ✓)
  RSI:        28.5 (sobrevendido, menor a 35 ✓)

  Sentimiento:
    CryptoPanic:  +0.35 (noticias positivas)
    NewsAPI:      +0.22 (neutral-positivo)
    Fear & Greed: 32 (miedo → normalizado: -0.36)
    Promedio ponderado: +0.12 (mayor a 0.0 ✓)

  Evaluación (estrategia balanceada, umbral_compra=35):
    ✓ RSI 28.5 < 35         → condición 1 cumplida
    ✓ Sentimiento 0.12 > 0  → condición 2 cumplida
    ✓ Precio < MA(50)       → condición 3 cumplida

  → SEÑAL: COMPRAR (confianza: 100%)

═══════════════════════════════════════════════════════
  10:00 AM - PaperTrader ejecuta la operación
═══════════════════════════════════════════════════════

  Abre posición:
    Entrada: $68,000
    Cantidad: 0.1 BTC
    Inversión: $6,800
    Stop Loss: $65,960 (-3%)
    Take Profit: $71,400 (+5%)

═══════════════════════════════════════════════════════
  (El bot monitorea cada 5 minutos...)
═══════════════════════════════════════════════════════

  10:05 AM → $68,100 (dentro del rango, sin acción)
  10:10 AM → $68,350 (dentro del rango, sin acción)
  ...
  02:00 PM → $70,200 (dentro del rango, sin acción)
  02:30 PM → $71,100 (dentro del rango, sin acción)

═══════════════════════════════════════════════════════
  03:00 PM - Precio alcanza Take Profit
═══════════════════════════════════════════════════════

  Precio actual: $71,450
  Take Profit:   $71,400

  $71,450 >= $71,400 → ¡TAKE PROFIT ACTIVADO!

  Cierra posición:
    Entrada:  $68,000
    Salida:   $71,450
    Cantidad: 0.1 BTC

    Ganancia: ($71,450 - $68,000) × 0.1 = $345.00
    Porcentaje: +5.07%

  → Operación cerrada exitosamente
```

### Escenario: Stop Loss activado

```
  Entrada: $68,000 (0.1 BTC)
  Stop Loss: $65,960 (-3%)

  El precio cae...
  $67,500 → $67,000 → $66,200 → $65,900

  $65,900 <= $65,960 → ¡STOP LOSS ACTIVADO!

  Pérdida: ($65,900 - $68,000) × 0.1 = -$210.00
  Porcentaje: -3.09%

  → La pérdida se limitó al ~3% gracias al Stop Loss
```

## Mecanismo de Stop Loss y Take Profit

El bot revisa **cada 5 minutos** si el precio actual activa alguno de estos niveles:

```
                    Take Profit (+5%)
                    ═══════════════════  $71,400


                    Zona de espera
                    (sin acción)


  Precio de entrada ─────────────────  $68,000


                    Zona de espera
                    (sin acción)


                    Stop Loss (-3%)
                    ═══════════════════  $65,960
```

**Fórmulas:**
```
stop_loss_price  = entry_price × (1 - stop_loss_percent / 100)
take_profit_price = entry_price × (1 + take_profit_percent / 100)
```

> **Nota:** Los porcentajes de SL/TP dependen de la estrategia activa. Por defecto son 3% y 5% respectivamente.
