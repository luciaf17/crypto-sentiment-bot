# Preguntas Frecuentes (FAQ)

## Sobre el bot

### ¿Qué hace este bot?

Es un bot de trading de Bitcoin que combina **análisis técnico** (RSI, MACD, medias móviles) con **análisis de sentimiento** (noticias, Fear & Greed Index) para generar señales de compra y venta. Opera en modo **paper trading** (simulado, sin dinero real).

### ¿El bot opera con dinero real?

**No.** El bot opera exclusivamente en modo paper trading. Simula operaciones con un balance ficticio de $10,000 USD. Nunca se conecta a una cuenta de exchange real ni mueve fondos.

### ¿Puedo perder dinero?

No podés perder dinero real porque el bot no opera con fondos reales. Las ganancias y pérdidas que ves en el dashboard son simuladas.

### ¿Por qué paper trading y no trading real?

- Permite probar estrategias **sin riesgo**
- Podés evaluar el rendimiento antes de considerar dinero real
- Es ideal para **aprender** sobre trading algorítmico
- Evita errores costosos mientras se calibra la estrategia

---

## Sobre las señales

### ¿Cada cuánto se genera una señal?

Cada **1 hora**. El bot evalúa las condiciones de mercado y genera una señal BUY, SELL o HOLD.

### ¿Por qué la mayoría de señales son HOLD?

Es normal. Para generar una señal de BUY se necesitan **3 condiciones simultáneas**:
1. RSI por debajo del umbral (sobrevendido)
2. Sentimiento positivo (noticias favorables)
3. Precio por debajo de la media móvil de 50 períodos

Lo mismo aplica para SELL. Estas condiciones se dan simultáneamente en ~22% de los casos. El otro 78% es HOLD.

### ¿Puedo forzar una compra o venta?

No. El bot es completamente automático y se basa en las condiciones del mercado y la estrategia configurada. Podés influir en la frecuencia de señales ajustando la **agresividad** de la estrategia.

### ¿Qué significa la confianza de una señal?

La confianza indica qué tan "clara" es la señal:
- **BUY/SELL:** Siempre tienen confianza del 100% (las 3 condiciones se cumplen)
- **HOLD:** La confianza baja según cuántas condiciones se cumplan parcialmente

---

## Sobre la estrategia

### ¿Qué agresividad me conviene?

| Tu perfil | Agresividad recomendada |
|---|---|
| Quiero proteger capital, pocas operaciones | 10-25% |
| Estoy probando, sin mucho riesgo | 30-40% |
| Balance general (recomendado para empezar) | 45-55% |
| Quiero más operaciones, acepto más riesgo | 60-70% |
| Máxima frecuencia, trading activo | 75-90% |

**Consejo:** Empezá con 50% y ajustá según los resultados del backtest.

### ¿Qué pasa cuando cambio la estrategia?

1. Todas las estrategias anteriores se **desactivan**
2. La nueva estrategia empieza a aplicarse en la **próxima señal** (cada hora)
3. Las operaciones abiertas **no se cierran** — mantienen el SL/TP con el que se abrieron

### ¿Puedo tener varias estrategias activas?

No. Solo una estrategia puede estar activa a la vez. Pero podés guardar varias y alternar entre ellas.

### ¿Qué son el Stop Loss y Take Profit?

- **Stop Loss (SL):** Si el precio cae un X% desde tu entrada, la posición se cierra automáticamente para limitar pérdidas.
- **Take Profit (TP):** Si el precio sube un X% desde tu entrada, la posición se cierra automáticamente para asegurar ganancias.

Se verifican **cada 5 minutos**.

---

## Sobre los datos

### ¿De dónde vienen los precios?

De **Binance** a través de la librería `ccxt`. Se obtienen velas OHLCV (Open, High, Low, Close, Volume) del par BTC/USDT cada 5 minutos. No se necesita cuenta de Binance para datos públicos.

### ¿De dónde viene el sentimiento?

De 3 fuentes con pesos diferentes:

| Fuente | Peso | Requiere API Key |
|---|---|---|
| CryptoPanic | 40% | Sí (gratis) |
| NewsAPI | 40% | Sí (gratis, 100 req/día) |
| Fear & Greed Index | 20% | No |

### ¿Qué es VADER?

VADER (Valence Aware Dictionary and sEntiment Reasoner) es un modelo de NLP diseñado para analizar sentimiento en texto. Es rápido, no requiere GPU, y funciona especialmente bien con textos cortos como titulares de noticias.

### ¿Qué pasa si una fuente de sentimiento falla?

El bot **redistribuye automáticamente los pesos** entre las fuentes disponibles. Por ejemplo, si CryptoPanic falla, el peso se reparte entre NewsAPI y Fear & Greed Index proporcionalmente.

### ¿Cada cuánto se actualizan los datos?

| Dato | Frecuencia |
|---|---|
| Precios (OHLCV) | Cada 5 minutos |
| Sentimiento | Cada 15 minutos |
| Señales | Cada 1 hora |
| Chequeo de SL/TP | Cada 5 minutos |
| Dashboard | Cada 10 segundos (polling) |

---

## Sobre el backtesting

### ¿Qué es el backtesting?

Es una simulación que prueba tu estrategia con **datos del pasado**. Te permite ver cómo habría funcionado sin arriesgar nada.

### ¿Un buen backtest garantiza ganancias futuras?

**No.** El rendimiento pasado no garantiza resultados futuros. El mercado puede comportarse de forma diferente. El backtest es una herramienta de evaluación, no una predicción.

### ¿Cuántos datos necesito para un backtest?

Al menos **250 velas** (≈21 horas de datos con velas de 5 minutos) para que se puedan calcular los indicadores técnicos (RSI, MACD, MA200). Cuantos más datos, más representativo el resultado.

### ¿Qué métricas debo mirar?

Las más importantes:
- **Win Rate > 50%:** Ganás más operaciones de las que perdés
- **Sharpe Ratio > 1.0:** Buen retorno ajustado por riesgo
- **Max Drawdown < 10%:** Las caídas son manejables
- **Profit Factor > 1.5:** Ganás bastante más de lo que perdés

### ¿Qué es el "lookahead bias"?

Es un error en backtesting donde se usan datos futuros para tomar decisiones pasadas. Nuestro motor **evita esto** calculando indicadores solo con datos disponibles hasta el momento simulado.

---

## Sobre la infraestructura

### ¿Qué necesito para correr el bot?

- **Docker** y **Docker Compose** instalados
- **Node.js 18+** para el frontend
- Conexión a internet (para datos de Binance y APIs de sentimiento)
- Al menos 2GB de RAM disponibles

### ¿Cuánto espacio en disco usa?

- Docker images: ~1.5GB
- Base de datos: ~50MB por mes de datos (288 precios/día × 30 días)
- Logs: Variable, depende de la configuración

### ¿Puedo correr el bot en una Raspberry Pi?

Teóricamente sí, pero el build de TA-Lib puede ser lento en ARM. Recomendamos al menos una RPi 4 con 4GB de RAM.

### ¿Necesito tener Docker corriendo siempre?

Sí, los servicios de Docker deben estar activos para recolectar datos y generar señales. Si parás Docker, el bot deja de operar.

### ¿Puedo acceder al dashboard desde otro dispositivo?

Sí, si el frontend y backend están corriendo, podés acceder desde cualquier dispositivo en la misma red local usando la IP de tu máquina (ej: `http://192.168.1.100:5173`). Recordá agregar esa IP a la lista de CORS en `backend/app/main.py`.

---

## Problemas comunes

### ¿Por qué no veo datos en el dashboard?

Puede ser un problema de CORS. Consultá la [guía de solución de problemas](TROUBLESHOOTING.md) para diagnóstico detallado.

### ¿Por qué el backtest da error?

Probablemente no hay suficientes datos históricos. Esperá a que se acumulen al menos 21 horas de datos antes de ejecutar un backtest.

### ¿Cómo reseteo todo y empiezo de cero?

```bash
docker-compose down -v        # Borra contenedores y volúmenes
docker-compose up -d --build  # Reconstruye y levanta todo
docker-compose exec backend alembic upgrade head  # Crea las tablas
```

> **Atención:** Esto borra toda la base de datos. Los datos de precios y operaciones se perderán.
