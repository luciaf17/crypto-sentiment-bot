export interface CurrentPrice {
  symbol: string;
  price: number;
  high: number;
  low: number;
  open: number;
  close: number;
  volume: number;
  timestamp: string;
}

export interface PricePoint {
  id: number;
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
  high: number;
  low: number;
  open: number;
  close: number;
  created_at: string;
}

export interface ChartDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartData {
  symbol: string;
  hours: number;
  data: ChartDataPoint[];
  count: number;
}

export type SignalAction = 'BUY' | 'SELL' | 'HOLD';

export interface Signal {
  id: number;
  symbol: string;
  action: SignalAction;
  confidence: number;
  price_at_signal: number;
  reasons: Record<string, unknown>;
  technical_indicators: {
    rsi?: number;
    macd?: number;
    bollinger_bands?: string;
    [key: string]: unknown;
  };
  sentiment_score: number | null;
  timestamp: string;
  created_at: string;
}

export interface SignalStats {
  total_signals: number;
  buy_count: number;
  sell_count: number;
  hold_count: number;
  buy_pct: number;
  sell_pct: number;
  hold_pct: number;
  avg_confidence: number;
  latest_signal_at: string;
}

export interface Trade {
  id: number;
  signal_id: number;
  entry_price: number;
  exit_price: number | null;
  quantity: number;
  pnl: number | null;
  status: 'OPEN' | 'CLOSED';
  opened_at: string;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TradeStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_pnl_percent: number;
  avg_win: number;
  avg_loss: number;
  best_trade: number;
  worst_trade: number;
  max_drawdown: number;
  sharpe_ratio: number;
  current_balance: number;
  open_trades: number;
}

export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  strategy_params: {
    rsi_oversold: number;
    rsi_overbought: number;
    position_size: number;
    stop_loss_percent: number;
    take_profit_percent: number;
    initial_balance: number;
  };
}

export interface BacktestTrade {
  entry_price: number;
  entry_time: string;
  exit_price: number;
  exit_time: string;
  quantity: number;
  pnl: number;
  pnl_percent: number;
  exit_reason: string;
  rsi: number;
  sentiment: number;
}

export interface EquityCurvePoint {
  timestamp: string;
  balance: number;
}

export interface BacktestResponse {
  id: number;
  status: string;
  symbol: string;
  period_start: string;
  period_end: string;
  data_points: number;
  parameters: Record<string, unknown>;
  metrics: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    total_pnl: number;
    total_pnl_percent: number;
    avg_win: number;
    avg_loss: number;
    profit_factor: number;
    max_drawdown: number;
    max_drawdown_percent: number;
    sharpe_ratio: number;
    best_trade: number;
    worst_trade: number;
    avg_hold_duration_hours: number;
    final_balance: number;
  };
  trades: BacktestTrade[];
  equity_curve: EquityCurvePoint[];
  error_reason: string | null;
  created_at: string;
}

export interface SentimentScore {
  symbol: string;
  score: number;
  source: string;
  raw_text: string | null;
  timestamp: string;
}
