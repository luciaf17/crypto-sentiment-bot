import { useState } from 'react';
import { ChevronDown, ChevronUp, Loader2, AlertCircle } from 'lucide-react';
import { useSignals } from '../hooks/useApiData';
import { InfoTooltip } from './Tooltip';
import type { Signal, SignalAction } from '../types';

const ACTION_COLORS: Record<SignalAction, string> = {
  BUY: 'text-emerald-400 bg-emerald-500/10',
  SELL: 'text-red-400 bg-red-500/10',
  HOLD: 'text-yellow-400 bg-yellow-500/10',
};

const ACTION_LABELS: Record<SignalAction, string> = {
  BUY: 'COMPRAR',
  SELL: 'VENDER',
  HOLD: 'MANTENER',
};

const PAGE_SIZE = 10;

function SignalRow({ signal }: { signal: Signal }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="border-b border-gray-700/50 hover:bg-gray-750/50 cursor-pointer transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-3 text-sm text-gray-300">
          {new Date(signal.timestamp).toLocaleString()}
        </td>
        <td className="px-4 py-3">
          <span
            className={`px-2 py-0.5 rounded text-xs font-semibold ${ACTION_COLORS[signal.action]}`}
          >
            {ACTION_LABELS[signal.action]}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-gray-300">
          {(signal.confidence * 100).toFixed(1)}%
        </td>
        <td className="px-4 py-3 text-sm text-gray-300">
          ${signal.price_at_signal.toLocaleString()}
        </td>
        <td className="px-4 py-3 text-sm text-gray-300">
          {signal.technical_indicators.rsi !== undefined
            ? Number(signal.technical_indicators.rsi).toFixed(1)
            : '—'}
        </td>
        <td className="px-4 py-3 text-sm text-gray-300">
          {signal.sentiment_score !== null ? signal.sentiment_score.toFixed(3) : '—'}
        </td>
        <td className="px-4 py-3 text-gray-500">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </td>
      </tr>
      {expanded && (
        <tr className="border-b border-gray-700/50">
          <td colSpan={7} className="px-4 py-3 bg-gray-900/50">
            <div className="text-sm">
              <div className="text-gray-400 mb-2 font-medium">Razones de la Señal</div>
              <pre className="text-xs text-gray-300 bg-gray-900 rounded-lg p-3 overflow-x-auto">
                {JSON.stringify(signal.reasons, null, 2)}
              </pre>
              {Object.keys(signal.technical_indicators).length > 0 && (
                <>
                  <div className="text-gray-400 mt-3 mb-2 font-medium">Indicadores Técnicos</div>
                  <pre className="text-xs text-gray-300 bg-gray-900 rounded-lg p-3 overflow-x-auto">
                    {JSON.stringify(signal.technical_indicators, null, 2)}
                  </pre>
                </>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function SignalsTable() {
  const [page, setPage] = useState(0);
  const signals = useSignals(100);

  if (signals.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (signals.error) {
    return (
      <div className="flex items-center justify-center py-20 text-red-400">
        <AlertCircle className="w-6 h-6 mr-2" />
        <span>Error al cargar señales</span>
      </div>
    );
  }

  const data = signals.data ?? [];
  const totalPages = Math.ceil(data.length / PAGE_SIZE);
  const pageData = data.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700/50 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-700/50">
        <h2 className="text-lg font-semibold text-white">Señales de Trading</h2>
        <p className="text-sm text-gray-400 mt-1">Haz clic en una fila para ver los detalles</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-900/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Hora
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Acción
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Confianza
                <InfoTooltip text="Nivel de confianza de la señal (0-100%). Mayor valor = más condiciones técnicas cumplidas." />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Precio
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                RSI
                <InfoTooltip text="Índice de Fuerza Relativa. Mide si el activo está sobrecomprado (>70) o sobrevendido (<30)." />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Sentimiento
                <InfoTooltip text="Puntuación de sentimiento del mercado (-1 a +1). Combina CryptoPanic, NewsAPI y Fear & Greed Index." />
              </th>
              <th className="px-4 py-3 w-10" />
            </tr>
          </thead>
          <tbody>
            {pageData.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No se encontraron señales
                </td>
              </tr>
            ) : (
              pageData.map((signal) => <SignalRow key={signal.id} signal={signal} />)
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-6 py-3 border-t border-gray-700/50">
          <span className="text-sm text-gray-400">
            Mostrando {page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, data.length)} de{' '}
            {data.length}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1 text-sm bg-gray-700 text-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-600 transition-colors"
            >
              Anterior
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 text-sm bg-gray-700 text-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-600 transition-colors"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
