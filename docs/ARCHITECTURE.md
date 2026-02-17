# Arquitectura del Sistema

## Diagrama general

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FUENTES EXTERNAS                             │
│   ┌──────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐  │
│   │ Binance  │    │ CryptoPanic │    │ NewsAPI  │    │ Fear &   │  │
│   │ (Precios)│    │ (Noticias)  │    │(Noticias)│    │ Greed    │  │
│   └────┬─────┘    └──────┬──────┘    └────┬─────┘    └────┬─────┘  │
└────────┼─────────────────┼────────────────┼───────────────┼────────┘
         │ cada 5min       │   cada 15min   │   cada 15min  │
         ▼                 ▼                ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CELERY WORKERS + BEAT                           │
│                                                                     │
│   ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│   │ Price Task   │  │ Sentiment Task   │  │ Signal Task        │   │
│   │ (cada 5min)  │  │ (cada 15min)     │  │ (cada 1hr)         │   │
│   └──────┬───────┘  └────────┬─────────┘  └──────────┬─────────┘   │
│          │                   │                        │             │
│          │     ┌─────────────────────────────┐        │             │
│          │     │ Trading Task (cada 5min)    │        │             │
│          │     │ - Ejecuta trades            │        │             │
│          │     │ - Chequea SL/TP            │        │             │
│          │     └─────────────┬───────────────┘        │             │
└──────────┼───────────────────┼────────────────────────┼─────────────┘
           │                   │                        │
           ▼                   ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL (Base de Datos)                     │
│                                                                     │
│   ┌───────────────┐ ┌─────────────────┐ ┌──────────┐ ┌──────────┐ │
│   │ price_history │ │ sentiment_scores│ │ signals  │ │ trades   │ │
│   │ (OHLCV)      │ │ (scores x src)  │ │ (B/S/H)  │ │ (P&L)    │ │
│   └───────────────┘ └─────────────────┘ └──────────┘ └──────────┘ │
│   ┌─────────────────┐ ┌──────────────────┐                        │
│   │ strategy_configs│ │ backtest_runs    │                        │
│   └─────────────────┘ └──────────────────┘                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (:8000)                        │
│                                                                     │
│   /api/prices/*    /api/signals/*    /api/trades/*                  │
│   /api/strategy/*  /api/backtest/*   /api/health/*                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP/JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     React Frontend (:5173)                          │
│                                                                     │
│   Vista General │ Gráficos │ Señales │ Operaciones │ Sentimiento   │
│   Prueba Histórica │ Estrategia                                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Componentes del sistema

### Backend (FastAPI)

El servidor API REST que expone todos los datos al frontend. Funciones:

- Sirve endpoints REST para precios, señales, trades, estrategias y backtesting
- Validación de datos con Pydantic schemas
- Middleware CORS para permitir peticiones del frontend
- No ejecuta la lógica de trading directamente — eso lo hacen los workers de Celery

**Archivo principal:** `backend/app/main.py`

### Base de datos (PostgreSQL 16)

Almacena todo el estado persistente del bot:

| Tabla | Contenido | Registros típicos |
|---|---|---|
| `price_history` | Precios OHLCV de BTC/USDT | ~288/día (cada 5min) |
| `sentiment_scores` | Scores de sentimiento por fuente | ~96/día (cada 15min × fuentes) |
| `signals` | Señales BUY/SELL/HOLD generadas | ~24/día (cada hora) |
| `trades` | Operaciones ejecutadas (paper) | Variable |
| `strategy_configs` | Configuraciones de estrategias | Pocas (creadas por usuario) |
| `backtest_runs` | Resultados de backtesting | Bajo demanda |

### Cola de tareas (Celery + Redis)

Celery ejecuta las tareas programadas que recolectan datos y operan:

| Tarea | Frecuencia | Qué hace |
|---|---|---|
| `collect_btc_price` | Cada 5 min | Obtiene OHLCV de Binance y lo guarda |
| `analyze_btc_sentiment` | Cada 15 min | Consulta CryptoPanic + NewsAPI + Fear&Greed |
| `generate_trading_signal` | Cada 1 hora | Calcula indicadores + sentimiento → señal |
| `execute_paper_trades` | Cada 5 min | Ejecuta trades y chequea Stop Loss/Take Profit |

**Redis** actúa como broker de mensajes (cola) y backend de resultados para Celery.

**Celery Beat** es el scheduler que dispara las tareas según el cronograma.

### Frontend (React + TypeScript)

Single Page Application que muestra el dashboard:

- **React 19** con TypeScript para el framework UI
- **React Query** (`@tanstack/react-query`) para data fetching con polling cada 10s
- **Recharts** para gráficos de precio y curvas de capital
- **Tailwind CSS** para estilos
- **Lucide React** para íconos
- **React Router** para navegación entre secciones

## Flujo de datos completo

### 1. Recolección de precios

```
Binance API → ccxt.fetch_ohlcv() → PriceCollectorService → price_history (PostgreSQL)
```

Cada 5 minutos, Celery Beat dispara `collect_btc_price`. El servicio usa la librería `ccxt` para obtener la última vela OHLCV (Open, High, Low, Close, Volume) de BTC/USDT.

### 2. Análisis de sentimiento

```
CryptoPanic API ──┐
NewsAPI ───────────┼─→ SentimentAnalyzer ──→ VADER NLP ──→ sentiment_scores (PostgreSQL)
Fear & Greed API ──┘
```

Cada 15 minutos, se consultan las 3 fuentes. Los textos de noticias se analizan con VADER para obtener un score (-1 a +1). Se calcula un promedio ponderado: CryptoPanic 40%, NewsAPI 40%, Fear & Greed 20%.

### 3. Generación de señales

```
price_history ──→ TechnicalIndicators ──┐
                  (RSI, MACD, MA)       ├─→ SignalGenerator ──→ signals (PostgreSQL)
sentiment_scores ──→ avg sentiment ─────┘
```

Cada hora, el generador obtiene los indicadores técnicos de los últimos 250 precios y el sentimiento promedio de las últimas 2 horas. Evalúa las condiciones de compra y venta según la estrategia activa.

### 4. Ejecución de trades

```
signals (último) ──┐
                   ├─→ PaperTrader ──→ trades (PostgreSQL)
current_price ─────┘
```

Cada 5 minutos, el paper trader revisa:
- Si hay señal BUY y no hay posición abierta → abre posición
- Si hay señal SELL y hay posición abierta → cierra posición
- Si hay posición abierta → chequea Stop Loss y Take Profit

## Esquema de base de datos

```sql
-- Precios históricos
price_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,          -- "BTC/USDT"
    price FLOAT NOT NULL,             -- Precio de cierre
    high FLOAT, low FLOAT,            -- Máximo y mínimo
    open FLOAT, close FLOAT,          -- Apertura y cierre
    volume FLOAT,                     -- Volumen
    timestamp TIMESTAMP WITH TZ,      -- Momento del dato
    created_at TIMESTAMP WITH TZ
)

-- Puntuaciones de sentimiento
sentiment_scores (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,          -- "BTC"
    score FLOAT NOT NULL,             -- -1.0 a +1.0
    source VARCHAR NOT NULL,          -- "cryptopanic", "newsapi", "fear_greed"
    raw_text TEXT,                    -- Texto original analizado
    timestamp TIMESTAMP WITH TZ,
    created_at TIMESTAMP WITH TZ
)

-- Señales de trading
signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    action VARCHAR NOT NULL,          -- "BUY", "SELL", "HOLD"
    confidence FLOAT NOT NULL,        -- 0.0 a 1.0
    price_at_signal FLOAT NOT NULL,
    reasons JSON,                     -- Explicación detallada
    technical_indicators JSON,        -- RSI, MACD, MAs
    sentiment_score FLOAT,
    timestamp TIMESTAMP WITH TZ,
    created_at TIMESTAMP WITH TZ
)

-- Operaciones (paper trading)
trades (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id),
    entry_price FLOAT NOT NULL,
    exit_price FLOAT,                 -- NULL si está abierta
    quantity FLOAT NOT NULL,          -- 0.1 BTC por defecto
    pnl FLOAT,                       -- Ganancia/Pérdida en USD
    status VARCHAR NOT NULL,          -- "OPEN" o "CLOSED"
    opened_at TIMESTAMP WITH TZ,
    closed_at TIMESTAMP WITH TZ,
    created_at TIMESTAMP WITH TZ,
    updated_at TIMESTAMP WITH TZ
)

-- Configuraciones de estrategia
strategy_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    aggressiveness INTEGER NOT NULL,  -- 0 a 100
    parameters JSON NOT NULL,         -- RSI buy/sell, sentiment, SL/TP
    is_active BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_by VARCHAR,
    activated_at TIMESTAMP WITH TZ,
    created_at TIMESTAMP WITH TZ,
    updated_at TIMESTAMP WITH TZ
)

-- Resultados de backtesting
backtest_runs (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    start_date TIMESTAMP WITH TZ,
    end_date TIMESTAMP WITH TZ,
    parameters JSON,
    metrics JSON,                     -- Win rate, P&L, Sharpe, etc.
    trades JSON,                      -- Lista de trades del backtest
    equity_curve JSON,                -- Curva de capital
    status VARCHAR,                   -- "completed", "error"
    error_reason TEXT,
    created_at TIMESTAMP WITH TZ
)
```

## Por qué cada tecnología

| Tecnología | Razón |
|---|---|
| **FastAPI** | Async, rápido, tipado con Pydantic, OpenAPI automático |
| **PostgreSQL** | Robusto, soporte JSON nativo, timestamps con timezone |
| **Celery** | Tareas programadas confiables, reintentos automáticos |
| **Redis** | Broker ligero y rápido para Celery |
| **React + TS** | Ecosistema maduro, tipado fuerte, gran comunidad |
| **ccxt** | Librería unificada para 100+ exchanges |
| **VADER** | Análisis de sentimiento rápido sin necesidad de GPU |
| **Docker** | Reproducibilidad, fácil despliegue, aislamiento |
