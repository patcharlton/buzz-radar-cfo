import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Rocket,
  Target,
  TrendingUp,
  Calendar,
  CheckCircle2,
  Circle,
} from 'lucide-react';
import api from '@/services/api';
import { formatCurrency } from '@/lib/utils';

export function TransitionProgress() {
  const [data, setData] = useState(null);
  const [goals, setGoals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [transitionResult, goalsResult] = await Promise.all([
          api.getTransition(),
          api.getGoals(),
        ]);

        if (transitionResult.success) {
          setData(transitionResult.transition);
        }
        if (goalsResult.success) {
          setGoals(goalsResult.q1_2026);
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
            <Rocket className="h-4 w-4" />
            Platform Transition
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-full mb-4" />
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
            <Rocket className="h-4 w-4" />
            Platform Transition
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const revenueMix = data?.revenue_mix || {};
  const current = revenueMix.current || { services: 100, platform: 0 };
  const target2026 = revenueMix.target_end_2026 || { services: 75, platform: 25 };
  const exitThesis = data?.exit_thesis || {};

  const platformProgress = (current.platform / target2026.platform) * 100;

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
              <Rocket className="h-4 w-4" />
              Platform Transition
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              {data?.current_state || 'Services-led'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Revenue Mix Progress */}
          <div>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-muted-foreground">Revenue Mix</span>
              <span className="font-medium">
                {current.platform}% Platform / {current.services}% Services
              </span>
            </div>
            <div className="h-4 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden flex">
              <motion.div
                className="bg-indigo-500 h-full"
                initial={{ width: 0 }}
                animate={{ width: `${current.platform}%` }}
                transition={{ duration: 1, delay: 0.3 }}
              />
              <motion.div
                className="bg-zinc-400 dark:bg-zinc-600 h-full flex-1"
                initial={{ width: 0 }}
                animate={{ width: `${current.services}%` }}
                transition={{ duration: 1, delay: 0.3 }}
              />
            </div>
            <div className="flex justify-between text-xs mt-1">
              <span className="text-indigo-600 dark:text-indigo-400">Platform</span>
              <span className="text-muted-foreground">Services</span>
            </div>
          </div>

          {/* Target Progress */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-indigo-50 dark:bg-indigo-950/30 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">2026 Target</p>
              <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                {target2026.platform}% Platform
              </p>
              <p className="text-xs text-muted-foreground">
                {formatCurrency(data?.platform_revenue_target_2026 || 450000)}
              </p>
            </div>
            <div className="p-3 bg-purple-50 dark:bg-purple-950/30 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">Exit Thesis</p>
              <p className="text-lg font-bold text-purple-600 dark:text-purple-400">
                {exitThesis.target_year || 2030}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatCurrency(exitThesis.valuation_low || 35000000)} - {formatCurrency(exitThesis.valuation_high || 50000000)}
              </p>
            </div>
          </div>

          {/* Q1 2026 Goals */}
          {goals && goals.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium">Q1 2026 Goals</span>
              </div>
              <div className="space-y-2">
                {goals.slice(0, 4).map((goal, index) => {
                  const isPriorityCritical = goal.priority === 'Critical';
                  const isPriorityHigh = goal.priority === 'High';

                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * index }}
                      className={`flex items-start gap-2 p-2 rounded-lg ${
                        isPriorityCritical
                          ? 'bg-red-50 dark:bg-red-950/30'
                          : isPriorityHigh
                          ? 'bg-amber-50 dark:bg-amber-950/30'
                          : 'bg-zinc-50 dark:bg-zinc-800/50'
                      }`}
                    >
                      <Circle className={`h-4 w-4 mt-0.5 ${
                        isPriorityCritical
                          ? 'text-red-500'
                          : isPriorityHigh
                          ? 'text-amber-500'
                          : 'text-zinc-400'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{goal.goal}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge
                            variant="outline"
                            className={`text-xs ${
                              isPriorityCritical
                                ? 'border-red-200 text-red-600'
                                : isPriorityHigh
                                ? 'border-amber-200 text-amber-600'
                                : ''
                            }`}
                          >
                            {goal.priority}
                          </Badge>
                          {(goal.value || goal.value_if_success) && (
                            <span className="text-xs font-mono text-muted-foreground">
                              {formatCurrency(goal.value || goal.value_if_success)}
                            </span>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Key Milestones */}
          <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800">
            <p className="text-xs text-muted-foreground mb-2">Key Milestones</p>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                <span>Q1: Ferring Pilot</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full" />
                <span>Q2: 3-4 Pilots</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-purple-500 rounded-full" />
                <span>Q4: 25% Platform</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default TransitionProgress;
