import React, { useState, useEffect } from 'react';
import api from '../services/api';

function NotionSync() {
  const [status, setStatus] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [cacheAge, setCacheAge] = useState(null);
  const [error, setError] = useState(null);

  const checkStatus = async () => {
    try {
      const result = await api.getNotionStatus();
      setStatus(result);
      if (!result.configured) {
        setError('Notion not configured');
      } else if (!result.success) {
        setError(result.error || 'Connection failed');
      } else {
        setError(null);
      }
    } catch (err) {
      setError('Failed to check Notion status');
      setStatus(null);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setError(null);
    try {
      const result = await api.syncNotionPipeline();
      if (result.success) {
        setLastSync(new Date());
        setCacheAge(0);
        // Optionally show deal count
        if (result.data?.deals) {
          console.log(`Synced ${result.data.deals.length} deals from Notion`);
        }
      } else {
        setError(result.error || 'Sync failed');
      }
    } catch (err) {
      setError('Sync failed: ' + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const fetchCacheInfo = async () => {
    try {
      const result = await api.getNotionPipeline();
      if (result.success && result.cache_age_minutes !== undefined) {
        setCacheAge(result.cache_age_minutes);
      }
    } catch (err) {
      // Silent fail - cache info is not critical
    }
  };

  useEffect(() => {
    checkStatus();
    fetchCacheInfo();
  }, []);

  // Don't render if not configured
  if (status && !status.configured) {
    return null;
  }

  const isConnected = status?.success && status?.connected;

  return (
    <div className="notion-sync">
      <button
        className={`btn btn-secondary notion-btn ${syncing ? 'syncing' : ''}`}
        onClick={handleSync}
        disabled={syncing || !isConnected}
        title={error || (cacheAge !== null ? `Cache: ${Math.round(cacheAge)} min ago` : 'Sync pipeline from Notion')}
      >
        <svg
          className={`notion-icon ${syncing ? 'spin' : ''}`}
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
          <path d="M21 3v5h-5" />
        </svg>
        {syncing ? 'Syncing...' : 'Pipeline'}
      </button>
      {isConnected && (
        <span
          className="notion-status connected"
          title="Connected to Notion"
        >
          <span className="status-dot connected"></span>
        </span>
      )}
      {error && !isConnected && (
        <span
          className="notion-status error"
          title={error}
        >
          <span className="status-dot disconnected"></span>
        </span>
      )}
    </div>
  );
}

export default NotionSync;
