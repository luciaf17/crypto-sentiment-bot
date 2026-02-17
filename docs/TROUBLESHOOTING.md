# Solución de Problemas

## Problemas comunes

### El frontend no carga datos

**Síntoma:** El dashboard muestra "Cargando..." indefinidamente o errores en la consola del navegador.

**Causa más probable:** Error de CORS (Cross-Origin Resource Sharing).

**Solución:**

1. Verificá que el backend esté corriendo:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Verificá la configuración CORS en `backend/app/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",
           "http://localhost:5173",
           "http://localhost:8080",
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. Si accedés al frontend desde `http://127.0.0.1:5173` en vez de `http://localhost:5173`, agregá esa URL a la lista de orígenes permitidos:
   ```python
   allow_origins=[
       "http://localhost:3000",
       "http://localhost:5173",
       "http://localhost:8080",
       "http://127.0.0.1:5173",
   ],
   ```

4. Asegurate de abrir el frontend siempre desde `http://localhost:5173` (no `127.0.0.1`).

---

### No hay datos de precios

**Síntoma:** El gráfico está vacío, no hay precios.

**Verificación:**
```bash
# ¿Hay datos en la base?
docker-compose exec db psql -U crypto_user -d crypto_bot \
  -c "SELECT COUNT(*) FROM price_history;"

# ¿El worker de Celery está corriendo?
docker-compose logs celery_worker | tail -20

# ¿Celery Beat está programando tareas?
docker-compose logs celery_beat | tail -20
```

**Posibles causas:**

| Causa | Solución |
|---|---|
| Celery worker no está corriendo | `docker-compose restart celery_worker` |
| Celery Beat no está corriendo | `docker-compose restart celery_beat` |
| Error de conexión a Binance | Verificar conexión a internet del contenedor |
| Base de datos vacía | Esperar 5 minutos para el primer dato |

---

### No hay datos de sentimiento

**Síntoma:** Sentimiento muestra 0 o no hay datos.

**Verificación:**
```bash
docker-compose exec db psql -U crypto_user -d crypto_bot \
  -c "SELECT source, COUNT(*) FROM sentiment_scores GROUP BY source;"
```

**Posibles causas:**

| Causa | Solución |
|---|---|
| `CRYPTOPANIC_API_KEY` no configurada | Agregar clave en `.env` |
| `NEWSAPI_KEY` no configurada | Agregar clave en `.env` |
| Rate limit de NewsAPI (100/día plan gratis) | Esperar al día siguiente |
| Fear & Greed API caída | Es raro pero posible, esperar |

> **Nota:** Si no tenés API keys de CryptoPanic o NewsAPI, el bot solo usará el Fear & Greed Index (que no requiere clave).

---

### Las señales son siempre HOLD

**Síntoma:** Todas las señales generadas son HOLD, nunca BUY ni SELL.

**Esto es normal en la mayoría de los casos.** El bot genera señal de BUY solo cuando se cumplen las 3 condiciones simultáneamente:

1. RSI < umbral de compra (ej: < 35)
2. Sentimiento > mínimo (ej: > 0.05)
3. Precio < MA(50)

Si el mercado está en zona neutral, estas condiciones rara vez se dan. Aproximadamente el 78% de las señales son HOLD.

**Si querés más señales de BUY/SELL:**
- Aumentá la agresividad de la estrategia (slider hacia la derecha)
- Una agresividad de 70-80% genera más señales (pero con menor precisión)

---

### Error de conexión a la base de datos

**Síntoma:** El backend devuelve errores `500` o no arranca.

**Verificación:**
```bash
# ¿PostgreSQL está corriendo?
docker-compose ps db

# ¿Se puede conectar?
docker-compose exec db pg_isready -U crypto_user -d crypto_bot
```

**Soluciones:**

```bash
# Reiniciar la base de datos
docker-compose restart db

# Esperar a que arranque y luego reiniciar el backend
sleep 5
docker-compose restart backend

# Si hay error de migraciones
docker-compose exec backend alembic upgrade head
```

---

### Error de conexión a Redis

**Síntoma:** Celery no procesa tareas, errores de conexión en los logs.

**Verificación:**
```bash
# ¿Redis está corriendo?
docker-compose exec redis redis-cli ping
# Debería responder: PONG
```

**Solución:**
```bash
docker-compose restart redis
docker-compose restart celery_worker celery_beat
```

---

### Backtest devuelve error

**Síntoma:** El backtest falla o devuelve `"status": "error"`.

**Posibles causas:**

| Causa | Solución |
|---|---|
| No hay suficientes datos históricos | Necesitás al menos 250 velas (≈21 horas) para calcular RSI y MAs. Esperá a que se acumulen datos. |
| Rango de fechas sin datos | Usá fechas donde el bot estuvo recolectando precios |
| Parámetros inválidos | RSI debe ser 0-100, SL/TP > 0 |

**Verificar datos disponibles:**
```bash
docker-compose exec db psql -U crypto_user -d crypto_bot \
  -c "SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM price_history;"
```

---

### El puerto 5433 o 8000 ya está en uso

**Síntoma:** `docker-compose up` falla con "port already in use".

**Solución:**

```bash
# Ver qué proceso usa el puerto (Linux/Mac)
lsof -i :8000

# En Windows
netstat -ano | findstr :8000

# Opción 1: Matar el proceso
kill <PID>

# Opción 2: Cambiar el puerto en docker-compose.yml
# Ej: "8001:8000" para mapear al puerto 8001
```

---

### Los contenedores se reinician constantemente

**Síntoma:** `docker-compose ps` muestra contenedores en estado "Restarting".

**Diagnóstico:**
```bash
# Ver logs del contenedor problemático
docker-compose logs --tail 50 <nombre_servicio>
```

**Causas comunes:**

| Servicio | Causa típica | Solución |
|---|---|---|
| `backend` | Error de importación Python | Revisar `requirements.txt`, reconstruir con `--build` |
| `celery_worker` | Falta conexión a Redis/DB | Asegurar que `db` y `redis` estén healthy primero |
| `celery_beat` | Archivo schedule corrupto | Borrar `backend/celerybeat-schedule` y reiniciar |

---

### El frontend muestra datos desactualizados

**Síntoma:** Los datos no se actualizan o muestran información vieja.

**Posibles causas:**

1. **React Query cache:** Hacé hard refresh en el navegador (Ctrl+Shift+R)
2. **Celery Beat detenido:** Verificá que esté corriendo
3. **Worker saturado:** Revisá los logs del worker

```bash
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

---

## Logs y debugging

### Ver todos los logs

```bash
docker-compose logs -f
```

### Logs de un servicio específico

```bash
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### Consultas útiles de diagnóstico

```sql
-- Últimos 5 precios registrados
SELECT timestamp, price FROM price_history ORDER BY timestamp DESC LIMIT 5;

-- Últimas 5 señales
SELECT timestamp, action, confidence FROM signals ORDER BY timestamp DESC LIMIT 5;

-- Trades abiertos
SELECT * FROM trades WHERE status = 'OPEN';

-- Estrategia activa
SELECT name, aggressiveness, activated_at FROM strategy_configs WHERE is_active = true;

-- Sentimiento por fuente (últimas 2 horas)
SELECT source, AVG(score), COUNT(*)
FROM sentiment_scores
WHERE timestamp > NOW() - INTERVAL '2 hours'
GROUP BY source;
```

### Reiniciar todo desde cero

```bash
# Parar todo y borrar volúmenes (BORRA LA BASE DE DATOS)
docker-compose down -v

# Reconstruir y levantar
docker-compose up -d --build

# Ejecutar migraciones
docker-compose exec backend alembic upgrade head
```

> **Advertencia:** `docker-compose down -v` elimina todos los datos. Hacé un backup antes si los necesitás.
