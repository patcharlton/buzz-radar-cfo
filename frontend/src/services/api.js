const API_BASE = 'http://localhost:5002';

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || 'Request failed');
  }
  return response.json();
}

export const api = {
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
};

export default api;
