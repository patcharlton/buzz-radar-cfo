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

function VendorSpendCard({ onDrillDown }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Request more vendors so we can show all if needed
        const result = await api.getVendorTrends(null, 50);
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

  const handleVendorClick = (vendor) => {
    if (onDrillDown) {
      // Open drill-down drawer with vendor transactions
      onDrillDown({
        type: 'vendor',
        vendor: vendor.vendor,
        year: data.current_year
      });
    }
  };

  if (loading) {
    return (
      <div className="metric-card vendor-card full-width">
        <h3>Vendor Spend Trends</h3>
        <div className="metric-loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metric-card vendor-card full-width">
        <h3>Vendor Spend Trends</h3>
        <div className="metric-error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const {
    top_vendors,
    total_current,
    total_prior,
    overall_change_pct,
    current_year,
    prior_year,
    period,
    all_vendors_count,
    new_vendors_count
  } = data;

  const displayedVendors = showAll ? top_vendors : top_vendors.slice(0, 10);
  const hasMore = top_vendors.length > 10;

  return (
    <div className="metric-card vendor-card full-width">
      <div className="vendor-header">
        <div className="vendor-title-section">
          <h3>Vendor Spend Trends</h3>
          <span className="vendor-period">{period}</span>
        </div>
        <div className="vendor-summary-badge">
          {overall_change_pct !== null && (
            <span className={`change-badge ${overall_change_pct >= 0 ? 'increase' : 'decrease'}`}>
              Total spend {overall_change_pct >= 0 ? '↑' : '↓'} {Math.abs(overall_change_pct).toFixed(1)}% YoY
            </span>
          )}
        </div>
      </div>

      <div className="vendor-totals">
        <div className="vendor-total-item">
          <span className="total-label">{current_year}</span>
          <span className="total-value">{formatCurrency(total_current)}</span>
        </div>
        <div className="vendor-total-item">
          <span className="total-label">{prior_year}</span>
          <span className="total-value muted">{formatCurrency(total_prior)}</span>
        </div>
        {new_vendors_count > 0 && (
          <div className="vendor-total-item">
            <span className="total-label">New Vendors</span>
            <span className="total-value new-badge">{new_vendors_count}</span>
          </div>
        )}
      </div>

      <div className="vendor-table">
        <div className="vendor-table-header">
          <div className="vendor-col vendor-col-name">Vendor</div>
          <div className="vendor-col vendor-col-amount">{current_year}</div>
          <div className="vendor-col vendor-col-amount">{prior_year}</div>
          <div className="vendor-col vendor-col-change">Change</div>
        </div>
        <div className="vendor-table-body">
          {displayedVendors.map((vendor, index) => (
            <div
              key={index}
              className={`vendor-table-row ${onDrillDown ? 'clickable' : ''}`}
              onClick={() => handleVendorClick(vendor)}
            >
              <div className="vendor-col vendor-col-name">
                <span className="vendor-rank">{index + 1}</span>
                <span className="vendor-name" title={vendor.vendor}>
                  {vendor.vendor}
                </span>
              </div>
              <div className="vendor-col vendor-col-amount">
                {formatCurrency(vendor.current_year)}
              </div>
              <div className="vendor-col vendor-col-amount muted">
                {vendor.prior_year > 0 ? formatCurrency(vendor.prior_year) : '—'}
              </div>
              <div className="vendor-col vendor-col-change">
                {vendor.is_new ? (
                  <span className="new-vendor-badge">NEW</span>
                ) : vendor.change_percent !== null ? (
                  <span className={`change-indicator ${vendor.change_percent >= 0 ? 'increase' : 'decrease'}`}>
                    {vendor.change_percent >= 0 ? '↑' : '↓'} {Math.abs(vendor.change_percent).toFixed(0)}%
                  </span>
                ) : (
                  <span className="change-indicator neutral">—</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {hasMore && (
        <button
          className="vendor-show-more"
          onClick={() => setShowAll(!showAll)}
        >
          {showAll ? `Show less` : `Show all ${all_vendors_count} vendors`}
        </button>
      )}
    </div>
  );
}

export default VendorSpendCard;
