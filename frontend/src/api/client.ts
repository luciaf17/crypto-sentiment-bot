import axios from 'axios';
import type {
  CurrentPrice,
  ChartData,
  Signal,
  SignalStats,
  Trade,
  TradeStats,
  BacktestRequest,
  BacktestResponse,
  SentimentScore,
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

export async function getCurrentPrice(symbol = 'BTC/USDT'): Promise<CurrentPrice> {
  const { data } = await api.get('/prices/current', { params: { symbol } });
  return data;
}

export async function getChartData(symbol = 'BTC/USDT', hours = 24): Promise<ChartData> {
  const { data } = await api.get('/prices/chart', { params: { symbol, hours } });
  return data;
}

export async function getLatestSignal(symbol = 'BTC/USDT'): Promise<Signal> {
  const { data } = await api.get('/signals/current', { params: { symbol } });
  return data;
}

export async function getSignals(limit = 20): Promise<Signal[]> {
  const { data } = await api.get('/signals/latest', { params: { limit } });
  return data;
}

export async function getSignalStats(): Promise<SignalStats> {
  const { data } = await api.get('/signals/stats');
  return data;
}

export async function getActiveTrades(): Promise<Trade[]> {
  const { data } = await api.get('/trades/active');
  return data;
}

export async function getTradeHistory(limit = 50, offset = 0): Promise<Trade[]> {
  const { data } = await api.get('/trades/history', { params: { limit, offset } });
  return data;
}

export async function getTradeStats(): Promise<TradeStats> {
  const { data } = await api.get('/trades/stats');
  return data;
}

export async function getSentimentData(symbol = 'BTC/USDT'): Promise<SentimentScore[]> {
  const { data } = await api.get('/prices/latest', { params: { limit: 1 } });
  // Sentiment data comes from signals - extract from latest signals
  void data;
  const signals = await getSignals(50);
  // Build pseudo sentiment data from signals
  const sentimentMap = new Map<string, SentimentScore[]>();
  for (const signal of signals) {
    if (signal.sentiment_score !== null) {
      const source = 'aggregate';
      if (!sentimentMap.has(source)) sentimentMap.set(source, []);
      sentimentMap.get(source)!.push({
        symbol: signal.symbol,
        score: signal.sentiment_score,
        source,
        raw_text: null,
        timestamp: signal.timestamp,
      });
    }
  }
  void symbol;
  return signals
    .filter((s) => s.sentiment_score !== null)
    .map((s) => ({
      symbol: s.symbol,
      score: s.sentiment_score!,
      source: 'aggregate',
      raw_text: JSON.stringify(s.reasons),
      timestamp: s.timestamp,
    }));
}

export async function runBacktest(params: BacktestRequest): Promise<BacktestResponse> {
  const { data } = await api.post('/backtest/run', params);
  return data;
}

export async function getBacktestResult(id: number): Promise<BacktestResponse> {
  const { data } = await api.get(`/backtest/results/${id}`);
  return data;
}
