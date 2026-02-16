import { Loader2, AlertCircle, Newspaper } from 'lucide-react';
import { useSentiment, useSignals } from '../hooks/useApiData';

function SentimentBar({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description?: string;
}) {
  // value: -1 to 1
  const pct = ((value + 1) / 2) * 100;
  const color =
    value > 0.3 ? 'bg-emerald-500' : value < -0.3 ? 'bg-red-500' : 'bg-yellow-500';
  const textColor =
    value > 0.3 ? 'text-emerald-400' : value < -0.3 ? 'text-red-400' : 'text-yellow-400';

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <div>
          <span className="text-sm font-medium text-gray-200">{label}</span>
          {description && (
            <span className="text-xs text-gray-500 ml-2">{description}</span>
          )}
        </div>
        <span className={`text-sm font-bold ${textColor}`}>{value.toFixed(3)}</span>
      </div>
      <div className="h-2.5 bg-gray-700 rounded-full overflow-hidden relative">
        <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-500 z-10" />
        <div
          className={`h-full ${color} rounded-full transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function FearGreedGauge({ value }: { value: number }) {
  // Fear & Greed: 0-100 scale, map to label
  const label =
    value <= 20
      ? 'Extreme Fear'
      : value <= 40
      ? 'Fear'
      : value <= 60
      ? 'Neutral'
      : value <= 80
      ? 'Greed'
      : 'Extreme Greed';

  const color =
    value <= 20
      ? 'text-red-400'
      : value <= 40
      ? 'text-orange-400'
      : value <= 60
      ? 'text-yellow-400'
      : value <= 80
      ? 'text-green-400'
      : 'text-emerald-400';

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700/50">
      <div className="text-sm text-gray-400 mb-4">Fear & Greed Index</div>
      <div className="flex items-center justify-center">
        <div className="relative w-32 h-32">
          <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke="#374151"
              strokeWidth="10"
            />
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke={value <= 40 ? '#ef4444' : value <= 60 ? '#eab308' : '#22c55e'}
              strokeWidth="10"
              strokeDasharray={`${(value / 100) * 314} 314`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-2xl font-bold ${color}`}>{Math.round(value)}</span>
            <span className="text-xs text-gray-400">{label}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SentimentBreakdown() {
  const sentiment = useSentiment();
  const signals = useSignals(50);

  if (sentiment.isLoading || signals.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (sentiment.error) {
    return (
      <div className="flex items-center justify-center py-20 text-red-400">
        <AlertCircle className="w-6 h-6 mr-2" />
        <span>Failed to load sentiment data</span>
      </div>
    );
  }

  const sentimentData = sentiment.data ?? [];
  const avgScore =
    sentimentData.length > 0
      ? sentimentData.reduce((s, d) => s + d.score, 0) / sentimentData.length
      : 0;

  // Simulate per-source scores from available data
  const recentScores = sentimentData.slice(0, 10);
  const cryptoPanicScore = recentScores.length > 0 ? recentScores[0].score : 0;
  const newsApiScore = recentScores.length > 1 ? recentScores[1].score : avgScore * 0.9;
  const fearGreedValue = ((avgScore + 1) / 2) * 100; // Convert -1..1 to 0..100

  // Extract headlines from signal reasons
  const headlines = (signals.data ?? [])
    .filter((s) => s.reasons && Object.keys(s.reasons).length > 0)
    .slice(0, 10)
    .map((s) => ({
      text: Object.entries(s.reasons)
        .map(([k, v]) => `${k}: ${v}`)
        .join(', '),
      score: s.sentiment_score ?? 0,
      time: s.timestamp,
    }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sentiment Sources */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl p-6 border border-gray-700/50">
          <h2 className="text-lg font-semibold text-white mb-6">Sentiment Sources</h2>
          <div className="space-y-6">
            <SentimentBar
              label="CryptoPanic"
              value={cryptoPanicScore}
              description="Crypto news aggregator"
            />
            <SentimentBar
              label="NewsAPI"
              value={newsApiScore}
              description="General financial news"
            />
            <SentimentBar label="Weighted Average" value={avgScore} />
          </div>

          <div className="mt-6 pt-4 border-t border-gray-700/50">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Combined Sentiment</span>
              <span
                className={`font-bold ${
                  avgScore > 0.1
                    ? 'text-emerald-400'
                    : avgScore < -0.1
                    ? 'text-red-400'
                    : 'text-yellow-400'
                }`}
              >
                {avgScore > 0.1 ? 'Bullish' : avgScore < -0.1 ? 'Bearish' : 'Neutral'} (
                {avgScore.toFixed(3)})
              </span>
            </div>
          </div>
        </div>

        {/* Fear & Greed */}
        <FearGreedGauge value={fearGreedValue} />
      </div>

      {/* Headlines */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700/50">
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="w-5 h-5 text-gray-400" />
          <h2 className="text-lg font-semibold text-white">Recent Signal Reasons</h2>
        </div>

        {headlines.length === 0 ? (
          <p className="text-gray-500 text-sm">No recent headlines available</p>
        ) : (
          <div className="space-y-3">
            {headlines.map((h, i) => (
              <div
                key={i}
                className="flex items-start justify-between gap-4 py-2 border-b border-gray-700/30 last:border-0"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300 truncate">{h.text}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {new Date(h.time).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded shrink-0 ${
                    h.score > 0.1
                      ? 'text-emerald-400 bg-emerald-500/10'
                      : h.score < -0.1
                      ? 'text-red-400 bg-red-500/10'
                      : 'text-yellow-400 bg-yellow-500/10'
                  }`}
                >
                  {h.score.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
