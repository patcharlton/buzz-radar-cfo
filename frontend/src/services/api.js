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
};

export default api;
