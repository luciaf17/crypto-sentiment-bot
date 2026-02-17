# Dashboard (Frontend)

## Vista general

El dashboard es una Single Page Application (SPA) construida con React 19, TypeScript y Tailwind CSS. Se comunica con el backend FastAPI mediante peticiones HTTP y actualiza los datos automáticamente cada 10 segundos.

**URL de desarrollo:** `http://localhost:5173`

---

## Secciones del dashboard

### 1. Vista General (Overview)

La pantalla principal muestra un resumen del estado actual del bot:

| Elemento | Qué muestra | Fuente de datos |
|---|---|---|
| **Precio actual** | Precio de BTC/USDT con cambio 24h | `/api/prices/current` |
| **Última señal** | COMPRAR, VENDER o MANTENER con confianza | `/api/signals/current` |
| **Sentimiento** | Gauge visual de -1 (bajista) a +1 (alcista) | `/api/signals/current` |
| **G/P Total** | Ganancia/pérdida total del paper trading | `/api/trades/stats` |
| **Tasa de Aciertos** | Porcentaje de trades ganadores | `/api/trades/stats` |
| **Operaciones Activas** | Cantidad de trades abiertos ahora | `/api/trades/stats` |
| **Total Señales** | Cantidad total de señales generadas | `/api/signals/stats` |

Cada métrica tiene un **tooltip educativo** (ícono ⓘ) que explica qué significa y cómo interpretarla.

### 2. Gráficos (PriceChart)

Gráfico de líneas interactivo del precio de BTC/USDT:

- **Rangos de tiempo:** 4H, 12H, 24H, 3D, 7D
- **Medias móviles:** MA(7) y MA(25) superpuestas
- **Marcadores de señal:** Puntos verdes (compra) y rojos (venta) en el gráfico
- **Tooltip:** Muestra precio exacto y hora al pasar el cursor

Los datos vienen de `/api/prices/chart` y las señales de `/api/signals/latest`.

### 3. Señales (SignalsTable)

Tabla paginada con todas las señales generadas:

| Columna | Descripción |
|---|---|
| **Hora** | Fecha y hora de la señal |
| **Acción** | COMPRAR (verde), VENDER (rojo), MANTENER (amarillo) |
| **Confianza** | 0% a 100%, qué tan segura es la señal |
| **Precio** | Precio de BTC al momento de la señal |
| **RSI** | Valor del RSI cuando se generó |
| **Sentimiento** | Score de sentimiento (-1 a +1) |

Haciendo clic en una fila se expande mostrando:
- **Razones de la Señal:** Por qué se generó esa señal
- **Indicadores Técnicos:** Valores de RSI, MACD, medias móviles

Navegación con botones **Anterior** y **Siguiente**, mostrando 10 señales por página.

### 4. Operaciones (TradesTable)

Historial de paper trading con filtros y estadísticas:

**Filtros:**
- **Todas** — Muestra todas las operaciones
- **Abiertas** — Solo operaciones activas
- **Cerradas** — Solo operaciones finalizadas

**Estadísticas en la parte superior:**
- Total Operaciones, Tasa de Aciertos, G/P Total, Mejor Operación, Peor Operación

**Tabla:**

| Columna | Descripción |
|---|---|
| **Hora Entrada** | Cuándo se abrió la posición |
| **Precio Entrada** | Precio al abrir |
| **Precio Salida** | Precio al cerrar (vacío si está abierta) |
| **Cant.** | Cantidad de BTC (típicamente 0.1) |
| **G/P** | Ganancia/Pérdida en USD |
| **G/P %** | Ganancia/Pérdida en porcentaje |
| **Estado** | ABIERTA (azul) o CERRADA (gris) |

### 5. Sentimiento (SentimentBreakdown)

Desglose visual del análisis de sentimiento:

- **Índice de Miedo y Codicia:** Gauge circular de 0 a 100 con clasificación (Miedo Extremo, Miedo, Neutral, Codicia, Codicia Extrema)
- **Fuentes individuales:** Barras de sentimiento para CryptoPanic y NewsAPI
- **Promedio Ponderado:** Score combinado final (-1 a +1)
- **Razones de señales recientes:** Titulares y motivos que influyeron en las señales

### 6. Prueba Histórica (Backtest)

Interfaz completa para ejecutar backtests:

**Parámetros configurables:**

| Parámetro | Descripción | Default |
|---|---|---|
| Fecha Inicio | Inicio del período a probar | Hace 7 días |
| Fecha Fin | Fin del período | Hoy |
| RSI Sobrevendido | Umbral de compra | 30 |
| RSI Sobrecomprado | Umbral de venta | 70 |
| Stop Loss % | Pérdida máxima tolerada | 3% |
| Take Profit % | Ganancia objetivo | 5% |
| Tamaño Posición | BTC por operación | 0.1 |
| Balance Inicial | Capital simulado | $10,000 |

**Resultados:**
- Grilla de métricas: G/P Total, Tasa de Aciertos, Total Operaciones, Factor de Ganancia, Sharpe Ratio, Máx. Drawdown, Balance Final, Duración Promedio
- **Curva de Capital:** Gráfico de líneas mostrando la evolución del balance
- **Tabla de operaciones:** Cada trade del backtest con entrada, salida, G/P y razón de cierre

### 7. Estrategia (StrategyTuner)

Herramienta para configurar y optimizar la estrategia de trading:

**Estrategia activa:** Muestra nombre, agresividad y fecha de activación de la estrategia actual.

**Slider de agresividad:** Control deslizante de 0% a 100% con tres zonas:
- 0-30%: Conservador
- 30-70%: Balanceado
- 70-100%: Agresivo

**Preview en tiempo real:** Al mover el slider, se actualizan automáticamente:
- RSI Compra / RSI Venta
- Sentimiento Mínimo / Peso Sentimiento
- Stop Loss % / Take Profit %
- Est. Trades/Día, Est. Tasa Aciertos, Nivel de Riesgo

**Acciones:**
- **Probar Primero** — Ejecuta un backtest rápido de 7 días con los parámetros seleccionados
- **Guardar y Activar** — Guarda la estrategia y la activa inmediatamente

**Modal de resultados:** Después del backtest rápido, muestra métricas y permite:
- **Activar Esta Estrategia** — Si los resultados son satisfactorios
- **Cerrar y Ajustar** — Para probar con otra agresividad

---

## Arquitectura técnica

### Stack

| Tecnología | Uso |
|---|---|
| React 19 | Framework de UI |
| TypeScript | Tipado estático |
| Vite | Build tool y dev server |
| Tailwind CSS | Estilos utilitarios |
| React Query | Data fetching con cache y polling |
| Recharts | Gráficos de precio y equity |
| React Router | Navegación entre secciones |
| Axios | Cliente HTTP |
| Lucide React | Librería de íconos |

### Polling automático

React Query (`@tanstack/react-query`) maneja la actualización automática de datos:

```typescript
const { data } = useQuery({
  queryKey: ['prices'],
  queryFn: () => axios.get('/api/prices/latest'),
  refetchInterval: 10000,  // Cada 10 segundos
});
```

Esto significa que **todos los datos del dashboard se actualizan cada 10 segundos** sin necesidad de recargar la página.

### Estructura de archivos

```
frontend/
├── src/
│   ├── App.tsx                  # Layout principal, navegación, routing
│   ├── main.tsx                 # Punto de entrada, providers
│   └── components/
│       ├── Tooltip.tsx          # Componente de tooltips educativos
│       ├── Overview.tsx         # Vista general con métricas clave
│       ├── PriceChart.tsx       # Gráfico de precio con señales
│       ├── SignalsTable.tsx     # Tabla paginada de señales
│       ├── TradesTable.tsx      # Historial de operaciones
│       ├── SentimentBreakdown.tsx # Desglose de sentimiento
│       ├── Backtest.tsx         # Interfaz de backtesting
│       └── StrategyTuner.tsx    # Configuración de estrategia
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

### Tooltips educativos

Cada métrica técnica tiene un tooltip que explica:
- **Qué es** el indicador o métrica
- **Cómo interpretarlo** en el contexto del trading
- **Valores de referencia** (qué es bueno, qué es malo)

Los tooltips usan el componente `InfoTooltip` que muestra un ícono ⓘ al lado del texto. Al pasar el cursor (o tocar en móvil), aparece la explicación.

---

## Temas de colores

| Elemento | Color | Significado |
|---|---|---|
| Verde (`green-*`) | Positivo | Compra, ganancia, sentimiento alcista |
| Rojo (`red-*`) | Negativo | Venta, pérdida, sentimiento bajista |
| Amarillo (`yellow-*`) | Neutral | HOLD, precaución, agresividad alta |
| Azul (`blue-*`) | Informativo | Trade abierto, enlace, botón primario |
| Gris (`gray-*`) | Inactivo | Trade cerrado, datos secundarios |
