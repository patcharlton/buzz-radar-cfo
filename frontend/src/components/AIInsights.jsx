import React, { useState, useEffect } from 'react';
import api from '../services/api';

function AIInsights() {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [generatedAt, setGeneratedAt] = useState(null);

  const fetchInsights = async () => {
    try {
      setError(null);
      const data = await api.getDailyInsights();
      if (data.success) {
        setInsights(data.insights);
        setGeneratedAt(data.generated_at);
      } else {
        setError(data.error || 'Failed to load insights');
      }
    } catch (err) {
      setError(err.message || 'Failed to load insights');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      setError(null);
      const data = await api.refreshInsights();
      if (data.success) {
        setInsights(data.insights);
        setGeneratedAt(data.generated_at);
      } else {
        setError(data.error || 'Failed to refresh insights');
      }
    } catch (err) {
      setError(err.message || 'Failed to refresh insights');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  // Simple markdown-like formatting
  const formatInsights = (text) => {
    if (!text) return null;

    return text.split('\n').map((line, index) => {
      // Headers
      if (line.startsWith('## ')) {
        return <h3 key={index} className="insights-header">{line.slice(3)}</h3>;
      }
      if (line.startsWith('### ')) {
        return <h4 key={index} className="insights-subheader">{line.slice(4)}</h4>;
      }
      // Bold text
      if (line.startsWith('**') && line.endsWith('**')) {
        return <p key={index} className="insights-bold">{line.slice(2, -2)}</p>;
      }
      // Bullet points
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={index} className="insights-bullet">{line.slice(2)}</li>;
      }
      // Numbered items
      if (/^\d+\.\s/.test(line)) {
        return <li key={index} className="insights-numbered">{line.replace(/^\d+\.\s/, '')}</li>;
      }
      // Empty lines
      if (line.trim() === '') {
        return <br key={index} />;
      }
      // Regular text
      return <p key={index} className="insights-text">{line}</p>;
    });
  };

  if (loading) {
    return (
      <div className="ai-insights-panel">
        <div className="ai-insights-header">
          <h2>AI CFO Insights</h2>
        </div>
        <div className="ai-insights-loading">
          <div className="spinner"></div>
          <p>Analysing your financial data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ai-insights-panel">
      <div className="ai-insights-header">
        <h2>AI CFO Insights</h2>
        <button
          className="btn btn-secondary"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="ai-insights-error">
          <p>{error}</p>
          {error.includes('ANTHROPIC_API_KEY') && (
            <p className="hint">Add your Anthropic API key to the .env file</p>
          )}
        </div>
      )}

      {insights && (
        <div className="ai-insights-content">
          {formatInsights(insights)}
        </div>
      )}

      {generatedAt && (
        <div className="ai-insights-footer">
          Generated: {new Date(generatedAt).toLocaleString()}
        </div>
      )}
    </div>
  );
}

export default AIInsights;
