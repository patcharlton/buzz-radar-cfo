import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RefreshCw,
  Moon,
  Sun,
  Wifi,
  WifiOff,
  TrendingUp,
  LogOut,
  Menu,
  X,
  History,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';
import api from '@/services/api';

export function Shell({
  children,
  isConnected,
  tenantName,
  lastSynced,
  onSync,
  onConnect,
  onDisconnect,
  onLogout,
  syncing
}) {
  const [darkMode, setDarkMode] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backfilling, setBackfilling] = useState(false);
  const [backfillProgress, setBackfillProgress] = useState(0);
  const [backfillElapsed, setBackfillElapsed] = useState(0);
  const progressIntervalRef = useRef(null);

  const TOTAL_MONTHS = 60;
  const SECONDS_PER_MONTH = 1.1;
  const ESTIMATED_TOTAL_SECONDS = TOTAL_MONTHS * SECONDS_PER_MONTH;

  const handleBackfill = async () => {
    setBackfilling(true);
    setBackfillProgress(0);
    setBackfillElapsed(0);

    // Start progress simulation
    const startTime = Date.now();
    progressIntervalRef.current = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      setBackfillElapsed(Math.floor(elapsed));
      // Progress based on elapsed time, max 95% until complete
      const estimatedProgress = Math.min((elapsed / ESTIMATED_TOTAL_SECONDS) * 100, 95);
      setBackfillProgress(estimatedProgress);
    }, 500);

    try {
      const result = await api.triggerBackfill(TOTAL_MONTHS);
      clearInterval(progressIntervalRef.current);

      if (result.success) {
        setBackfillProgress(100);
        toast.success(`Loaded ${result.result?.success || 0} months of history`);
        // Short delay to show 100% before reload
        setTimeout(() => {
          window.location.reload();
        }, 500);
      } else {
        toast.error(result.error || 'Failed to load history');
        setBackfilling(false);
      }
    } catch (err) {
      clearInterval(progressIntervalRef.current);
      toast.error('Failed to load history: ' + (err.message || 'Unknown error'));
      setBackfilling(false);
    }
  };

  // Warn user before navigating away during backfill
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (backfilling) {
        e.preventDefault();
        e.returnValue = 'History loading is in progress. Are you sure you want to leave?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, [backfilling]);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Close mobile menu when clicking outside
  useEffect(() => {
    if (mobileMenuOpen) {
      const handleClick = () => setMobileMenuOpen(false);
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [mobileMenuOpen]);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-zinc-200 dark:border-zinc-800 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-sm">
        <div className="container mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex h-14 sm:h-16 items-center justify-between">
            {/* Logo and Title */}
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
                <TrendingUp className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
              </div>
              <div>
                <h1 className="text-base sm:text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Buzz Radar CFO
                </h1>
                {isConnected && tenantName && (
                  <p className="text-xs text-muted-foreground hidden sm:block">{tenantName}</p>
                )}
              </div>
            </div>

            {/* Desktop actions */}
            <div className="hidden md:flex items-center gap-3">
              {/* Last synced */}
              {lastSynced && (
                <span className="text-xs text-muted-foreground">
                  Synced {formatDistanceToNow(new Date(lastSynced), { addSuffix: true })}
                </span>
              )}

              {/* Connection status */}
              {isConnected ? (
                <Badge variant="secondary" className="gap-1.5">
                  <Wifi className="h-3 w-3 text-emerald-500" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1.5">
                  <WifiOff className="h-3 w-3 text-zinc-400" />
                  Disconnected
                </Badge>
              )}

              {/* Sync button */}
              {isConnected && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onSync}
                  disabled={syncing}
                  className="gap-2"
                >
                  <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                  {syncing ? 'Syncing...' : 'Sync'}
                </Button>
              )}

              {/* Load History button */}
              {isConnected && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBackfill}
                  disabled={backfilling}
                  className="gap-2"
                >
                  {backfilling ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <History className="h-4 w-4" />
                  )}
                  {backfilling ? 'Loading...' : 'Load History'}
                </Button>
              )}

              {/* Disconnect button */}
              {isConnected && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onDisconnect}
                  className="gap-2 text-muted-foreground"
                >
                  <LogOut className="h-4 w-4" />
                  Disconnect
                </Button>
              )}

              {/* Dark mode toggle */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setDarkMode(!darkMode)}
                className="h-9 w-9"
              >
                {darkMode ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </Button>

              {/* Logout button */}
              {onLogout && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onLogout}
                  className="gap-2 text-muted-foreground hover:text-red-600"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              )}
            </div>

            {/* Mobile actions */}
            <div className="flex md:hidden items-center gap-2">
              {/* Connection indicator */}
              {isConnected ? (
                <Wifi className="h-4 w-4 text-emerald-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-zinc-400" />
              )}

              {/* Sync button - always visible on mobile */}
              {isConnected && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onSync}
                  disabled={syncing}
                  className="h-8 w-8"
                >
                  <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                </Button>
              )}

              {/* Dark mode toggle */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setDarkMode(!darkMode)}
                className="h-8 w-8"
              >
                {darkMode ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </Button>

              {/* Mobile menu button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation();
                  setMobileMenuOpen(!mobileMenuOpen);
                }}
                className="h-8 w-8"
              >
                {mobileMenuOpen ? (
                  <X className="h-4 w-4" />
                ) : (
                  <Menu className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile dropdown menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="container mx-auto px-3 py-3 space-y-2">
                {/* Last synced */}
                {lastSynced && (
                  <p className="text-xs text-muted-foreground px-2">
                    Last synced {formatDistanceToNow(new Date(lastSynced), { addSuffix: true })}
                  </p>
                )}

                {/* Tenant name */}
                {isConnected && tenantName && (
                  <p className="text-sm text-foreground px-2 font-medium">
                    {tenantName}
                  </p>
                )}

                <div className="border-t border-zinc-100 dark:border-zinc-800 pt-2 space-y-1">
                  {/* Load History */}
                  {isConnected && (
                    <button
                      onClick={() => {
                        handleBackfill();
                        setMobileMenuOpen(false);
                      }}
                      disabled={backfilling}
                      className="w-full flex items-center gap-2 px-2 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md disabled:opacity-50"
                    >
                      {backfilling ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <History className="h-4 w-4" />
                      )}
                      {backfilling ? 'Loading History...' : 'Load History'}
                    </button>
                  )}

                  {/* Disconnect */}
                  {isConnected && (
                    <button
                      onClick={() => {
                        onDisconnect();
                        setMobileMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-2 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md"
                    >
                      <LogOut className="h-4 w-4" />
                      Disconnect Xero
                    </button>
                  )}

                  {/* Logout */}
                  {onLogout && (
                    <button
                      onClick={() => {
                        onLogout();
                        setMobileMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-2 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-md"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-6 max-w-7xl">
        {!isConnected ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center min-h-[60vh] text-center"
          >
            <div className="mb-8">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-6">
                <TrendingUp className="h-10 w-10 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
                Connect to Xero
              </h2>
              <p className="text-muted-foreground max-w-md mx-auto">
                Connect your Xero account to view real-time financial data,
                AI-powered insights, and cash flow forecasts for Buzz Radar.
              </p>
            </div>
            <Button
              size="lg"
              onClick={onConnect}
              className="gap-2"
            >
              <Wifi className="h-4 w-4" />
              Connect to Xero
            </Button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        )}
      </main>

      {/* Backfill Progress Overlay */}
      <AnimatePresence>
        {backfilling && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-zinc-900 rounded-xl shadow-2xl p-6 mx-4 max-w-md w-full"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
                  <History className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                    Loading Historical Data
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Fetching {TOTAL_MONTHS} months from Xero
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <Progress value={backfillProgress} className="h-2" />

                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    {Math.round(backfillProgress)}% complete
                  </span>
                  <span className="text-muted-foreground font-mono">
                    {backfillElapsed}s / ~{Math.round(ESTIMATED_TOTAL_SECONDS)}s
                  </span>
                </div>
              </div>

              <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-900">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800 dark:text-amber-200">
                    Please don't close or navigate away from this page until loading is complete.
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default Shell;
