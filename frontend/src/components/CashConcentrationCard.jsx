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

function CashConcentrationCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.getCashConcentration();
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
        <h3>Revenue Concentration</h3>
        <div className="metric-loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metric-card">
        <h3>Revenue Concentration</h3>
        <div className="metric-error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const {
    top_client_percentage,
    top_3_percentage,
    risk_level,
    top_clients,
    total_revenue,
    period_months
  } = data;

  // Determine visual styling based on risk
  let riskClass = 'low';
  let riskLabel = 'Low Risk';
  if (risk_level === 'high') {
    riskClass = 'critical';
    riskLabel = 'High Risk';
  } else if (risk_level === 'medium') {
    riskClass = 'warning';
    riskLabel = 'Medium Risk';
  }

  return (
    <div className={`metric-card concentration-card ${riskClass}`}>
      <div className="concentration-header">
        <h3>Revenue Concentration</h3>
        <span className={`risk-badge ${riskClass}`}>{riskLabel}</span>
      </div>

      <div className="concentration-main">
        <div className="concentration-metric">
          <span className="metric-value">{top_client_percentage.toFixed(0)}%</span>
          <span className="metric-label">Top Client</span>
        </div>
        <div className="concentration-divider" />
        <div className="concentration-metric">
          <span className="metric-value">{top_3_percentage.toFixed(0)}%</span>
          <span className="metric-label">Top 3 Clients</span>
        </div>
      </div>

      <div className="concentration-chart">
        {top_clients && top_clients.map((client, index) => (
          <div key={index} className="client-bar-row">
            <div className="client-info">
              <span className="client-name" title={client.client}>
                {client.client.length > 20 ? client.client.substring(0, 20) + '...' : client.client}
              </span>
              <span className="client-percentage">{client.percentage.toFixed(1)}%</span>
            </div>
            <div className="client-bar-container">
              <div
                className={`client-bar color-${index}`}
                style={{ width: `${client.percentage}%` }}
              />
            </div>
            <div className="client-amount">{formatCurrency(client.total_revenue)}</div>
          </div>
        ))}

        {/* Show "Others" if top clients don't sum to 100% */}
        {top_clients && top_3_percentage < 100 && (
          <div className="client-bar-row others">
            <div className="client-info">
              <span className="client-name">Others</span>
              <span className="client-percentage">{(100 - top_3_percentage).toFixed(1)}%</span>
            </div>
            <div className="client-bar-container">
              <div
                className="client-bar color-others"
                style={{ width: `${100 - top_3_percentage}%` }}
              />
            </div>
            <div className="client-amount">
              {formatCurrency(total_revenue * (100 - top_3_percentage) / 100)}
            </div>
          </div>
        )}
      </div>

      <div className="concentration-footer">
        Based on {period_months}-month revenue • Total: {formatCurrency(total_revenue)}
      </div>
    </div>
  );
}

export default CashConcentrationCard;
