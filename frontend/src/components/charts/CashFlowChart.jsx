import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';
import api from '@/services/api';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="chart-tooltip">
        <p className="font-medium text-sm mb-2">{label}</p>
        <div className="space-y-1 text-sm">
          <p className="flex justify-between gap-4">
            <span className="text-muted-foreground">Balance:</span>
            <span className="font-mono tabular-nums font-medium">
              {formatCurrency(data.projected_balance)}
            </span>
          </p>
          {data.expected_inflows > 0 && (
            <p className="flex justify-between gap-4">
              <span className="text-muted-foreground">Inflows:</span>
              <span className="font-mono tabular-nums text-positive">
                +{formatCurrency(data.expected_inflows)}
              </span>
            </p>
          )}
          {data.expected_outflows > 0 && (
            <p className="flex justify-between gap-4">
              <span className="text-muted-foreground">Outflows:</span>
              <span className="font-mono tabular-nums text-negative">
                -{formatCurrency(data.expected_outflows)}
              </span>
            </p>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export function CashFlowChart() {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchForecast = async () => {
      try {
        setError(null);
        const data = await api.getCashForecast();
        if (data.success) {
          setForecast(data.forecast);
        } else {
          setError(data.error || 'Failed to load forecast');
        }
      } catch (err) {
        setError(err.message || 'Failed to load forecast');
      } finally {
        setLoading(false);
      }
    };

    fetchForecast();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">4-Week Cash Flow Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">4-Week Cash Flow Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[250px] text-muted-foreground">
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare chart data
  const chartData = [
    {
      name: 'Today',
      projected_balance: forecast?.current_balance || 0,
      expected_inflows: 0,
      expected_outflows: 0,
      isToday: true
    },
    ...(forecast?.forecast?.map((week) => ({
      name: `Week ${week.week}`,
      projected_balance: week.projected_balance,
      expected_inflows: week.expected_inflows,
      expected_outflows: week.expected_outflows
    })) || [])
  ];

  const minBalance = Math.min(...chartData.map(d => d.projected_balance));
  const maxBalance = Math.max(...chartData.map(d => d.projected_balance));
  const trend = chartData.length > 1
    ? chartData[chartData.length - 1].projected_balance - chartData[0].projected_balance
    : 0;
  const minReserve = 200000; // From rules

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
          <div>
            <CardTitle className="text-base font-medium">4-Week Cash Flow Forecast</CardTitle>
            <p className="text-xs sm:text-sm text-muted-foreground mt-1">
              Projected cash position over 4 weeks
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {minBalance < minReserve && (
              <Badge variant="destructive" className="gap-1 text-xs">
                <AlertTriangle className="h-3 w-3" />
                <span className="hidden sm:inline">Below Reserve</span>
                <span className="sm:hidden">Low</span>
              </Badge>
            )}
            <Badge variant={trend >= 0 ? 'success' : 'destructive'} className="gap-1 text-xs">
              {trend >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {formatCurrency(Math.abs(trend))}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="px-2 sm:px-6">
          <div className="h-[200px] sm:h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 5, left: -15, bottom: 0 }}>
                <defs>
                  <linearGradient id="cashGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `£${(value / 1000).toFixed(0)}k`}
                  width={45}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine
                  y={minReserve}
                  stroke="#ef4444"
                  strokeDasharray="5 5"
                  label={{
                    value: 'Min',
                    position: 'right',
                    fill: '#ef4444',
                    fontSize: 9
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="projected_balance"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="url(#cashGradient)"
                  animationDuration={1000}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Risks and Recommendations */}
          {(forecast?.risks?.length > 0 || forecast?.recommendations?.length > 0) && (
            <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-zinc-200 dark:border-zinc-800">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                {forecast?.risks?.length > 0 && (
                  <div>
                    <h4 className="text-xs sm:text-sm font-medium text-negative mb-1.5 sm:mb-2">Risks</h4>
                    <ul className="space-y-1 text-xs sm:text-sm text-muted-foreground">
                      {forecast.risks.slice(0, 2).map((risk, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-red-500 mt-0.5">•</span>
                          <span>{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {forecast?.recommendations?.length > 0 && (
                  <div>
                    <h4 className="text-xs sm:text-sm font-medium text-positive mb-1.5 sm:mb-2">Recommendations</h4>
                    <ul className="space-y-1 text-xs sm:text-sm text-muted-foreground">
                      {forecast.recommendations.slice(0, 2).map((rec, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-emerald-500 mt-0.5">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default CashFlowChart;
