import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Play, Loader2, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { runBacktest } from '../api/client';
import { InfoTooltip } from './Tooltip';
import type { BacktestRequest, BacktestResponse } from '../types';

const DEFAULT_PARAMS: BacktestRequest = {
  symbol: 'BTC/USDT',
  start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  end_date: new Date().toISOString(),
  strategy_params: {
    rsi_oversold: 30,
    rsi_overbought: 70,
    position_size: 0.1,
    stop_loss_percent: 2.0,
    take_profit_percent: 5.0,
    initial_balance: 100000,
  },
};

function ParamInput({
  label,
  value,
  onChange,
  step = 1,
  min,
  max,
  tooltip,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  max?: number;
  tooltip?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">
        {label}
        {tooltip && <InfoTooltip text={tooltip} />}
      </label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        step={step}
        min={min}
        max={max}
        className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500 transition-colors"
      />
    </div>
  );
}

export default function Backtest() {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const mutation = useMutation({
    mutationFn: runBacktest,
  });

  const updateStrategy = (key: string, value: number) => {
    setParams((p) => ({
      ...p,
      strategy_params: { ...p.strategy_params, [key]: value },
    }));
  };

  const result: BacktestResponse | undefined = mutation.data;

  return (
    <div className="space-y-6">
      {/* Parameters */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700/50">
        <h2 className="text-lg font-semibold text-white mb-4">Configuración de Prueba Histórica</h2>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Fecha Inicio</label>
            <input
              type="date"
              value={params.start_date.slice(0, 10)}
              onChange={(e) =>
                setParams((p) => ({ ...p, start_date: new Date(e.target.value).toISOString() }))
              }
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Fecha Fin</label>
            <input
              type="date"
              value={params.end_date.slice(0, 10)}
              onChange={(e) =>
                setParams((p) => ({ ...p, end_date: new Date(e.target.value).toISOString() }))
              }
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <ParamInput
            label="RSI Sobrevendido"
            value={params.strategy_params.rsi_oversold}
            onChange={(v) => updateStrategy('rsi_oversold', v)}
            min={10}
            max={50}
            tooltip="Índice de Fuerza Relativa. Valores por debajo de este umbral indican posible oportunidad de compra."
          />
          <ParamInput
            label="RSI Sobrecomprado"
            value={params.strategy_params.rsi_overbought}
            onChange={(v) => updateStrategy('rsi_overbought', v)}
            min={50}
            max={90}
            tooltip="Índice de Fuerza Relativa. Valores por encima de este umbral indican posible oportunidad de venta."
          />
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <ParamInput
            label="Tamaño Posición"
            value={params.strategy_params.position_size}
            onChange={(v) => updateStrategy('position_size', v)}
            step={0.01}
            min={0.01}
            max={1}
          />
          <ParamInput
            label="Stop Loss %"
            value={params.strategy_params.stop_loss_percent}
            onChange={(v) => updateStrategy('stop_loss_percent', v)}
            step={0.5}
            min={0.5}
            max={20}
            tooltip="Pérdida máxima permitida antes de cerrar automáticamente. Protege tu capital limitando pérdidas."
          />
          <ParamInput
            label="Take Profit %"
            value={params.strategy_params.take_profit_percent}
            onChange={(v) => updateStrategy('take_profit_percent', v)}
            step={0.5}
            min={1}
            max={50}
            tooltip="Ganancia objetivo antes de cerrar automáticamente. Asegura ganancias cuando el precio alcanza tu meta."
          />
          <ParamInput
            label="Balance Inicial"
            value={params.strategy_params.initial_balance}
            onChange={(v) => updateStrategy('initial_balance', v)}
            step={1000}
            min={1000}
          />
        </div>

        <button
          onClick={() => mutation.mutate(params)}
          disabled={mutation.isPending}
          className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Ejecutando prueba...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Ejecutar Prueba
            </>
          )}
        </button>

        {mutation.isError && (
          <div className="mt-4 flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>Error en prueba: {(mutation.error as Error).message}</span>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Metrics Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              {
                label: 'G/P Total',
                value: `$${result.metrics.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
                color: result.metrics.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400',
                icon: result.metrics.total_pnl >= 0 ? TrendingUp : TrendingDown,
              },
              {
                label: 'Tasa de Aciertos',
                value: `${result.metrics.win_rate.toFixed(1)}%`,
                color: result.metrics.win_rate >= 50 ? 'text-emerald-400' : 'text-red-400',
              },
              {
                label: 'Total Operaciones',
                value: String(result.metrics.total_trades),
                color: 'text-blue-400',
              },
              {
                label: 'Factor de Ganancia',
                value: result.metrics.profit_factor.toFixed(2),
                color: result.metrics.profit_factor >= 1 ? 'text-emerald-400' : 'text-red-400',
              },
              {
                label: 'Sharpe Ratio',
                value: result.metrics.sharpe_ratio.toFixed(2),
                color: result.metrics.sharpe_ratio >= 1 ? 'text-emerald-400' : 'text-yellow-400',
                tooltip: 'Retorno ajustado por riesgo. >1 es bueno, >2 es excelente. Valores negativos indican pérdidas.',
              },
              {
                label: 'Máx. Drawdown',
                value: `${result.metrics.max_drawdown_percent.toFixed(2)}%`,
                color: 'text-red-400',
                tooltip: 'Máxima pérdida desde un pico hasta un valle. Mide el peor escenario posible.',
              },
              {
                label: 'Balance Final',
                value: `$${result.metrics.final_balance.toLocaleString()}`,
                color: 'text-gray-200',
              },
              {
                label: 'Duración Prom. (hrs)',
                value: result.metrics.avg_hold_duration_hours.toFixed(1),
                color: 'text-gray-200',
              },
            ].map((m) => (
              <div key={m.label} className="bg-gray-800 rounded-xl p-4 border border-gray-700/50">
                <div className="text-xs text-gray-400">
                  {m.label}
                  {'tooltip' in m && m.tooltip && <InfoTooltip text={m.tooltip} />}
                </div>
                <div className={`text-lg font-bold mt-1 ${m.color}`}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Equity Curve */}
          {result.equity_curve && result.equity_curve.length > 0 && (
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700/50">
              <h3 className="text-lg font-semibold text-white mb-4">Curva de Capital</h3>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={result.equity_curve.map((d) => ({
                      ...d,
                      time: new Date(d.timestamp).toLocaleDateString(),
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#6b7280" tick={{ fontSize: 11 }} />
                    <YAxis
                      stroke="#6b7280"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#f3f4f6',
                      }}
                      formatter={(value: number) => [
                        `$${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
                        'Balance',
                      ]}
                    />
                    <Line
                      type="monotone"
                      dataKey="balance"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Backtest Trades */}
          {result.trades && result.trades.length > 0 && (
            <div className="bg-gray-800 rounded-xl border border-gray-700/50 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700/50">
                <h3 className="text-lg font-semibold text-white">Operaciones de la Prueba</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-900/50">
                      {['Hora Entrada', 'Entrada', 'Salida', 'G/P', 'G/P %', 'Razón Salida', 'RSI'].map(
                        (h) => (
                          <th
                            key={h}
                            className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                          >
                            {h}
                          </th>
                        )
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.map((t, i) => (
                      <tr key={i} className="border-b border-gray-700/50">
                        <td className="px-4 py-2 text-sm text-gray-300">
                          {new Date(t.entry_time).toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-300">
                          ${t.entry_price.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-300">
                          ${t.exit_price.toLocaleString()}
                        </td>
                        <td
                          className={`px-4 py-2 text-sm font-medium ${
                            t.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                          }`}
                        >
                          {t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}
                        </td>
                        <td
                          className={`px-4 py-2 text-sm font-medium ${
                            t.pnl_percent >= 0 ? 'text-emerald-400' : 'text-red-400'
                          }`}
                        >
                          {t.pnl_percent >= 0 ? '+' : ''}{t.pnl_percent.toFixed(2)}%
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-400">{t.exit_reason}</td>
                        <td className="px-4 py-2 text-sm text-gray-300">{t.rsi.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
