import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  AlertTriangle,
  Lightbulb,
  RefreshCw,
  ChevronDown,
  Clock,
  ArrowDownLeft,
  ArrowUpRight,
} from 'lucide-react';
import api from '../services/api';
import { formatCurrency, cn } from '@/lib/utils';

function CashForecast() {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generatedAt, setGeneratedAt] = useState(null);
  const [cached, setCached] = useState(false);
  const [showAssumptions, setShowAssumptions] = useState(false);

  const fetchForecast = async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await api.getCashForecast();
      if (data.success) {
        setForecast(data.forecast);
        setGeneratedAt(data.generated_at);
        setCached(data.cached || false);
      } else {
        setError(data.error || 'Failed to load forecast');
      }
    } catch (err) {
      setError(err.message || 'Failed to load forecast');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, []);

  const getBalanceClass = (balance, minReserve = 200000) => {
    if (balance >= minReserve * 1.5) return 'text-emerald-600 dark:text-emerald-400';
    if (balance >= minReserve) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getBalanceBg = (balance, minReserve = 200000) => {
    if (balance >= minReserve * 1.5) return 'bg-emerald-50 dark:bg-emerald-950/30';
    if (balance >= minReserve) return 'bg-amber-50 dark:bg-amber-950/30';
    return 'bg-red-50 dark:bg-red-950/30';
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-blue-500" />
              4-Week Cash Forecast
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <RefreshCw className="h-6 w-6 text-muted-foreground animate-spin" />
              <p className="text-sm text-muted-foreground">Generating forecast...</p>
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
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-blue-500" />
              4-Week Cash Forecast
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-6 gap-3">
              <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-full">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              <Button variant="outline" size="sm" onClick={fetchForecast} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="h-full"
    >
      <Card className="h-full flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-blue-500" />
              4-Week Cash Forecast
            </CardTitle>
            {cached && (
              <Badge variant="secondary" className="text-xs">
                <Clock className="h-3 w-3 mr-1" />
                Cached
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4 flex-1">
          {forecast && (
            <>
              {/* Current Balance */}
              <div className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg">
                <span className="text-sm text-muted-foreground">Current Balance</span>
                <span className={`text-lg font-bold font-mono tabular-nums ${getBalanceClass(forecast.current_balance)}`}>
                  {formatCurrency(forecast.current_balance)}
                </span>
              </div>

              {/* Weekly Projections */}
              <TooltipProvider delayDuration={200}>
                <div className="overflow-x-auto -mx-4 px-4">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-zinc-100 dark:border-zinc-800">
                        <th className="text-left py-2 font-medium text-muted-foreground">Week</th>
                        <th className="text-left py-2 font-medium text-muted-foreground">Ending</th>
                        <th className="text-right py-2 font-medium text-muted-foreground">In</th>
                        <th className="text-right py-2 font-medium text-muted-foreground">Out</th>
                        <th className="text-right py-2 font-medium text-muted-foreground">Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.forecast?.map((week, index) => {
                        const inflowDetails = week.inflow_details || [];
                        const outflowDetails = week.outflow_details || [];
                        const hasInflowDetails = inflowDetails.length > 0;
                        const hasOutflowDetails = outflowDetails.length > 0;

                        return (
                          <motion.tr
                            key={week.week}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 * index }}
                            className="border-b border-zinc-50 dark:border-zinc-800/50"
                          >
                            <td className="py-2 font-medium">W{week.week}</td>
                            <td className="py-2 text-muted-foreground">{week.ending_date}</td>

                            {/* Inflows with tooltip */}
                            <td className="py-2 text-right">
                              {hasInflowDetails ? (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button className="font-mono tabular-nums text-emerald-600 dark:text-emerald-400 hover:underline cursor-help inline-flex items-center gap-1">
                                      <ArrowDownLeft className="h-3 w-3" />
                                      +{formatCurrency(week.inflows || week.expected_inflows || 0)}
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="left" className="max-w-xs p-0">
                                    <div className="p-3">
                                      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-zinc-100 dark:border-zinc-700">
                                        <ArrowDownLeft className="h-4 w-4 text-emerald-500" />
                                        <span className="font-medium text-sm">Expected Inflows</span>
                                      </div>
                                      <div className="space-y-2 max-h-48 overflow-y-auto">
                                        {inflowDetails.map((item, i) => (
                                          <div key={i} className="text-xs">
                                            <div className="flex items-center justify-between gap-2">
                                              <span className="font-medium truncate">{item.source}</span>
                                              <span className="font-mono text-emerald-600 dark:text-emerald-400 whitespace-nowrap">
                                                {formatCurrency(item.amount)}
                                              </span>
                                            </div>
                                            <div className="text-muted-foreground flex items-center justify-between mt-0.5">
                                              <span className="truncate">{item.description}</span>
                                              {item.likelihood && (
                                                <Badge variant="outline" className={cn(
                                                  "text-[10px] ml-2",
                                                  item.likelihood === 'High' && "border-emerald-500 text-emerald-600",
                                                  item.likelihood === 'Medium' && "border-amber-500 text-amber-600",
                                                  item.likelihood === 'Low' && "border-red-500 text-red-600"
                                                )}>
                                                  {item.likelihood}
                                                </Badge>
                                              )}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              ) : (
                                <span className="font-mono tabular-nums text-emerald-600 dark:text-emerald-400">
                                  +{formatCurrency(week.inflows || week.expected_inflows || 0)}
                                </span>
                              )}
                            </td>

                            {/* Outflows with tooltip */}
                            <td className="py-2 text-right">
                              {hasOutflowDetails ? (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button className="font-mono tabular-nums text-red-600 dark:text-red-400 hover:underline cursor-help inline-flex items-center gap-1">
                                      <ArrowUpRight className="h-3 w-3" />
                                      -{formatCurrency(week.outflows || week.expected_outflows || 0)}
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="left" className="max-w-xs p-0">
                                    <div className="p-3">
                                      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-zinc-100 dark:border-zinc-700">
                                        <ArrowUpRight className="h-4 w-4 text-red-500" />
                                        <span className="font-medium text-sm">Expected Outflows</span>
                                      </div>
                                      <div className="space-y-2 max-h-48 overflow-y-auto">
                                        {outflowDetails.map((item, i) => (
                                          <div key={i} className="text-xs">
                                            <div className="flex items-center justify-between gap-2">
                                              <span className="font-medium truncate">{item.category}</span>
                                              <span className="font-mono text-red-600 dark:text-red-400 whitespace-nowrap">
                                                {formatCurrency(item.amount)}
                                              </span>
                                            </div>
                                            <div className="text-muted-foreground mt-0.5">
                                              {item.description}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              ) : (
                                <span className="font-mono tabular-nums text-red-600 dark:text-red-400">
                                  -{formatCurrency(week.outflows || week.expected_outflows || 0)}
                                </span>
                              )}
                            </td>

                            <td className={`py-2 text-right font-mono tabular-nums font-medium ${getBalanceClass(week.projected_balance)}`}>
                              {formatCurrency(week.projected_balance)}
                            </td>
                          </motion.tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </TooltipProvider>

              {/* Risks */}
              <AnimatePresence>
                {forecast.risks && forecast.risks.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-lg"
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-1">Risks</h4>
                        <ul className="space-y-1">
                          {forecast.risks.map((risk, index) => (
                            <li key={index} className="text-xs text-amber-700 dark:text-amber-300">
                              {risk}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Recommendations */}
              <AnimatePresence>
                {forecast.recommendations && forecast.recommendations.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="p-3 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-lg"
                  >
                    <div className="flex items-start gap-2">
                      <Lightbulb className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">Recommendations</h4>
                        <ul className="space-y-1">
                          {forecast.recommendations.map((rec, index) => (
                            <li key={index} className="text-xs text-blue-700 dark:text-blue-300">
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Key Assumptions */}
              {forecast.key_assumptions && forecast.key_assumptions.length > 0 && (
                <div className="border-t border-zinc-100 dark:border-zinc-800 pt-3">
                  <button
                    onClick={() => setShowAssumptions(!showAssumptions)}
                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full"
                  >
                    <ChevronDown
                      className={`h-4 w-4 transition-transform ${showAssumptions ? 'rotate-180' : ''}`}
                    />
                    Key Assumptions
                  </button>
                  <AnimatePresence>
                    {showAssumptions && (
                      <motion.ul
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-2 space-y-1 pl-6"
                      >
                        {forecast.key_assumptions.map((assumption, index) => (
                          <li key={index} className="text-xs text-muted-foreground list-disc">
                            {assumption}
                          </li>
                        ))}
                      </motion.ul>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </>
          )}

          {generatedAt && (
            <div className="text-xs text-muted-foreground text-center pt-2 border-t border-zinc-100 dark:border-zinc-800">
              Generated: {new Date(generatedAt).toLocaleString()}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default CashForecast;
