import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Activity,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  RefreshCw,
  Clock,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import api from '../services/api';

function Anomalies() {
  const [anomalyData, setAnomalyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generatedAt, setGeneratedAt] = useState(null);
  const [cached, setCached] = useState(false);

  const fetchAnomalies = async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await api.getAnomalies();
      if (data.success) {
        setAnomalyData(data.anomalies);
        setGeneratedAt(data.generated_at);
        setCached(data.cached || false);
      } else {
        setError(data.error || 'Failed to load anomalies');
      }
    } catch (err) {
      setError(err.message || 'Failed to load anomalies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, []);

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
      case 'warning':
        return {
          icon: AlertCircle,
          bg: 'bg-amber-50 dark:bg-amber-950/30',
          border: 'border-amber-200 dark:border-amber-900',
          text: 'text-amber-700 dark:text-amber-300',
          badge: 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300',
        };
      case 'info':
      default:
        return {
          icon: Info,
          bg: 'bg-blue-50 dark:bg-blue-950/30',
          border: 'border-blue-200 dark:border-blue-900',
          text: 'text-blue-700 dark:text-blue-300',
          badge: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
        };
    }
  };

  const getHealthConfig = (health) => {
    switch (health?.toLowerCase()) {
      case 'good':
        return {
          icon: ShieldCheck,
          bg: 'bg-emerald-50 dark:bg-emerald-950/30',
          border: 'border-emerald-200 dark:border-emerald-900',
          text: 'text-emerald-700 dark:text-emerald-300',
        };
      case 'caution':
        return {
          icon: ShieldAlert,
          bg: 'bg-amber-50 dark:bg-amber-950/30',
          border: 'border-amber-200 dark:border-amber-900',
          text: 'text-amber-700 dark:text-amber-300',
        };
      case 'at risk':
        return {
          icon: ShieldAlert,
          bg: 'bg-red-50 dark:bg-red-950/30',
          border: 'border-red-200 dark:border-red-900',
          text: 'text-red-700 dark:text-red-300',
        };
      default:
        return {
          icon: Activity,
          bg: 'bg-zinc-50 dark:bg-zinc-800',
          border: 'border-zinc-200 dark:border-zinc-700',
          text: 'text-zinc-700 dark:text-zinc-300',
        };
    }
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-purple-500" />
              Financial Health Check
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <RefreshCw className="h-6 w-6 text-muted-foreground animate-spin" />
              <p className="text-sm text-muted-foreground">Analysing for anomalies...</p>
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
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-purple-500" />
              Financial Health Check
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-6 gap-3">
              <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-full">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              <Button variant="outline" size="sm" onClick={fetchAnomalies} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  const summary = anomalyData?.summary || {};
  const anomalies = anomalyData?.anomalies || [];
  const healthConfig = getHealthConfig(summary.overall_health);
  const HealthIcon = healthConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="h-full"
    >
      <Card className="h-full flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-purple-500" />
              Financial Health Check
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
          {/* Health Summary */}
          <div className={`flex items-center justify-between p-3 rounded-lg border ${healthConfig.bg} ${healthConfig.border}`}>
            <div className="flex items-center gap-2">
              <HealthIcon className={`h-5 w-5 ${healthConfig.text}`} />
              <div>
                <span className="text-sm text-muted-foreground">Overall Health:</span>
                <span className={`ml-2 font-semibold ${healthConfig.text}`}>
                  {summary.overall_health || 'Unknown'}
                </span>
              </div>
            </div>
            {summary.critical_count > 0 && (
              <Badge variant="destructive" className="text-xs">
                {summary.critical_count} critical
              </Badge>
            )}
          </div>

          {/* Anomalies List */}
          {anomalies.length > 0 ? (
            <div className="space-y-3">
              {anomalies.map((anomaly, index) => {
                const config = getSeverityConfig(anomaly.severity);
                const Icon = config.icon;
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 * index }}
                    className={`p-3 rounded-lg border ${config.bg} ${config.border}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-1.5 rounded ${config.badge}`}>
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={`text-xs ${config.badge}`}>
                            {anomaly.severity}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {anomaly.category}
                          </span>
                        </div>
                        <h4 className={`text-sm font-medium ${config.text}`}>
                          {anomaly.title}
                        </h4>
                        <p className="text-xs text-muted-foreground mt-1">
                          {anomaly.description}
                        </p>
                        {anomaly.recommendation && (
                          <div className="mt-2 pt-2 border-t border-zinc-200 dark:border-zinc-700">
                            <p className="text-xs">
                              <span className="font-medium text-foreground">Action: </span>
                              <span className="text-muted-foreground">{anomaly.recommendation}</span>
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-6 gap-2"
            >
              <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 rounded-full">
                <CheckCircle2 className="h-6 w-6 text-emerald-500" />
              </div>
              <p className="text-sm text-muted-foreground text-center">
                No significant anomalies detected.<br />
                Your finances look healthy!
              </p>
            </motion.div>
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

export default Anomalies;
