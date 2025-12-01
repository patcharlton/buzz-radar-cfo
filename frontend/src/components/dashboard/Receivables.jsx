import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowDownLeft, Clock, AlertCircle } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';

export function Receivables({ data, loading }) {
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
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <ArrowDownLeft className="h-4 w-4" />
              Receivables
            </CardTitle>
            <Badge variant="secondary" className="text-xs">
              {invoiceCount} invoice{invoiceCount !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-3xl font-bold font-mono tabular-nums">
              {formatCurrency(total)}
            </span>
          </div>

          {/* Overdue callout */}
          {hasOverdue && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 mt-3 p-2 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-900"
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
            <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800">
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
              <p className="text-xs text-muted-foreground">Current</p>
              <p className="text-sm font-mono tabular-nums font-medium text-emerald-600 dark:text-emerald-400">
                {formatCurrency(total - overdueTotal)}
              </p>
            </div>
            <div className="text-center p-2 bg-amber-50 dark:bg-amber-950/30 rounded-lg">
              <p className="text-xs text-muted-foreground">30d</p>
              <p className="text-sm font-mono tabular-nums font-medium text-amber-600 dark:text-amber-400">
                {formatCurrency(data?.aging_30 || 0)}
              </p>
            </div>
            <div className="text-center p-2 bg-red-50 dark:bg-red-950/30 rounded-lg">
              <p className="text-xs text-muted-foreground">60d+</p>
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
