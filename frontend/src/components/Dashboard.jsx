import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import CashPosition from './CashPosition';
import Receivables from './Receivables';
import Payables from './Payables';
import InvoiceList from './InvoiceList';
import ProfitLoss from './ProfitLoss';
import AIInsights from './AIInsights';
import QuickQuestion from './QuickQuestion';
import CashForecast from './CashForecast';
import Anomalies from './Anomalies';

function Dashboard() {
  const [isConnected, setIsConnected] = useState(false);
  const [tenantName, setTenantName] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [lastSynced, setLastSynced] = useState(null);

  const checkConnection = useCallback(async () => {
    try {
      const status = await api.getAuthStatus();
      setIsConnected(status.connected);
      setTenantName(status.tenant_name || '');
      return status.connected;
    } catch (err) {
      setIsConnected(false);
      return false;
    }
  }, []);

  const fetchDashboardData = useCallback(async () => {
    try {
      setError(null);
      const data = await api.getDashboard();
      setDashboardData(data);
      setLastSynced(data.last_synced);
    } catch (err) {
      setError(err.message);
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
      setError(null);
    } catch (err) {
      setError(err.message);
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
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      const connected = await checkConnection();
      if (connected) {
        await fetchDashboardData();
      }
      setLoading(false);
    };
    init();
  }, [checkConnection, fetchDashboardData]);

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Buzz Radar CFO Dashboard</h1>
        <div className="header-actions">
          {isConnected ? (
            <>
              <button
                className="btn btn-secondary"
                onClick={handleSync}
                disabled={syncing}
              >
                {syncing ? 'Syncing...' : 'Sync'}
              </button>
              <div className="connection-status connected">
                <span className="status-dot connected"></span>
                {tenantName || 'Connected'}
              </div>
              <button className="btn btn-secondary" onClick={handleDisconnect}>
                Disconnect
              </button>
            </>
          ) : (
            <div className="connection-status disconnected">
              <span className="status-dot disconnected"></span>
              Not Connected
            </div>
          )}
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      {!isConnected ? (
        <div className="connect-prompt">
          <h2>Connect to Xero</h2>
          <p>
            Connect your Xero account to view real-time financial data and metrics
            for Buzz Radar Limited.
          </p>
          <button className="btn btn-primary" onClick={handleConnect}>
            Connect to Xero
          </button>
        </div>
      ) : dashboardData ? (
        <>
          {/* Key Metrics Row */}
          <div className="metrics-grid">
            <CashPosition data={dashboardData.cash_position} />
            <Receivables data={dashboardData.receivables} />
            <Payables data={dashboardData.payables} />
          </div>

          {/* AI Insights Panel */}
          <AIInsights />

          {/* Quick Question Panel */}
          <QuickQuestion />

          {/* Cash Forecast and Anomalies Row */}
          <div className="ai-panels-grid">
            <CashForecast />
            <Anomalies />
          </div>

          {/* Outstanding Invoices */}
          <InvoiceList
            invoices={dashboardData.receivables?.invoices}
            title="Outstanding Invoices"
          />

          {/* P&L Summary */}
          <ProfitLoss data={dashboardData.profit_loss} />

          {lastSynced && (
            <div className="last-synced">
              Last synced: {new Date(lastSynced).toLocaleString()}
            </div>
          )}
        </>
      ) : (
        <div className="loading">
          <div className="spinner"></div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
