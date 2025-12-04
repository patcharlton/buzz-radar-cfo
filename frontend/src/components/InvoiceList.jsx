import React, { useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';

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

// Virtual scrolling threshold - use virtual list for larger datasets
const VIRTUAL_SCROLL_THRESHOLD = 30;
const ROW_HEIGHT = 52;
const MAX_VISIBLE_ROWS = 10;

// Row renderer for virtual list
function InvoiceRow({ invoice, style }) {
  const dueStatus = formatDueDate(invoice.days_until_due);
  return (
    <div style={style} className="invoice-row-virtual">
      <div className="invoice-cell invoice-number">{invoice.invoice_number}</div>
      <div className="invoice-cell invoice-contact">{invoice.contact_name}</div>
      <div className="invoice-cell invoice-amount">{formatCurrency(invoice.amount_due)}</div>
      <div className="invoice-cell invoice-status">
        <span className={`due-badge ${dueStatus.className}`}>
          {dueStatus.text}
        </span>
      </div>
    </div>
  );
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

  const useVirtualScroll = invoices.length > VIRTUAL_SCROLL_THRESHOLD;
  const listHeight = Math.min(invoices.length, MAX_VISIBLE_ROWS) * ROW_HEIGHT;

  // Memoized row renderer for virtual list
  const Row = useCallback(({ index, style }) => (
    <InvoiceRow invoice={invoices[index]} style={style} />
  ), [invoices]);

  // Use virtual scrolling for larger lists
  if (useVirtualScroll) {
    return (
      <div className="invoice-section">
        <h2>{title} ({invoices.length})</h2>
        <div className="invoice-table-virtual">
          <div className="invoice-header-virtual">
            <div className="invoice-cell">Invoice</div>
            <div className="invoice-cell">Customer</div>
            <div className="invoice-cell">Amount</div>
            <div className="invoice-cell">Status</div>
          </div>
          <List
            height={listHeight}
            itemCount={invoices.length}
            itemSize={ROW_HEIGHT}
            width="100%"
          >
            {Row}
          </List>
        </div>
      </div>
    );
  }

  // Standard table for smaller lists
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
