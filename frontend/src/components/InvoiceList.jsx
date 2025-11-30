import React from 'react';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDueDate(daysUntilDue) {
  if (daysUntilDue === null) return { text: 'No date', className: 'on-time' };

  if (daysUntilDue < 0) {
    const overdueDays = Math.abs(daysUntilDue);
    return {
      text: overdueDays === 1 ? '1 day overdue' : `${overdueDays} days overdue`,
      className: 'overdue',
    };
  }

  if (daysUntilDue === 0) {
    return { text: 'Due today', className: 'due-soon' };
  }

  if (daysUntilDue <= 7) {
    return {
      text: daysUntilDue === 1 ? 'Due in 1 day' : `Due in ${daysUntilDue} days`,
      className: 'due-soon',
    };
  }

  return {
    text: `Due in ${daysUntilDue} days`,
    className: 'on-time',
  };
}

function InvoiceList({ invoices, title = 'Outstanding Invoices' }) {
  if (!invoices || invoices.length === 0) {
    return (
      <div className="invoice-section">
        <h2>{title}</h2>
        <p style={{ color: '#64748b', padding: '20px 0' }}>No outstanding invoices</p>
      </div>
    );
  }

  return (
    <div className="invoice-section">
      <h2>{title}</h2>
      <table className="invoice-table">
        <thead>
          <tr>
            <th>Invoice</th>
            <th>Customer</th>
            <th>Amount</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((invoice) => {
            const dueStatus = formatDueDate(invoice.days_until_due);
            return (
              <tr key={invoice.invoice_id}>
                <td className="invoice-number">{invoice.invoice_number}</td>
                <td>{invoice.contact_name}</td>
                <td className="invoice-amount">{formatCurrency(invoice.amount_due)}</td>
                <td>
                  <span className={`due-badge ${dueStatus.className}`}>
                    {dueStatus.text}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default InvoiceList;
