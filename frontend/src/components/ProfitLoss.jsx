import React from 'react';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function ProfitLoss({ data }) {
  if (!data) return null;

  const { revenue, expenses, net_profit, period } = data;
  const isPositive = net_profit >= 0;

  return (
    <div className="pnl-section">
      <h2>P&L Summary ({period})</h2>
      <div className="pnl-grid">
        <div className="pnl-item">
          <label>Revenue</label>
          <div className="value revenue">{formatCurrency(revenue)}</div>
        </div>
        <div className="pnl-item">
          <label>Expenses</label>
          <div className="value expenses">{formatCurrency(expenses)}</div>
        </div>
        <div className="pnl-item">
          <label>Net Profit</label>
          <div className={`value profit ${isPositive ? 'positive' : 'negative'}`}>
            {formatCurrency(net_profit)}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfitLoss;
