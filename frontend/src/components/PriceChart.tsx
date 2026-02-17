import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import { Loader2, AlertCircle } from 'lucide-react';
import { useChartData, useSignals } from '../hooks/useApiData';
import { InfoTooltip } from './Tooltip';

const TIME_RANGES = [
  { label: '4H', hours: 4 },
  { label: '12H', hours: 12 },
  { label: '24H', hours: 24 },
  { label: '3D', hours: 72 },
  { label: '7D', hours: 168 },
];

export default function PriceChart() {
  const [hours, setHours] = useState(24);
  const chart = useChartData('BTC/USDT', hours);
  const signals = useSignals(50);

  if (chart.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (chart.error) {
    return (
      <div className="flex items-center justify-center py-20 text-red-400">
        <AlertCircle className="w-6 h-6 mr-2" />
        <span>Error al cargar datos del gráfico</span>
      </div>
    );
  }

  const data = chart.data!.data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    dateStr: new Date(d.timestamp).toLocaleDateString(),
    ts: new Date(d.timestamp).getTime(),
  }));

  // Calculate simple moving averages
  const withMA = data.map((d, i, arr) => {
    const ma7 =
      i >= 6
        ? arr.slice(i - 6, i + 1).reduce((s, x) => s + x.close, 0) / 7
        : undefined;
    const ma25 =
      i >= 24
        ? arr.slice(i - 24, i + 1).reduce((s, x) => s + x.close, 0) / 25
        : undefined;
    return { ...d, ma7, ma25 };
  });

  // Map signals to chart data points
  const signalDots =
    signals.data
      ?.filter((s) => s.action !== 'HOLD')
      .map((s) => {
        const sigTime = new Date(s.timestamp).getTime();
        const closest = withMA.reduce((prev, curr) =>
          Math.abs(curr.ts - sigTime) < Math.abs(prev.ts - sigTime) ? curr : prev
        );
        return {
          time: closest.time,
          close: closest.close,
          action: s.action,
        };
      })
      .slice(0, 20) ?? [];

  const minPrice = Math.min(...data.map((d) => d.low)) * 0.999;
  const maxPrice = Math.max(...data.map((d) => d.high)) * 1.001;

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700/50">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Gráfico de Precio BTC/USDT</h2>
          <div className="flex gap-1">
            {TIME_RANGES.map((r) => (
              <button
                key={r.hours}
                onClick={() => setHours(r.hours)}
                className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                  hours === r.hours
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        <div className="h-[400px] lg:h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={withMA} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="time"
                stroke="#6b7280"
                tick={{ fontSize: 11 }}
                interval="preserveStartEnd"
              />
              <YAxis
                stroke="#6b7280"
                tick={{ fontSize: 11 }}
                domain={[minPrice, maxPrice]}
                tickFormatter={(v: number) => `$${v.toLocaleString()}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#f3f4f6',
                }}
                formatter={(value: number, name: string) => [
                  `$${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
                  name === 'close' ? 'Precio' : name === 'ma7' ? 'MA(7)' : 'MA(25)',
                ]}
                labelFormatter={(label: string) => `Hora: ${label}`}
              />
              <Line
                type="monotone"
                dataKey="close"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#3b82f6' }}
              />
              <Line
                type="monotone"
                dataKey="ma7"
                stroke="#f59e0b"
                strokeWidth={1}
                dot={false}
                strokeDasharray="4 2"
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="ma25"
                stroke="#8b5cf6"
                strokeWidth={1}
                dot={false}
                strokeDasharray="4 2"
                connectNulls={false}
              />

              {/* Signal markers */}
              {signalDots.map((s, i) => (
                <ReferenceDot
                  key={i}
                  x={s.time}
                  y={s.close}
                  r={6}
                  fill={s.action === 'BUY' ? '#10b981' : '#ef4444'}
                  stroke={s.action === 'BUY' ? '#10b981' : '#ef4444'}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-blue-500" />
            <span className="text-gray-400">Precio</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-yellow-500 border-dashed" />
            <span className="text-gray-400">
              MA(7)
              <InfoTooltip text="Media Móvil de 7 períodos. Promedio del precio en los últimos 7 intervalos. Identifica tendencias a corto plazo." />
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-purple-500 border-dashed" />
            <span className="text-gray-400">
              MA(25)
              <InfoTooltip text="Media Móvil de 25 períodos. Promedio del precio en los últimos 25 intervalos. Identifica tendencias a mediano plazo." />
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-gray-400">Señal Compra</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-gray-400">Señal Venta</span>
          </div>
        </div>
      </div>
    </div>
  );
}
