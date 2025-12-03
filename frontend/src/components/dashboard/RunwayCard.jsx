import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { MetricTooltip, CardTitleTooltip } from '@/components/ui/info-tooltip';
import { Gauge, Flame, TrendingUp, Infinity, AlertTriangle, CheckCircle } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';

export function RunwayCard({ data, loading }) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Gauge className="h-4 w-4" />
            Cash Runway
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Gauge className="h-4 w-4" />
            Cash Runway
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No runway data available</p>
        </CardContent>
      </Card>
    );
  }

  const { runway_months, avg_monthly_burn, current_cash, is_profitable, calculation_basis, months_analyzed } = data;

  // Determine runway status and styling
  // For a profitable business, runway is a "what if" metric, not an emergency indicator
  const isPositiveCashFlow = is_profitable === true;
  const isHealthy = runway_months === null || runway_months > 6 || isPositiveCashFlow;
  const isModerate = !isPositiveCashFlow && runway_months !== null && runway_months <= 6 && runway_months > 3;
  const isLow = !isPositiveCashFlow && runway_months !== null && runway_months <= 3;

  const getStatusColor = () => {
    if (isHealthy) return 'text-emerald-600 dark:text-emerald-400';
    if (isModerate) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getStatusBgColor = () => {
    if (isHealthy) return 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900';
    if (isModerate) return 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900';
    return 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900';
  };

  const StatusIcon = isHealthy ? CheckCircle : isLow ? AlertTriangle : Gauge;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className="h-full"
    >
      <Card className="h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitleTooltip description="How long your current cash would last if all revenue stopped. A worst-case scenario metric for planning purposes.">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Gauge className="h-4 w-4" />
                Cash Runway
              </CardTitle>
            </CardTitleTooltip>
            {calculation_basis && (
              <Badge variant="secondary" className="text-xs">
                {calculation_basis}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Main runway display */}
          <div className={`p-4 rounded-lg border ${getStatusBgColor()}`}>
            <div className="flex items-center gap-3">
              <StatusIcon className={`h-8 w-8 ${getStatusColor()}`} />
              <div>
                <div className="flex items-baseline gap-2">
                  {isPositiveCashFlow ? (
                    <>
                      <Infinity className={`h-8 w-8 ${getStatusColor()}`} />
                      <span className={`text-xl font-bold ${getStatusColor()}`}>
                        Positive Cash Flow
                      </span>
                    </>
                  ) : (
                    <>
                      <span className={`text-3xl font-bold font-mono tabular-nums ${getStatusColor()}`}>
                        {runway_months?.toFixed(1)}
                      </span>
                      <span className={`text-lg ${getStatusColor()}`}>months</span>
                    </>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  {isPositiveCashFlow
                    ? 'Revenue exceeds expenses'
                    : 'if revenue stopped (worst case)'}
                </p>
              </div>
            </div>
          </div>

          {/* Burn rate display */}
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <Flame className="h-4 w-4" />
                <MetricTooltip
                  label="Avg Expenses"
                  description="Your average monthly operating expenses based on recent P&L data. Includes salaries, rent, software, and other recurring costs."
                  className="text-xs"
                />
              </div>
              <p className="text-lg font-bold font-mono tabular-nums text-red-600 dark:text-red-400">
                {formatCurrency(avg_monthly_burn)}
              </p>
              <p className="text-xs text-muted-foreground">/month (P&L)</p>
            </div>

            <div className="text-center p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <TrendingUp className="h-4 w-4" />
                <MetricTooltip
                  label="Cash Balance"
                  description="Current total cash across all bank accounts. This is what's available to cover expenses."
                  className="text-xs"
                />
              </div>
              <p className="text-lg font-bold font-mono tabular-nums">
                {formatCurrency(current_cash)}
              </p>
              <p className="text-xs text-muted-foreground">available</p>
            </div>
          </div>

        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RunwayCard;
