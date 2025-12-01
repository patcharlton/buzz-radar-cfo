import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Sparkles,
  RefreshCw,
  Send,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Info,
  ChevronDown,
  ChevronUp,
  MessageSquare,
} from 'lucide-react';
import api from '@/services/api';

function InsightItem({ insight, index }) {
  const [expanded, setExpanded] = useState(false);

  const getSeverityIcon = (text) => {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('critical') || lowerText.includes('risk') || lowerText.includes('warning')) {
      return <AlertTriangle className="h-4 w-4 text-amber-500" />;
    }
    if (lowerText.includes('increase') || lowerText.includes('growth') || lowerText.includes('positive')) {
      return <TrendingUp className="h-4 w-4 text-emerald-500" />;
    }
    if (lowerText.includes('decrease') || lowerText.includes('decline')) {
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    }
    return <Info className="h-4 w-4 text-blue-500" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="border-b border-zinc-100 dark:border-zinc-800 last:border-0"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors flex items-start gap-3"
      >
        {getSeverityIcon(insight)}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-foreground line-clamp-2">{insight}</p>
        </div>
        {insight.length > 100 && (
          <span className="text-muted-foreground">
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </span>
        )}
      </button>
      <AnimatePresence>
        {expanded && insight.length > 100 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-3 pb-3 pl-10"
          >
            <p className="text-sm text-muted-foreground">{insight}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function AiInsights() {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [cached, setCached] = useState(false);

  const fetchInsights = async () => {
    try {
      setError(null);
      const data = await api.getDailyInsights();
      if (data.success) {
        setInsights(data.insights);
        setCached(data.cached || false);
      } else {
        setError(data.error || 'Failed to load insights');
      }
    } catch (err) {
      setError(err.message || 'Failed to load insights');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      setError(null);
      const data = await api.refreshInsights();
      if (data.success) {
        setInsights(data.insights);
        setCached(false);
      } else {
        setError(data.error || 'Failed to refresh insights');
      }
    } catch (err) {
      setError(err.message || 'Failed to refresh insights');
    } finally {
      setRefreshing(false);
    }
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim() || asking) return;

    setAsking(true);
    setAnswer(null);
    try {
      const data = await api.askQuestion(question);
      if (data.success) {
        setAnswer(data.answer);
      } else {
        setAnswer(`Error: ${data.error}`);
      }
    } catch (err) {
      setAnswer(`Error: ${err.message}`);
    } finally {
      setAsking(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  // Parse insights into bullet points
  const parseInsights = (text) => {
    if (!text) return [];
    return text
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => line.replace(/^[-*•]\s*/, '').trim())
      .filter((line) => line.length > 0);
  };

  const insightsList = parseInsights(insights);

  if (loading) {
    return (
      <Card className="ai-gradient-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            AI CFO Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-3/4" />
          </div>
          <div className="mt-4 flex items-center justify-center gap-2 text-muted-foreground">
            <div className="flex gap-1">
              <motion.div
                className="w-2 h-2 bg-purple-500 rounded-full"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
              <motion.div
                className="w-2 h-2 bg-purple-500 rounded-full"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
              />
              <motion.div
                className="w-2 h-2 bg-purple-500 rounded-full"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
              />
            </div>
            <span className="text-sm">Analyzing your financial data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <Card className="ai-gradient-border overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              AI CFO Insights
              {cached && (
                <Badge variant="secondary" className="text-xs">
                  Cached
                </Badge>
              )}
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="gap-1"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-950/30 border-b border-red-200 dark:border-red-900">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Insights List */}
          <div className="max-h-[300px] overflow-y-auto">
            {insightsList.length > 0 ? (
              insightsList.slice(0, 5).map((insight, index) => (
                <InsightItem key={index} insight={insight} index={index} />
              ))
            ) : (
              <div className="p-4 text-center text-muted-foreground">
                No insights available
              </div>
            )}
          </div>

          {/* Ask Question Section */}
          <div className="border-t border-zinc-200 dark:border-zinc-800 p-4 bg-zinc-50/50 dark:bg-zinc-900/50">
            <form onSubmit={handleAskQuestion} className="flex gap-2">
              <div className="flex-1 relative">
                <MessageSquare className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Ask about your finances..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="pl-10"
                  disabled={asking}
                />
              </div>
              <Button type="submit" size="icon" disabled={asking || !question.trim()}>
                {asking ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>

            {/* Answer */}
            <AnimatePresence>
              {answer && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 p-3 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800"
                >
                  <p className="text-sm text-foreground whitespace-pre-wrap">{answer}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default AiInsights;
