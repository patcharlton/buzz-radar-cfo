import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ClickableAmount } from '@/components/ui/clickable-amount';
import { MetricTooltip, CardTitleTooltip } from '@/components/ui/info-tooltip';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  ArrowUpRight,
  Calendar,
  AlertTriangle,
  TrendingUp,
  ChevronDown,
  RefreshCw,
  Building2,
} from 'lucide-react';
import { formatCurrency, cn } from '@/lib/utils';
import api from '@/services/api';
import { Sparkline } from '@/components/charts/Sparkline';
import { YoYBadge } from '@/components/ui/yoy-badge';
import { useDrillDown, DRILL_TYPES } from '@/contexts/DrillDownContext';

export function Payables({ data, loading, trends, yoyComparison }) {
  const { openDrill } = useDrillDown();

  const handleTotalClick = () => {
    openDrill(DRILL_TYPES.PAYABLES, {
      title: 'Outstanding Bills',
    });
  };

  const handleOverdueClick = () => {
    openDrill(DRILL_TYPES.PAYABLES, {
      title: 'Overdue Bills',
      filters: { overdueOnly: true },
    });
  };
  const [recurringCosts, setRecurringCosts] = useState(null);
  const [costsLoading, setCostsLoading] = useState(false);
  const [showPredictions, setShowPredictions] = useState(false);
  const [costsError, setCostsError] = useState(null);

  useEffect(() => {
    const fetchRecurringCosts = async () => {
      setCostsLoading(true);
      setCostsError(null);
      try {
        const result = await api.getRecurringCosts(6);
        if (result.success) {
          setRecurringCosts(result);
        } else {
          setCostsError(result.error || 'Failed to load');
        }
      } catch (err) {
        setCostsError(err.message);
      } finally {
        setCostsLoading(false);
      }
    };

    if (!loading && data) {
      fetchRecurringCosts();
    }
  }, [loading, data]);

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

  // Sparkline data from trends prop
  const sparklineData = trends?.payables || [];
  const yoyPct = yoyComparison?.payables;
  const comparisonMonth = yoyComparison?.comparison_month;

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return 'text-emerald-600 dark:text-emerald-400';
    if (confidence >= 0.5) return 'text-amber-600 dark:text-amber-400';
    return 'text-zinc-500';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="h-full"
    >
      <Card className="h-full flex flex-col">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitleTooltip description="Money you owe to suppliers and vendors. These are bills and expenses that need to be paid.">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <ArrowUpRight className="h-4 w-4" />
                Payables
              </CardTitle>
            </CardTitleTooltip>
            <Badge variant="secondary" className="text-xs">
              {billCount} bill{billCount !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col">
          <div className="flex items-baseline gap-2 mb-1">
            <ClickableAmount
              onClick={handleTotalClick}
              className="text-3xl font-bold font-mono tabular-nums text-negative"
            >
              {formatCurrency(total)}
            </ClickableAmount>
          </div>

          {/* YoY comparison badge - inverted because lower payables is better */}
          {yoyPct !== null && yoyPct !== undefined && (
            <div className="mt-1">
              <YoYBadge percentage={yoyPct} comparisonMonth={comparisonMonth} inverted />
            </div>
          )}

          {/* 12-month sparkline */}
          {sparklineData.length > 0 && (
            <div className="mt-3">
              <Sparkline
                data={sparklineData}
                color="#ef4444"
                height={32}
              />
              <p className="text-xs text-muted-foreground text-center mt-1">
                12-month trend
              </p>
            </div>
          )}

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
              className="flex items-center gap-2 mt-3 p-2 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-900 cursor-pointer hover:bg-red-100 dark:hover:bg-red-950/50 transition-colors"
              onClick={handleOverdueClick}
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
              <MetricTooltip
                label="This week"
                description="Bills due within the next 7 days. Prioritize these to avoid late payments."
                className="text-xs text-muted-foreground"
              />
              <p className="text-sm font-mono tabular-nums font-medium text-emerald-600 dark:text-emerald-400">
                {formatCurrency(dueThisWeek)}
              </p>
            </div>
            <div className="text-center p-2 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
              <MetricTooltip
                label="Next week"
                description="Bills coming due in 8-14 days. Plan your cash flow accordingly."
                className="text-xs text-muted-foreground"
              />
              <p className="text-sm font-mono tabular-nums font-medium text-blue-600 dark:text-blue-400">
                {formatCurrency(data?.due_next_week || 0)}
              </p>
            </div>
            <div className="text-center p-2 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
              <MetricTooltip
                label="Later"
                description="Bills due more than 2 weeks from now. Less urgent but should be on your radar."
                className="text-xs text-muted-foreground"
              />
              <p className="text-sm font-mono tabular-nums font-medium">
                {formatCurrency(data?.due_later || 0)}
              </p>
            </div>
          </div>

          {/* Cost Predictions Section */}
          <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 flex-1">
            <button
              onClick={() => setShowPredictions(!showPredictions)}
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors w-full"
            >
              <TrendingUp className="h-4 w-4" />
              <span>Cost Predictions</span>
              <ChevronDown
                className={cn(
                  'h-4 w-4 ml-auto transition-transform',
                  showPredictions && 'rotate-180'
                )}
              />
            </button>

            <AnimatePresence>
              {showPredictions && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 space-y-3"
                >
                  {costsLoading && (
                    <div className="flex items-center justify-center py-4">
                      <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
                      <span className="ml-2 text-xs text-muted-foreground">Analyzing costs...</span>
                    </div>
                  )}

                  {costsError && (
                    <p className="text-xs text-red-500 text-center py-2">{costsError}</p>
                  )}

                  {recurringCosts && !costsLoading && (
                    <>
                      {/* Average Monthly Spend */}
                      <div className="p-3 bg-purple-50 dark:bg-purple-950/30 rounded-lg border border-purple-200 dark:border-purple-900">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-purple-700 dark:text-purple-300">
                            Avg Monthly Spend
                          </span>
                          <span className="text-sm font-mono tabular-nums font-bold text-purple-700 dark:text-purple-300">
                            {formatCurrency(recurringCosts.average_monthly_spend)}
                          </span>
                        </div>
                        <div className="mt-2 space-y-1">
                          {recurringCosts.other_costs_monthly > 0 && (
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-purple-600 dark:text-purple-400">
                                Salaries, PAYE & Fixed
                              </span>
                              <span className="font-mono text-purple-600 dark:text-purple-400">
                                {formatCurrency(recurringCosts.other_costs_monthly)}
                              </span>
                            </div>
                          )}
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-purple-600 dark:text-purple-400">
                              Supplier Invoices
                            </span>
                            <span className="font-mono text-purple-600 dark:text-purple-400">
                              {formatCurrency(recurringCosts.vendor_costs_monthly || 0)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* 3-Month Predictions */}
                      {recurringCosts.predictions && recurringCosts.predictions.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs font-medium text-muted-foreground">
                            Predicted Monthly Costs
                          </p>
                          <TooltipProvider delayDuration={200}>
                            {recurringCosts.predictions.map((pred, index) => (
                              <Tooltip key={pred.month_key}>
                                <TooltipTrigger asChild>
                                  <div
                                    className={cn(
                                      'flex items-center justify-between p-2 rounded-lg cursor-help transition-colors',
                                      index === 0
                                        ? 'bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900'
                                        : 'bg-zinc-50 dark:bg-zinc-800/50'
                                    )}
                                  >
                                    <span className="text-xs font-medium">{pred.month}</span>
                                    <span className="text-sm font-mono tabular-nums font-medium">
                                      {formatCurrency(pred.predicted_total)}
                                    </span>
                                  </div>
                                </TooltipTrigger>
                                <TooltipContent side="left" className="max-w-xs p-0">
                                  <div className="p-3">
                                    <div className="flex items-center gap-2 mb-2 pb-2 border-b border-zinc-100 dark:border-zinc-700">
                                      <Building2 className="h-4 w-4 text-purple-500" />
                                      <span className="font-medium text-sm">
                                        Expected Costs - {pred.month}
                                      </span>
                                    </div>
                                    <div className="space-y-2 max-h-48 overflow-y-auto">
                                      {pred.top_costs && pred.top_costs.length > 0 ? (
                                        pred.top_costs.map((cost, i) => (
                                          <div key={i} className="text-xs">
                                            <div className="flex items-center justify-between gap-2">
                                              <span className="font-medium truncate">
                                                {cost.vendor}
                                              </span>
                                              <span className="font-mono whitespace-nowrap">
                                                {formatCurrency(cost.predicted_amount)}
                                              </span>
                                            </div>
                                            <div className="text-muted-foreground flex items-center justify-between mt-0.5">
                                              <span>Recurring expense</span>
                                              <Badge
                                                variant="outline"
                                                className={cn(
                                                  'text-[10px]',
                                                  getConfidenceColor(cost.confidence)
                                                )}
                                              >
                                                {getConfidenceLabel(cost.confidence)}
                                              </Badge>
                                            </div>
                                          </div>
                                        ))
                                      ) : (
                                        <p className="text-xs text-muted-foreground">
                                          No significant recurring costs predicted
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                </TooltipContent>
                              </Tooltip>
                            ))}
                          </TooltipProvider>
                        </div>
                      )}

                      {/* Top Recurring Vendors */}
                      {recurringCosts.recurring_costs && recurringCosts.recurring_costs.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs font-medium text-muted-foreground">
                            Top Recurring Vendors
                          </p>
                          <div className="space-y-1.5 max-h-32 overflow-y-auto">
                            {recurringCosts.recurring_costs
                              .filter((c) => c.is_recurring)
                              .slice(0, 5)
                              .map((cost, index) => (
                                <div
                                  key={index}
                                  className="flex items-center justify-between text-xs p-2 bg-zinc-50 dark:bg-zinc-800/50 rounded"
                                >
                                  <div className="flex-1 min-w-0">
                                    <p className="font-medium truncate">{cost.vendor}</p>
                                    <p className="text-muted-foreground">
                                      {cost.occurrences} bills in {cost.months_active} months
                                    </p>
                                  </div>
                                  <div className="text-right">
                                    <p className="font-mono tabular-nums font-medium">
                                      {formatCurrency(cost.average_amount)}
                                    </p>
                                    <p className="text-muted-foreground">/avg</p>
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default Payables;
