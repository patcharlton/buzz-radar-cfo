import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Search,
  ArrowLeft,
  ExternalLink,
  Download,
  ChevronRight,
  Loader2,
  AlertCircle,
  FileText,
  RefreshCw,
} from 'lucide-react';
import { format, parseISO, subDays, subMonths, startOfYear } from 'date-fns';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useDrillDown, DRILL_TYPES } from '@/contexts/DrillDownContext';
import api, { xeroLinks } from '@/services/api';
import { formatCurrency } from '@/lib/utils';

/**
 * Slide-in drawer for transaction drill-down views
 */
export function DrillDownDrawer() {
  const {
    isOpen,
    drillType,
    title,
    filters,
    breadcrumb,
    closeDrill,
    goBack,
    openDrill,
    updateFilters,
  } = useDrillDown();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  // Default to 'all' for receivables/payables to show historical CSV data
  const [dateRange, setDateRange] = useState('all');
  const [statusFilter, setStatusFilter] = useState('ALL'); // Default to all statuses to show historical data
  const [cashSource, setCashSource] = useState('transactions'); // 'transactions' = Accounting API (Finance API requires special approval)

  // Date range presets
  const getDateRangeFilters = useCallback(() => {
    const today = new Date();
    let fromDate;

    switch (dateRange) {
      case '30':
        fromDate = subDays(today, 30);
        break;
      case '90':
        fromDate = subDays(today, 90);
        break;
      case '180':
        fromDate = subMonths(today, 6);
        break;
      case '365':
        fromDate = subMonths(today, 12);
        break;
      case '730':
        fromDate = subMonths(today, 24); // 2 years
        break;
      case '1825':
        fromDate = subMonths(today, 60); // 5 years
        break;
      case 'ytd':
        fromDate = startOfYear(today);
        break;
      case 'all':
        // Pass null for fromDate so backend fetches all history (no start date filter)
        return { fromDate: null, toDate: format(today, 'yyyy-MM-dd') };
      default:
        fromDate = subDays(today, 90);
    }

    return {
      fromDate: format(fromDate, 'yyyy-MM-dd'),
      toDate: format(today, 'yyyy-MM-dd'),
    };
  }, [dateRange]);

  // Fetch data when drill type or filters change
  useEffect(() => {
    if (!isOpen || !drillType) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        let result;
        const dateFilters = getDateRangeFilters();
        const combinedFilters = { ...filters, ...dateFilters };

        // Always use historical data for receivables/payables - contains complete CSV import
        // Xero API only returns recent data, historical import has full history

        switch (drillType) {
          case DRILL_TYPES.CASH:
            // Use Finance API (bank statements) or Accounting API (transactions)
            if (cashSource === 'statements') {
              result = await api.drillCashStatements({ ...combinedFilters, page });
            } else {
              result = await api.drillCash({ ...combinedFilters, page });
            }
            break;
          case DRILL_TYPES.RECEIVABLES:
            // Always use historical data - contains complete invoice history
            result = await api.drillHistoricalReceivables({ ...combinedFilters, status: statusFilter === 'ALL' ? null : statusFilter, page });
            break;
          case DRILL_TYPES.RECEIVABLES_DETAIL:
            // Historical invoices have IDs like "hist_123"
            result = await api.drillHistoricalInvoice(filters.invoiceId);
            break;
          case DRILL_TYPES.PAYABLES:
            // Always use historical data - contains complete bill history
            result = await api.drillHistoricalPayables({ ...combinedFilters, status: statusFilter === 'ALL' ? null : statusFilter, page });
            break;
          case DRILL_TYPES.PAYABLES_DETAIL:
            // Historical invoices have IDs like "hist_123"
            result = await api.drillHistoricalInvoice(filters.invoiceId);
            break;
          case DRILL_TYPES.PNL:
            result = await api.drillPnl(combinedFilters);
            break;
          case DRILL_TYPES.PNL_ACCOUNT:
            result = await api.drillPnlAccount(filters.accountId, { ...combinedFilters, page });
            break;
          default:
            throw new Error(`Unknown drill type: ${drillType}`);
        }

        if (!result.success) {
          throw new Error(result.error || 'Failed to fetch data');
        }

        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [isOpen, drillType, filters, page, dateRange, statusFilter, cashSource, getDateRangeFilters]);

  // Reset page when filters or date range change
  useEffect(() => {
    setPage(1);
  }, [filters, dateRange, statusFilter, cashSource]);

  // Filter data client-side by search query
  const filteredData = useMemo(() => {
    if (!data || !searchQuery.trim()) return data;

    const query = searchQuery.toLowerCase();

    // Clone data to avoid mutating
    const filtered = { ...data };

    if (filtered.transactions) {
      filtered.transactions = filtered.transactions.filter(t =>
        (t.description || '').toLowerCase().includes(query) ||
        (t.reference || '').toLowerCase().includes(query) ||
        (t.contact_name || '').toLowerCase().includes(query)
      );
    }

    if (filtered.invoices) {
      filtered.invoices = filtered.invoices.filter(inv =>
        (inv.invoice_number || '').toLowerCase().includes(query) ||
        (inv.reference || '').toLowerCase().includes(query) ||
        (inv.contact_name || '').toLowerCase().includes(query)
      );
    }

    if (filtered.journals) {
      filtered.journals = filtered.journals.filter(j =>
        (j.description || '').toLowerCase().includes(query) ||
        (j.reference || '').toLowerCase().includes(query) ||
        (j.account_name || '').toLowerCase().includes(query)
      );
    }

    if (filtered.categories) {
      filtered.categories = filtered.categories.filter(c =>
        (c.category || '').toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [data, searchQuery]);

  // Export to CSV
  const handleExport = useCallback(() => {
    if (!filteredData) return;

    let csvContent = '';
    let filename = `${drillType}-export-${format(new Date(), 'yyyy-MM-dd')}.csv`;

    if (filteredData.transactions) {
      csvContent = 'Date,Description,Contact,Reference,Amount,Reconciled\n';
      filteredData.transactions.forEach(t => {
        csvContent += `"${t.date || ''}","${t.description || ''}","${t.contact_name || ''}","${t.reference || ''}",${t.amount || 0},"${t.is_reconciled ? 'Yes' : 'No'}"\n`;
      });
    } else if (filteredData.invoices) {
      csvContent = 'Invoice #,Contact,Issue Date,Due Date,Amount Due,Status,Overdue\n';
      filteredData.invoices.forEach(inv => {
        csvContent += `"${inv.invoice_number || ''}","${inv.contact_name || ''}","${inv.issue_date || ''}","${inv.due_date || ''}",${inv.amount_due || 0},"${inv.status || ''}","${inv.is_overdue ? 'Yes' : 'No'}"\n`;
      });
    } else if (filteredData.journals) {
      csvContent = 'Date,Account,Description,Reference,Debit,Credit\n';
      filteredData.journals.forEach(j => {
        csvContent += `"${j.date || ''}","${j.account_name || ''}","${j.description || ''}","${j.reference || ''}",${j.debit || 0},${j.credit || 0}\n`;
      });
    } else if (filteredData.categories) {
      csvContent = 'Category,Total\n';
      filteredData.categories.forEach(c => {
        csvContent += `"${c.category || ''}",${c.total || 0}\n`;
      });
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }, [filteredData, drillType]);

  // Handle clicking on an invoice to see line items
  const handleInvoiceClick = useCallback((invoice) => {
    const type = drillType === DRILL_TYPES.RECEIVABLES
      ? DRILL_TYPES.RECEIVABLES_DETAIL
      : DRILL_TYPES.PAYABLES_DETAIL;

    openDrill(type, {
      title: `${invoice.invoice_number} - ${invoice.contact_name}`,
      filters: { invoiceId: invoice.invoice_id },
      addToBreadcrumb: true,
    });
  }, [drillType, openDrill]);

  // Handle clicking on a P&L category to see transactions
  const handleCategoryClick = useCallback((category, account) => {
    openDrill(DRILL_TYPES.PNL_ACCOUNT, {
      title: `${account.account_name} Transactions`,
      filters: {
        accountId: account.account_id,
        fromDate: filters.fromDate,
        toDate: filters.toDate,
      },
      addToBreadcrumb: true,
    });
  }, [openDrill, filters]);

  // Render content based on drill type
  const renderContent = () => {
    if (loading) {
      return <LoadingSkeleton />;
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
          <p className="text-lg font-medium text-red-600 mb-2">Failed to load data</p>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => setPage(p => p)} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        </div>
      );
    }

    if (!filteredData) {
      return null;
    }

    switch (drillType) {
      case DRILL_TYPES.CASH:
        return <CashTransactionTable data={filteredData} />;
      case DRILL_TYPES.RECEIVABLES:
        return <InvoiceTable data={filteredData} onInvoiceClick={handleInvoiceClick} type="invoice" />;
      case DRILL_TYPES.RECEIVABLES_DETAIL:
      case DRILL_TYPES.PAYABLES_DETAIL:
        return <InvoiceDetailView data={filteredData} type={drillType === DRILL_TYPES.RECEIVABLES_DETAIL ? 'invoice' : 'bill'} />;
      case DRILL_TYPES.PAYABLES:
        return <InvoiceTable data={filteredData} onInvoiceClick={handleInvoiceClick} type="bill" />;
      case DRILL_TYPES.PNL:
        return <PnlCategoryTable data={filteredData} onCategoryClick={handleCategoryClick} />;
      case DRILL_TYPES.PNL_ACCOUNT:
        return <JournalTable data={filteredData} />;
      default:
        return <p>Unknown drill type</p>;
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeDrill}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full sm:w-[600px] lg:w-[700px] bg-white dark:bg-zinc-900 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="sticky top-0 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-4 py-3 z-10">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {breadcrumb.length > 0 && (
                    <Button variant="ghost" size="icon" onClick={goBack} className="h-8 w-8">
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                  )}
                  <h2 className="text-lg font-semibold">{title}</h2>
                </div>
                <Button variant="ghost" size="icon" onClick={closeDrill} className="h-8 w-8">
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Summary bar */}
              {filteredData?.summary && (
                <SummaryBar summary={filteredData.summary} drillType={drillType} />
              )}

              {/* Search, date filter, and export */}
              <div className="flex items-center gap-2 mt-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                {/* Note: Finance API Bank Statements require special Xero approval */}
                {/* Status filter for Receivables/Payables */}
                {[DRILL_TYPES.RECEIVABLES, DRILL_TYPES.PAYABLES].includes(drillType) && (
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="AUTHORISED">Outstanding</SelectItem>
                      <SelectItem value="PAID">Paid</SelectItem>
                      <SelectItem value="ALL">All statuses</SelectItem>
                    </SelectContent>
                  </Select>
                )}
                {/* Date range filter - show for CASH, RECEIVABLES, PAYABLES, PNL */}
                {[DRILL_TYPES.CASH, DRILL_TYPES.RECEIVABLES, DRILL_TYPES.PAYABLES, DRILL_TYPES.PNL, DRILL_TYPES.PNL_ACCOUNT].includes(drillType) && (
                  <Select value={dateRange} onValueChange={setDateRange}>
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="Date range" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="30">Last 30 days</SelectItem>
                      <SelectItem value="90">Last 90 days</SelectItem>
                      <SelectItem value="180">Last 6 months</SelectItem>
                      <SelectItem value="365">Last 12 months</SelectItem>
                      <SelectItem value="730">Last 2 years</SelectItem>
                      <SelectItem value="1825">Last 5 years</SelectItem>
                      <SelectItem value="ytd">Year to date</SelectItem>
                      <SelectItem value="all">All history</SelectItem>
                    </SelectContent>
                  </Select>
                )}
                <Button variant="outline" size="sm" onClick={handleExport} className="gap-1.5">
                  <Download className="h-4 w-4" />
                  CSV
                </Button>
              </div>

              {/* Date range display */}
              {(filteredData?.from_date || filteredData?.to_date) && (
                <p className="text-xs text-muted-foreground mt-2">
                  Showing: {filteredData.from_date && formatDate(filteredData.from_date)}
                  {filteredData.from_date && filteredData.to_date && ' – '}
                  {filteredData.to_date && formatDate(filteredData.to_date)}
                </p>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
              {renderContent()}
            </div>

            {/* Pagination */}
            {filteredData?.has_more && (
              <div className="sticky bottom-0 bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800 px-4 py-3 flex justify-center">
                <Button
                  variant="outline"
                  onClick={() => setPage(p => p + 1)}
                  disabled={loading}
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : null}
                  Load More
                </Button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

function SummaryBar({ summary, drillType }) {
  const items = [];

  if (drillType === DRILL_TYPES.CASH) {
    if (summary.total_in !== undefined) items.push({ label: 'Money In', value: formatCurrency(summary.total_in), color: 'text-emerald-600' });
    if (summary.total_out !== undefined) items.push({ label: 'Money Out', value: formatCurrency(summary.total_out), color: 'text-red-600' });
    if (summary.net_change !== undefined) items.push({ label: 'Net', value: formatCurrency(summary.net_change), color: summary.net_change >= 0 ? 'text-emerald-600' : 'text-red-600' });
  } else if (drillType === DRILL_TYPES.RECEIVABLES || drillType === DRILL_TYPES.PAYABLES) {
    if (summary.total_outstanding !== undefined) items.push({ label: 'Outstanding', value: formatCurrency(summary.total_outstanding) });
    if (summary.total_overdue !== undefined && summary.total_overdue > 0) items.push({ label: 'Overdue', value: formatCurrency(summary.total_overdue), color: 'text-red-600' });
    if (summary.invoice_count !== undefined) items.push({ label: 'Count', value: summary.invoice_count || summary.bill_count });
  } else if (drillType === DRILL_TYPES.PNL_ACCOUNT) {
    if (summary.total_debits !== undefined) items.push({ label: 'Debits', value: formatCurrency(summary.total_debits) });
    if (summary.total_credits !== undefined) items.push({ label: 'Credits', value: formatCurrency(summary.total_credits) });
    if (summary.net_amount !== undefined) items.push({ label: 'Net', value: formatCurrency(summary.net_amount) });
  }

  if (items.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-4 text-sm">
      {items.map((item, i) => (
        <div key={i}>
          <span className="text-muted-foreground">{item.label}: </span>
          <span className={`font-medium font-mono ${item.color || ''}`}>{item.value}</span>
        </div>
      ))}
    </div>
  );
}

function CashTransactionTable({ data }) {
  const transactions = data.transactions || [];

  if (transactions.length === 0) {
    return <EmptyState message="No transactions found" />;
  }

  return (
    <div className="space-y-2">
      {transactions.map((txn) => (
        <div
          key={txn.transaction_id}
          className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium truncate">{txn.description || 'No description'}</span>
              {txn.is_reconciled && (
                <Badge variant="secondary" className="text-xs">Reconciled</Badge>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-0.5">
              <span>{formatDate(txn.date)}</span>
              {txn.contact_name && (
                <>
                  <span>•</span>
                  <span className="truncate">{txn.contact_name}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`font-mono font-medium ${txn.amount >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {txn.amount >= 0 ? '+' : ''}{formatCurrency(txn.amount)}
            </span>
            <a
              href={xeroLinks.bankTransaction(txn.transaction_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground"
              title="View in Xero"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}

function InvoiceTable({ data, onInvoiceClick, type }) {
  const invoices = data.invoices || [];

  if (invoices.length === 0) {
    return <EmptyState message={`No ${type === 'invoice' ? 'invoices' : 'bills'} found`} />;
  }

  return (
    <div className="space-y-2">
      {invoices.map((inv) => (
        <div
          key={inv.invoice_id}
          className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          onClick={() => onInvoiceClick(inv)}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium">{inv.invoice_number}</span>
              {inv.status === 'PAID' && (
                <Badge variant="outline" className="text-xs text-emerald-600 border-emerald-600">
                  Paid
                </Badge>
              )}
              {inv.is_overdue && (
                <Badge variant="destructive" className="text-xs">
                  {inv.days_overdue}d overdue
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-0.5">
              <span className="truncate">{inv.contact_name}</span>
              <span>•</span>
              <span>Due {formatDate(inv.due_date)}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className={`font-mono font-medium ${inv.status === 'PAID' ? 'text-muted-foreground' : ''}`}>
                {formatCurrency(inv.total)}
              </span>
              {inv.amount_due > 0 && inv.amount_due !== inv.total && (
                <div className="text-xs text-amber-600 font-mono">
                  {formatCurrency(inv.amount_due)} due
                </div>
              )}
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
            <a
              href={type === 'invoice' ? xeroLinks.invoice(inv.invoice_id) : xeroLinks.bill(inv.invoice_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground"
              title="View in Xero"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}

function InvoiceDetailView({ data, type }) {
  const invoice = data.invoice;

  if (!invoice) {
    return <EmptyState message="Invoice not found" />;
  }

  return (
    <div className="space-y-6">
      {/* Invoice header */}
      <div className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">{invoice.invoice_number}</h3>
            <p className="text-muted-foreground">{invoice.contact_name}</p>
          </div>
          <Badge variant={invoice.status === 'PAID' ? 'default' : 'secondary'}>
            {invoice.status}
          </Badge>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Issue Date:</span>
            <span className="ml-2">{formatDate(invoice.issue_date)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Due Date:</span>
            <span className="ml-2">{formatDate(invoice.due_date)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Subtotal:</span>
            <span className="ml-2 font-mono">{formatCurrency(invoice.subtotal)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Tax:</span>
            <span className="ml-2 font-mono">{formatCurrency(invoice.tax)}</span>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700 flex justify-between items-center">
          <span className="font-medium">Total</span>
          <span className="text-xl font-bold font-mono">{formatCurrency(invoice.total)}</span>
        </div>
        {invoice.amount_due > 0 && (
          <div className="flex justify-between items-center text-red-600 mt-2">
            <span className="font-medium">Amount Due</span>
            <span className="font-bold font-mono">{formatCurrency(invoice.amount_due)}</span>
          </div>
        )}
      </div>

      {/* Line items */}
      <div>
        <h4 className="font-medium mb-3">Line Items</h4>
        <div className="space-y-2">
          {invoice.line_items?.map((item, i) => (
            <div
              key={item.line_item_id || i}
              className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{item.description || 'No description'}</p>
                <p className="text-sm text-muted-foreground">
                  {item.quantity} × {formatCurrency(item.unit_price)}
                  {item.account_code && <span className="ml-2">({item.account_code})</span>}
                </p>
              </div>
              <span className="font-mono font-medium">{formatCurrency(item.amount)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* View in Xero */}
      <div className="flex justify-center">
        <a
          href={type === 'invoice' ? xeroLinks.invoice(invoice.invoice_id) : xeroLinks.bill(invoice.invoice_id)}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700"
        >
          <ExternalLink className="h-4 w-4" />
          View in Xero
        </a>
      </div>
    </div>
  );
}

function PnlCategoryTable({ data, onCategoryClick }) {
  const categories = data.categories || [];

  if (categories.length === 0) {
    return <EmptyState message="No P&L categories found" />;
  }

  return (
    <div className="space-y-4">
      {categories.map((cat, i) => (
        <div key={i} className="border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <div className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800/50">
            <span className="font-medium">{cat.category}</span>
            <span className="font-mono font-bold">{formatCurrency(cat.total)}</span>
          </div>
          {cat.accounts && cat.accounts.length > 0 && (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {cat.accounts.map((acc, j) => (
                <div
                  key={j}
                  className="flex items-center justify-between p-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/30 cursor-pointer transition-colors"
                  onClick={() => onCategoryClick(cat, acc)}
                >
                  <span className="text-sm">{acc.account_name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">{formatCurrency(acc.amount)}</span>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function JournalTable({ data }) {
  const journals = data.journals || [];

  if (journals.length === 0) {
    return <EmptyState message="No journal entries found" />;
  }

  return (
    <div className="space-y-2">
      {journals.map((j, i) => (
        <div
          key={`${j.journal_id}-${i}`}
          className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg"
        >
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{j.description || 'No description'}</p>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-0.5">
              <span>{formatDate(j.date)}</span>
              {j.source_type && (
                <>
                  <span>•</span>
                  <span>{j.source_type}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            {j.debit > 0 && (
              <div className="text-right">
                <span className="text-xs text-muted-foreground">DR</span>
                <span className="ml-1 font-mono">{formatCurrency(j.debit)}</span>
              </div>
            )}
            {j.credit > 0 && (
              <div className="text-right">
                <span className="text-xs text-muted-foreground">CR</span>
                <span className="ml-1 font-mono">{formatCurrency(j.credit)}</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <FileText className="h-12 w-12 text-muted-foreground mb-4" />
      <p className="text-muted-foreground">{message}</p>
    </div>
  );
}

// =============================================================================
// HELPERS
// =============================================================================

function formatDate(dateStr) {
  if (!dateStr) return '';
  // Only try to parse if it looks like a date (YYYY-MM-DD format)
  if (typeof dateStr !== 'string' || !/^\d{4}-\d{2}-\d{2}/.test(dateStr)) {
    return String(dateStr);
  }
  try {
    return format(parseISO(dateStr), 'd MMM yyyy');
  } catch {
    return dateStr;
  }
}

export default DrillDownDrawer;

