import React, { useEffect, useState } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Landmark, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';

function AnimatedNumber({ value, duration = 1 }) {
  const spring = useSpring(0, { duration: duration * 1000 });
  const display = useTransform(spring, (current) =>
    formatCurrency(Math.floor(current))
  );

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return <motion.span>{display}</motion.span>;
}

export function CashPosition({ data, loading }) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Landmark className="h-4 w-4" />
            Cash Position
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </CardContent>
      </Card>
    );
  }

  const total = data?.total_balance || data?.total || 0;
  const accounts = data?.accounts || [];
  const minReserve = 200000;
  const isLow = total < minReserve;
  const trend = data?.trend_percentage || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="h-full"
    >
      <Card className={`h-full ${isLow ? 'border-red-200 dark:border-red-900' : ''}`}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Landmark className="h-4 w-4" />
              Cash Position
            </CardTitle>
            {isLow && (
              <Badge variant="destructive" className="gap-1">
                <AlertTriangle className="h-3 w-3" />
                Low
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-2 mb-1">
            <span className={`text-3xl font-bold font-mono tabular-nums ${isLow ? 'text-negative' : ''}`}>
              <AnimatedNumber value={total} />
            </span>
            {trend !== 0 && (
              <Badge
                variant={trend > 0 ? 'success' : 'destructive'}
                className="gap-0.5 text-xs"
              >
                {trend > 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {Math.abs(trend).toFixed(1)}%
              </Badge>
            )}
          </div>

          {/* Account breakdown */}
          {accounts.length > 0 && (
            <div className="mt-4 space-y-2">
              {accounts.map((account, index) => (
                <motion.div
                  key={account.name || index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * (index + 1) }}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-muted-foreground truncate flex-1">
                    {account.name}
                  </span>
                  <span className="font-mono tabular-nums">
                    {formatCurrency(account.balance)}
                  </span>
                </motion.div>
              ))}
            </div>
          )}

          {/* Min reserve indicator */}
          <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Min Reserve</span>
              <span className="font-mono tabular-nums text-muted-foreground">
                {formatCurrency(minReserve)}
              </span>
            </div>
            <div className="mt-2 h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${
                  total >= minReserve * 1.5
                    ? 'bg-emerald-500'
                    : total >= minReserve
                    ? 'bg-amber-500'
                    : 'bg-red-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min((total / minReserve) * 100, 100)}%` }}
                transition={{ duration: 1, delay: 0.3 }}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default CashPosition;
