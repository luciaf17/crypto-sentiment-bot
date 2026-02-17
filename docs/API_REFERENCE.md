# Referencia de API

Base URL: `http://localhost:8000/api`

Todos los endpoints devuelven JSON. No se requiere autenticación.

---

## Health (Estado del Sistema)

### `GET /health`

Verificación básica de que el servidor está corriendo.

**Respuesta:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### `GET /health/system`

Estado detallado de todos los servicios (base de datos, Redis, Celery).

**Respuesta:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "services": {
    "database": { "status": "healthy", "detail": null },
    "redis": { "status": "healthy", "detail": null },
    "celery": { "status": "healthy", "detail": null }
  }
}
```

| Campo | Valores posibles |
|---|---|
| `status` | `"healthy"` (todo funciona) o `"degraded"` (algún servicio caído) |
| `services.*.status` | `"healthy"` o `"unhealthy"` |

---

## Precios

### `GET /prices/latest`

Obtiene los registros de precio más recientes.

**Parámetros query:**

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `limit` | int | 100 | 1-1000 | Cantidad de registros a devolver |

**Respuesta:** Array de precios

```json
[
  {
    "id": 1,
    "symbol": "BTC/USDT",
    "price": 68200.00,
    "high": 68350.72,
    "low": 67950.40,
    "open": 68100.00,
    "close": 68200.00,
    "volume": 8.11,
    "timestamp": "2026-02-16T22:55:00Z",
    "created_at": "2026-02-16T22:55:01Z"
  }
]
```

### `GET /prices/chart`

Datos OHLCV formateados para gráficos.

**Parámetros query:**

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `symbol` | string | "BTC/USDT" | - | Par de trading |
| `hours` | int | 24 | 1-168 | Horas de historia a devolver |

**Respuesta:**
```json
{
  "symbol": "BTC/USDT",
  "hours": 24,
  "data": [
    {
      "timestamp": "2026-02-16T22:55:00Z",
      "open": 68100.00,
      "high": 68350.72,
      "low": 67950.40,
      "close": 68200.00,
      "volume": 8.11
    }
  ],
  "count": 288
}
```

### `GET /prices/current`

Precio actual (último registro) de un símbolo.

**Parámetros query:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `symbol` | string | "BTC/USDT" | Par de trading |

**Respuesta:**
```json
{
  "symbol": "BTC/USDT",
  "price": 68200.00,
  "high": 68350.72,
  "low": 67950.40,
  "open": 68100.00,
  "close": 68200.00,
  "volume": 8.11,
  "timestamp": "2026-02-16T22:55:00Z"
}
```

---

## Señales

### `GET /signals/latest`

Señales de trading más recientes (orden descendente por fecha).

**Parámetros query:**

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `limit` | int | 20 | 1-100 | Cantidad de señales |

**Respuesta:**
```json
[
  {
    "id": 42,
    "symbol": "BTC/USDT",
    "action": "BUY",
    "confidence": 1.0,
    "price_at_signal": 68000.00,
    "reasons": {
      "rsi_oversold": true,
      "sentiment_positive": true,
      "price_below_ma": true
    },
    "technical_indicators": {
      "rsi": 28.5,
      "macd": 150.0,
      "ma_20": 68500.0,
      "ma_50": 69200.0,
      "ma_200": 67000.0
    },
    "sentiment_score": 0.35,
    "timestamp": "2026-02-16T22:00:00Z",
    "created_at": "2026-02-16T22:00:01Z"
  }
]
```

**Valores de `action`:** `"BUY"`, `"SELL"`, `"HOLD"`

### `GET /signals/current`

Última señal generada para un símbolo.

**Parámetros query:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `symbol` | string | "BTC/USDT" | Par de trading |

**Respuesta:** Mismo formato que un elemento de `/signals/latest`

**Error:** `404` si no hay señales para ese símbolo.

### `GET /signals/stats`

Estadísticas agregadas de todas las señales.

**Respuesta:**
```json
{
  "total_signals": 240,
  "buy_count": 28,
  "sell_count": 25,
  "hold_count": 187,
  "buy_pct": 11.7,
  "sell_pct": 10.4,
  "hold_pct": 77.9,
  "avg_confidence": 0.72,
  "latest_signal_at": "2026-02-16T22:00:00Z"
}
```

---

## Operaciones (Trades)

### `GET /trades/active`

Operaciones actualmente abiertas.

**Respuesta:**
```json
[
  {
    "id": 5,
    "signal_id": 42,
    "entry_price": 68000.00,
    "exit_price": null,
    "quantity": 0.1,
    "pnl": null,
    "status": "OPEN",
    "opened_at": "2026-02-16T22:00:00Z",
    "closed_at": null,
    "created_at": "2026-02-16T22:00:01Z",
    "updated_at": "2026-02-16T22:05:01Z"
  }
]
```

### `GET /trades/history`

Operaciones cerradas con paginación.

**Parámetros query:**

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `limit` | int | 50 | 1-500 | Cantidad por página |
| `offset` | int | 0 | 0+ | Registros a saltar |

**Respuesta:** Array de trades (mismo formato que `/trades/active`, pero con `exit_price`, `pnl` y `closed_at` completados).

### `GET /trades/stats`

Métricas de rendimiento de todas las operaciones de paper trading.

**Respuesta:**
```json
{
  "total_trades": 50,
  "winning_trades": 30,
  "losing_trades": 20,
  "win_rate": 60.0,
  "total_pnl": 1275.00,
  "total_pnl_percent": 12.75,
  "avg_win": 250.00,
  "avg_loss": -125.00,
  "best_trade": 800.00,
  "worst_trade": -300.00,
  "max_drawdown": 410.00,
  "sharpe_ratio": 1.35,
  "current_balance": 11275.00,
  "open_trades": 1
}
```

---

## Estrategias

### `GET /strategy/current`

Estrategia activa actualmente.

**Respuesta:**
```json
{
  "id": 3,
  "name": "Balanceada",
  "aggressiveness": 50,
  "parameters": {
    "rsi_buy": 35.0,
    "rsi_sell": 65.0,
    "sentiment_weight": 0.40,
    "sentiment_min": 0.05,
    "min_confidence": 0.50,
    "stop_loss_percent": 3.5,
    "take_profit_percent": 5.5
  },
  "is_active": true,
  "description": "Estrategia equilibrada",
  "created_by": null,
  "created_at": "2026-02-15T10:00:00Z",
  "activated_at": "2026-02-15T10:30:00Z"
}
```

**Error:** `404` si no hay estrategia activa.

### `GET /strategy/list`

Lista todas las estrategias guardadas.

**Parámetros query:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `limit` | int | 20 | Cantidad máxima |

**Respuesta:** Array de estrategias (mismo formato que `/strategy/current`).

### `POST /strategy/preview`

Previsualiza los parámetros que produce un nivel de agresividad dado, sin guardar nada.

**Body:**
```json
{
  "aggressiveness": 75
}
```

**Respuesta:**
```json
{
  "aggressiveness": 75,
  "parameters": {
    "rsi_buy": 40.0,
    "rsi_sell": 60.0,
    "sentiment_weight": 0.50,
    "sentiment_min": -0.075,
    "min_confidence": 0.40,
    "stop_loss_percent": 4.25,
    "take_profit_percent": 4.25
  },
  "estimated_trades_per_day": 3.8,
  "estimated_win_rate": 0.52,
  "risk_level": "High"
}
```

### `POST /strategy/create`

Crea y guarda una nueva estrategia.

**Body:**
```json
{
  "name": "Mi Estrategia Agresiva",
  "aggressiveness": 80,
  "description": "Para mercados volátiles"
}
```

**Respuesta:** La estrategia creada (mismo formato que `/strategy/current`). Se crea inactiva por defecto.

### `POST /strategy/activate`

Activa una estrategia. Desactiva todas las demás automáticamente.

**Body:**
```json
{
  "strategy_id": 3
}
```

**Respuesta:** La estrategia activada.

**Error:** `404` si no existe la estrategia.

---

## Backtesting (Pruebas Históricas)

### `POST /backtest/run`

Ejecuta un backtest completo con parámetros personalizados.

**Body:**
```json
{
  "symbol": "BTC/USDT",
  "start_date": "2026-02-01T00:00:00Z",
  "end_date": "2026-02-15T23:59:59Z",
  "strategy_params": {
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "position_size": 0.1,
    "stop_loss_percent": 3.0,
    "take_profit_percent": 5.0,
    "initial_balance": 10000
  }
}
```

**Respuesta:**
```json
{
  "id": 7,
  "status": "completed",
  "symbol": "BTC/USDT",
  "period_start": "2026-02-01T00:00:00Z",
  "period_end": "2026-02-15T23:59:59Z",
  "data_points": 4032,
  "parameters": { "..." },
  "metrics": {
    "total_trades": 8,
    "winning_trades": 5,
    "losing_trades": 3,
    "win_rate": 62.5,
    "total_pnl": 427.50,
    "total_pnl_percent": 4.28,
    "avg_win": 145.00,
    "avg_loss": -72.50,
    "profit_factor": 1.87,
    "max_drawdown": 185.00,
    "max_drawdown_percent": 1.82,
    "sharpe_ratio": 1.42,
    "best_trade": 345.00,
    "worst_trade": -120.00,
    "avg_hold_duration_hours": 8.5,
    "final_balance": 10427.50
  },
  "trades": [
    {
      "entry_price": 68000.00,
      "entry_time": "2026-02-03T14:00:00Z",
      "exit_price": 69200.00,
      "exit_time": "2026-02-03T22:00:00Z",
      "quantity": 0.1,
      "pnl": 120.00,
      "pnl_percent": 1.76,
      "exit_reason": "signal_sell",
      "rsi": 28.5,
      "sentiment": 0.35
    }
  ],
  "equity_curve": [
    { "timestamp": "2026-02-01T00:00:00Z", "balance": 10000.00 },
    { "timestamp": "2026-02-03T22:00:00Z", "balance": 10120.00 }
  ],
  "error_reason": null,
  "created_at": "2026-02-16T10:00:00Z"
}
```

**Valores de `exit_reason`:** `"signal_sell"`, `"stop_loss"`, `"take_profit"`, `"end_of_period"`

### `POST /backtest/quick`

Backtest rápido (últimos 7 días por defecto) con comparación contra la estrategia activa.

**Body:**
```json
{
  "symbol": "BTC/USDT",
  "strategy_params": {
    "rsi_buy": 35.0,
    "rsi_sell": 65.0,
    "sentiment_weight": 0.40,
    "sentiment_min": 0.05,
    "min_confidence": 0.50,
    "stop_loss_percent": 3.5,
    "take_profit_percent": 5.5
  },
  "days": 7
}
```

**Respuesta:**
```json
{
  "result": { "... (mismo formato que /backtest/run)" },
  "comparison": {
    "active_strategy_name": "Conservadora",
    "active_pnl": 85.00,
    "active_pnl_percent": 0.85,
    "active_win_rate": 55.0,
    "active_total_trades": 3,
    "active_sharpe_ratio": 0.92,
    "pnl_difference": 342.50,
    "pnl_percent_difference": 3.43,
    "win_rate_difference": 7.5,
    "is_better": true
  }
}
```

### `GET /backtest/results/{backtest_id}`

Recupera un backtest guardado previamente.

**Parámetro de ruta:** `backtest_id` (int)

**Respuesta:** Mismo formato que `/backtest/run`

**Error:** `404` si no existe el backtest.

### `GET /backtest/compare`

Compara múltiples backtests lado a lado.

**Parámetros query:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `ids` | string | IDs separados por coma, ej: `"1,2,3"` |

**Respuesta:**
```json
{
  "runs": [ "..." ],
  "best_by_pnl": 2,
  "best_by_sharpe": 1,
  "best_by_drawdown": 3
}
```

**Error:** `400` si se proporcionan menos de 2 IDs.

---

## Códigos de Error

| Código | Significado |
|---|---|
| `200` | OK — solicitud exitosa |
| `400` | Bad Request — parámetros inválidos |
| `404` | Not Found — recurso no encontrado |
| `500` | Internal Server Error — error del servidor |

Formato de error:
```json
{
  "detail": "Descripción del error"
}
```

---

## Ejemplos con curl

### Obtener precio actual
```bash
curl http://localhost:8000/api/prices/current
```

### Últimas 10 señales
```bash
curl "http://localhost:8000/api/signals/latest?limit=10"
```

### Ejecutar un backtest
```bash
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "start_date": "2026-02-01T00:00:00Z",
    "end_date": "2026-02-15T23:59:59Z",
    "strategy_params": {
      "rsi_oversold": 30,
      "rsi_overbought": 70,
      "position_size": 0.1,
      "stop_loss_percent": 3.0,
      "take_profit_percent": 5.0,
      "initial_balance": 10000
    }
  }'
```

### Crear y activar una estrategia
```bash
# Crear
curl -X POST http://localhost:8000/api/strategy/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Agresiva", "aggressiveness": 80}'

# Activar (usar el ID devuelto)
curl -X POST http://localhost:8000/api/strategy/activate \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 4}'
```
