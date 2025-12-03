import React, { useState, useEffect, useCallback } from 'react';
import { Toaster, toast } from 'sonner';
import { Shell } from '@/components/layout/Shell';
import { CashPosition } from '@/components/dashboard/CashPosition';
import { Receivables } from '@/components/dashboard/Receivables';
import { Payables } from '@/components/dashboard/Payables';
import { InvoiceTable } from '@/components/dashboard/InvoiceTable';
import { AiCfoPanel } from '@/components/dashboard/AiCfoPanel';
import { PipelineSummary } from '@/components/dashboard/PipelineSummary';
import { RisksSummary } from '@/components/dashboard/RisksSummary';
import { TransitionProgress } from '@/components/dashboard/TransitionProgress';
import { RunwayCard } from '@/components/dashboard/RunwayCard';
import { RevenueHistoryCard } from '@/components/dashboard/RevenueHistoryCard';
import { CashFlowChart } from '@/components/charts/CashFlowChart';
import CashForecast from '@/components/CashForecast';
import Anomalies from '@/components/Anomalies';
import ProjectionWidget from '@/components/ProjectionWidget';
import { LoginPage } from '@/components/LoginPage';
import { DrillDownDrawer } from '@/components/DrillDownDrawer';
import { DrillDownProvider } from '@/contexts/DrillDownContext';
import api from '@/services/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('buzzradar_authenticated') === 'true';
  });
  const [isConnected, setIsConnected] = useState(false);
  const [tenantName, setTenantName] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [lastSynced, setLastSynced] = useState(null);
  const [historyTrends, setHistoryTrends] = useState(null);
  const [runwayData, setRunwayData] = useState(null);

  const checkConnection = useCallback(async () => {
    try {
      const status = await api.getAuthStatus();
      setIsConnected(status.connected);
      setTenantName(status.tenant_name || '');
      return status.connected;
    } catch {
      setIsConnected(false);
      return false;
    }
  }, []);

  const fetchDashboardData = useCallback(async () => {
    try {
      const data = await api.getDashboard();
      setDashboardData(data);
      setLastSynced(data.last_synced);
    } catch (err) {
      toast.error('Failed to load dashboard data');
    }
  }, []);

  const fetchHistoryTrends = useCallback(async () => {
    try {
      const data = await api.getHistoryTrends(12);
      if (data.success) {
        setHistoryTrends(data);
      }
    } catch (err) {
      // Silently fail - trends are optional
      console.warn('Failed to load history trends:', err);
    }
  }, []);

  const fetchRunway = useCallback(async () => {
    try {
      const data = await api.getRunway();
      if (data.success) {
        setRunwayData(data);
      }
    } catch (err) {
      // Silently fail - runway data is optional
      console.warn('Failed to load runway data:', err);
    }
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await api.sync();
      if (result.data) {
        setDashboardData(result.data);
        setLastSynced(result.data.last_synced);
      }
      toast.success('Data synced successfully');
    } catch (err) {
      toast.error('Failed to sync data');
    } finally {
      setSyncing(false);
    }
  };

  const handleConnect = () => {
    window.location.href = api.getLoginUrl();
  };

  const handleDisconnect = async () => {
    try {
      await api.disconnect();
      setIsConnected(false);
      setDashboardData(null);
      setTenantName('');
      toast.success('Disconnected from Xero');
    } catch (err) {
      toast.error('Failed to disconnect');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('buzzradar_authenticated');
    setIsAuthenticated(false);
    setIsConnected(false);
    setDashboardData(null);
    setTenantName('');
  };

  useEffect(() => {
    const init = async () => {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }
      setLoading(true);
      const connected = await checkConnection();
      if (connected) {
        // Fetch all data in parallel
        await Promise.all([
          fetchDashboardData(),
          fetchHistoryTrends(),
          fetchRunway(),
        ]);
      }
      setLoading(false);
    };
    init();
  }, [checkConnection, fetchDashboardData, fetchHistoryTrends, fetchRunway, isAuthenticated]);

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

  // Wrap main app with DrillDownProvider
  return (
    <DrillDownProvider>
      <AppContent
        loading={loading}
        isConnected={isConnected}
        tenantName={tenantName}
        lastSynced={lastSynced}
        dashboardData={dashboardData}
        historyTrends={historyTrends}
        runwayData={runwayData}
        syncing={syncing}
        onSync={handleSync}
        onConnect={handleConnect}
        onDisconnect={handleDisconnect}
        onLogout={handleLogout}
      />
    </DrillDownProvider>
  );
}

function AppContent({
  loading,
  isConnected,
  tenantName,
  lastSynced,
  dashboardData,
  historyTrends,
  runwayData,
  syncing,
  onSync,
  onConnect,
  onDisconnect,
  onLogout,
}) {

  if (loading) {
    return (
      <Shell
        isConnected={false}
        tenantName=""
        lastSynced={null}
        onSync={() => {}}
        onConnect={() => {}}
        onDisconnect={() => {}}
        onLogout={onLogout}
        syncing={false}
        loading={true}
      >
        <LoadingDashboard />
      </Shell>
    );
  }

  return (
    <>
      <Shell
        isConnected={isConnected}
        tenantName={tenantName}
        lastSynced={lastSynced}
        onSync={onSync}
        onConnect={onConnect}
        onDisconnect={onDisconnect}
        onLogout={onLogout}
        syncing={syncing}
      >
        {dashboardData && (
          <div className="space-y-3 sm:space-y-4">
            {/* Key Metrics Row - 3 equal columns on tablet+ */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4 items-stretch">
              <CashPosition
                data={dashboardData.cash_position}
                loading={!dashboardData}
                trends={historyTrends?.trends}
                yoyComparison={historyTrends?.yoy_comparisons}
              />
              <Receivables
                data={dashboardData.receivables}
                loading={!dashboardData}
                trends={historyTrends?.trends}
                yoyComparison={historyTrends?.yoy_comparisons}
              />
              <div className="sm:col-span-2 md:col-span-1">
                <Payables
                  data={dashboardData.payables}
                  loading={!dashboardData}
                  trends={historyTrends?.trends}
                  yoyComparison={historyTrends?.yoy_comparisons}
                />
              </div>
            </div>

            {/* AI CFO Panel - Priority on mobile */}
            <AiCfoPanel />

            {/* Strategic Context Row - Pipeline, Risks, Transition */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 items-stretch">
              <PipelineSummary />
              <RisksSummary />
              <div className="sm:col-span-2 lg:col-span-1">
                <TransitionProgress />
              </div>
            </div>

            {/* Runway and Revenue History Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 items-stretch">
              <RunwayCard data={runwayData} loading={!dashboardData} />
              <RevenueHistoryCard trends={historyTrends} loading={!dashboardData} />
            </div>

            {/* 3-Month Financial Projection */}
            <ProjectionWidget />

            {/* Cash Forecast and Anomalies Row - Equal height cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 items-stretch">
              <CashForecast />
              <Anomalies />
            </div>

            {/* Cash Flow Chart - Full Width */}
            <CashFlowChart />

            {/* Invoice Table - Full Width */}
            <InvoiceTable
              invoices={dashboardData.receivables?.invoices}
              loading={!dashboardData}
            />
          </div>
        )}
      </Shell>
      <DrillDownDrawer />
      <Toaster richColors position="bottom-right" />
    </>
  );
}

/**
 * Loading state component that shows skeleton cards and a clear loading message
 */
function LoadingDashboard() {
  return (
    <div className="space-y-4">
      {/* Loading header */}
      <div className="flex flex-col items-center justify-center py-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-indigo-600 border-t-transparent" />
          <span className="text-lg font-medium text-zinc-700 dark:text-zinc-300">
            Loading your financial data...
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          Connecting to Xero and fetching the latest numbers
        </p>
      </div>

      {/* Skeleton cards - mimics the real layout */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <SkeletonCard title="Cash Position" />
        <SkeletonCard title="Receivables" />
        <div className="sm:col-span-2 md:col-span-1">
          <SkeletonCard title="Payables" />
        </div>
      </div>

      {/* AI CFO skeleton */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="h-5 w-5 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse" />
          <div className="h-5 w-24 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse" />
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse w-full" />
          <div className="h-4 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse w-5/6" />
          <div className="h-4 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse w-4/6" />
        </div>
      </div>

      {/* More skeleton rows */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
        <SkeletonCard title="Pipeline" small />
        <SkeletonCard title="Risks" small />
        <div className="sm:col-span-2 lg:col-span-1">
          <SkeletonCard title="Transition" small />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        <SkeletonCard title="Runway" />
        <SkeletonCard title="Revenue History" />
      </div>
    </div>
  );
}

/**
 * Skeleton card component for loading state
 */
function SkeletonCard({ title, small = false }) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse" />
          <span className="text-sm font-medium text-muted-foreground">{title}</span>
        </div>
        <div className="h-5 w-12 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse" />
      </div>

      {/* Main value skeleton */}
      <div className={`${small ? 'h-7' : 'h-9'} w-32 bg-zinc-200 dark:bg-zinc-700 rounded animate-pulse mb-3`} />

      {/* Sparkline skeleton */}
      {!small && (
        <div className="h-8 w-full bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse mb-3" />
      )}

      {/* Detail rows skeleton */}
      <div className="space-y-2 mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800">
        <div className="flex justify-between">
          <div className="h-3 w-20 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
          <div className="h-3 w-16 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
        </div>
        <div className="flex justify-between">
          <div className="h-3 w-24 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
          <div className="h-3 w-14 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
        </div>
      </div>
    </div>
  );
}

export default App;
