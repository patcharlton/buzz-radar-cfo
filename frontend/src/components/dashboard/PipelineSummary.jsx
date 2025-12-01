import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Target,
  AlertTriangle,
  Clock,
  TrendingUp,
  Calendar,
  User,
} from 'lucide-react';
import api from '@/services/api';
import { formatCurrency } from '@/lib/utils';

export function PipelineSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getContextSummary();
        if (result.success) {
          setData(result);
        } else {
          setError(result.error || 'Failed to load pipeline');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Target className="h-4 w-4" />
            Sales Pipeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2 mb-4" />
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Target className="h-4 w-4" />
            Sales Pipeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const pipeline = data?.pipeline_summary || {};
  const overdueDeals = pipeline.overdue_deals || [];
  const closingThisMonth = pipeline.closing_this_month || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="h-full"
    >
      <Card className="h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Target className="h-4 w-4" />
              Sales Pipeline
            </CardTitle>
            <Badge variant="secondary" className="text-xs">
              {pipeline.deal_count || 0} deals
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Pipeline Value Summary */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">Total Pipeline</p>
              <p className="text-xl font-bold font-mono tabular-nums">
                {formatCurrency(pipeline.total_value || 0)}
              </p>
            </div>
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">Weighted Value</p>
              <p className="text-xl font-bold font-mono tabular-nums text-emerald-600 dark:text-emerald-400">
                {formatCurrency(pipeline.weighted_value || 0)}
              </p>
            </div>
          </div>

          {/* High Confidence Deals */}
          <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-100 dark:border-blue-900">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                High Confidence (8+/10)
              </span>
            </div>
            <p className="text-lg font-bold font-mono tabular-nums text-blue-600 dark:text-blue-400">
              {formatCurrency(pipeline.high_confidence_value || 0)}
            </p>
          </div>

          {/* Overdue Deals */}
          {overdueDeals.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <span className="text-sm font-medium text-red-600 dark:text-red-400">
                  Overdue Deals ({overdueDeals.length})
                </span>
              </div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {overdueDeals.map((deal, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 * index }}
                    className="p-2 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-100 dark:border-red-900"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-red-800 dark:text-red-200 truncate">
                          {deal.name}
                        </p>
                        <p className="text-xs text-red-600 dark:text-red-400">
                          {deal.client}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-mono tabular-nums font-medium text-red-700 dark:text-red-300">
                          {formatCurrency(deal.value)}
                        </p>
                        <Badge variant="destructive" className="text-xs">
                          {deal.days_overdue}d overdue
                        </Badge>
                      </div>
                    </div>
                    {deal.decision_maker && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-red-600 dark:text-red-400">
                        <User className="h-3 w-3" />
                        {deal.decision_maker}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Closing This Month */}
          {closingThisMonth.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium">
                  Closing This Month ({closingThisMonth.length})
                </span>
              </div>
              <div className="space-y-1.5 max-h-40 overflow-y-auto">
                {closingThisMonth.slice(0, 5).map((deal, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg text-sm"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{deal.name}</p>
                      <p className="text-xs text-muted-foreground">{deal.client}</p>
                    </div>
                    <div className="text-right flex items-center gap-2">
                      <span className="font-mono tabular-nums">
                        {formatCurrency(deal.value)}
                      </span>
                      <Badge
                        variant={deal.likelihood >= 8 ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {deal.likelihood}/10
                      </Badge>
                    </div>
                  </div>
                ))}
                {closingThisMonth.length > 5 && (
                  <p className="text-xs text-muted-foreground text-center">
                    +{closingThisMonth.length - 5} more deals
                  </p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default PipelineSummary;
