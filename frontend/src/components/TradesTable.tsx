import { useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { useActiveTrades, useTradeHistory, useTradeStats } from '../hooks/useApiData';

type FilterStatus = 'all' | 'open' | 'closed';

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
        <span>Failed to load trades</span>
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
            { label: 'Total Trades', value: stats.total_trades },
            {
              label: 'Win Rate',
              value: `${stats.win_rate.toFixed(1)}%`,
              color: stats.win_rate >= 50 ? 'text-emerald-400' : 'text-red-400',
            },
            {
              label: 'Total P&L',
              value: `$${stats.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
              color: stats.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400',
            },
            {
              label: 'Best Trade',
              value: `$${stats.best_trade.toLocaleString()}`,
              color: 'text-emerald-400',
            },
            {
              label: 'Worst Trade',
              value: `$${stats.worst_trade.toLocaleString()}`,
              color: 'text-red-400',
            },
          ].map((s) => (
            <div
              key={s.label}
              className="bg-gray-800 rounded-xl p-4 border border-gray-700/50"
            >
              <div className="text-xs text-gray-400">{s.label}</div>
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
          <h2 className="text-lg font-semibold text-white">Trades</h2>
          <div className="flex gap-1">
            {(['all', 'open', 'closed'] as FilterStatus[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-sm rounded-lg capitalize transition-colors ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-900/50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Entry Time
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Entry Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Exit Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Qty
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  P&L %
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No trades found
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
                          {trade.status}
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
