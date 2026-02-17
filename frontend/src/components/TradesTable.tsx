import { useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { useActiveTrades, useTradeHistory, useTradeStats } from '../hooks/useApiData';
import { InfoTooltip } from './Tooltip';

type FilterStatus = 'all' | 'open' | 'closed';

const FILTER_LABELS: Record<FilterStatus, string> = {
  all: 'Todas',
  open: 'Abiertas',
  closed: 'Cerradas',
};

const STATUS_LABELS: Record<string, string> = {
  OPEN: 'ABIERTA',
  CLOSED: 'CERRADA',
};

export default function TradesTable() {
  const [filter, setFilter] = useState<FilterStatus>('all');
  const activeTrades = useActiveTrades();
  const tradeHistory = useTradeHistory(100);
  const tradeStats = useTradeStats();

  const isLoading = activeTrades.isLoading || tradeHistory.isLoading;
  const error = activeTrades.error || tradeHistory.error;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20 text-red-400">
        <AlertCircle className="w-6 h-6 mr-2" />
        <span>Error al cargar operaciones</span>
      </div>
    );
  }

  const allTrades = [...(activeTrades.data ?? []), ...(tradeHistory.data ?? [])];
  const filteredTrades =
    filter === 'all'
      ? allTrades
      : allTrades.filter((t) => (filter === 'open' ? t.status === 'OPEN' : t.status === 'CLOSED'));

  const stats = tradeStats.data;

  return (
    <div className="space-y-4">
      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            { label: 'Total Operaciones', value: stats.total_trades },
            {
              label: 'Tasa de Aciertos',
              value: `${stats.win_rate.toFixed(1)}%`,
              color: stats.win_rate >= 50 ? 'text-emerald-400' : 'text-red-400',
              tooltip: 'Porcentaje de operaciones ganadoras. >60% se considera bueno.',
            },
            {
              label: 'G/P Total',
              value: `$${stats.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
              color: stats.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400',
              tooltip: 'Ganancia o Pérdida total acumulada de todas las operaciones cerradas.',
            },
            {
              label: 'Mejor Operación',
              value: `$${stats.best_trade.toLocaleString()}`,
              color: 'text-emerald-400',
            },
            {
              label: 'Peor Operación',
              value: `$${stats.worst_trade.toLocaleString()}`,
              color: 'text-red-400',
            },
          ].map((s) => (
            <div
              key={s.label}
              className="bg-gray-800 rounded-xl p-4 border border-gray-700/50"
            >
              <div className="text-xs text-gray-400">
                {s.label}
                {'tooltip' in s && s.tooltip && <InfoTooltip text={s.tooltip} />}
              </div>
              <div className={`text-lg font-bold mt-1 ${s.color ?? 'text-gray-200'}`}>
                {s.value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="bg-gray-800 rounded-xl border border-gray-700/50 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700/50">
          <h2 className="text-lg font-semibold text-white">Operaciones</h2>
          <div className="flex gap-1">
            {(['all', 'open', 'closed'] as FilterStatus[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {FILTER_LABELS[f]}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-900/50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Hora Entrada
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Precio Entrada
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Precio Salida
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Cant.
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  G/P
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  G/P %
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No se encontraron operaciones
                  </td>
                </tr>
              ) : (
                filteredTrades.map((trade) => {
                  const pnlPct =
                    trade.pnl !== null && trade.entry_price > 0
                      ? (trade.pnl / (trade.entry_price * trade.quantity)) * 100
                      : null;
                  return (
                    <tr
                      key={trade.id}
                      className="border-b border-gray-700/50 hover:bg-gray-750/50 transition-colors"
                    >
                      <td className="px-4 py-3 text-sm text-gray-300">
                        {new Date(trade.opened_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">
                        ${trade.entry_price.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">
                        {trade.exit_price !== null ? `$${trade.exit_price.toLocaleString()}` : '—'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">
                        {trade.quantity}
                      </td>
                      <td
                        className={`px-4 py-3 text-sm font-medium ${
                          trade.pnl === null
                            ? 'text-gray-500'
                            : trade.pnl >= 0
                            ? 'text-emerald-400'
                            : 'text-red-400'
                        }`}
                      >
                        {trade.pnl !== null
                          ? `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                          : '—'}
                      </td>
                      <td
                        className={`px-4 py-3 text-sm font-medium ${
                          pnlPct === null
                            ? 'text-gray-500'
                            : pnlPct >= 0
                            ? 'text-emerald-400'
                            : 'text-red-400'
                        }`}
                      >
                        {pnlPct !== null ? `${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%` : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            trade.status === 'OPEN'
                              ? 'text-blue-400 bg-blue-500/10'
                              : 'text-gray-400 bg-gray-500/10'
                          }`}
                        >
                          {STATUS_LABELS[trade.status] ?? trade.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
