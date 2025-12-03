import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ClickableAmount } from '@/components/ui/clickable-amount';
import { MetricTooltip, CardTitleTooltip } from '@/components/ui/info-tooltip';
import {
  ArrowDownLeft,
  Clock,
  ChevronDown,
  ChevronUp,
  FileText,
  ExternalLink,
} from 'lucide-react';
import { formatCurrency, cn } from '@/lib/utils';
import { Sparkline } from '@/components/charts/Sparkline';
import { YoYBadge } from '@/components/ui/yoy-badge';
import { useDrillDown, DRILL_TYPES } from '@/contexts/DrillDownContext';
import { formatDistanceToNow, parseISO, differenceInDays } from 'date-fns';

export function Receivables({ data, loading, trends, yoyComparison }) {
  const { openDrill } = useDrillDown();
  const [expanded, setExpanded] = useState(false);

  const handleTotalClick = () => {
    openDrill(DRILL_TYPES.RECEIVABLES, {
      title: 'Outstanding Invoices',
    });
  };

  const handleOverdueClick = () => {
    openDrill(DRILL_TYPES.RECEIVABLES, {
      title: 'Overdue Invoices',
      filters: { overdueOnly: true },
    });
  };

  const handleInvoiceClick = (invoice) => {
    openDrill(DRILL_TYPES.RECEIVABLES_DETAIL, {
      title: `${invoice.invoice_number} - ${invoice.contact_name}`,
      filters: { invoiceId: invoice.invoice_id },
    });
  };

  // Sort invoices: overdue first (by days overdue desc), then by due date (soonest first)
  const sortedInvoices = useMemo(() => {
    const invoices = data?.invoices || [];
    return [...invoices].sort((a, b) => {
      // Overdue invoices first
      const aOverdue = a.days_overdue > 0;
      const bOverdue = b.days_overdue > 0;
      if (aOverdue && !bOverdue) return -1;
      if (!aOverdue && bOverdue) return 1;

      // If both overdue, sort by days overdue (most overdue first)
      if (aOverdue && bOverdue) {
        return (b.days_overdue || 0) - (a.days_overdue || 0);
      }

      // If neither overdue, sort by due date (soonest first)
      const aDate = a.due_date ? new Date(a.due_date) : new Date('9999-12-31');
      const bDate = b.due_date ? new Date(b.due_date) : new Date('9999-12-31');
      return aDate - bDate;
    });
  }, [data?.invoices]);

  const getStatusBadge = (invoice) => {
    const daysOverdue = invoice.days_overdue || 0;

    if (daysOverdue > 30) {
      return <Badge variant="destructive" className="text-xs">30d+</Badge>;
    }
    if (daysOverdue > 0) {
      return <Badge variant="warning" className="text-xs">{daysOverdue}d late</Badge>;
    }

    const dueDate = invoice.due_date ? parseISO(invoice.due_date) : null;
    const daysUntilDue = dueDate ? differenceInDays(dueDate, new Date()) : 0;

    if (daysUntilDue <= 7 && daysUntilDue >= 0) {
      return <Badge variant="secondary" className="text-xs">Due soon</Badge>;
    }

    return null;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <ArrowDownLeft className="h-4 w-4" />
            Receivables
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </CardContent>
      </Card>
    );
  }

  const total = data?.total || 0;
  const overdueTotal = data?.overdue || data?.overdue_total || 0;
  const invoiceCount = data?.count || data?.invoice_count || 0;
  const overdueCount = data?.overdue_count || 0;
  const hasOverdue = overdueTotal > 0;
  const hasInvoices = sortedInvoices.length > 0;

  // Sparkline data from trends prop
  const sparklineData = trends?.receivables || [];
  const yoyPct = yoyComparison?.receivables;
  const comparisonMonth = yoyComparison?.comparison_month;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="h-full"
    >
      <Card className={cn(
        'h-full flex flex-col transition-all duration-300',
        hasOverdue && 'border-amber-200 dark:border-amber-900',
        expanded && 'md:col-span-2 lg:col-span-1'
      )}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitleTooltip description="Money owed to you by customers. This is cash you're expecting to receive from unpaid invoices.">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <ArrowDownLeft className="h-4 w-4" />
                Receivables
              </CardTitle>
            </CardTitleTooltip>
            <Badge variant="secondary" className="text-xs">
              {invoiceCount} invoice{invoiceCount !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col">
          {/* Main total - clickable for full drill-down */}
          <div className="flex items-baseline gap-2 mb-1">
            <ClickableAmount
              onClick={handleTotalClick}
              className="text-3xl font-bold font-mono tabular-nums"
            >
              {formatCurrency(total)}
            </ClickableAmount>
          </div>

          {/* YoY comparison badge */}
          {yoyPct !== null && yoyPct !== undefined && (
            <div className="mt-1">
              <YoYBadge percentage={yoyPct} comparisonMonth={comparisonMonth} />
            </div>
          )}

          {/* Sparkline - hide when expanded to save space */}
          <AnimatePresence>
            {sparklineData.length > 0 && !expanded && (
              <motion.div
                initial={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3"
              >
                <Sparkline
                  data={sparklineData}
                  color="#10b981"
                  height={32}
                />
                <p className="text-xs text-muted-foreground text-center mt-1">
                  12-month trend
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Overdue callout */}
          {hasOverdue && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 mt-3 p-2 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-900 cursor-pointer hover:bg-amber-100 dark:hover:bg-amber-950/50 transition-colors"
              onClick={handleOverdueClick}
            >
              <Clock className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  {formatCurrency(overdueTotal)} overdue
                </p>
                <p className="text-xs text-amber-600 dark:text-amber-400">
                  {overdueCount} invoice{overdueCount !== 1 ? 's' : ''} past due
                </p>
              </div>
              <ExternalLink className="h-3 w-3 text-amber-500 opacity-50" />
            </motion.div>
          )}

          {/* Aging breakdown */}
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="text-center p-2 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg">
              <MetricTooltip
                label="Current"
                description="Invoices not yet past their due date. These are healthy receivables."
                className="text-xs text-muted-foreground"
              />
              <p className="text-sm font-mono tabular-nums font-medium text-emerald-600 dark:text-emerald-400">
                {formatCurrency(total - overdueTotal)}
              </p>
            </div>
            <div className="text-center p-2 bg-amber-50 dark:bg-amber-950/30 rounded-lg">
              <MetricTooltip
                label="30d"
                description="Invoices 1-30 days past due. Follow up promptly to maintain cash flow."
                className="text-xs text-muted-foreground"
              />
              <p className="text-sm font-mono tabular-nums font-medium text-amber-600 dark:text-amber-400">
                {formatCurrency(data?.aging_30 || 0)}
              </p>
            </div>
            <div className="text-center p-2 bg-red-50 dark:bg-red-950/30 rounded-lg">
              <MetricTooltip
                label="60d+"
                description="Invoices more than 60 days overdue. High risk of non-payment - consider escalation."
                className="text-xs text-muted-foreground"
              />
              <p className="text-sm font-mono tabular-nums font-medium text-red-600 dark:text-red-400">
                {formatCurrency(data?.aging_60_plus || 0)}
              </p>
            </div>
          </div>

          {/* Expand/Collapse toggle for invoice list */}
          {hasInvoices && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between w-full text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <span className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                {expanded ? 'Hide invoices' : 'View all invoices'}
              </span>
              {expanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
          )}

          {/* Expandable Invoice List */}
          <AnimatePresence>
            {expanded && hasInvoices && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="mt-3 space-y-2 max-h-64 overflow-y-auto pr-1">
                  {sortedInvoices.map((invoice, index) => (
                    <motion.div
                      key={invoice.invoice_id || invoice.invoice_number || index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                      onClick={() => handleInvoiceClick(invoice)}
                      className="p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/30 cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-800/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-sm truncate">
                            {invoice.contact_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {invoice.invoice_number}
                          </p>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="font-mono tabular-nums font-semibold text-sm">
                            {formatCurrency(invoice.amount_due)}
                          </p>
                          {getStatusBadge(invoice)}
                        </div>
                      </div>
                      {invoice.due_date && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Due {formatDistanceToNow(parseISO(invoice.due_date), { addSuffix: true })}
                        </p>
                      )}
                    </motion.div>
                  ))}
                </div>

                {/* Link to full drill-down for more options */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTotalClick();
                  }}
                  className="mt-3 w-full py-2 text-xs text-center text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors flex items-center justify-center gap-1"
                >
                  <span>View full details with filters</span>
                  <ExternalLink className="h-3 w-3" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default Receivables;
