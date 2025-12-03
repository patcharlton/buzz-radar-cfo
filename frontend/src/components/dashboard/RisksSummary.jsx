import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { CardTitleTooltip } from '@/components/ui/info-tooltip';
import {
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import api from '@/services/api';
import { formatCurrency } from '@/lib/utils';

export function RisksSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedRisk, setExpandedRisk] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getRisks();
        if (result.success) {
          setData(result);
        } else {
          setError(result.error || 'Failed to load risks');
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
            <ShieldAlert className="h-4 w-4" />
            Risk Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-16 w-full mb-2" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <ShieldAlert className="h-4 w-4" />
            Risk Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const criticalRisks = data?.critical_risks || [];
  const criticalCount = criticalRisks.filter(r => r.severity === 'Critical').length;
  const highCount = criticalRisks.filter(r => r.severity === 'High').length;

  const getSeverityConfig = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return {
          icon: AlertTriangle,
          bg: 'bg-red-50 dark:bg-red-950/30',
          border: 'border-red-200 dark:border-red-900',
          text: 'text-red-700 dark:text-red-300',
          badge: 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
        };
      case 'high':
        return {
          icon: AlertCircle,
          bg: 'bg-amber-50 dark:bg-amber-950/30',
          border: 'border-amber-200 dark:border-amber-900',
          text: 'text-amber-700 dark:text-amber-300',
          badge: 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300',
        };
      default:
        return {
          icon: AlertCircle,
          bg: 'bg-blue-50 dark:bg-blue-950/30',
          border: 'border-blue-200 dark:border-blue-900',
          text: 'text-blue-700 dark:text-blue-300',
          badge: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
        };
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="h-full"
    >
      <Card className="h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitleTooltip description="Key business risks identified from financial data and business context. Click each risk to see details and mitigation strategies.">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <ShieldAlert className="h-4 w-4" />
                Risk Management
              </CardTitle>
            </CardTitleTooltip>
            <div className="flex gap-1">
              {criticalCount > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {criticalCount} critical
                </Badge>
              )}
              {highCount > 0 && (
                <Badge className="text-xs bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300">
                  {highCount} high
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {criticalRisks.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground">No critical risks identified</p>
            </div>
          ) : (
            criticalRisks.map((risk, index) => {
              const config = getSeverityConfig(risk.severity);
              const Icon = config.icon;
              const isExpanded = expandedRisk === risk.id;

              return (
                <motion.div
                  key={risk.id || index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * index }}
                  className={`rounded-lg border ${config.bg} ${config.border}`}
                >
                  <button
                    onClick={() => setExpandedRisk(isExpanded ? null : risk.id)}
                    className="w-full p-3 text-left"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-1.5 rounded ${config.badge}`}>
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={`text-xs ${config.badge}`}>
                            {risk.severity}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {risk.category}
                          </span>
                        </div>
                        <h4 className={`text-sm font-medium ${config.text}`}>
                          {risk.name}
                        </h4>
                      </div>
                      <span className="text-muted-foreground">
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </span>
                    </div>
                  </button>

                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      className="px-3 pb-3 border-t border-zinc-200 dark:border-zinc-700"
                    >
                      {/* Current State */}
                      {risk.current_state && Object.keys(risk.current_state).length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-foreground mb-1">Current State:</p>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(risk.current_state).map(([key, value]) => (
                              <div key={key} className="text-xs">
                                <span className="text-muted-foreground">
                                  {key.replace(/_/g, ' ')}:
                                </span>{' '}
                                <span className="font-medium">
                                  {typeof value === 'number' && value > 1000
                                    ? formatCurrency(value)
                                    : typeof value === 'number'
                                    ? `${value}%`
                                    : value}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Specific Threats */}
                      {risk.specific_threats && risk.specific_threats.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-foreground mb-1">Threats:</p>
                          <ul className="space-y-1">
                            {risk.specific_threats.slice(0, 2).map((threat, i) => (
                              <li key={i} className="text-xs text-muted-foreground">
                                <span className="font-medium">{threat.client}:</span> {threat.threat}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Mitigation */}
                      {risk.mitigation && risk.mitigation.length > 0 && (
                        <div className="mt-3 p-2 bg-emerald-50 dark:bg-emerald-950/30 rounded">
                          <p className="text-xs font-medium text-emerald-700 dark:text-emerald-300 mb-1">
                            Mitigation:
                          </p>
                          <p className="text-xs text-emerald-600 dark:text-emerald-400">
                            {risk.mitigation[0]}
                          </p>
                        </div>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              );
            })
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RisksSummary;
