const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002';

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || 'Request failed');
  }
  return response.json();
}

export const api = {
  // =============================================================================
  // FINANCIAL PROJECTIONS
  // =============================================================================

  /**
   * Get full 3-month financial projection
   */
  async getProjections(months = 3) {
    const response = await fetch(`${API_BASE}/api/projections?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get cost breakdown only
   */
  async getProjectionCosts(months = 3) {
    const response = await fetch(`${API_BASE}/api/projections/costs?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get gap analysis only
   */
  async getProjectionGap(months = 3, target = null) {
    let url = `${API_BASE}/api/projections/gap?months=${months}`;
    if (target) {
      url += `&target=${target}`;
    }
    const response = await fetch(url, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get revenue scenarios only (no auth required)
   */
  async getProjectionScenarios(months = 3) {
    const response = await fetch(`${API_BASE}/api/projections/scenarios?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  // =============================================================================
  // AUTH
  // =============================================================================

  /**
   * Check if connected to Xero
   */
  async getAuthStatus() {
    const response = await fetch(`${API_BASE}/auth/status`, {
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Get the Xero login URL
   */
  getLoginUrl() {
    return `${API_BASE}/auth/login`;
  },

  /**
   * Disconnect from Xero
   */
  async disconnect() {
    const response = await fetch(`${API_BASE}/auth/disconnect`, {
      method: 'POST',
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Get all dashboard data
   */
  async getDashboard() {
    const response = await fetch(`${API_BASE}/api/dashboard`, {
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Get cash position
   */
  async getCashPosition() {
    const response = await fetch(`${API_BASE}/api/cash-position`, {
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Get receivables
   */
  async getReceivables() {
    const response = await fetch(`${API_BASE}/api/receivables`, {
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Get payables
   */
  async getPayables() {
    const response = await fetch(`${API_BASE}/api/payables`, {
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Get profit & loss
   */
  async getProfitLoss() {
    const response = await fetch(`${API_BASE}/api/pnl`, {
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Trigger data sync
   */
  async sync() {
    const response = await fetch(`${API_BASE}/api/sync`, {
      method: 'POST',
      credentials: 'include',
    });
    return handleResponse(response);
  },

  /**
   * Get recurring costs analysis and predictions
   */
  async getRecurringCosts(months = 6) {
    const response = await fetch(`${API_BASE}/api/recurring-costs?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get AI-generated daily insights
   */
  async getDailyInsights() {
    const response = await fetch(`${API_BASE}/api/ai/daily-insights`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get AI-generated monthly analysis
   */
  async getMonthlyAnalysis() {
    const response = await fetch(`${API_BASE}/api/ai/monthly-analysis`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Ask the AI CFO a question
   */
  async askQuestion(question) {
    const response = await fetch(`${API_BASE}/api/ai/ask`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });
    return response.json();
  },

  /**
   * Refresh insights (sync data + regenerate)
   */
  async refreshInsights() {
    const response = await fetch(`${API_BASE}/api/ai/refresh-insights`, {
      method: 'POST',
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get AI-generated cash flow forecast
   */
  async getCashForecast() {
    const response = await fetch(`${API_BASE}/api/ai/forecast`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get AI-detected anomalies
   */
  async getAnomalies() {
    const response = await fetch(`${API_BASE}/api/ai/anomalies`, {
      credentials: 'include',
    });
    return response.json();
  },

  // =============================================================================
  // CONTEXT DATA (Pipeline, Clients, Risks, Metrics)
  // =============================================================================

  /**
   * Get full pipeline data
   */
  async getPipeline() {
    const response = await fetch(`${API_BASE}/api/context/pipeline`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get client portfolio data
   */
  async getClients() {
    const response = await fetch(`${API_BASE}/api/context/clients`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get risk data
   */
  async getRisks() {
    const response = await fetch(`${API_BASE}/api/context/risks`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get business metrics
   */
  async getMetrics() {
    const response = await fetch(`${API_BASE}/api/context/metrics`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get strategic goals
   */
  async getGoals() {
    const response = await fetch(`${API_BASE}/api/context/goals`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get transition status
   */
  async getTransition() {
    const response = await fetch(`${API_BASE}/api/context/transition`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get comprehensive context summary
   */
  async getContextSummary() {
    const response = await fetch(`${API_BASE}/api/context/summary`, {
      credentials: 'include',
    });
    return response.json();
  },

  // =============================================================================
  // NOTION INTEGRATION
  // =============================================================================

  /**
   * Get Notion connection status
   */
  async getNotionStatus() {
    const response = await fetch(`${API_BASE}/api/notion/status`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get pipeline data from Notion (uses cache)
   */
  async getNotionPipeline() {
    const response = await fetch(`${API_BASE}/api/notion/pipeline`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Force sync pipeline from Notion (bypasses cache)
   */
  async syncNotionPipeline() {
    const response = await fetch(`${API_BASE}/api/notion/pipeline/sync`, {
      method: 'POST',
      credentials: 'include',
    });
    return response.json();
  },

  // =============================================================================
  // HISTORY & METRICS
  // =============================================================================

  /**
   * Get historical monthly snapshots
   */
  async getHistorySnapshots(months = 60) {
    const response = await fetch(`${API_BASE}/api/history/snapshots?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get cash position history
   */
  async getCashHistory(months = 12) {
    const response = await fetch(`${API_BASE}/api/history/cash?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get revenue history with MoM% and YoY%
   */
  async getRevenueHistory(months = 12) {
    const response = await fetch(`${API_BASE}/api/history/revenue?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get cash runway metrics
   */
  async getRunway() {
    const response = await fetch(`${API_BASE}/api/metrics/runway`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get combined trends for dashboard sparklines
   */
  async getHistoryTrends(months = 12) {
    const response = await fetch(`${API_BASE}/api/history/trends?months=${months}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Trigger historical data backfill
   */
  async triggerBackfill(months = 60, dryRun = false) {
    const response = await fetch(`${API_BASE}/api/history/backfill`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ months, dry_run: dryRun }),
    });
    return response.json();
  },

  /**
   * Manually trigger snapshot capture
   */
  async triggerSnapshot(dryRun = false) {
    const response = await fetch(`${API_BASE}/api/history/snapshot`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ dry_run: dryRun }),
    });
    return response.json();
  },

  // =============================================================================
  // DRILL-DOWN ENDPOINTS
  // =============================================================================

  /**
   * Get bank transactions for cash drill-down
   */
  async drillCash({ fromDate, toDate, accountId, page = 1, pageSize = 50 } = {}) {
    const params = new URLSearchParams();
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    if (accountId) params.set('account_id', accountId);
    params.set('page', page);
    params.set('page_size', pageSize);

    const response = await fetch(`${API_BASE}/api/drill/cash?${params}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get bank accounts list for filtering
   */
  async drillCashAccounts() {
    const response = await fetch(`${API_BASE}/api/drill/cash/accounts`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get receivables (invoices) for drill-down
   */
  async drillReceivables({ fromDate, toDate, status, overdueOnly, page = 1, pageSize = 50 } = {}) {
    const params = new URLSearchParams();
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    if (status) params.set('status', status);
    if (overdueOnly) params.set('overdue_only', 'true');
    params.set('page', page);
    params.set('page_size', pageSize);

    const response = await fetch(`${API_BASE}/api/drill/receivables?${params}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get single invoice details with line items
   */
  async drillReceivablesDetail(invoiceId) {
    const response = await fetch(`${API_BASE}/api/drill/receivables/${invoiceId}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get payables (bills) for drill-down
   */
  async drillPayables({ fromDate, toDate, status, overdueOnly, page = 1, pageSize = 50 } = {}) {
    const params = new URLSearchParams();
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    if (status) params.set('status', status);
    if (overdueOnly) params.set('overdue_only', 'true');
    params.set('page', page);
    params.set('page_size', pageSize);

    const response = await fetch(`${API_BASE}/api/drill/payables?${params}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get single bill details with line items
   */
  async drillPayablesDetail(invoiceId) {
    const response = await fetch(`${API_BASE}/api/drill/payables/${invoiceId}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get P&L categories for drill-down
   */
  async drillPnl({ fromDate, toDate } = {}) {
    const params = new URLSearchParams();
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);

    const response = await fetch(`${API_BASE}/api/drill/pnl?${params}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get journal entries for a specific P&L account
   */
  async drillPnlAccount(accountId, { fromDate, toDate, page = 1 } = {}) {
    const params = new URLSearchParams();
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    params.set('page', page);

    const response = await fetch(`${API_BASE}/api/drill/pnl/account/${accountId}?${params}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Search across transactions
   */
  async drillSearch({ query, type = 'all', fromDate, toDate, page = 1, pageSize = 50 } = {}) {
    const params = new URLSearchParams();
    params.set('q', query);
    params.set('type', type);
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    params.set('page', page);
    params.set('page_size', pageSize);

    const response = await fetch(`${API_BASE}/api/drill/search?${params}`, {
      credentials: 'include',
    });
    return response.json();
  },

  /**
   * Get all account codes
   */
  async drillAccounts(refresh = false) {
    const params = new URLSearchParams();
    if (refresh) params.set('refresh', 'true');

    const response = await fetch(`${API_BASE}/api/drill/accounts?${params}`, {
      credentials: 'include',
    });
    return response.json();
  },
};

// Xero deep link helpers
export const xeroLinks = {
  invoice: (id) => `https://go.xero.com/AccountsReceivable/View.aspx?invoiceID=${id}`,
  bill: (id) => `https://go.xero.com/AccountsPayable/View.aspx?invoiceID=${id}`,
  bankTransaction: (id) => `https://go.xero.com/Bank/ViewTransaction.aspx?bankTransactionID=${id}`,
  contact: (id) => `https://go.xero.com/Contacts/View/${id}`,
  account: (code) => `https://go.xero.com/ChartOfAccounts/View.aspx?accountCode=${code}`,
};

export default api;
