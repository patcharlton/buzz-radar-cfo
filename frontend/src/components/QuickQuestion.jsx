import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  MessageCircle,
  Send,
  RefreshCw,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Users,
  FileText,
} from 'lucide-react';
import api from '../services/api';

const SUGGESTED_QUESTIONS = [
  { text: "What's our cash runway?", icon: TrendingUp },
  { text: "How is ViiV tracking?", icon: DollarSign },
  { text: "What invoices need chasing?", icon: FileText },
  { text: "Can we afford to hire?", icon: Users },
  { text: "What's our biggest risk?", icon: AlertTriangle },
];

function QuickQuestion() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const data = await api.askQuestion(question);
      if (data.success) {
        setAnswer(data.answer);
      } else {
        setError(data.error || 'Failed to get answer');
      }
    } catch (err) {
      setError(err.message || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuestion(suggestion);
    setLoading(true);
    setError(null);
    setAnswer(null);

    api.askQuestion(suggestion)
      .then((data) => {
        if (data.success) {
          setAnswer(data.answer);
        } else {
          setError(data.error || 'Failed to get answer');
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to get answer');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const formatAnswer = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let listItems = [];
    let inList = false;

    lines.forEach((line, index) => {
      const trimmedLine = line.trim();

      if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ') || /^\d+\.\s/.test(trimmedLine)) {
        inList = true;
        const content = trimmedLine.replace(/^[-*]\s*/, '').replace(/^\d+\.\s*/, '');
        listItems.push(
          <li key={index} className="text-sm text-foreground ml-4 mb-1">
            {content}
          </li>
        );
      } else {
        if (inList && listItems.length > 0) {
          elements.push(
            <ul key={`list-${index}`} className="list-disc pl-4 mb-3">
              {listItems}
            </ul>
          );
          listItems = [];
          inList = false;
        }

        if (trimmedLine === '') {
          if (elements.length > 0) {
            elements.push(<div key={index} className="h-2" />);
          }
        } else if (trimmedLine.endsWith(':')) {
          elements.push(
            <h4 key={index} className="text-sm font-semibold text-foreground mt-3 mb-1">
              {trimmedLine}
            </h4>
          );
        } else {
          elements.push(
            <p key={index} className="text-sm text-foreground mb-2 leading-relaxed">
              {trimmedLine}
            </p>
          );
        }
      }
    });

    if (listItems.length > 0) {
      elements.push(
        <ul key="list-final" className="list-disc pl-4 mb-3">
          {listItems}
        </ul>
      );
    }

    return elements;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <Card className="overflow-hidden">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <MessageCircle className="h-4 w-4 text-indigo-500" />
            Ask Your AI CFO
            <Badge variant="secondary" className="text-xs ml-2">
              <Sparkles className="h-3 w-3 mr-1" />
              AI Powered
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Input Form */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="flex-1 relative">
              <Input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a financial question..."
                disabled={loading}
                className="pr-4"
              />
            </div>
            <Button
              type="submit"
              disabled={loading || !question.trim()}
              className="gap-2"
            >
              {loading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{loading ? 'Thinking...' : 'Ask'}</span>
            </Button>
          </form>

          {/* Suggested Questions */}
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((suggestion, index) => {
              const Icon = suggestion.icon;
              return (
                <motion.button
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1 * index }}
                  onClick={() => handleSuggestionClick(suggestion.text)}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full
                           bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300
                           hover:bg-indigo-100 dark:hover:bg-indigo-900/30 hover:text-indigo-700 dark:hover:text-indigo-300
                           transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Icon className="h-3 w-3" />
                  {suggestion.text}
                </motion.button>
              );
            })}
          </div>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg"
              >
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Loading State */}
          <AnimatePresence>
            {loading && !answer && (
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
                <span className="text-sm text-muted-foreground">Analyzing your financial data...</span>
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
                className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30
                         border border-indigo-100 dark:border-indigo-900/50 rounded-lg"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-white dark:bg-zinc-900 rounded-lg shadow-sm">
                    <Sparkles className="h-4 w-4 text-indigo-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide mb-2">
                      AI CFO Response
                    </h4>
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {formatAnswer(answer)}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default QuickQuestion;
