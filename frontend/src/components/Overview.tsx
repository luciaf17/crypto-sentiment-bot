import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  BarChart3,
  Percent,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { usePriceData, useLatestSignal, useTradeStats, useActiveTrades, useSignalStats, useSentiment } from '../hooks/useApiData';
import { InfoTooltip } from './Tooltip';
import type { SignalAction } from '../types';

const ACTION_LABELS: Record<SignalAction, string> = {
  BUY: 'COMPRAR',
  SELL: 'VENDER',
  HOLD: 'MANTENER',
};

function SignalBadge({ action }: { action: SignalAction }) {
  const colors: Record<SignalAction, string> = {
    BUY: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    SELL: 'bg-red-500/20 text-red-400 border-red-500/30',
    HOLD: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  };
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${colors[action]}`}>
      {ACTION_LABELS[action]}
    </span>
  );
}

function SentimentGauge({ value }: { value: number }) {
  // value is -1 to 1, map to 0-100%
  const pct = ((value + 1) / 2) * 100;
  const color =
    value > 0.3 ? 'bg-emerald-500' : value < -0.3 ? 'bg-red-500' : 'bg-yellow-500';
  const label = value > 0.3 ? 'Alcista' : value < -0.3 ? 'Bajista' : 'Neutral';

  return (
    <div>
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>Bajista</span>
        <span>{label} ({value.toFixed(2)})</span>
        <span>Alcista</span>
      </div>
      <div className="h-3 bg-gray-700 rounded-full overflow-hidden relative">
        {/* Center marker */}
        <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-500 z-10" />
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'text-gray-300',
  subtext,
  tooltip,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color?: string;
  subtext?: string;
  tooltip?: string;
}) {
  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700/50 hover:border-gray-600/50 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-400">
          {label}
          {tooltip && <InfoTooltip text={tooltip} />}
        </span>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {subtext && <div className="text-xs text-gray-500 mt-1">{subtext}</div>}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      <span className="ml-3 text-gray-400">Cargando datos...</span>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-20 text-red-400">
      <AlertCircle className="w-6 h-6 mr-2" />
      <span>{message}</span>
    </div>
  );
}

export default function Overview() {
  const price = usePriceData();
  const signal = useLatestSignal();
  const tradeStats = useTradeStats();
  const activeTrades = useActiveTrades();
  const signalStats = useSignalStats();
  const sentiment = useSentiment();

  const isLoading = price.isLoading || signal.isLoading || tradeStats.isLoading;
  const error = price.error || signal.error || tradeStats.error;

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Error al cargar datos del panel. ¿El backend está corriendo?" />;

  const priceData = price.data!;
  const signalData = signal.data;
  const stats = tradeStats.data;
  const activeCount = activeTrades.data?.length ?? 0;
  const todaySignals = signalStats.data?.total_signals ?? 0;

  const avgSentiment =
    sentiment.data && sentiment.data.length > 0
      ? sentiment.data.reduce((sum, s) => sum + s.score, 0) / sentiment.data.length
      : 0;

  const priceChange = priceData.close - priceData.open;
  const priceChangePct = (priceChange / priceData.open) * 100;

  return (
    <div className="space-y-6">
      {/* Price + Signal Header */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* BTC Price */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
            <Activity className="w-4 h-4" />
            <span>{priceData.symbol}</span>
            <InfoTooltip text="Precio actual del par de trading. Se actualiza automáticamente cada 10 segundos." />
          </div>
          <div className="flex items-baseline gap-4">
            <span className="text-4xl lg:text-5xl font-bold text-white">
              ${priceData.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span
              className={`flex items-center gap-1 text-lg font-medium ${
                priceChange >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {priceChange >= 0 ? (
                <TrendingUp className="w-5 h-5" />
              ) : (
                <TrendingDown className="w-5 h-5" />
              )}
              {priceChange >= 0 ? '+' : ''}
              {priceChangePct.toFixed(2)}%
            </span>
          </div>
          <div className="flex gap-6 mt-4 text-sm text-gray-400">
            <span>
              Máx: <span className="text-emerald-400">${priceData.high.toLocaleString()}</span>
            </span>
            <span>
              Mín: <span className="text-red-400">${priceData.low.toLocaleString()}</span>
            </span>
            <span>
              Vol: <span className="text-gray-300">{(priceData.volume / 1e6).toFixed(1)}M</span>
            </span>
          </div>
        </div>

        {/* Latest Signal */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700/50">
          <div className="text-sm text-gray-400 mb-3">
            Última Señal
            <InfoTooltip text="Señal de trading más reciente generada por el bot basada en indicadores técnicos y sentimiento." />
          </div>
          {signalData ? (
            <>
              <div className="flex items-center gap-3 mb-4">
                <SignalBadge action={signalData.action} />
                <span className="text-gray-300 text-sm">
                  {(signalData.confidence * 100).toFixed(0)}% confianza
                  <InfoTooltip text="Nivel de confianza de la señal (0-100%). Mayor valor = más condiciones técnicas cumplidas." />
                </span>
              </div>
              <div className="text-sm text-gray-400 space-y-1">
                <div>
                  Precio: ${signalData.price_at_signal.toLocaleString()}
                </div>
                {signalData.technical_indicators.rsi !== undefined && (
                  <div>
                    RSI: {Number(signalData.technical_indicators.rsi).toFixed(1)}
                    <InfoTooltip text="Índice de Fuerza Relativa. Mide si el activo está sobrecomprado (>70) o sobrevendido (<30)." />
                  </div>
                )}
                <div className="text-xs text-gray-500 mt-2">
                  {new Date(signalData.timestamp).toLocaleString()}
                </div>
              </div>
            </>
          ) : (
            <div className="text-gray-500">Sin señales aún</div>
          )}
        </div>
      </div>

      {/* Sentiment Gauge */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700/50">
        <div className="text-sm text-gray-400 mb-3">
          Sentimiento del Mercado
          <InfoTooltip text="Puntuación de sentimiento basada en noticias y redes sociales. Escala -1 (muy negativo) a +1 (muy positivo)." />
        </div>
        <SentimentGauge value={avgSentiment} />
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="G/P Total"
          value={`$${(stats?.total_pnl ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          icon={DollarSign}
          color={(stats?.total_pnl ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}
          subtext={`${(stats?.total_pnl_percent ?? 0).toFixed(2)}%`}
          tooltip="Ganancia o Pérdida total acumulada de todas las operaciones cerradas."
        />
        <StatCard
          label="Tasa de Aciertos"
          value={`${(stats?.win_rate ?? 0).toFixed(1)}%`}
          icon={Percent}
          color="text-blue-400"
          subtext={`${stats?.winning_trades ?? 0}G / ${stats?.losing_trades ?? 0}P`}
          tooltip="Porcentaje de operaciones ganadoras. >60% se considera bueno."
        />
        <StatCard
          label="Operaciones Activas"
          value={String(activeCount)}
          icon={BarChart3}
          color="text-purple-400"
          tooltip="Número de operaciones abiertas actualmente en el mercado."
        />
        <StatCard
          label="Total Señales"
          value={String(todaySignals)}
          icon={Activity}
          color="text-cyan-400"
          tooltip="Cantidad total de señales generadas por el bot."
        />
      </div>
    </div>
  );
}
