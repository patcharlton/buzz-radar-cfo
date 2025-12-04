import React, { useState, useEffect } from 'react';
import api from '../services/api';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function FixedCostFloorCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.getFixedCosts();
        if (result.success) {
          setData(result);
        } else {
          setError(result.error);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="metric-card">
        <h3>Fixed Cost Floor</h3>
        <div className="metric-loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metric-card">
        <h3>Fixed Cost Floor</h3>
        <div className="metric-error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const { total_monthly_fixed, zero_revenue_runway_months, breakdown, months_analyzed } = data;

  // Determine health status based on zero-revenue runway
  let healthStatus = 'healthy';
  if (zero_revenue_runway_months < 2) {
    healthStatus = 'critical';
  } else if (zero_revenue_runway_months < 4) {
    healthStatus = 'warning';
  }

  return (
    <div className={`metric-card fixed-cost-card ${healthStatus}`}>
      <div className="fixed-cost-header">
        <h3>Fixed Cost Floor</h3>
        <button
          className="expand-btn"
          onClick={() => setExpanded(!expanded)}
          aria-label={expanded ? 'Collapse breakdown' : 'Expand breakdown'}
        >
          {expanded ? '−' : '+'}
        </button>
      </div>

      <div className="fixed-cost-main">
        <div className="fixed-cost-value">
          {formatCurrency(total_monthly_fixed)}<span className="fixed-cost-period">/month</span>
        </div>
        <div className="fixed-cost-label">minimum fixed costs</div>
      </div>

      <div className="fixed-cost-runway">
        <span className="runway-label">Zero-revenue runway:</span>
        <span className={`runway-value ${healthStatus}`}>
          {zero_revenue_runway_months.toFixed(1)} months
        </span>
      </div>

      {expanded && breakdown && breakdown.length > 0 && (
        <div className="fixed-cost-breakdown">
          <div className="breakdown-title">Cost Breakdown</div>
          {breakdown.map((item, index) => (
            <div key={index} className="breakdown-item">
              <div className="breakdown-category">
                <span className="category-name">{item.category}</span>
                <span className="category-percentage">{item.percentage.toFixed(0)}%</span>
              </div>
              <div className="breakdown-bar-container">
                <div
                  className="breakdown-bar"
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
              <div className="breakdown-amount">{formatCurrency(item.monthly_amount)}</div>
            </div>
          ))}
        </div>
      )}

      <div className="fixed-cost-footer">
        Based on {months_analyzed}-month recurring expense analysis
      </div>
    </div>
  );
}

export default FixedCostFloorCard;
