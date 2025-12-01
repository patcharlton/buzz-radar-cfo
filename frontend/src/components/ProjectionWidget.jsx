import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  Lightbulb,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  PieChart,
} from 'lucide-react';
import api from '../services/api';
import { formatCurrency, cn } from '@/lib/utils';

const PERIOD_OPTIONS = [
  { value: 1, label: '1 Month' },
  { value: 2, label: '2 Months' },
  { value: 3, label: '3 Months' },
  { value: 6, label: '6 Months' },
];

function ProjectionWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeals, setShowDeals] = useState(false);
  const [showCosts, setShowCosts] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(3);

  const fetchProjections = async (months = selectedPeriod) => {
    try {
      setError(null);
      setLoading(true);
      const result = await api.getProjections(months);
      if (result.success) {
        setData(result);
      } else {
        setError(result.error || 'Failed to load projections');
      }
    } catch (err) {
      setError(err.message || 'Failed to load projections');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjections(selectedPeriod);
  }, [selectedPeriod]);

  const handlePeriodChange = (period) => {
    setSelectedPeriod(period);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'on_track':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300';
      case 'at_risk':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300';
      case 'behind':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      default:
        return 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'on_track':
        return <TrendingUp className="h-4 w-4" />;
      case 'at_risk':
        return <AlertTriangle className="h-4 w-4" />;
      case 'behind':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Target className="h-4 w-4" />;
    }
  };

  const periodLabel = PERIOD_OPTIONS.find(o => o.value === selectedPeriod)?.label || `${selectedPeriod} Months`;

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Target className="h-4 w-4 text-purple-500" />
                Financial Projection
              </CardTitle>
              <div className="flex items-center bg-zinc-100 dark:bg-zinc-800 rounded-lg p-0.5">
                {PERIOD_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handlePeriodChange(option.value)}
                    className={cn(
                      'px-2.5 py-1 text-xs font-medium rounded-md transition-all',
                      selectedPeriod === option.value
                        ? 'bg-white dark:bg-zinc-700 text-purple-600 dark:text-purple-400 shadow-sm'
                        : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <RefreshCw className="h-6 w-6 text-muted-foreground animate-spin" />
              <p className="text-sm text-muted-foreground">Loading {periodLabel.toLowerCase()} projection...</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Target className="h-4 w-4 text-purple-500" />
                Financial Projection
              </CardTitle>
              <div className="flex items-center bg-zinc-100 dark:bg-zinc-800 rounded-lg p-0.5">
                {PERIOD_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handlePeriodChange(option.value)}
                    className={cn(
                      'px-2.5 py-1 text-xs font-medium rounded-md transition-all',
                      selectedPeriod === option.value
                        ? 'bg-white dark:bg-zinc-700 text-purple-600 dark:text-purple-400 shadow-sm'
                        : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-6 gap-3">
              <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-full">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              <Button variant="outline" size="sm" onClick={() => fetchProjections(selectedPeriod)} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  const { revenue, costs, cost_breakdown, gap_analysis, target } = data || {};
  const months = revenue?.months || [];
  const totals = revenue?.totals || {};

  // Prepare chart data
  const chartData = months.map((m) => ({
    month: m.month_label.split(' ')[0].substring(0, 3), // "Jan", "Feb", etc.
    Conservative: m.conservative,
    Base: m.base,
    Optimistic: m.optimistic,
  }));

  // Prepare cost breakdown data
  const costCategories = cost_breakdown?.categories || {};
  const costData = Object.entries(costCategories).map(([key, val]) => ({
    name: val.label,
    amount: val.amount,
    percentage: val.percentage,
  })).sort((a, b) => b.amount - a.amount);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Target className="h-4 w-4 text-purple-500" />
              Financial Projection
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-zinc-100 dark:bg-zinc-800 rounded-lg p-0.5">
                {PERIOD_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handlePeriodChange(option.value)}
                    className={cn(
                      'px-2.5 py-1 text-xs font-medium rounded-md transition-all',
                      selectedPeriod === option.value
                        ? 'bg-white dark:bg-zinc-700 text-purple-600 dark:text-purple-400 shadow-sm'
                        : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <Button variant="ghost" size="sm" onClick={() => fetchProjections(selectedPeriod)} className="gap-1 h-7 w-7 p-0">
                <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Gap Analysis Alert */}
          {gap_analysis && gap_analysis.gap > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className={cn(
                'p-4 rounded-lg border',
                gap_analysis.status === 'behind'
                  ? 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-900'
                  : 'bg-amber-50 border-amber-200 dark:bg-amber-950/30 dark:border-amber-900'
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn('p-2 rounded-full', getStatusColor(gap_analysis.status))}>
                  {getStatusIcon(gap_analysis.status)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">
                      {gap_analysis.status_label}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      Gap: {formatCurrency(gap_analysis.gap)}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    Target: {formatCurrency(target)} | Base Projection: {formatCurrency(gap_analysis.base_projection)}
                  </p>

                  {/* Deal Recommendations */}
                  {gap_analysis.deals_to_close?.length > 0 && (
                    <div className="mt-2">
                      <button
                        onClick={() => setShowDeals(!showDeals)}
                        className="flex items-center gap-1 text-xs font-medium text-amber-700 dark:text-amber-300 hover:underline"
                      >
                        {showDeals ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                        {gap_analysis.deals_count} deals could close the gap
                      </button>
                      <AnimatePresence>
                        {showDeals && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-2 space-y-1"
                          >
                            {gap_analysis.deals_to_close.slice(0, 3).map((deal, idx) => (
                              <div key={idx} className="flex items-center justify-between text-xs bg-white/50 dark:bg-zinc-800/50 rounded px-2 py-1">
                                <span className="font-medium">{deal.name}</span>
                                <span className="text-muted-foreground">
                                  {formatCurrency(deal.deal_value)} ({deal.likelihood}/10)
                                </span>
                              </div>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* On Track Success Message */}
          {gap_analysis && gap_analysis.gap <= 0 && (
            <div className="p-4 rounded-lg border bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-900">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-emerald-100 dark:bg-emerald-900/50">
                  <TrendingUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <span className="font-medium text-sm text-emerald-800 dark:text-emerald-200">On Track</span>
                  <p className="text-xs text-emerald-600 dark:text-emerald-400">
                    Pipeline exceeds target by {formatCurrency(gap_analysis.surplus)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Revenue Scenarios Table */}
          <div>
            <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-500" />
              Revenue Scenarios
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-100 dark:border-zinc-800">
                    <th className="text-left py-2 font-medium text-muted-foreground">Scenario</th>
                    {months.map((m) => (
                      <th key={m.month} className="text-right py-2 font-medium text-muted-foreground">
                        {m.month_label.split(' ')[0].substring(0, 3)}
                      </th>
                    ))}
                    <th className="text-right py-2 font-medium text-muted-foreground">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-zinc-50 dark:border-zinc-800/50">
                    <td className="py-2 text-muted-foreground">Conservative</td>
                    {months.map((m) => (
                      <td key={m.month} className="py-2 text-right font-mono tabular-nums">
                        {formatCurrency(m.conservative)}
                      </td>
                    ))}
                    <td className="py-2 text-right font-mono tabular-nums font-medium">
                      {formatCurrency(totals.conservative)}
                    </td>
                  </tr>
                  <tr className="border-b border-zinc-50 dark:border-zinc-800/50 bg-purple-50/50 dark:bg-purple-950/20">
                    <td className="py-2 font-medium">Base (Weighted)</td>
                    {months.map((m) => (
                      <td key={m.month} className="py-2 text-right font-mono tabular-nums font-medium">
                        {formatCurrency(m.base)}
                      </td>
                    ))}
                    <td className="py-2 text-right font-mono tabular-nums font-bold text-purple-600 dark:text-purple-400">
                      {formatCurrency(totals.base)}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 text-muted-foreground">Optimistic</td>
                    {months.map((m) => (
                      <td key={m.month} className="py-2 text-right font-mono tabular-nums">
                        {formatCurrency(m.optimistic)}
                      </td>
                    ))}
                    <td className="py-2 text-right font-mono tabular-nums font-medium">
                      {formatCurrency(totals.optimistic)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Bar Chart */}
          {chartData.length > 0 && (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-700" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <YAxis
                    tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Bar dataKey="Conservative" fill="#94a3b8" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Base" fill="#a855f7" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Optimistic" fill="#22c55e" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Cost Breakdown */}
          {costData.length > 0 && (
            <div>
              <button
                onClick={() => setShowCosts(!showCosts)}
                className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors w-full"
              >
                <PieChart className="h-4 w-4" />
                Cost Breakdown (Monthly Avg: {formatCurrency(cost_breakdown?.total || 0)})
                {showCosts ? <ChevronUp className="h-4 w-4 ml-auto" /> : <ChevronDown className="h-4 w-4 ml-auto" />}
              </button>
              <AnimatePresence>
                {showCosts && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 space-y-2"
                  >
                    {costData.map((cat, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span>{cat.name}</span>
                          <span className="font-mono tabular-nums">
                            {formatCurrency(cat.amount)} ({cat.percentage}%)
                          </span>
                        </div>
                        <div className="h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${cat.percentage}%` }}
                            transition={{ delay: idx * 0.05 }}
                            className="h-full bg-purple-500 rounded-full"
                          />
                        </div>
                      </div>
                    ))}
                    {cost_breakdown?.is_estimate && (
                      <p className="text-xs text-muted-foreground mt-2 italic">
                        * Estimated based on typical SaaS cost structure
                      </p>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Recommendations */}
          {gap_analysis?.recommendations?.length > 0 && (
            <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800">
              <div className="flex items-start gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium mb-1">Recommendations</h4>
                  <ul className="space-y-1">
                    {gap_analysis.recommendations.slice(0, 2).map((rec, idx) => (
                      <li key={idx} className="text-xs text-muted-foreground">
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default ProjectionWidget;
