# Backtesting (Pruebas Históricas)

## Qué es el backtesting

El backtesting consiste en **probar una estrategia con datos del pasado** para ver cómo habría funcionado. Es como viajar en el tiempo y simular operaciones.

**¿Por qué es importante?**
- Te permite evaluar una estrategia **sin arriesgar dinero**
- Podés comparar distintas configuraciones objetivamente
- Te muestra métricas como win rate, drawdown y Sharpe ratio
- Ayuda a encontrar la agresividad óptima para las condiciones del mercado

> **Importante:** Un buen resultado en backtesting **no garantiza** resultados futuros. El mercado puede comportarse diferente.

## Cómo funciona el motor de backtesting

### Paso a paso

```
1. Recibir parámetros (RSI buy/sell, SL%, TP%, fechas)
         │
         ▼
2. Obtener datos históricos de price_history
   (filtra por rango de fechas)
         │
         ▼
3. Recorrer cada vela cronológicamente
         │
         ▼
4. Para cada vela:
   ├── Calcular RSI con los datos HASTA ese momento
   ├── (NO usa datos futuros — evita lookahead bias)
   ├── Evaluar señal: ¿se cumplen condiciones de compra/venta?
   │
   ├── Si señal BUY y no hay posición abierta → ABRIR
   ├── Si señal SELL y hay posición abierta → CERRAR
   ├── Si hay posición abierta → verificar SL/TP
   └── Registrar balance actual
         │
         ▼
5. Cerrar posiciones abiertas al final del período
         │
         ▼
6. Calcular métricas finales
         │
         ▼
7. Devolver resultados (métricas + trades + curva de capital)
```

### Evitando el lookahead bias

El motor de backtesting **solo usa datos disponibles hasta el momento actual de la simulación**. Nunca "mira hacia adelante". Si estamos simulando las 10:00 AM, solo usamos datos de antes de las 10:00 AM para calcular indicadores.

## Métricas y cómo interpretarlas

### Win Rate (Tasa de Aciertos)

```
Win Rate = (operaciones_ganadoras / total_operaciones) × 100
```

| Win Rate | Interpretación |
|---|---|
| < 40% | Malo — perdés más de lo que ganás |
| 40-50% | Mediocre — puede ser rentable si ganancias > pérdidas |
| 50-60% | Aceptable — estás en el camino correcto |
| 60-70% | Bueno — la estrategia tiene ventaja |
| > 70% | Excelente — pero verificá que no sea un período muy favorable |

> Un win rate del 45% puede ser rentable si en promedio ganás $500 por trade ganador y perdés $200 por trade perdedor.

### Sharpe Ratio (Retorno Ajustado por Riesgo)

```
Sharpe = promedio_retornos / desviación_estándar_retornos
```

El Sharpe Ratio mide **cuánta ganancia obtenés por cada unidad de riesgo** que tomás.

| Sharpe | Interpretación |
|---|---|
| < 0 | Negativo — estás perdiendo dinero |
| 0-0.5 | Bajo — poco retorno para el riesgo que tomás |
| 0.5-1.0 | Aceptable |
| 1.0-2.0 | Bueno — retorno sólido ajustado al riesgo |
| > 2.0 | Excelente — muy buen retorno para el nivel de riesgo |

### Max Drawdown (Máxima Caída)

```
Max Drawdown = (pico_máximo - valle_mínimo) / pico_máximo × 100
```

Mide la **peor caída** desde un punto máximo hasta un punto mínimo. Es el "peor momento" que habrías vivido.

| Max Drawdown | Interpretación |
|---|---|
| < 5% | Conservador — poca volatilidad |
| 5-10% | Moderado — fluctuaciones normales |
| 10-20% | Significativo — podría ser incómodo |
| > 20% | Alto riesgo — necesitás nervios de acero |

**Ejemplo:** Si tu balance llegó a $11,000 y luego bajó a $9,500, el drawdown fue:
```
($11,000 - $9,500) / $11,000 = 13.6%
```

### Profit Factor (Factor de Ganancia)

```
Profit Factor = suma_ganancias / suma_pérdidas
```

| Profit Factor | Interpretación |
|---|---|
| < 1.0 | Perdés dinero — las pérdidas superan las ganancias |
| 1.0-1.5 | Marginal — apenas rentable |
| 1.5-2.0 | Bueno — ganás significativamente más de lo que perdés |
| > 2.0 | Excelente |

## Cómo interpretar resultados

### Ejemplo: Resultado de un backtest

```
Período:           7 días
Total Operaciones: 5
Win Rate:          60% (3 ganadoras, 2 perdedoras)
G/P Total:         +$127.50 (+1.28%)
Sharpe Ratio:      1.35
Max Drawdown:      -$85.00 (-0.85%)
Profit Factor:     1.72
Balance Final:     $10,127.50
```

**Interpretación:**
- 60% win rate es bueno — la mayoría de trades son exitosos
- Sharpe de 1.35 es bueno — buen retorno para el riesgo
- Max drawdown de -0.85% es bajo — la estrategia no tuvo caídas fuertes
- Profit factor de 1.72 — ganaste $1.72 por cada $1 perdido

**Veredicto:** Estrategia sólida para este período. Podés considerar activarla.

### Ejemplo: Resultado preocupante

```
Período:           7 días
Total Operaciones: 12
Win Rate:          42% (5 ganadoras, 7 perdedoras)
G/P Total:         -$230.00 (-2.30%)
Sharpe Ratio:      -0.45
Max Drawdown:      -$410.00 (-4.10%)
Profit Factor:     0.68
Balance Final:     $9,770.00
```

**Interpretación:**
- 42% win rate — perdés más operaciones de las que ganás
- Sharpe negativo — estás perdiendo dinero por unidad de riesgo
- Drawdown de 4.1% — caída moderada pero constante
- Profit factor < 1 — las pérdidas superan las ganancias

**Veredicto:** NO actives esta estrategia. Ajustá la agresividad o los parámetros.

## Usando backtest para validar estrategias

### Workflow recomendado

1. **Configurá la agresividad** en el slider
2. Hacé clic en **"Probar Primero"** para un backtest rápido (7 días)
3. **Analizá los resultados:**
   - ¿Win rate > 50%?
   - ¿Sharpe > 0.5?
   - ¿Max drawdown tolerable?
   - ¿Profit factor > 1.0?
4. Si los resultados son buenos → **"Activar Esta Estrategia"**
5. Si no → **"Cerrar y Ajustar"** → probá otra agresividad

### Backtest completo vs rápido

| Tipo | Acceso | Período | Parámetros |
|---|---|---|---|
| **Rápido** | Desde "Estrategia" → "Probar Primero" | Últimos 7 días | Automático según agresividad |
| **Completo** | Desde "Prueba Histórica" | Personalizable | Personalizables individualmente |

El backtest completo te da más control sobre las fechas y parámetros individuales. El rápido es más conveniente para comparar estrategias.
