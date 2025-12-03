import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
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
            Revenue History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-3/4 mb-2" />
          <Skeleton className="h-12 w-full" />
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
            Revenue History
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

  // Calculate latest and previous for comparison
  const latestRevenue = revenueData[revenueData.length - 1]?.value || 0;
  const previousRevenue = revenueData.length > 1 ? revenueData[revenueData.length - 2]?.value : null;
  const momChange = previousRevenue ? ((latestRevenue - previousRevenue) / previousRevenue) * 100 : null;

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
              <BarChart3 className="h-4 w-4" />
              Revenue History
            </CardTitle>
            {latestMonth && (
              <span className="text-xs text-muted-foreground">
                {latestMonth}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Latest revenue */}
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-2xl font-bold font-mono tabular-nums">
              {formatCurrency(latestRevenue)}
            </span>
            {momChange !== null && (
              <span className={`text-sm flex items-center gap-0.5 ${momChange >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {momChange >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {Math.abs(momChange).toFixed(1)}% MoM
              </span>
            )}
          </div>

          {/* YoY comparison */}
          {yoyComparisons?.revenue !== null && yoyComparisons?.revenue !== undefined && (
            <div className="mb-3">
              <YoYBadge
                percentage={yoyComparisons.revenue}
                comparisonMonth={yoyComparisons.comparison_month}
              />
            </div>
          )}

          {/* Sparkline */}
          <div className="mt-3">
            <Sparkline
              data={revenueData}
              color="#6366f1"
              height={50}
            />
            <p className="text-xs text-muted-foreground text-center mt-1">
              {revenueData.length}-month revenue trend
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RevenueHistoryCard;
