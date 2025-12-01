import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
  MessageCircle,
  Clock,
  DollarSign,
  Users,
  FileText,
  Target,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import api from '@/services/api';

const SUGGESTED_QUESTIONS = [
  { text: "What's our cash runway?", icon: TrendingUp },
  { text: "How is ViiV tracking?", icon: DollarSign },
  { text: "What invoices need chasing?", icon: FileText },
  { text: "What's the BRIANN pilot status?", icon: Target },
  { text: "What's our biggest risk?", icon: AlertTriangle },
];

function formatMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let listItems = [];
  let inList = false;
  let currentListType = null;

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // Headers
    if (trimmedLine.startsWith('# ')) {
      if (inList && listItems.length > 0) {
        elements.push(
          <ul key={`list-${index}`} className="list-disc pl-5 mb-3 space-y-1">
            {listItems}
          </ul>
        );
        listItems = [];
        inList = false;
      }
      elements.push(
        <h2 key={index} className="text-lg font-bold text-foreground mt-4 mb-2">
          {trimmedLine.slice(2)}
        </h2>
      );
      return;
    }

    if (trimmedLine.startsWith('## ')) {
      if (inList && listItems.length > 0) {
        elements.push(
          <ul key={`list-${index}`} className="list-disc pl-5 mb-3 space-y-1">
            {listItems}
          </ul>
        );
        listItems = [];
        inList = false;
      }
      elements.push(
        <h3 key={index} className="text-base font-semibold text-foreground mt-3 mb-2 flex items-center gap-2">
          {trimmedLine.includes('CRITICAL') || trimmedLine.includes('IMMEDIATE') ? (
            <AlertTriangle className="h-4 w-4 text-red-500" />
          ) : trimmedLine.includes('CASH') || trimmedLine.includes('REVENUE') ? (
            <DollarSign className="h-4 w-4 text-emerald-500" />
          ) : trimmedLine.includes('RISK') ? (
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          ) : trimmedLine.includes('TRANSITION') || trimmedLine.includes('PLATFORM') ? (
            <Target className="h-4 w-4 text-indigo-500" />
          ) : (
            <Info className="h-4 w-4 text-blue-500" />
          )}
          {trimmedLine.slice(3)}
        </h3>
      );
      return;
    }

    if (trimmedLine.startsWith('### ')) {
      if (inList && listItems.length > 0) {
        elements.push(
          <ul key={`list-${index}`} className="list-disc pl-5 mb-3 space-y-1">
            {listItems}
          </ul>
        );
        listItems = [];
        inList = false;
      }
      elements.push(
        <h4 key={index} className="text-sm font-semibold text-foreground mt-2 mb-1">
          {trimmedLine.slice(4)}
        </h4>
      );
      return;
    }

    // List items
    if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ') || /^\d+\.\s/.test(trimmedLine)) {
      inList = true;
      const content = trimmedLine.replace(/^[-*]\s*/, '').replace(/^\d+\.\s*/, '');

      // Parse bold text
      const parts = content.split(/(\*\*.*?\*\*)/g);
      const formattedContent = parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
        }
        return part;
      });

      listItems.push(
        <li key={index} className="text-sm text-foreground">
          {formattedContent}
        </li>
      );
      return;
    }

    // Flush list if we hit a non-list line
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`list-${index}`} className="list-disc pl-5 mb-3 space-y-1">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }

    // Empty lines
    if (trimmedLine === '') {
      return;
    }

    // Bold paragraphs
    if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**')) {
      elements.push(
        <p key={index} className="text-sm font-semibold text-foreground mb-2">
          {trimmedLine.slice(2, -2)}
        </p>
      );
      return;
    }

    // Regular text with inline bold
    const parts = trimmedLine.split(/(\*\*.*?\*\*)/g);
    const formattedContent = parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
      }
      return part;
    });

    elements.push(
      <p key={index} className="text-sm text-foreground mb-2 leading-relaxed">
        {formattedContent}
      </p>
    );
  });

  // Flush remaining list items
  if (listItems.length > 0) {
    elements.push(
      <ul key="list-final" className="list-disc pl-5 mb-3 space-y-1">
        {listItems}
      </ul>
    );
  }

  return elements;
}

export function AiCfoPanel() {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [cached, setCached] = useState(false);
  const [generatedAt, setGeneratedAt] = useState(null);
  const [showFullInsights, setShowFullInsights] = useState(false);

  const fetchInsights = async () => {
    try {
      setError(null);
      const data = await api.getDailyInsights();
      if (data.success) {
        setInsights(data.insights);
        setCached(data.cached || false);
        setGeneratedAt(data.generated_at);
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
        setGeneratedAt(data.generated_at);
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
    e?.preventDefault();
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

  const handleSuggestionClick = (suggestion) => {
    setQuestion(suggestion);
    setAsking(true);
    setAnswer(null);

    api.askQuestion(suggestion)
      .then((data) => {
        if (data.success) {
          setAnswer(data.answer);
        } else {
          setAnswer(`Error: ${data.error}`);
        }
      })
      .catch((err) => {
        setAnswer(`Error: ${err.message}`);
      })
      .finally(() => {
        setAsking(false);
      });
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  if (loading) {
    return (
      <Card className="ai-gradient-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            AI CFO Assistant
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
            <span className="text-sm">Analyzing your financial data & strategic context...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <Card className="ai-gradient-border overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              AI CFO Assistant
              <Badge variant="secondary" className="text-xs ml-1">
                Xero + Context
              </Badge>
            </CardTitle>
            <div className="flex items-center gap-2">
              {cached && (
                <Badge variant="outline" className="text-xs">
                  <Clock className="h-3 w-3 mr-1" />
                  Cached
                </Badge>
              )}
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
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-950/30 border-b border-red-200 dark:border-red-900">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Daily Insights */}
          {insights && (
            <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                  Daily Insights
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFullInsights(!showFullInsights)}
                  className="text-xs"
                >
                  {showFullInsights ? 'Show Less' : 'Show Full Report'}
                  {showFullInsights ? (
                    <ChevronUp className="h-3 w-3 ml-1" />
                  ) : (
                    <ChevronDown className="h-3 w-3 ml-1" />
                  )}
                </Button>
              </div>
              <div className={`prose prose-sm dark:prose-invert max-w-none ${showFullInsights ? '' : 'max-h-64 overflow-y-auto'}`}>
                {formatMarkdown(insights)}
              </div>
              {generatedAt && (
                <p className="text-xs text-muted-foreground mt-3 pt-2 border-t border-zinc-100 dark:border-zinc-800">
                  Generated: {new Date(generatedAt).toLocaleString()}
                </p>
              )}
            </div>
          )}

          {/* Ask Question Section */}
          <div className="p-4 bg-gradient-to-br from-indigo-50/50 to-purple-50/50 dark:from-indigo-950/20 dark:to-purple-950/20">
            <div className="flex items-center gap-2 mb-3">
              <MessageCircle className="h-4 w-4 text-indigo-500" />
              <span className="text-sm font-semibold">Ask Your AI CFO</span>
            </div>

            {/* Suggested Questions */}
            <div className="flex flex-wrap gap-2 mb-3">
              {SUGGESTED_QUESTIONS.map((suggestion, index) => {
                const Icon = suggestion.icon;
                return (
                  <motion.button
                    key={index}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.05 * index }}
                    onClick={() => handleSuggestionClick(suggestion.text)}
                    disabled={asking}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full
                             bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300
                             border border-zinc-200 dark:border-zinc-700
                             hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-700 dark:hover:text-indigo-300
                             hover:border-indigo-200 dark:hover:border-indigo-800
                             transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Icon className="h-3 w-3" />
                    {suggestion.text}
                  </motion.button>
                );
              })}
            </div>

            {/* Input Form */}
            <form onSubmit={handleAskQuestion} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about finances, pipeline, risks, or strategy..."
                disabled={asking}
                className="flex-1 h-9 rounded-md border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-1 text-sm shadow-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
              />
              <Button
                type="submit"
                disabled={asking || !question.trim()}
                className="gap-2"
              >
                {asking ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                <span className="hidden sm:inline">{asking ? 'Thinking...' : 'Ask'}</span>
              </Button>
            </form>

            {/* Loading State */}
            <AnimatePresence>
              {asking && !answer && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center justify-center gap-3 py-6"
                >
                  <div className="flex gap-1">
                    <motion.div
                      className="w-2 h-2 bg-indigo-500 rounded-full"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    />
                    <motion.div
                      className="w-2 h-2 bg-indigo-500 rounded-full"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                    />
                    <motion.div
                      className="w-2 h-2 bg-indigo-500 rounded-full"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground">Analyzing with Xero data + strategic context...</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Answer */}
            <AnimatePresence>
              {answer && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mt-4 p-4 bg-white dark:bg-zinc-900 rounded-lg border border-indigo-100 dark:border-indigo-900/50"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-sm flex-shrink-0">
                      <Sparkles className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide mb-2">
                        AI CFO Response
                      </h4>
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        {formatMarkdown(answer)}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default AiCfoPanel;
