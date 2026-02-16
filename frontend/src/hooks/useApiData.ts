import { useQuery } from '@tanstack/react-query';
import {
  getCurrentPrice,
  getChartData,
  getLatestSignal,
  getSignals,
  getSignalStats,
  getActiveTrades,
  getTradeHistory,
  getTradeStats,
  getSentimentData,
} from '../api/client';

const POLL_INTERVAL = 10_000;

export function usePriceData(symbol = 'BTC/USDT') {
  return useQuery({
    queryKey: ['currentPrice', symbol],
    queryFn: () => getCurrentPrice(symbol),
    refetchInterval: POLL_INTERVAL,
  });
}

export function useChartData(symbol = 'BTC/USDT', hours = 24) {
  return useQuery({
    queryKey: ['chartData', symbol, hours],
    queryFn: () => getChartData(symbol, hours),
    refetchInterval: POLL_INTERVAL,
  });
}

export function useLatestSignal(symbol = 'BTC/USDT') {
  return useQuery({
    queryKey: ['latestSignal', symbol],
    queryFn: () => getLatestSignal(symbol),
    refetchInterval: POLL_INTERVAL,
  });
}

export function useSignals(limit = 20) {
  return useQuery({
    queryKey: ['signals', limit],
    queryFn: () => getSignals(limit),
    refetchInterval: POLL_INTERVAL,
  });
}

export function useSignalStats() {
  return useQuery({
    queryKey: ['signalStats'],
    queryFn: getSignalStats,
    refetchInterval: POLL_INTERVAL,
  });
}

export function useActiveTrades() {
  return useQuery({
    queryKey: ['activeTrades'],
    queryFn: getActiveTrades,
    refetchInterval: POLL_INTERVAL,
  });
}

export function useTradeHistory(limit = 50) {
  return useQuery({
    queryKey: ['tradeHistory', limit],
    queryFn: () => getTradeHistory(limit),
    refetchInterval: POLL_INTERVAL,
  });
}

export function useTradeStats() {
  return useQuery({
    queryKey: ['tradeStats'],
    queryFn: getTradeStats,
    refetchInterval: POLL_INTERVAL,
  });
}

export function useSentiment(symbol = 'BTC/USDT') {
  return useQuery({
    queryKey: ['sentiment', symbol],
    queryFn: () => getSentimentData(symbol),
    refetchInterval: POLL_INTERVAL,
  });
}
