import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowUpRight, Calendar, AlertTriangle } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';

export function Payables({ data, loading }) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <ArrowUpRight className="h-4 w-4" />
            Payables
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
  const billCount = data?.count || data?.bill_count || 0;
  const dueThisWeek = data?.due_this_week || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="h-full"
    >
      <Card className="h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <ArrowUpRight className="h-4 w-4" />
              Payables
            </CardTitle>
            <Badge variant="secondary" className="text-xs">
              {billCount} bill{billCount !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-3xl font-bold font-mono tabular-nums text-negative">
              {formatCurrency(total)}
            </span>
          </div>

          {/* Due this week */}
          {dueThisWeek > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 mt-3 p-2 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-900"
            >
              <Calendar className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  {formatCurrency(dueThisWeek)} due this week
                </p>
              </div>
            </motion.div>
          )}

          {/* Overdue warning */}
          {overdueTotal > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="flex items-center gap-2 mt-3 p-2 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-900"
            >
              <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  {formatCurrency(overdueTotal)} overdue
                </p>
              </div>
            </motion.div>
          )}

          {/* Net position */}
          <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Next 30 days</span>
              <span className="font-mono tabular-nums font-medium text-negative">
                -{formatCurrency(data?.due_30_days || total)}
              </span>
            </div>
          </div>

          {/* Payment schedule */}
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="text-center p-2 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg">
              <p className="text-xs text-muted-foreground">This week</p>
              <p className="text-sm font-mono tabular-nums font-medium text-emerald-600 dark:text-emerald-400">
                {formatCurrency(dueThisWeek)}
              </p>
            </div>
            <div className="text-center p-2 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
              <p className="text-xs text-muted-foreground">Next week</p>
              <p className="text-sm font-mono tabular-nums font-medium text-blue-600 dark:text-blue-400">
                {formatCurrency(data?.due_next_week || 0)}
              </p>
            </div>
            <div className="text-center p-2 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
              <p className="text-xs text-muted-foreground">Later</p>
              <p className="text-sm font-mono tabular-nums font-medium">
                {formatCurrency(data?.due_later || 0)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default Payables;
