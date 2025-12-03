import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
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
  const isPositiveCashFlow = is_profitable === true;
  const isHealthy = runway_months === null || runway_months > 12;
  const isWarning = runway_months !== null && runway_months <= 12 && runway_months > 6;
  const isCritical = runway_months !== null && runway_months <= 6;

  const getStatusColor = () => {
    if (isPositiveCashFlow || isHealthy) return 'text-emerald-600 dark:text-emerald-400';
    if (isWarning) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getStatusBgColor = () => {
    if (isPositiveCashFlow || isHealthy) return 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900';
    if (isWarning) return 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900';
    return 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900';
  };

  const StatusIcon = isPositiveCashFlow || isHealthy ? CheckCircle : isCritical ? AlertTriangle : Gauge;

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
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Cash Runway
            </CardTitle>
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
                    : 'at current burn rate'}
                </p>
              </div>
            </div>
          </div>

          {/* Burn rate display */}
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <Flame className="h-4 w-4" />
                <span className="text-xs">Avg Expenses</span>
              </div>
              <p className="text-lg font-bold font-mono tabular-nums text-red-600 dark:text-red-400">
                {formatCurrency(avg_monthly_burn)}
              </p>
              <p className="text-xs text-muted-foreground">/month (P&L)</p>
            </div>

            <div className="text-center p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <TrendingUp className="h-4 w-4" />
                <span className="text-xs">Cash Balance</span>
              </div>
              <p className="text-lg font-bold font-mono tabular-nums">
                {formatCurrency(current_cash)}
              </p>
              <p className="text-xs text-muted-foreground">available</p>
            </div>
          </div>

          {/* Warning message for critical runway */}
          {isCritical && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-4 p-3 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-900"
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-200">
                    Critical Runway Alert
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    Consider immediate action: reduce expenses, accelerate receivables, or secure additional funding.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RunwayCard;
