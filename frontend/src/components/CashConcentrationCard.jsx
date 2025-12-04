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

// Donut chart colors for top clients
const SEGMENT_COLORS = [
  '#6366f1', // indigo - top client
  '#8b5cf6', // violet
  '#a855f7', // purple
  '#d946ef', // fuchsia
  '#ec4899', // pink
];
const OTHERS_COLOR = '#94a3b8'; // slate-400

function CashConcentrationCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedClient, setSelectedClient] = useState(null);

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
      <div className="metric-card concentration-card">
        <h3>Cash Concentration Risk</h3>
        <div className="metric-loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metric-card concentration-card">
        <h3>Cash Concentration Risk</h3>
        <div className="metric-error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const {
    top_1_percent,
    top_3_percent,
    top_5_percent,
    concentration_risk,
    clients,
    total_received,
    client_count,
    period
  } = data;

  // Get top 5 clients and calculate "Others"
  const topClients = clients.slice(0, 5);
  const othersPercent = clients.length > 5
    ? 100 - (topClients[topClients.length - 1]?.cumulative_percent || 0)
    : 0;

  // Calculate SVG donut chart segments
  const chartSize = 160;
  const strokeWidth = 28;
  const radius = (chartSize - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  // Build segment data for donut chart
  const segments = [];
  let currentOffset = 0;

  topClients.forEach((client, index) => {
    const segmentLength = (client.percent / 100) * circumference;
    segments.push({
      client: client.client,
      percent: client.percent,
      amount: client.amount,
      color: SEGMENT_COLORS[index] || SEGMENT_COLORS[4],
      dashArray: `${segmentLength} ${circumference - segmentLength}`,
      dashOffset: -currentOffset,
    });
    currentOffset += segmentLength;
  });

  // Add "Others" segment if there are more than 5 clients
  if (othersPercent > 0) {
    const segmentLength = (othersPercent / 100) * circumference;
    segments.push({
      client: 'Others',
      percent: othersPercent,
      amount: total_received * (othersPercent / 100),
      color: OTHERS_COLOR,
      dashArray: `${segmentLength} ${circumference - segmentLength}`,
      dashOffset: -currentOffset,
    });
  }

  // Risk level styling
  const getRiskStyles = () => {
    switch (concentration_risk) {
      case 'HIGH':
        return {
          badge: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
          icon: '⚠️',
          label: 'HIGH RISK'
        };
      case 'MEDIUM':
        return {
          badge: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
          icon: '⚡',
          label: 'MEDIUM'
        };
      default:
        return {
          badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
          icon: '✓',
          label: 'LOW'
        };
    }
  };

  const riskStyles = getRiskStyles();
  const topClient = clients[0];

  return (
    <div className="metric-card concentration-card">
      <div className="concentration-header">
        <div className="concentration-title-row">
          <h3>Cash Concentration Risk</h3>
          {concentration_risk === 'HIGH' && (
            <span className="warning-icon" title="High concentration risk">⚠️</span>
          )}
        </div>
        <span className="concentration-period">{period}</span>
      </div>

      <div className="concentration-content">
        {/* Donut Chart */}
        <div className="donut-chart-container">
          <svg
            width={chartSize}
            height={chartSize}
            viewBox={`0 0 ${chartSize} ${chartSize}`}
            className="donut-chart"
          >
            {/* Background circle */}
            <circle
              cx={chartSize / 2}
              cy={chartSize / 2}
              r={radius}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth={strokeWidth}
              className="dark:stroke-zinc-700"
            />
            {/* Segment circles */}
            {segments.map((segment, index) => (
              <circle
                key={index}
                cx={chartSize / 2}
                cy={chartSize / 2}
                r={radius}
                fill="none"
                stroke={segment.color}
                strokeWidth={strokeWidth}
                strokeDasharray={segment.dashArray}
                strokeDashoffset={segment.dashOffset}
                transform={`rotate(-90 ${chartSize / 2} ${chartSize / 2})`}
                className={`donut-segment ${selectedClient === segment.client ? 'selected' : ''}`}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setSelectedClient(segment.client)}
                onMouseLeave={() => setSelectedClient(null)}
                onClick={() => setSelectedClient(selectedClient === segment.client ? null : segment.client)}
              />
            ))}
          </svg>
          {/* Center content - Risk Badge */}
          <div className="donut-center">
            <span className={`risk-badge-donut ${riskStyles.badge}`}>
              {riskStyles.label}
            </span>
          </div>
        </div>

        {/* Key Stats */}
        <div className="concentration-stats">
          {/* Top client highlight */}
          {topClient && (
            <div className="top-client-stat">
              <span className="stat-value" style={{ color: SEGMENT_COLORS[0] }}>
                {topClient.client.length > 18
                  ? topClient.client.substring(0, 18) + '...'
                  : topClient.client}
              </span>
              <span className="stat-label">
                <strong>{top_1_percent.toFixed(0)}%</strong> of revenue
              </span>
            </div>
          )}

          {/* Summary line */}
          <div className="concentration-summary">
            Top 3 clients = <strong>{top_3_percent.toFixed(0)}%</strong> of cash received
          </div>

          {/* Client legend */}
          <div className="client-legend">
            {segments.map((segment, index) => (
              <div
                key={index}
                className={`legend-item ${selectedClient === segment.client ? 'selected' : ''}`}
                onMouseEnter={() => setSelectedClient(segment.client)}
                onMouseLeave={() => setSelectedClient(null)}
              >
                <span
                  className="legend-color"
                  style={{ backgroundColor: segment.color }}
                />
                <span className="legend-label" title={segment.client}>
                  {segment.client.length > 12
                    ? segment.client.substring(0, 12) + '...'
                    : segment.client}
                </span>
                <span className="legend-percent">{segment.percent.toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Selected client detail */}
      {selectedClient && (
        <div className="selected-client-detail">
          {(() => {
            const client = segments.find(s => s.client === selectedClient);
            if (!client) return null;
            return (
              <>
                <span className="detail-name">{client.client}</span>
                <span className="detail-amount">{formatCurrency(client.amount)}</span>
                <span className="detail-percent">({client.percent.toFixed(1)}%)</span>
              </>
            );
          })()}
        </div>
      )}

      <div className="concentration-footer">
        {client_count} clients • Total received: {formatCurrency(total_received)}
      </div>
    </div>
  );
}

export default CashConcentrationCard;
