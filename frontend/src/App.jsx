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
import { CashFlowChart } from '@/components/charts/CashFlowChart';
import CashForecast from '@/components/CashForecast';
import Anomalies from '@/components/Anomalies';
import ProjectionWidget from '@/components/ProjectionWidget';
import { LoginPage } from '@/components/LoginPage';
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
        await fetchDashboardData();
      }
      setLoading(false);
    };
    init();
  }, [checkConnection, fetchDashboardData, isAuthenticated]);

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

  if (loading) {
    return (
      <Shell
        isConnected={false}
        tenantName=""
        lastSynced={null}
        onSync={() => {}}
        onConnect={() => {}}
        onDisconnect={() => {}}
        onLogout={handleLogout}
        syncing={false}
      >
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      </Shell>
    );
  }

  return (
    <>
      <Shell
        isConnected={isConnected}
        tenantName={tenantName}
        lastSynced={lastSynced}
        onSync={handleSync}
        onConnect={handleConnect}
        onDisconnect={handleDisconnect}
        onLogout={handleLogout}
        syncing={syncing}
      >
        {dashboardData && (
          <div className="space-y-4">
            {/* Key Metrics Row - 3 equal columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-stretch">
              <CashPosition
                data={dashboardData.cash_position}
                loading={!dashboardData}
              />
              <Receivables
                data={dashboardData.receivables}
                loading={!dashboardData}
              />
              <Payables
                data={dashboardData.payables}
                loading={!dashboardData}
              />
            </div>

            {/* Strategic Context Row - Pipeline, Risks, Transition */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-stretch">
              <PipelineSummary />
              <RisksSummary />
              <TransitionProgress />
            </div>

            {/* AI CFO Panel - Unified insights and Q&A */}
            <AiCfoPanel />

            {/* 3-Month Financial Projection */}
            <ProjectionWidget />

            {/* Cash Forecast and Anomalies Row - Equal height cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-stretch">
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
      <Toaster richColors position="bottom-right" />
    </>
  );
}

export default App;
