import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { MetricTooltip, CardTitleTooltip } from '@/components/ui/info-tooltip';
import { TrendingUp, TrendingDown, BarChart3, DollarSign, Receipt, PiggyBank } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';
import { Sparkline } from '@/components/charts/Sparkline';
import { YoYBadge } from '@/components/ui/yoy-badge';

export function RevenueHistoryCard({ trends, loading }) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            P&L History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-3/4 mb-2" />
          <Skeleton className="h-12 w-full mb-4" />
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    );
  }

  const revenueData = trends?.trends?.revenue || [];
  const yoyComparisons = trends?.yoy_comparisons || {};
  const latestMonth = trends?.latest_month;

  if (revenueData.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            P&L History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No historical data. Click "Load History" to fetch from Xero.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Get the last 12 months or available data
  const displayData = revenueData.slice(-12);

  // If latest month has 0 revenue (incomplete month), use previous month as "latest"
  const lastEntry = displayData[displayData.length - 1];
  const hasCurrentMonthData = lastEntry?.value > 0;

  // For display purposes, skip the current month if it has no data
  const effectiveData = hasCurrentMonthData ? displayData : displayData.slice(0, -1);

  // Calculate statistics using effective data (excluding incomplete current month)
  const latestRevenue = effectiveData[effectiveData.length - 1]?.value || 0;
  const previousRevenue = effectiveData.length > 1 ? effectiveData[effectiveData.length - 2]?.value : null;
  const momChange = previousRevenue && previousRevenue > 0
    ? ((latestRevenue - previousRevenue) / previousRevenue) * 100
    : null;

  // Get the latest month name from effective data
  const effectiveLatestMonth = effectiveData[effectiveData.length - 1]?.month || latestMonth;

  // Calculate averages and totals using effective data
  const totalRevenue = effectiveData.reduce((sum, d) => sum + (d.value || 0), 0);
  const avgRevenue = effectiveData.length > 0 ? totalRevenue / effectiveData.length : 0;
  const maxRevenue = Math.max(...effectiveData.map(d => d.value || 0));
  const minRevenue = Math.min(...effectiveData.map(d => d.value || 0));

  // Find best and worst months
  const bestMonth = effectiveData.find(d => d.value === maxRevenue);
  const worstMonth = effectiveData.find(d => d.value === minRevenue);

  // Calculate growth trend (first half vs second half)
  const midPoint = Math.floor(effectiveData.length / 2);
  const firstHalf = effectiveData.slice(0, midPoint);
  const secondHalf = effectiveData.slice(midPoint);
  const firstHalfAvg = firstHalf.length > 0
    ? firstHalf.reduce((sum, d) => sum + (d.value || 0), 0) / firstHalf.length
    : 0;
  const secondHalfAvg = secondHalf.length > 0
    ? secondHalf.reduce((sum, d) => sum + (d.value || 0), 0) / secondHalf.length
    : 0;
  const trendDirection = secondHalfAvg >= firstHalfAvg ? 'up' : 'down';
  const trendPct = firstHalfAvg > 0
    ? ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100
    : 0;

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
            <CardTitleTooltip description="Historical revenue from your Profit & Loss statements. Shows trends, averages, and year-over-year comparisons.">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                P&L History
              </CardTitle>
            </CardTitleTooltip>
            <Badge variant="secondary" className="text-xs">
              {effectiveData.length} months
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Latest month highlight */}
          <div className="p-3 bg-indigo-50 dark:bg-indigo-950/30 rounded-lg border border-indigo-200 dark:border-indigo-900">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
                {effectiveLatestMonth} Revenue
              </span>
              {momChange !== null && (
                <Badge
                  variant={momChange >= 0 ? 'default' : 'destructive'}
                  className="text-xs gap-0.5"
                >
                  {momChange >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {Math.abs(momChange).toFixed(1)}% MoM
                </Badge>
              )}
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono tabular-nums text-indigo-700 dark:text-indigo-300">
                {formatCurrency(latestRevenue)}
              </span>
            </div>
            {/* YoY comparison */}
            {yoyComparisons?.revenue !== null && yoyComparisons?.revenue !== undefined && (
              <div className="mt-2">
                <YoYBadge
                  percentage={yoyComparisons.revenue}
                  comparisonMonth={yoyComparisons.comparison_month}
                />
              </div>
            )}
          </div>

          {/* Revenue Sparkline */}
          <div>
            <Sparkline
              data={effectiveData}
              color="#6366f1"
              height={60}
              showTooltip
            />
          </div>

          {/* Key metrics grid */}
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center p-2 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <DollarSign className="h-3 w-3" />
                <MetricTooltip
                  label="Average"
                  description="Mean monthly revenue over the displayed period. Useful for setting baseline expectations."
                  className="text-xs"
                />
              </div>
              <p className="text-sm font-bold font-mono tabular-nums">
                {formatCurrency(avgRevenue)}
              </p>
            </div>

            <div className="text-center p-2 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg">
              <div className="flex items-center justify-center gap-1 text-emerald-600 dark:text-emerald-400 mb-1">
                <TrendingUp className="h-3 w-3" />
                <MetricTooltip
                  label="Best"
                  description="Highest revenue month in the period. Understand what drove this peak to replicate success."
                  className="text-xs"
                />
              </div>
              <p className="text-sm font-bold font-mono tabular-nums text-emerald-700 dark:text-emerald-300">
                {formatCurrency(maxRevenue)}
              </p>
              <p className="text-xs text-muted-foreground">{bestMonth?.month}</p>
            </div>

            <div className="text-center p-2 bg-amber-50 dark:bg-amber-950/30 rounded-lg">
              <div className="flex items-center justify-center gap-1 text-amber-600 dark:text-amber-400 mb-1">
                <TrendingDown className="h-3 w-3" />
                <MetricTooltip
                  label="Lowest"
                  description="Lowest revenue month in the period. Review for seasonality patterns or one-time events."
                  className="text-xs"
                />
              </div>
              <p className="text-sm font-bold font-mono tabular-nums text-amber-700 dark:text-amber-300">
                {formatCurrency(minRevenue)}
              </p>
              <p className="text-xs text-muted-foreground">{worstMonth?.month}</p>
            </div>
          </div>

          {/* Period totals */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
              <div className="flex items-center gap-1 text-muted-foreground mb-1">
                <Receipt className="h-4 w-4" />
                <MetricTooltip
                  label="Period Total"
                  description="Sum of all revenue over the displayed period. Useful for understanding total business volume."
                  className="text-xs"
                />
              </div>
              <p className="text-lg font-bold font-mono tabular-nums">
                {formatCurrency(totalRevenue)}
              </p>
              <p className="text-xs text-muted-foreground">
                Last {effectiveData.length} months
              </p>
            </div>

            <div className={`p-3 rounded-lg ${
              trendDirection === 'up'
                ? 'bg-emerald-50 dark:bg-emerald-950/30'
                : 'bg-red-50 dark:bg-red-950/30'
            }`}>
              <div className={`flex items-center gap-1 mb-1 ${
                trendDirection === 'up'
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}>
                <PiggyBank className="h-4 w-4" />
                <MetricTooltip
                  label="Trend"
                  description="Compares average revenue of recent months vs earlier months. Positive means revenue is growing over time."
                  className="text-xs"
                />
              </div>
              <div className="flex items-center gap-1">
                {trendDirection === 'up' ? (
                  <TrendingUp className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
                )}
                <span className={`text-lg font-bold font-mono tabular-nums ${
                  trendDirection === 'up'
                    ? 'text-emerald-700 dark:text-emerald-300'
                    : 'text-red-700 dark:text-red-300'
                }`}>
                  {trendPct >= 0 ? '+' : ''}{trendPct.toFixed(1)}%
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {trendDirection === 'up' ? 'Growing' : 'Declining'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RevenueHistoryCard;
