# Crypto Sentiment Trading Bot

Bot de trading automatizado que combina **análisis técnico** con **análisis de sentimiento** del mercado para generar señales de compra/venta de Bitcoin.

## Qué hace este bot

1. **Recolecta precios** de BTC/USDT desde Binance cada 5 minutos
2. **Analiza el sentimiento** del mercado usando noticias (CryptoPanic, NewsAPI) y el índice Fear & Greed cada 15 minutos
3. **Genera señales** de COMPRAR/VENDER/MANTENER cada hora combinando indicadores técnicos (RSI, MACD, medias móviles) con el sentimiento
4. **Ejecuta operaciones simuladas** (paper trading) con Stop Loss y Take Profit automáticos
5. **Muestra todo** en un dashboard web en tiempo real con gráficos y métricas

> **Importante:** Por defecto opera en modo paper trading (dinero virtual). No se arriesga dinero real.

## Características principales

- Análisis técnico: RSI (14 períodos), MACD (12/26/9), Medias Móviles (20, 50, 200)
- Sentimiento multi-fuente: CryptoPanic (40%), NewsAPI (40%), Fear & Greed Index (20%)
- Sistema de estrategias configurables con control de agresividad (0-100%)
- Paper trading con Stop Loss (3%) y Take Profit (5%) automáticos
- Backtesting para probar estrategias con datos históricos
- Dashboard interactivo con gráficos en tiempo real
- Tooltips educativos explicando cada métrica y concepto

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend API | FastAPI + Python 3.11 |
| Base de datos | PostgreSQL 16 |
| Cola de tareas | Celery + Redis 7 |
| Frontend | React 19 + TypeScript + Vite |
| Gráficos | Recharts |
| Estilos | Tailwind CSS |
| Datos de precio | Binance (ccxt) |
| Sentimiento | CryptoPanic, NewsAPI, Fear & Greed Index |
| NLP | VADER Sentiment |
| Contenedores | Docker Compose |

## Inicio rápido

### Prerrequisitos

- Docker y Docker Compose instalados
- Node.js 18+ (para el frontend)
- Claves API (opcionales pero recomendadas):
  - [CryptoPanic](https://cryptopanic.com/developers/api/) (gratis)
  - [NewsAPI](https://newsapi.org/) (gratis)

### 1. Configurar variables de entorno

```bash
cp backend/.env.example backend/.env
# Edita backend/.env y agrega tus API keys
```

### 2. Levantar el backend

```bash
docker-compose up -d
```

Esto inicia: PostgreSQL, Redis, el backend FastAPI, Celery Worker y Celery Beat.

### 3. Aplicar migraciones

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Cargar datos históricos (opcional)

```bash
docker-compose exec backend python -m app.scripts.load_price_history --limit 500
```

### 5. Levantar el frontend

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173 en tu navegador.

### 6. Verificar que todo funciona

```bash
# Verificar que el backend responde
curl http://localhost:8000/api/health

# Ver los logs del bot
docker-compose logs -f celery_worker
```

## Estructura del proyecto

```
crypto-sentiment-bot/
├── backend/
│   ├── app/
│   │   ├── api/            # Endpoints de la API REST
│   │   ├── models/         # Modelos SQLAlchemy (tablas de BD)
│   │   ├── schemas/        # Schemas Pydantic (validación)
│   │   ├── services/       # Lógica de negocio
│   │   │   ├── price_collector.py      # Recolector de precios
│   │   │   ├── sentiment_analyzer.py   # Análisis de sentimiento
│   │   │   ├── technical_indicators.py # Indicadores técnicos
│   │   │   ├── signal_generator.py     # Generador de señales
│   │   │   ├── paper_trader.py         # Paper trading
│   │   │   ├── strategy_manager.py     # Gestión de estrategias
│   │   │   └── backtester.py           # Motor de backtesting
│   │   ├── tasks/          # Tareas programadas de Celery
│   │   ├── config.py       # Configuración del proyecto
│   │   ├── database.py     # Conexión a PostgreSQL
│   │   └── main.py         # Aplicación FastAPI
│   ├── alembic/            # Migraciones de base de datos
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── hooks/          # Custom hooks (useApiData)
│   │   ├── api/            # Cliente API (axios)
│   │   └── types/          # Tipos TypeScript
│   └── package.json
├── docs/                   # Documentación detallada
├── docker-compose.yml
└── README.md
```

## Documentación detallada

| Documento | Descripción |
|---|---|
| [Arquitectura](docs/ARCHITECTURE.md) | Diseño del sistema, flujo de datos, esquema de BD |
| [Cómo Funciona](docs/HOW_IT_WORKS.md) | Explicación detallada de la lógica de trading |
| [Sistema de Estrategias](docs/STRATEGY_SYSTEM.md) | Configuración de agresividad y parámetros |
| [Backtesting](docs/BACKTESTING.md) | Pruebas históricas y métricas |
| [Fuentes de Datos](docs/DATA_SOURCES.md) | Binance, CryptoPanic, NewsAPI, Fear & Greed |
| [API Reference](docs/API_REFERENCE.md) | Documentación completa de endpoints |
| [Deployment](docs/DEPLOYMENT.md) | Docker, migraciones, despliegue |
| [Dashboard](docs/DASHBOARD.md) | Frontend, componentes, tooltips |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Problemas comunes y soluciones |
| [Roadmap](docs/ROADMAP.md) | Funcionalidades futuras |
| [FAQ](docs/FAQ.md) | Preguntas frecuentes |

## Puertos

| Servicio | Puerto |
|---|---|
| Frontend (Vite) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| PostgreSQL | localhost:5433 |
| Redis | localhost:6379 |

## Licencia

Proyecto personal - Uso educativo.
