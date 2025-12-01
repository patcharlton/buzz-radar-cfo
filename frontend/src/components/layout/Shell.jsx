import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  RefreshCw,
  Moon,
  Sun,
  Wifi,
  WifiOff,
  TrendingUp,
  LogOut
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';

export function Shell({
  children,
  isConnected,
  tenantName,
  lastSynced,
  onSync,
  onConnect,
  onDisconnect,
  syncing
}) {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo and Title */}
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Buzz Radar CFO
                </h1>
                {isConnected && tenantName && (
                  <p className="text-xs text-muted-foreground">{tenantName}</p>
                )}
              </div>
            </div>

            {/* Right side actions */}
            <div className="flex items-center gap-3">
              {/* Last synced */}
              {lastSynced && (
                <span className="hidden sm:inline text-xs text-muted-foreground">
                  Synced {formatDistanceToNow(new Date(lastSynced), { addSuffix: true })}
                </span>
              )}

              {/* Connection status */}
              {isConnected ? (
                <Badge variant="secondary" className="gap-1.5">
                  <Wifi className="h-3 w-3 text-emerald-500" />
                  <span className="hidden sm:inline">Connected</span>
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1.5">
                  <WifiOff className="h-3 w-3 text-zinc-400" />
                  <span className="hidden sm:inline">Disconnected</span>
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
                  <span className="hidden sm:inline">{syncing ? 'Syncing...' : 'Sync'}</span>
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
                  <span className="hidden sm:inline">Disconnect</span>
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
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 max-w-7xl">
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
    </div>
  );
}

export default Shell;
