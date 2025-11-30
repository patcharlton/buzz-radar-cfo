import React from 'react';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function CashPosition({ data }) {
  if (!data) return null;

  const { total_balance, accounts } = data;

  return (
    <div className="metric-card">
      <h3>Cash Position</h3>
      <div className="metric-value">{formatCurrency(total_balance)}</div>
      {accounts && accounts.length > 0 && (
        <div className="metric-subvalue">
          {accounts.length} account{accounts.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}

export default CashPosition;
