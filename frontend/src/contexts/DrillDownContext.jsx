import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

const DrillDownContext = createContext(null);

/**
 * Drill-down types supported by the drawer
 */
export const DRILL_TYPES = {
  CASH: 'cash',
  RECEIVABLES: 'receivables',
  RECEIVABLES_DETAIL: 'receivables_detail',
  PAYABLES: 'payables',
  PAYABLES_DETAIL: 'payables_detail',
  PNL: 'pnl',
  PNL_ACCOUNT: 'pnl_account',
};

/**
 * Provider for drill-down state management.
 * Handles opening/closing the drawer, preserving filters, and URL sync.
 */
export function DrillDownProvider({ children }) {
  const [isOpen, setIsOpen] = useState(false);
  const [drillType, setDrillType] = useState(null);
  const [title, setTitle] = useState('');
  const [filters, setFilters] = useState({});
  const [breadcrumb, setBreadcrumb] = useState([]); // For nested drill-downs

  // Sync with URL params on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const drill = params.get('drill');

    if (drill && Object.values(DRILL_TYPES).includes(drill)) {
      const urlFilters = {};
      if (params.get('from')) urlFilters.fromDate = params.get('from');
      if (params.get('to')) urlFilters.toDate = params.get('to');
      if (params.get('account_id')) urlFilters.accountId = params.get('account_id');
      if (params.get('invoice_id')) urlFilters.invoiceId = params.get('invoice_id');
      if (params.get('overdue')) urlFilters.overdueOnly = params.get('overdue') === 'true';

      setDrillType(drill);
      setFilters(urlFilters);
      setIsOpen(true);
    }
  }, []);

  // Update URL when drill state changes
  const updateUrl = useCallback((type, newFilters) => {
    const url = new URL(window.location.href);

    if (type) {
      url.searchParams.set('drill', type);
      if (newFilters.fromDate) url.searchParams.set('from', newFilters.fromDate);
      if (newFilters.toDate) url.searchParams.set('to', newFilters.toDate);
      if (newFilters.accountId) url.searchParams.set('account_id', newFilters.accountId);
      if (newFilters.invoiceId) url.searchParams.set('invoice_id', newFilters.invoiceId);
      if (newFilters.overdueOnly) url.searchParams.set('overdue', 'true');
    } else {
      url.searchParams.delete('drill');
      url.searchParams.delete('from');
      url.searchParams.delete('to');
      url.searchParams.delete('account_id');
      url.searchParams.delete('invoice_id');
      url.searchParams.delete('overdue');
    }

    window.history.replaceState({}, '', url.toString());
  }, []);

  /**
   * Open the drill-down drawer
   */
  const openDrill = useCallback((type, options = {}) => {
    const { title: newTitle, filters: newFilters = {}, addToBreadcrumb = false } = options;

    if (addToBreadcrumb && drillType) {
      setBreadcrumb(prev => [...prev, { type: drillType, title, filters }]);
    } else if (!addToBreadcrumb) {
      setBreadcrumb([]);
    }

    setDrillType(type);
    setTitle(newTitle || getTitleForType(type));
    setFilters(newFilters);
    setIsOpen(true);
    updateUrl(type, newFilters);
  }, [drillType, title, filters, updateUrl]);

  /**
   * Close the drill-down drawer
   */
  const closeDrill = useCallback(() => {
    setIsOpen(false);
    setDrillType(null);
    setFilters({});
    setBreadcrumb([]);
    updateUrl(null, {});
  }, [updateUrl]);

  /**
   * Go back in breadcrumb
   */
  const goBack = useCallback(() => {
    if (breadcrumb.length > 0) {
      const prev = breadcrumb[breadcrumb.length - 1];
      setBreadcrumb(breadcrumb.slice(0, -1));
      setDrillType(prev.type);
      setTitle(prev.title);
      setFilters(prev.filters);
      updateUrl(prev.type, prev.filters);
    } else {
      closeDrill();
    }
  }, [breadcrumb, closeDrill, updateUrl]);

  /**
   * Update filters without closing
   */
  const updateFilters = useCallback((newFilters) => {
    const merged = { ...filters, ...newFilters };
    setFilters(merged);
    updateUrl(drillType, merged);
  }, [filters, drillType, updateUrl]);

  const value = {
    isOpen,
    drillType,
    title,
    filters,
    breadcrumb,
    openDrill,
    closeDrill,
    goBack,
    updateFilters,
  };

  return (
    <DrillDownContext.Provider value={value}>
      {children}
    </DrillDownContext.Provider>
  );
}

/**
 * Hook to access drill-down context
 */
export function useDrillDown() {
  const context = useContext(DrillDownContext);
  if (!context) {
    throw new Error('useDrillDown must be used within a DrillDownProvider');
  }
  return context;
}

/**
 * Get default title for drill type
 */
function getTitleForType(type) {
  switch (type) {
    case DRILL_TYPES.CASH:
      return 'Bank Transactions';
    case DRILL_TYPES.RECEIVABLES:
      return 'Outstanding Invoices';
    case DRILL_TYPES.RECEIVABLES_DETAIL:
      return 'Invoice Details';
    case DRILL_TYPES.PAYABLES:
      return 'Outstanding Bills';
    case DRILL_TYPES.PAYABLES_DETAIL:
      return 'Bill Details';
    case DRILL_TYPES.PNL:
      return 'P&L Categories';
    case DRILL_TYPES.PNL_ACCOUNT:
      return 'Account Transactions';
    default:
      return 'Transactions';
  }
}

export default DrillDownContext;
