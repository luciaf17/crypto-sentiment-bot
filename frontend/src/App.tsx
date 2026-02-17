import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  LineChart,
  Radio,
  ArrowLeftRight,
  Brain,
  FlaskConical,
  Settings,
  Menu,
  X,
  Bitcoin,
} from 'lucide-react';
import Overview from './components/Overview';
import PriceChart from './components/PriceChart';
import SignalsTable from './components/SignalsTable';
import TradesTable from './components/TradesTable';
import SentimentBreakdown from './components/SentimentBreakdown';
import Backtest from './components/Backtest';
import StrategyTuner from './components/StrategyTuner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5000,
    },
  },
});

const NAV_ITEMS = [
  { path: '/', label: 'Vista General', icon: LayoutDashboard },
  { path: '/charts', label: 'Gráficos', icon: LineChart },
  { path: '/signals', label: 'Señales', icon: Radio },
  { path: '/trades', label: 'Operaciones', icon: ArrowLeftRight },
  { path: '/sentiment', label: 'Sentimiento', icon: Brain },
  { path: '/backtest', label: 'Prueba Histórica', icon: FlaskConical },
  { path: '/strategy', label: 'Estrategia', icon: Settings },
];

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-gray-900 border-r border-gray-800 z-50 transform transition-transform duration-200 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 h-16 border-b border-gray-800">
          <Bitcoin className="w-7 h-7 text-orange-500" />
          <span className="text-lg font-bold text-white">CryptoBot</span>
          <button onClick={onClose} className="ml-auto lg:hidden text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Status Footer */}
        <div className="absolute bottom-0 left-0 right-0 px-6 py-4 border-t border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-gray-400">En Vivo - actualización cada 10s</span>
          </div>
        </div>
      </aside>
    </>
  );
}

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 bg-gray-950/80 backdrop-blur-sm border-b border-gray-800 flex items-center px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-gray-400 hover:text-white mr-4"
          >
            <Menu className="w-6 h-6" />
          </button>
          <h1 className="text-lg font-semibold text-white">
            Bot de Trading con Sentimiento Cripto
          </h1>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-6 max-w-7xl">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/charts" element={<PriceChart />} />
            <Route path="/signals" element={<SignalsTable />} />
            <Route path="/trades" element={<TradesTable />} />
            <Route path="/sentiment" element={<SentimentBreakdown />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/strategy" element={<StrategyTuner />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
