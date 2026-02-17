import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { InfoTooltip } from './Tooltip';

const API_URL = 'http://localhost:8000/api';

interface StrategyParams {
  rsi_buy: number;
  rsi_sell: number;
  sentiment_weight: number;
  sentiment_min: number;
  min_confidence: number;
  stop_loss_percent: number;
  take_profit_percent: number;
}

interface StrategyPreview {
  aggressiveness: number;
  parameters: StrategyParams;
  estimated_trades_per_day: number;
  estimated_win_rate: number;
  risk_level: string;
}

interface Strategy {
  id: number;
  name: string;
  aggressiveness: number;
  parameters: StrategyParams;
  is_active: boolean;
  description: string | null;
  created_by: string | null;
  created_at: string;
  activated_at: string | null;
}

interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_pnl_percent: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number | null;
  max_drawdown: number;
  max_drawdown_percent: number;
  sharpe_ratio: number | null;
  best_trade: number;
  worst_trade: number;
  avg_hold_duration_hours: number | null;
  final_balance: number;
}

interface BacktestResult {
  id: number | null;
  status: string;
  symbol: string;
  period_start: string | null;
  period_end: string | null;
  data_points: number;
  parameters: Record<string, number>;
  metrics: BacktestMetrics;
  trades: unknown[];
  error_reason: string | null;
}

interface ActiveStrategyComparison {
  active_strategy_name: string;
  active_pnl: number;
  active_pnl_percent: number;
  active_win_rate: number;
  active_total_trades: number;
  active_sharpe_ratio: number | null;
  pnl_difference: number;
  pnl_percent_difference: number;
  win_rate_difference: number;
  is_better: boolean;
}

interface QuickBacktestResponse {
  result: BacktestResult;
  comparison: ActiveStrategyComparison | null;
}

const RISK_LABELS: Record<string, string> = {
  Low: 'Bajo',
  Medium: 'Medio',
  High: 'Alto',
};

export default function StrategyTuner() {
  const [aggressiveness, setAggressiveness] = useState(50);
  const [preview, setPreview] = useState<StrategyPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [strategyName, setStrategyName] = useState('');
  const [activeStrategy, setActiveStrategy] = useState<Strategy | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Backtest state
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState<QuickBacktestResponse | null>(null);
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const [showBacktestResults, setShowBacktestResults] = useState(false);

  const fetchActiveStrategy = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_URL}/strategy/current`);
      setActiveStrategy(data);
    } catch {
      setActiveStrategy(null);
    }
  }, []);

  const fetchStrategies = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_URL}/strategy/list`);
      setStrategies(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchActiveStrategy();
    fetchStrategies();
  }, [fetchActiveStrategy, fetchStrategies]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const { data } = await axios.post(`${API_URL}/strategy/preview`, {
          aggressiveness,
        });
        setPreview(data);
      } catch {
        console.error('Failed to fetch preview');
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [aggressiveness]);

  const handleSaveAndActivate = async () => {
    if (!strategyName.trim()) {
      setError('Ingresa un nombre para la estrategia');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const { data: created } = await axios.post(`${API_URL}/strategy/create`, {
        name: strategyName,
        aggressiveness,
        description: `Estrategia personalizada con ${aggressiveness}% de agresividad`,
      });

      await axios.post(`${API_URL}/strategy/activate`, {
        strategy_id: created.id,
      });

      setActiveStrategy({ ...created, is_active: true });
      setStrategyName('');
      await fetchStrategies();
    } catch {
      setError('Error al guardar estrategia. Verifica la conexión con el backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleActivateExisting = async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post(`${API_URL}/strategy/activate`, {
        strategy_id: id,
      });
      setActiveStrategy(data);
      await fetchStrategies();
    } catch {
      setError('Error al activar estrategia');
    } finally {
      setLoading(false);
    }
  };

  const handleBacktest = async () => {
    if (!preview) return;

    setBacktestLoading(true);
    setBacktestError(null);
    setBacktestResult(null);
    setShowBacktestResults(true);

    try {
      const { data } = await axios.post<QuickBacktestResponse>(
        `${API_URL}/backtest/quick`,
        {
          strategy_params: preview.parameters,
          days: 7,
        }
      );

      if (data.result.status === 'error') {
        setBacktestError(
          data.result.error_reason || 'La prueba falló — datos históricos insuficientes.'
        );
      } else {
        setBacktestResult(data);
      }
    } catch {
      setBacktestError('Error al ejecutar prueba. Verifica la conexión con el backend y que haya datos históricos disponibles.');
    } finally {
      setBacktestLoading(false);
    }
  };

  const handleActivateFromBacktest = async () => {
    if (!strategyName.trim()) {
      setError('Ingresa un nombre para la estrategia antes de activarla');
      setShowBacktestResults(false);
      return;
    }
    setShowBacktestResults(false);
    await handleSaveAndActivate();
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'text-green-400';
      case 'Medium': return 'text-yellow-400';
      case 'High': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getRiskBg = (risk: string) => {
    switch (risk) {
      case 'Low': return 'bg-green-500/10 border-green-500/20';
      case 'Medium': return 'bg-yellow-500/10 border-yellow-500/20';
      case 'High': return 'bg-red-500/10 border-red-500/20';
      default: return 'bg-gray-500/10 border-gray-500/20';
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return 'N/D';
    return new Date(iso).toLocaleDateString();
  };

  const formatPnl = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${value.toFixed(2)}`;
  };

  const pnlColor = (value: number) => (value >= 0 ? 'text-emerald-400' : 'text-red-400');

  const sliderGradient =
    aggressiveness < 30
      ? 'accent-green-500'
      : aggressiveness < 70
        ? 'accent-yellow-500'
        : 'accent-red-500';

  return (
    <div className="space-y-6">
      {/* Active Strategy Banner */}
      {activeStrategy && (
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-blue-400 font-medium uppercase tracking-wider">Estrategia Activa</div>
            <div className="text-white font-semibold mt-1">{activeStrategy.name}</div>
            <div className="text-sm text-gray-400 mt-0.5">
              Agresividad: {activeStrategy.aggressiveness}% &middot; Activada{' '}
              {activeStrategy.activated_at
                ? new Date(activeStrategy.activated_at).toLocaleString()
                : 'N/D'}
            </div>
          </div>
          <div className="text-2xl font-bold text-blue-400">{activeStrategy.aggressiveness}%</div>
        </div>
      )}

      {/* Strategy Tuner Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Ajuste de Estrategia</h2>

        {/* Aggressiveness Slider */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-3">
            <label className="text-sm font-medium text-gray-400">
              Agresividad
              <InfoTooltip text="Controla la frecuencia de operaciones. Conservador = pocos trades precisos con alto win rate. Agresivo = muchos trades con más riesgo." />
            </label>
            <span className="text-3xl font-bold text-white">{aggressiveness}%</span>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            value={aggressiveness}
            onChange={(e) => setAggressiveness(Number(e.target.value))}
            className={`w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer ${sliderGradient}`}
          />

          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>Conservador</span>
            <span>Balanceado</span>
            <span>Agresivo</span>
          </div>
        </div>

        {/* Preview Cards */}
        {preview && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wider">Est. Trades/Día</div>
              <div className="text-2xl font-bold text-white mt-1">{preview.estimated_trades_per_day}</div>
            </div>

            <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wider">
                Est. Tasa Aciertos
                <InfoTooltip text="Porcentaje estimado de operaciones ganadoras con esta configuración." />
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                {(preview.estimated_win_rate * 100).toFixed(0)}%
              </div>
            </div>

            <div className={`rounded-lg p-4 border ${getRiskBg(preview.risk_level)}`}>
              <div className="text-xs text-gray-500 uppercase tracking-wider">Nivel de Riesgo</div>
              <div className={`text-2xl font-bold mt-1 ${getRiskColor(preview.risk_level)}`}>
                {RISK_LABELS[preview.risk_level] ?? preview.risk_level}
              </div>
            </div>

            <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wider">
                Confianza Mín.
                <InfoTooltip text="Nivel mínimo de confianza requerido para ejecutar una operación." />
              </div>
              <div className="text-2xl font-bold text-white mt-1">
                {preview.parameters.min_confidence.toFixed(2)}
              </div>
            </div>
          </div>
        )}

        {/* Technical Parameters */}
        {preview && (
          <div className="bg-gray-800/30 border border-gray-700/50 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">
              Parámetros Técnicos
            </h3>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">
                  RSI Compra
                  <InfoTooltip text="Umbral RSI para señales de compra. Si el RSI cae por debajo de este valor, se considera sobrevendido." />
                </span>
                <span className="font-mono text-white">&lt; {preview.parameters.rsi_buy.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">
                  RSI Venta
                  <InfoTooltip text="Umbral RSI para señales de venta. Si el RSI sube por encima de este valor, se considera sobrecomprado." />
                </span>
                <span className="font-mono text-white">&gt; {preview.parameters.rsi_sell.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">
                  Sentimiento Mín.
                  <InfoTooltip text="Puntuación mínima de sentimiento requerida para confirmar señales de compra." />
                </span>
                <span className="font-mono text-white">{preview.parameters.sentiment_min.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">
                  Peso Sentimiento
                  <InfoTooltip text="Importancia del sentimiento del mercado en la decisión de trading (0-100%)." />
                </span>
                <span className="font-mono text-white">
                  {(preview.parameters.sentiment_weight * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">
                  Stop Loss
                  <InfoTooltip text="Pérdida máxima permitida antes de cerrar automáticamente. Protege tu capital limitando pérdidas." />
                </span>
                <span className="font-mono text-red-400">
                  {preview.parameters.stop_loss_percent.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">
                  Take Profit
                  <InfoTooltip text="Ganancia objetivo antes de cerrar automáticamente. Asegura ganancias cuando el precio alcanza tu meta." />
                </span>
                <span className="font-mono text-emerald-400">
                  {preview.parameters.take_profit_percent.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* High Risk Warning */}
        {aggressiveness > 70 && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3">
            <span className="text-red-400 text-lg leading-none mt-0.5">!</span>
            <div className="text-sm text-red-300">
              <strong>Advertencia de Alto Riesgo:</strong> Las estrategias agresivas operan con mayor frecuencia y
              umbrales más amplios. Esto aumenta la exposición y puede resultar en menores tasas de aciertos. Monitorea las posiciones de cerca.
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Save Section */}
        <div className="border-t border-gray-800 pt-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-400 mb-2">Nombre de Estrategia</label>
            <input
              type="text"
              value={strategyName}
              onChange={(e) => setStrategyName(e.target.value)}
              placeholder="ej. Mi Estrategia Agresiva"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleSaveAndActivate}
              disabled={loading || !strategyName.trim()}
              className="flex-1 bg-blue-600 text-white py-2.5 px-4 rounded-lg font-medium hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Guardando...' : 'Guardar y Activar Estrategia'}
            </button>

            <button
              className="px-4 py-2.5 border border-gray-700 text-gray-300 rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              disabled={backtestLoading || !preview}
              onClick={handleBacktest}
            >
              {backtestLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Probando...
                </span>
              ) : (
                'Probar Primero'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Backtest Results Modal/Section */}
      {showBacktestResults && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white">Resultados de Prueba</h2>
                <button
                  onClick={() => setShowBacktestResults(false)}
                  className="text-gray-400 hover:text-white transition-colors text-xl leading-none"
                >
                  &times;
                </button>
              </div>

              {/* Loading State */}
              {backtestLoading && (
                <div className="flex flex-col items-center justify-center py-16">
                  <svg className="animate-spin h-10 w-10 text-blue-400 mb-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <p className="text-gray-400 text-sm">Probando contra los últimos 7 días de datos...</p>
                  <p className="text-gray-600 text-xs mt-1">Esto puede tomar 5-10 segundos</p>
                </div>
              )}

              {/* Error State */}
              {backtestError && !backtestLoading && (
                <div className="py-8">
                  <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400 mb-6">
                    {backtestError}
                  </div>
                  <div className="flex justify-end">
                    <button
                      onClick={() => setShowBacktestResults(false)}
                      className="px-4 py-2 border border-gray-700 text-gray-300 rounded-lg hover:bg-gray-800 transition-colors"
                    >
                      Cerrar
                    </button>
                  </div>
                </div>
              )}

              {/* Results */}
              {backtestResult && !backtestLoading && (
                <div className="space-y-5">
                  {/* Period */}
                  <div className="text-sm text-gray-400">
                    Período: {formatDate(backtestResult.result.period_start)} &mdash;{' '}
                    {formatDate(backtestResult.result.period_end)} &middot;{' '}
                    {backtestResult.result.data_points} puntos de datos
                  </div>

                  {/* Profitability Banner */}
                  {(() => {
                    const m = backtestResult.result.metrics;
                    const profitable = m.total_pnl >= 0;
                    return (
                      <div
                        className={`p-4 rounded-lg border ${
                          profitable
                            ? 'bg-emerald-500/10 border-emerald-500/20'
                            : 'bg-red-500/10 border-red-500/20'
                        }`}
                      >
                        <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">
                          G/P Total
                        </div>
                        <div className={`text-3xl font-bold ${pnlColor(m.total_pnl)}`}>
                          {formatPnl(m.total_pnl)}{' '}
                          <span className="text-lg">({m.total_pnl_percent >= 0 ? '+' : ''}{m.total_pnl_percent.toFixed(2)}%)</span>
                        </div>
                        <div className="text-sm text-gray-400 mt-1">
                          {profitable
                            ? 'Esta estrategia habría sido rentable'
                            : 'Esta estrategia habría perdido dinero'}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                      <div className="text-xs text-gray-500 uppercase">
                        Tasa de Aciertos
                        <InfoTooltip text="Porcentaje de operaciones ganadoras. >60% se considera bueno." />
                      </div>
                      <div className="text-xl font-bold text-white mt-1">
                        {backtestResult.result.metrics.win_rate.toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        {backtestResult.result.metrics.winning_trades}G / {backtestResult.result.metrics.losing_trades}P
                      </div>
                    </div>

                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                      <div className="text-xs text-gray-500 uppercase">Total Operaciones</div>
                      <div className="text-xl font-bold text-white mt-1">
                        {backtestResult.result.metrics.total_trades}
                      </div>
                    </div>

                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                      <div className="text-xs text-gray-500 uppercase">
                        Máx. Drawdown
                        <InfoTooltip text="Máxima pérdida desde un pico hasta un valle. Mide el peor escenario posible." />
                      </div>
                      <div className="text-xl font-bold text-red-400 mt-1">
                        ${backtestResult.result.metrics.max_drawdown.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {backtestResult.result.metrics.max_drawdown_percent.toFixed(1)}%
                      </div>
                    </div>

                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                      <div className="text-xs text-gray-500 uppercase">
                        Sharpe Ratio
                        <InfoTooltip text="Retorno ajustado por riesgo. >1 es bueno, >2 es excelente. Valores negativos indican pérdidas." />
                      </div>
                      <div className="text-xl font-bold text-white mt-1">
                        {backtestResult.result.metrics.sharpe_ratio?.toFixed(2) ?? 'N/D'}
                      </div>
                    </div>

                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                      <div className="text-xs text-gray-500 uppercase">Mejor Operación</div>
                      <div className={`text-xl font-bold mt-1 ${pnlColor(backtestResult.result.metrics.best_trade)}`}>
                        {formatPnl(backtestResult.result.metrics.best_trade)}
                      </div>
                    </div>

                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                      <div className="text-xs text-gray-500 uppercase">Peor Operación</div>
                      <div className={`text-xl font-bold mt-1 ${pnlColor(backtestResult.result.metrics.worst_trade)}`}>
                        {formatPnl(backtestResult.result.metrics.worst_trade)}
                      </div>
                    </div>
                  </div>

                  {/* Comparison with Active Strategy */}
                  {backtestResult.comparison && (
                    <div
                      className={`p-4 rounded-lg border ${
                        backtestResult.comparison.is_better
                          ? 'bg-emerald-500/5 border-emerald-500/20'
                          : 'bg-amber-500/5 border-amber-500/20'
                      }`}
                    >
                      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
                        vs. Estrategia Activa: {backtestResult.comparison.active_strategy_name}
                      </h3>
                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <div>
                          <div className="text-xs text-gray-500">Diferencia G/P</div>
                          <div className={`font-bold ${pnlColor(backtestResult.comparison.pnl_difference)}`}>
                            {formatPnl(backtestResult.comparison.pnl_difference)}
                          </div>
                          <div className={`text-xs ${pnlColor(backtestResult.comparison.pnl_percent_difference)}`}>
                            {backtestResult.comparison.pnl_percent_difference >= 0 ? '+' : ''}
                            {backtestResult.comparison.pnl_percent_difference.toFixed(2)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">Dif. Tasa Aciertos</div>
                          <div className={`font-bold ${pnlColor(backtestResult.comparison.win_rate_difference)}`}>
                            {backtestResult.comparison.win_rate_difference >= 0 ? '+' : ''}
                            {backtestResult.comparison.win_rate_difference.toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">G/P Activa</div>
                          <div className={`font-bold ${pnlColor(backtestResult.comparison.active_pnl)}`}>
                            {formatPnl(backtestResult.comparison.active_pnl)}
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 text-sm">
                        {backtestResult.comparison.is_better ? (
                          <span className="text-emerald-400">
                            Esta estrategia habría rendido{' '}
                            <strong>{formatPnl(backtestResult.comparison.pnl_difference)}</strong> mejor
                            que la estrategia activa actual.
                          </span>
                        ) : (
                          <span className="text-amber-400">
                            Esta estrategia habría rendido{' '}
                            <strong>${Math.abs(backtestResult.comparison.pnl_difference).toFixed(2)}</strong> peor
                            que la estrategia activa actual.
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-2 border-t border-gray-800">
                    <button
                      onClick={() => setShowBacktestResults(false)}
                      className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-lg hover:bg-gray-800 transition-colors"
                    >
                      Cerrar y Ajustar
                    </button>
                    <button
                      onClick={handleActivateFromBacktest}
                      disabled={loading}
                      className="flex-1 bg-blue-600 text-white py-2.5 px-4 rounded-lg font-medium hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      {loading ? 'Activando...' : 'Activar Esta Estrategia'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Saved Strategies List */}
      {strategies.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Estrategias Guardadas</h2>
          <div className="space-y-2">
            {strategies.map((s) => (
              <div
                key={s.id}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  s.is_active
                    ? 'bg-blue-500/10 border-blue-500/30'
                    : 'bg-gray-800/30 border-gray-700/50 hover:bg-gray-800/60'
                } transition-colors`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{s.name}</span>
                    {s.is_active && (
                      <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">
                        Activa
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {s.aggressiveness}% agresividad &middot;{' '}
                    {new Date(s.created_at).toLocaleDateString()}
                  </div>
                </div>
                {!s.is_active && (
                  <button
                    onClick={() => handleActivateExisting(s.id)}
                    disabled={loading}
                    className="text-sm text-blue-400 hover:text-blue-300 font-medium disabled:opacity-40"
                  >
                    Activar
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
