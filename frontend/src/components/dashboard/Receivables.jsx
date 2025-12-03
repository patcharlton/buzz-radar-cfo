import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ClickableAmount } from '@/components/ui/clickable-amount';
import { MetricTooltip, CardTitleTooltip } from '@/components/ui/info-tooltip';
import { ArrowDownLeft, Clock, AlertCircle } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';
import { Sparkline } from '@/components/charts/Sparkline';
import { YoYBadge } from '@/components/ui/yoy-badge';
import { useDrillDown, DRILL_TYPES } from '@/contexts/DrillDownContext';

export function Receivables({ data, loading, trends, yoyComparison }) {
  const { openDrill } = useDrillDown();

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
  const largestInvoice = data?.invoices?.[0];
  const hasOverdue = overdueTotal > 0;

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
      <Card className={`h-full ${hasOverdue ? 'border-amber-200 dark:border-amber-900' : ''}`}>
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
        <CardContent>
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

          {/* 12-month sparkline */}
          {sparklineData.length > 0 && (
            <div className="mt-3">
              <Sparkline
                data={sparklineData}
                color="#10b981"
                height={32}
              />
              <p className="text-xs text-muted-foreground text-center mt-1">
                12-month trend
              </p>
            </div>
          )}

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
            </motion.div>
          )}

          {/* Largest invoice */}
          {largestInvoice && (
            <div
              className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/50 -mx-6 px-6 py-2 transition-colors"
              onClick={() => handleInvoiceClick(largestInvoice)}
            >
              <p className="text-xs text-muted-foreground mb-1">Largest Outstanding</p>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium truncate flex-1 mr-2">
                  {largestInvoice.contact_name}
                </span>
                <span className="text-sm font-mono tabular-nums text-positive">
                  {formatCurrency(largestInvoice.amount_due)}
                </span>
              </div>
            </div>
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
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default Receivables;
