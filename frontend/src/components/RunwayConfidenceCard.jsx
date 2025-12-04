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

function RunwayConfidenceCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.getRunwayConfidence();
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
        <h3>Cash Runway</h3>
        <div className="metric-loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metric-card">
        <h3>Cash Runway</h3>
        <div className="metric-error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  // Handle profitable scenario
  if (data.is_profitable) {
    return (
      <div className="metric-card runway-card profitable">
        <h3>Cash Runway</h3>
        <div className="runway-profitable">
          <div className="runway-badge success">Profitable</div>
          <div className="metric-value text-positive">
            +{formatCurrency(data.avg_monthly_surplus)}/mo
          </div>
          <div className="metric-subvalue">
            Average monthly surplus
          </div>
        </div>
        <div className="runway-footer">
          Based on {data.months_analyzed}-month history
        </div>
      </div>
    );
  }

  // Burning cash - show confidence bands
  const { best_case_months, expected_months, worst_case_months, avg_monthly_burn } = data;

  // Calculate bar widths (normalized to best case)
  const maxMonths = Math.max(best_case_months, 24);
  const bestWidth = (best_case_months / maxMonths) * 100;
  const expectedWidth = (expected_months / maxMonths) * 100;
  const worstWidth = (worst_case_months / maxMonths) * 100;

  // Determine health status
  let healthStatus = 'healthy';
  let healthLabel = 'Healthy';
  if (expected_months < 6) {
    healthStatus = 'critical';
    healthLabel = 'Critical';
  } else if (expected_months < 12) {
    healthStatus = 'warning';
    healthLabel = 'Caution';
  }

  return (
    <div className={`metric-card runway-card ${healthStatus}`}>
      <div className="runway-header">
        <h3>Cash Runway</h3>
        <span className={`runway-badge ${healthStatus}`}>{healthLabel}</span>
      </div>

      <div className="runway-main">
        <div className="runway-expected">
          <span className="runway-value">{expected_months.toFixed(1)}</span>
          <span className="runway-unit">months</span>
        </div>
        <div className="runway-burn">
          Burn: {formatCurrency(avg_monthly_burn)}/mo
        </div>
      </div>

      <div className="runway-bands">
        <div className="runway-band best">
          <div className="runway-bar" style={{ width: `${bestWidth}%` }}>
            <span className="runway-label">Best</span>
            <span className="runway-months">{best_case_months.toFixed(1)}mo</span>
          </div>
        </div>
        <div className="runway-band expected">
          <div className="runway-bar" style={{ width: `${expectedWidth}%` }}>
            <span className="runway-label">Expected</span>
            <span className="runway-months">{expected_months.toFixed(1)}mo</span>
          </div>
        </div>
        <div className="runway-band worst">
          <div className="runway-bar" style={{ width: `${worstWidth}%` }}>
            <span className="runway-label">Worst</span>
            <span className="runway-months">{worst_case_months.toFixed(1)}mo</span>
          </div>
        </div>
      </div>

      <div className="runway-footer">
        Based on {data.months_analyzed}-month cash flow variance
      </div>
    </div>
  );
}

export default RunwayConfidenceCard;
