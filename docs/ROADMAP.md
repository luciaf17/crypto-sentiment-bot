# Roadmap (Hoja de Ruta)

## Estado actual

### Funcionalidades implementadas

| Funcionalidad | Estado | Descripción |
|---|---|---|
| Recolección de precios | Implementado | Velas OHLCV de BTC/USDT cada 5 min via Binance/ccxt |
| Análisis de sentimiento | Implementado | CryptoPanic + NewsAPI + Fear & Greed Index |
| Indicadores técnicos | Implementado | RSI (14), MACD (12/26/9), MA (20/50/200) |
| Generación de señales | Implementado | BUY/SELL/HOLD cada hora con 3 condiciones |
| Paper trading | Implementado | Ejecución simulada con Stop Loss y Take Profit |
| Dashboard React | Implementado | 7 secciones con gráficos interactivos |
| Sistema de estrategias | Implementado | Slider de agresividad 0-100% con 7 parámetros |
| Backtesting | Implementado | Motor completo con métricas, curva de capital y comparación |
| Tooltips educativos | Implementado | Explicaciones en español de todos los indicadores |
| Documentación en español | Implementado | Documentación completa del sistema |

### Limitaciones conocidas

- Solo opera con el par **BTC/USDT**
- **Paper trading** únicamente (no ejecuta trades reales)
- El sentimiento de NewsAPI tiene delay de algunas horas
- Fear & Greed Index se actualiza solo 1 vez por día
- Plan gratuito de NewsAPI: 100 peticiones por día
- No tiene autenticación de usuarios
- No envía notificaciones de señales

---

## Mejoras a corto plazo

### Soporte multi-moneda

Permitir seguir múltiples pares (ETH/USDT, SOL/USDT, etc.):
- Selección de par desde el dashboard
- Recolección de precios para cada par
- Señales y trades independientes por moneda

### Notificaciones

Alertas cuando se genera una señal de BUY o SELL:
- Notificaciones del navegador (Web Push)
- Integración con Telegram Bot
- Email (opcional)

### Más indicadores técnicos

- **Bollinger Bands:** Bandas de volatilidad para detectar rupturas
- **EMA:** Medias exponenciales además de las simples
- **Volume Profile:** Análisis de volumen por niveles de precio
- **ATR (Average True Range):** Volatilidad para ajustar SL/TP dinámicamente

### Mejoras al backtesting

- **Backtest multi-estrategia:** Probar varias configuraciones automáticamente y encontrar la óptima
- **Walk-forward analysis:** Dividir datos en entrenamiento y validación
- **Comisiones simuladas:** Incluir fees de exchange en las métricas
- **Slippage:** Simular el deslizamiento de precio en la ejecución

---

## Mejoras a mediano plazo

### Trading real (con precaución)

Conectar con Binance para ejecutar trades reales:
- Modo "semi-automático": el bot sugiere, el usuario confirma
- Límites de capital máximo
- Kill switch de emergencia
- Logging detallado de cada operación real

> **Importante:** Esto requiere un sistema de seguridad robusto antes de implementarse.

### Más fuentes de sentimiento

- **Reddit:** Análisis de r/Bitcoin y r/CryptoCurrency
- **Twitter/X:** Monitoreo de cuentas influyentes
- **YouTube:** Detección de tendencias en títulos de videos cripto
- **Google Trends:** Búsquedas relacionadas con Bitcoin

### Autenticación de usuarios

- Login con usuario y contraseña
- Múltiples usuarios con estrategias independientes
- Roles: admin, trader, viewer

### Machine Learning

- Modelo entrenado con datos históricos para mejorar predicciones
- Feature engineering con indicadores técnicos + sentimiento
- Evaluación continua del modelo vs estrategia basada en reglas

---

## Mejoras a largo plazo

### Portfolio management

- Gestión de múltiples posiciones simultáneas
- Diversificación automática entre monedas
- Rebalanceo periódico
- Tracking de rendimiento por moneda

### Análisis on-chain

- Movimientos de ballenas (grandes transacciones)
- Flujos de exchanges (entrada/salida de BTC)
- Hash rate y dificultad de minería
- Métricas de red (direcciones activas, transacciones por día)

### API pública

- Endpoints autenticados para acceso externo
- Webhooks para integración con otros sistemas
- Rate limiting y planes de uso
- Documentación con OpenAPI/Swagger

### App móvil

- React Native o PWA
- Notificaciones push nativas
- Dashboard simplificado para pantallas pequeñas
- Ejecución rápida de operaciones

---

## Ideas de la comunidad

Si tenés ideas para mejorar el bot, podés:

1. Abrir un **issue** en el repositorio
2. Proponer un **pull request** con la mejora
3. Comentar en las discusiones del proyecto

Las contribuciones son bienvenidas, especialmente en:
- Nuevos indicadores técnicos
- Nuevas fuentes de sentimiento
- Mejoras de rendimiento
- Tests automatizados
- Mejoras de UI/UX
