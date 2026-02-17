# Despliegue y Configuración

## Requisitos previos

- **Docker** y **Docker Compose** instalados
- **Node.js 18+** (para el frontend en desarrollo)
- **Git**

## Inicio rápido

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd crypto-sentiment-bot
```

### 2. Configurar variables de entorno

```bash
cp backend/.env.example backend/.env
```

Editá `backend/.env` con tus claves de API:

```bash
# Base de datos (ya configurado para Docker)
DATABASE_URL=postgresql://crypto_user:crypto_pass@db:5432/crypto_bot

# Redis (ya configurado para Docker)
REDIS_URL=redis://redis:6379/0

# CryptoPanic - Obtener en https://cryptopanic.com/developers/api/
CRYPTOPANIC_API_KEY=tu_clave_aqui

# NewsAPI - Obtener en https://newsapi.org/
NEWSAPI_KEY=tu_clave_aqui

# Binance - No necesario para datos públicos
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Aplicación
DEBUG=True
LOG_LEVEL=INFO
```

### 3. Levantar los servicios con Docker

```bash
docker-compose up -d
```

Esto levanta 5 servicios:

| Servicio | Puerto | Descripción |
|---|---|---|
| `db` | 5433 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 (broker de Celery) |
| `backend` | 8000 | FastAPI (API REST) |
| `celery_worker` | - | Worker que ejecuta tareas |
| `celery_beat` | - | Scheduler que programa tareas |

### 4. Ejecutar migraciones de base de datos

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Levantar el frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend estará disponible en `http://localhost:5173`.

### 6. Verificar que todo funciona

```bash
# Verificar el backend
curl http://localhost:8000/api/health/system

# Debería devolver:
# {"status":"healthy","services":{"database":{"status":"healthy"},...}}
```

Abrí `http://localhost:5173` en el navegador. Después de unos minutos deberías ver datos de precios.

---

## Servicios Docker en detalle

### PostgreSQL (db)

```yaml
image: postgres:16-alpine
ports:
  - "5433:5432"    # Puerto externo 5433 para evitar conflictos
environment:
  POSTGRES_DB: crypto_bot
  POSTGRES_USER: crypto_user
  POSTGRES_PASSWORD: crypto_pass
volumes:
  - postgres_data:/var/lib/postgresql/data   # Persistencia
```

**Conectarte directamente a la base:**
```bash
docker-compose exec db psql -U crypto_user -d crypto_bot
```

### Redis

```yaml
image: redis:7-alpine
ports:
  - "6379:6379"
```

**Verificar conexión:**
```bash
docker-compose exec redis redis-cli ping
# Debería responder: PONG
```

### Backend (FastAPI)

```yaml
build: ./backend
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
ports:
  - "8000:8000"
volumes:
  - ./backend:/app    # Hot reload en desarrollo
```

El flag `--reload` reinicia el servidor automáticamente cuando cambiás archivos Python.

**Documentación interactiva de la API:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Celery Worker

```yaml
build: ./backend
command: celery -A app.tasks.celery_app worker --loglevel=info
```

Ejecuta las tareas que programa Celery Beat (recolección de precios, sentimiento, señales, trades).

**Ver logs del worker:**
```bash
docker-compose logs -f celery_worker
```

### Celery Beat

```yaml
build: ./backend
command: celery -A app.tasks.celery_app beat --loglevel=info
```

Scheduler que dispara las tareas periódicas:

| Tarea | Frecuencia |
|---|---|
| `collect_btc_price` | Cada 5 minutos |
| `analyze_btc_sentiment` | Cada 15 minutos |
| `generate_trading_signal` | Cada 1 hora |
| `execute_paper_trades` | Cada 5 minutos |

---

## Migraciones con Alembic

### Aplicar todas las migraciones pendientes

```bash
docker-compose exec backend alembic upgrade head
```

### Ver el estado actual

```bash
docker-compose exec backend alembic current
```

### Ver el historial de migraciones

```bash
docker-compose exec backend alembic history
```

### Crear una nueva migración

```bash
docker-compose exec backend alembic revision --autogenerate -m "descripcion del cambio"
```

### Revertir la última migración

```bash
docker-compose exec backend alembic downgrade -1
```

---

## Variables de entorno

### Requeridas

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL | `postgresql://user:pass@db:5432/crypto_bot` |
| `REDIS_URL` | Conexión a Redis | `redis://redis:6379/0` |

### Opcionales (APIs externas)

| Variable | Descripción | Cómo obtenerla |
|---|---|---|
| `CRYPTOPANIC_API_KEY` | Noticias de CryptoPanic | Registrarte en [cryptopanic.com/developers/api](https://cryptopanic.com/developers/api/) |
| `NEWSAPI_KEY` | Titulares financieros | Registrarte en [newsapi.org](https://newsapi.org/) |
| `BINANCE_API_KEY` | API de Binance (no necesaria para datos públicos) | [binance.com](https://www.binance.com/) |
| `BINANCE_API_SECRET` | Secret de Binance | Junto con la API key |

### De aplicación

| Variable | Descripción | Default |
|---|---|---|
| `DEBUG` | Modo debug | `True` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |

> **Nota:** Si no configurás `CRYPTOPANIC_API_KEY` o `NEWSAPI_KEY`, esas fuentes de sentimiento no funcionarán, pero el bot seguirá operando con las fuentes disponibles (Fear & Greed Index no requiere clave).

---

## Comandos útiles

### Gestión de servicios

```bash
# Levantar todos los servicios
docker-compose up -d

# Parar todos los servicios
docker-compose down

# Parar y eliminar volúmenes (borra la base de datos)
docker-compose down -v

# Reconstruir imágenes (después de cambiar requirements.txt o Dockerfile)
docker-compose up -d --build

# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Reiniciar un servicio
docker-compose restart backend
```

### Base de datos

```bash
# Conectarse a PostgreSQL
docker-compose exec db psql -U crypto_user -d crypto_bot

# Ver tablas
docker-compose exec db psql -U crypto_user -d crypto_bot -c "\dt"

# Contar registros de precios
docker-compose exec db psql -U crypto_user -d crypto_bot \
  -c "SELECT COUNT(*) FROM price_history;"

# Backup de la base
docker-compose exec db pg_dump -U crypto_user crypto_bot > backup.sql

# Restaurar backup
cat backup.sql | docker-compose exec -T db psql -U crypto_user crypto_bot
```

### Frontend

```bash
# Instalar dependencias
cd frontend && npm install

# Desarrollo (hot reload)
npm run dev

# Build de producción
npm run build

# Preview del build
npm run preview

# Verificar tipos TypeScript
npx tsc --noEmit
```

---

## Dockerfile del backend

El Dockerfile instala TA-Lib (librería de análisis técnico en C) y las dependencias Python:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencias de sistema para TA-Lib
RUN apt-get update && apt-get install -y \
    build-essential wget \
    && rm -rf /var/lib/apt/lists/*

# Compilar TA-Lib desde fuente
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && ./configure --prefix=/usr && make && make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Dependencias principales

### Backend (Python)

| Paquete | Versión | Uso |
|---|---|---|
| `fastapi` | 0.109.0 | Framework API REST |
| `uvicorn` | 0.27.0 | Servidor ASGI |
| `sqlalchemy` | 2.0.25 | ORM para PostgreSQL |
| `alembic` | 1.13.1 | Migraciones de BD |
| `celery` | 5.3.6 | Cola de tareas |
| `redis` | 5.0.1 | Broker para Celery |
| `ccxt` | 4.2.25 | Datos de exchanges |
| `pandas` | 2.1.4 | Análisis de datos |
| `vaderSentiment` | 3.3.2 | NLP de sentimiento |
| `httpx` | 0.26.0 | Cliente HTTP async |
| `pydantic` | 2.5.3 | Validación de datos |
| `psycopg2-binary` | 2.9.9 | Driver PostgreSQL |

### Frontend (Node.js)

| Paquete | Versión | Uso |
|---|---|---|
| `react` | 19.2.0 | Framework UI |
| `react-router-dom` | 7.13.0 | Navegación SPA |
| `@tanstack/react-query` | 5.90.21 | Data fetching + cache |
| `axios` | 1.13.5 | Cliente HTTP |
| `recharts` | 3.7.0 | Gráficos |
| `tailwindcss` | 4.1.18 | Estilos CSS |
| `lucide-react` | 0.564.0 | Íconos |
| `vite` | 7.3.1 | Build tool |
| `typescript` | 5.9.3 | Tipado estático |
