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

function formatPercentChange(change) {
  if (change === null || change === undefined) return 'New';
  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(0)}%`;
}

function VendorSpendCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.getVendorTrends(selectedYear);
        if (result.success) {
          setData(result);
          // Set default year if not set
          if (!selectedYear && result.available_years && result.available_years.length > 0) {
            setSelectedYear(result.available_years[0]);
          }
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
  }, [selectedYear]);

  if (loading && !data) {
    return (
      <div className="metric-card vendor-card">
        <h3>Vendor Spend Trends</h3>
        <div className="metric-loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metric-card vendor-card">
        <h3>Vendor Spend Trends</h3>
        <div className="metric-error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const { vendors, total_spend, yoy_change, available_years, year } = data;

  // Find max spend for bar scaling
  const maxSpend = vendors && vendors.length > 0
    ? Math.max(...vendors.map(v => v.current_year_spend || 0))
    : 0;

  return (
    <div className="metric-card vendor-card full-width">
      <div className="vendor-header">
        <h3>Vendor Spend Trends</h3>
        <div className="vendor-controls">
          {available_years && available_years.length > 1 && (
            <select
              value={year || ''}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="year-select"
            >
              {available_years.map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="vendor-summary">
        <div className="vendor-total">
          <span className="total-label">Total Vendor Spend ({year})</span>
          <span className="total-value">{formatCurrency(total_spend)}</span>
        </div>
        {yoy_change !== null && (
          <div className={`vendor-yoy ${yoy_change >= 0 ? 'increase' : 'decrease'}`}>
            <span className="yoy-value">{formatPercentChange(yoy_change)}</span>
            <span className="yoy-label">vs prior year</span>
          </div>
        )}
      </div>

      <div className="vendor-list">
        {vendors && vendors.map((vendor, index) => (
          <div key={index} className="vendor-item">
            <div className="vendor-rank">{index + 1}</div>
            <div className="vendor-details">
              <div className="vendor-name">{vendor.vendor}</div>
              <div className="vendor-bar-container">
                <div
                  className="vendor-bar"
                  style={{ width: `${maxSpend > 0 ? (vendor.current_year_spend / maxSpend) * 100 : 0}%` }}
                />
              </div>
            </div>
            <div className="vendor-amounts">
              <div className="vendor-current">{formatCurrency(vendor.current_year_spend)}</div>
              <div className={`vendor-change ${
                vendor.yoy_change === null ? 'new' :
                vendor.yoy_change >= 0 ? 'increase' : 'decrease'
              }`}>
                {formatPercentChange(vendor.yoy_change)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {vendors && vendors.length === 0 && (
        <div className="vendor-empty">No vendor data available for {year}</div>
      )}
    </div>
  );
}

export default VendorSpendCard;
