import React, { useState } from 'react';
import api from '../services/api';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function FinancialQueryInput() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const exampleQueries = [
    "How much did we spend on software last quarter?",
    "What were our total payroll costs in 2024?",
    "Show me HMRC payments this year",
    "What did we spend on marketing last month?",
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await api.queryFinancial(query);

      if (response.success) {
        setResult(response);
      } else {
        setError(response.error || 'Failed to process query');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
  };

  return (
    <div className="metric-card query-card full-width">
      <h3>Financial Query</h3>

      <form onSubmit={handleSubmit} className="query-form">
        <div className="query-input-wrapper">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a financial question..."
            className="query-input"
            disabled={loading}
          />
          <button
            type="submit"
            className="query-submit"
            disabled={loading || !query.trim()}
          >
            {loading ? '...' : '→'}
          </button>
        </div>
      </form>

      <div className="query-examples">
        <span className="examples-label">Try:</span>
        {exampleQueries.map((eq, index) => (
          <button
            key={index}
            className="example-chip"
            onClick={() => handleExampleClick(eq)}
            disabled={loading}
          >
            {eq}
          </button>
        ))}
      </div>

      {loading && (
        <div className="query-loading">
          <div className="loading-spinner" />
          <span>Analyzing your question...</span>
        </div>
      )}

      {error && (
        <div className="query-error">
          <span className="error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="query-result">
          <div className="result-answer">
            <div className="answer-value">{formatCurrency(result.total)}</div>
            <div className="answer-context">
              {result.category && <span className="context-category">{result.category}</span>}
              <span className="context-period">{result.period_description}</span>
            </div>
          </div>

          {result.breakdown && result.breakdown.length > 0 && (
            <div className="result-breakdown">
              <div className="breakdown-header">
                <span>Transaction Breakdown</span>
                <span className="breakdown-count">{result.transaction_count} transactions</span>
              </div>
              <div className="breakdown-list">
                {result.breakdown.slice(0, 10).map((item, index) => (
                  <div key={index} className="breakdown-row">
                    <span className="breakdown-desc">{item.description}</span>
                    <span className="breakdown-amount">{formatCurrency(item.amount)}</span>
                  </div>
                ))}
                {result.breakdown.length > 10 && (
                  <div className="breakdown-more">
                    +{result.breakdown.length - 10} more transactions
                  </div>
                )}
              </div>
            </div>
          )}

          {result.interpreted_as && (
            <div className="result-interpretation">
              Interpreted as: <em>{result.interpreted_as}</em>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FinancialQueryInput;
