import React from 'react';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * A badge showing Year-over-Year comparison.
 *
 * @param {number} percentage - YoY percentage change (positive = growth, negative = decline)
 * @param {string} comparisonMonth - The month being compared to (e.g., "Dec 2024")
 * @param {boolean} inverted - If true, negative is good (e.g., for expenses)
 * @param {string} className - Additional CSS classes
 */
export function YoYBadge({ percentage, comparisonMonth, inverted = false, className }) {
  if (percentage === null || percentage === undefined) {
    return null;
  }

  const isPositive = percentage > 0;
  const isZero = percentage === 0;

  // Determine if this is "good" or "bad"
  // For inverted metrics (like expenses), lower is better
  const isGood = inverted ? percentage < 0 : percentage > 0;

  const Icon = isZero ? Minus : isPositive ? TrendingUp : TrendingDown;
  const arrow = isPositive ? '↑' : isZero ? '→' : '↓';

  return (
    <Badge
      variant="outline"
      className={cn(
        'gap-1 text-xs font-normal',
        isZero && 'text-muted-foreground border-muted',
        !isZero && isGood && 'text-emerald-600 border-emerald-200 bg-emerald-50 dark:text-emerald-400 dark:border-emerald-800 dark:bg-emerald-950/30',
        !isZero && !isGood && 'text-red-600 border-red-200 bg-red-50 dark:text-red-400 dark:border-red-800 dark:bg-red-950/30',
        className
      )}
    >
      <Icon className="h-3 w-3" />
      <span>
        {arrow} {Math.abs(percentage).toFixed(1)}%
        {comparisonMonth && (
          <span className="text-muted-foreground ml-1">vs {comparisonMonth}</span>
        )}
      </span>
    </Badge>
  );
}

export default YoYBadge;
