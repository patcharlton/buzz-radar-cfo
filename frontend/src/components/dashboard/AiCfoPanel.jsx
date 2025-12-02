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

// Helper to get icon and color based on content keywords
function getSectionStyle(text) {
  const upper = text.toUpperCase();
  if (upper.includes('CRITICAL') || upper.includes('IMMEDIATE') || upper.includes('URGENT') || upper.includes('ALERT')) {
    return { icon: AlertTriangle, color: 'red', bgColor: 'bg-red-50 dark:bg-red-950/30', borderColor: 'border-red-200 dark:border-red-900', textColor: 'text-red-700 dark:text-red-300', iconColor: 'text-red-500' };
  }
  if (upper.includes('CASH') || upper.includes('REVENUE') || upper.includes('PAYMENT') || upper.includes('INCOME') || upper.includes('PROFIT')) {
    return { icon: DollarSign, color: 'emerald', bgColor: 'bg-emerald-50 dark:bg-emerald-950/30', borderColor: 'border-emerald-200 dark:border-emerald-900', textColor: 'text-emerald-700 dark:text-emerald-300', iconColor: 'text-emerald-500' };
  }
  if (upper.includes('RISK') || upper.includes('WARNING') || upper.includes('CONCERN') || upper.includes('ISSUE')) {
    return { icon: AlertTriangle, color: 'amber', bgColor: 'bg-amber-50 dark:bg-amber-950/30', borderColor: 'border-amber-200 dark:border-amber-900', textColor: 'text-amber-700 dark:text-amber-300', iconColor: 'text-amber-500' };
  }
  if (upper.includes('GROWTH') || upper.includes('OPPORTUNITY') || upper.includes('POSITIVE') || upper.includes('SUCCESS')) {
    return { icon: TrendingUp, color: 'emerald', bgColor: 'bg-emerald-50 dark:bg-emerald-950/30', borderColor: 'border-emerald-200 dark:border-emerald-900', textColor: 'text-emerald-700 dark:text-emerald-300', iconColor: 'text-emerald-500' };
  }
  if (upper.includes('TRANSITION') || upper.includes('PLATFORM') || upper.includes('STRATEGY') || upper.includes('GOAL')) {
    return { icon: Target, color: 'indigo', bgColor: 'bg-indigo-50 dark:bg-indigo-950/30', borderColor: 'border-indigo-200 dark:border-indigo-900', textColor: 'text-indigo-700 dark:text-indigo-300', iconColor: 'text-indigo-500' };
  }
  if (upper.includes('CLIENT') || upper.includes('CUSTOMER') || upper.includes('ACCOUNT')) {
    return { icon: Users, color: 'blue', bgColor: 'bg-blue-50 dark:bg-blue-950/30', borderColor: 'border-blue-200 dark:border-blue-900', textColor: 'text-blue-700 dark:text-blue-300', iconColor: 'text-blue-500' };
  }
  if (upper.includes('INVOICE') || upper.includes('BILL') || upper.includes('DOCUMENT')) {
    return { icon: FileText, color: 'violet', bgColor: 'bg-violet-50 dark:bg-violet-950/30', borderColor: 'border-violet-200 dark:border-violet-900', textColor: 'text-violet-700 dark:text-violet-300', iconColor: 'text-violet-500' };
  }
  return { icon: Info, color: 'zinc', bgColor: 'bg-zinc-50 dark:bg-zinc-800/50', borderColor: 'border-zinc-200 dark:border-zinc-700', textColor: 'text-zinc-700 dark:text-zinc-300', iconColor: 'text-zinc-500' };
}

// Parse inline formatting (bold, code, etc.)
function parseInlineFormatting(text) {
  if (!text) return null;

  // Split by bold markers and code backticks
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="px-1.5 py-0.5 bg-zinc-100 dark:bg-zinc-800 rounded text-sm font-mono text-purple-600 dark:text-purple-400">{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

function formatMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let listItems = [];
  let inList = false;
  let sectionIndex = 0;

  const flushList = (index) => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${index}`} className="space-y-2 mb-5">
          {listItems}
        </ul>
      );
      listItems = [];
    }
    inList = false;
  };

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // H1 Headers - Major sections with card styling
    if (trimmedLine.startsWith('# ')) {
      flushList(index);
      const headerText = trimmedLine.slice(2);
      const style = getSectionStyle(headerText);
      const Icon = style.icon;
      sectionIndex++;

      elements.push(
        <div key={index} className={`rounded-lg border ${style.borderColor} ${style.bgColor} p-4 mb-5 mt-6 first:mt-0`}>
          <h2 className={`text-base font-bold ${style.textColor} flex items-center gap-2`}>
            <Icon className={`h-5 w-5 ${style.iconColor}`} />
            {headerText}
          </h2>
        </div>
      );
      return;
    }

    // H2 Headers - Sub-sections with left border accent
    if (trimmedLine.startsWith('## ')) {
      flushList(index);
      const headerText = trimmedLine.slice(3);
      const style = getSectionStyle(headerText);
      const Icon = style.icon;

      elements.push(
        <div key={index} className={`border-l-4 ${style.borderColor} pl-4 py-2 mb-4 mt-5`}>
          <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Icon className={`h-4 w-4 ${style.iconColor}`} />
            {headerText}
          </h3>
        </div>
      );
      return;
    }

    // H3 Headers - Minor sections
    if (trimmedLine.startsWith('### ')) {
      flushList(index);
      const headerText = trimmedLine.slice(4);

      elements.push(
        <h4 key={index} className="text-sm font-semibold text-foreground mt-4 mb-2 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
          {headerText}
        </h4>
      );
      return;
    }

    // List items - enhanced with better styling
    if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ') || /^\d+\.\s/.test(trimmedLine)) {
      inList = true;
      const isNumbered = /^\d+\.\s/.test(trimmedLine);
      const content = trimmedLine.replace(/^[-*]\s*/, '').replace(/^\d+\.\s*/, '');
      const formattedContent = parseInlineFormatting(content);

      listItems.push(
        <li key={index} className="flex items-start gap-3 text-sm text-muted-foreground leading-relaxed">
          <span className="flex-shrink-0 mt-1.5">
            {isNumbered ? (
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 text-xs font-medium">
                {trimmedLine.match(/^\d+/)?.[0]}
              </span>
            ) : (
              <span className="block w-1.5 h-1.5 rounded-full bg-purple-400 dark:bg-purple-500" />
            )}
          </span>
          <span className="flex-1">{formattedContent}</span>
        </li>
      );
      return;
    }

    // Flush list if we hit a non-list line
    if (inList) {
      flushList(index);
    }

    // Empty lines - add spacing
    if (trimmedLine === '') {
      return;
    }

    // Bold paragraphs - callout style
    if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**')) {
      const innerText = trimmedLine.slice(2, -2);
      const style = getSectionStyle(innerText);

      elements.push(
        <p key={index} className={`text-sm font-semibold ${style.textColor} mb-3 py-2 px-3 rounded-md ${style.bgColor} border ${style.borderColor}`}>
          {innerText}
        </p>
      );
      return;
    }

    // Regular paragraphs
    const formattedContent = parseInlineFormatting(trimmedLine);
    elements.push(
      <p key={index} className="text-sm text-muted-foreground mb-3 leading-relaxed">
        {formattedContent}
      </p>
    );
  });

  // Flush remaining list items
  flushList('final');

  return <div className="space-y-1">{elements}</div>;
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
            <div className="p-3 sm:p-5 border-b border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <div className="p-1.5 rounded-md bg-emerald-100 dark:bg-emerald-900/30">
                    <TrendingUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  Daily Insights
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFullInsights(!showFullInsights)}
                  className="text-xs gap-1 px-2 sm:px-3"
                >
                  <span className="hidden sm:inline">{showFullInsights ? 'Show Less' : 'Show Full Report'}</span>
                  <span className="sm:hidden">{showFullInsights ? 'Less' : 'More'}</span>
                  {showFullInsights ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                </Button>
              </div>
              <div className={`max-w-none ${showFullInsights ? '' : 'max-h-64 sm:max-h-80 overflow-y-auto pr-1 sm:pr-2'}`}>
                {formatMarkdown(insights)}
              </div>
              {generatedAt && (
                <p className="text-xs text-muted-foreground mt-3 sm:mt-4 pt-2 sm:pt-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center gap-1.5">
                  <Clock className="h-3 w-3" />
                  <span className="hidden sm:inline">Generated: {new Date(generatedAt).toLocaleString()}</span>
                  <span className="sm:hidden">{new Date(generatedAt).toLocaleDateString()}</span>
                </p>
              )}
            </div>
          )}

          {/* Ask Question Section */}
          <div className="p-3 sm:p-5 bg-gradient-to-br from-indigo-50/50 to-purple-50/50 dark:from-indigo-950/20 dark:to-purple-950/20">
            <div className="flex items-center gap-2 mb-3 sm:mb-4">
              <div className="p-1.5 rounded-md bg-indigo-100 dark:bg-indigo-900/30">
                <MessageCircle className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              </div>
              <span className="text-sm font-semibold">Ask Your AI CFO</span>
            </div>

            {/* Suggested Questions - Horizontal scroll on mobile */}
            <div className="flex gap-2 mb-3 overflow-x-auto pb-2 -mx-3 px-3 sm:mx-0 sm:px-0 sm:flex-wrap sm:overflow-visible scrollbar-hide">
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
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap flex-shrink-0
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
                placeholder="Ask about finances..."
                disabled={asking}
                className="flex-1 h-10 sm:h-9 rounded-md border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-1 text-base sm:text-sm shadow-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
              />
              <Button
                type="submit"
                disabled={asking || !question.trim()}
                className="gap-2 h-10 sm:h-9 px-3 sm:px-4"
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
                  className="flex items-center justify-center gap-3 py-4 sm:py-6"
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
                  <span className="text-xs sm:text-sm text-muted-foreground">Analyzing...</span>
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
                  className="mt-4 sm:mt-5"
                >
                  <div className="bg-white dark:bg-zinc-900 rounded-xl border border-indigo-200 dark:border-indigo-900/50 overflow-hidden shadow-sm">
                    {/* Header */}
                    <div className="px-3 sm:px-4 py-2 sm:py-3 bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-white" />
                      <span className="text-sm font-medium text-white">AI CFO Response</span>
                    </div>
                    {/* Content */}
                    <div className="p-3 sm:p-5">
                      {formatMarkdown(answer)}
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
