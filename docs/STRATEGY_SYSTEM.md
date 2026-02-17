# Sistema de Estrategias

## Qué es la agresividad

La agresividad es un número de **0 a 100** que controla qué tan frecuentemente el bot opera y cuánto riesgo toma:

- **0% (Ultra Conservador):** Muy pocas operaciones, condiciones estrictas, bajo riesgo
- **50% (Balanceado):** Frecuencia moderada, equilibrio entre riesgo y ganancia
- **100% (Ultra Agresivo):** Muchas operaciones, condiciones amplias, alto riesgo

## Cómo funciona: Interpolación de parámetros

Cuando movés el slider de agresividad, el bot calcula automáticamente 7 parámetros usando **interpolación lineal** entre los valores conservadores y agresivos.

### Fórmulas exactas

```python
agg = aggressiveness  # 0 a 100

rsi_buy            = 25 + (agg × 0.20)      # 25 → 45
rsi_sell           = 75 - (agg × 0.20)      # 75 → 55
sentiment_weight   = 0.20 + (agg × 0.004)   # 20% → 60%
sentiment_min      = 0.30 - (agg × 0.005)   # 0.30 → -0.20
min_confidence     = 0.70 - (agg × 0.004)   # 0.70 → 0.30
stop_loss_percent  = 2.0 + (agg × 0.03)     # 2% → 5%
take_profit_percent = 8.0 - (agg × 0.05)    # 8% → 3%
```

### Explicación de cada parámetro

| Parámetro | Qué hace | Conservador (0%) | Balanceado (50%) | Agresivo (100%) |
|---|---|---|---|---|
| **RSI Compra** | Umbral RSI para señal de compra | < 25 | < 35 | < 45 |
| **RSI Venta** | Umbral RSI para señal de venta | > 75 | > 65 | > 55 |
| **Peso Sentimiento** | Importancia del sentimiento | 20% | 40% | 60% |
| **Sentimiento Mín.** | Score mínimo para comprar | > 0.30 | > 0.05 | > -0.20 |
| **Confianza Mín.** | Confianza mínima de la señal | 0.70 | 0.50 | 0.30 |
| **Stop Loss** | Pérdida máxima tolerada | 2% | 3.5% | 5% |
| **Take Profit** | Ganancia objetivo | 8% | 5.5% | 3% |

## Comparación: Conservador vs Balanceado vs Agresivo

### Conservador (0-30%)

```
RSI Compra: < 25-31    │  Sólo compra en zonas MUY sobrevendidas
RSI Venta:  > 69-75    │  Sólo vende en zonas MUY sobrecompradas
Sent. Mín:  0.15-0.30  │  Requiere sentimiento claramente positivo
Stop Loss:  2.0-2.9%   │  Protección muy ajustada
Take Profit: 6.5-8.0%  │  Espera ganancias grandes antes de cerrar
```

**Perfil:** Pocas operaciones pero con alta probabilidad de éxito. Ideal si preferís proteger el capital y no te importa perder oportunidades.

**Ejemplo:** En un día típico, un bot conservador podría generar 0-1 señales de compra/venta. La mayoría serán HOLD.

### Balanceado (30-70%)

```
RSI Compra: < 31-39    │  Compra en zonas moderadamente sobrevendidas
RSI Venta:  > 61-69    │  Vende en zonas moderadamente sobrecompradas
Sent. Mín:  0.00-0.15  │  Acepta sentimiento neutral o positivo
Stop Loss:  2.9-4.1%   │  Protección moderada
Take Profit: 4.5-6.5%  │  Balance entre asegurar y dejar correr
```

**Perfil:** Equilibrio entre frecuencia y precisión. La opción por defecto recomendada para empezar.

### Agresivo (70-100%)

```
RSI Compra: < 39-45    │  Compra con RSI por debajo de neutral
RSI Venta:  > 55-61    │  Vende con RSI apenas por encima de neutral
Sent. Mín:  -0.20-0.00 │  Acepta incluso sentimiento negativo
Stop Loss:  4.1-5.0%   │  Permite más margen de fluctuación
Take Profit: 3.0-4.5%  │  Toma ganancias rápidas y frecuentes
```

**Perfil:** Muchas operaciones con ganancias pequeñas por trade. Mayor riesgo acumulado. Solo recomendable con backtest previo.

> **Advertencia:** Con agresividad > 70%, el bot muestra una advertencia visual en el dashboard. Las estrategias agresivas pueden tener menores tasas de aciertos.

## Cómo elegir la agresividad correcta

| Si querés... | Agresividad recomendada |
|---|---|
| Proteger capital, pocas operaciones | 10-25% |
| Empezar a probar sin mucho riesgo | 30-40% |
| Balance general (recomendado) | 45-55% |
| Más operaciones, acepto más riesgo | 60-70% |
| Máxima frecuencia, trading activo | 75-90% |

**Consejo:** Siempre hacé un backtest antes de activar una estrategia nueva. Compará los resultados con tu estrategia actual.

## Workflow de creación y activación

```
1. Ajustar slider de agresividad
         │
         ▼
2. Ver preview de parámetros (actualización en tiempo real)
         │
         ▼
3. (Opcional) "Probar Primero" → Backtest de 7 días
         │
         ▼
4. Ver resultados del backtest
         │          │
         ▼          ▼
   "Cerrar y      "Activar Esta
    Ajustar"       Estrategia"
         │              │
         ▼              ▼
  Volver al paso 1   Ingresá nombre
                         │
                         ▼
                  Estrategia activa
                  (la anterior se desactiva)
```

## Qué pasa cuando activás una estrategia

1. Todas las estrategias existentes se **desactivan**
2. La nueva estrategia se marca como **activa** con timestamp
3. La próxima vez que se genere una señal (cada hora), usará los **nuevos parámetros**
4. Las operaciones abiertas existentes **no se cierran automáticamente** — siguen con el SL/TP original

## Ejemplos con números reales

### Escenario: Agresividad 20% (Conservador)

```python
rsi_buy = 25 + (20 × 0.20) = 29.0
rsi_sell = 75 - (20 × 0.20) = 71.0
sentiment_min = 0.30 - (20 × 0.005) = 0.20
stop_loss = 2.0 + (20 × 0.03) = 2.6%
take_profit = 8.0 - (20 × 0.05) = 7.0%
```

Para comprar: RSI debe ser < 29 (raro), sentimiento > 0.20 (claramente positivo), precio < MA(50). Cuando estas 3 condiciones se dan, la probabilidad de éxito es alta.

### Escenario: Agresividad 80% (Agresivo)

```python
rsi_buy = 25 + (80 × 0.20) = 41.0
rsi_sell = 75 - (80 × 0.20) = 59.0
sentiment_min = 0.30 - (80 × 0.005) = -0.10
stop_loss = 2.0 + (80 × 0.03) = 4.4%
take_profit = 8.0 - (80 × 0.05) = 4.0%
```

Para comprar: RSI < 41 (bastante común), sentimiento > -0.10 (acepta casi todo), precio < MA(50). Se generan más señales pero con menor selectividad.
