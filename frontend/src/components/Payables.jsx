import React from 'react';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function Payables({ data }) {
  if (!data) return null;

  const { total, overdue, count, overdue_count } = data;

  return (
    <div className="metric-card">
      <h3>Payables</h3>
      <div className="metric-value">{formatCurrency(total)}</div>
      <div className="metric-subvalue">
        {count} outstanding bill{count !== 1 ? 's' : ''}
      </div>
      {overdue > 0 && (
        <div className="metric-subvalue overdue">
          {formatCurrency(overdue)} overdue ({overdue_count} bill{overdue_count !== 1 ? 's' : ''})
        </div>
      )}
    </div>
  );
}

export default Payables;
