import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { FileText, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';
import { formatDistanceToNow, parseISO, differenceInDays } from 'date-fns';

function SortableHeader({ label, sortKey, currentSort, onSort }) {
  const isActive = currentSort.key === sortKey;

  return (
    <button
      onClick={() => onSort(sortKey)}
      className="flex items-center gap-1 hover:text-foreground transition-colors"
    >
      {label}
      {isActive ? (
        currentSort.direction === 'asc' ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )
      ) : (
        <ChevronsUpDown className="h-3 w-3 opacity-50" />
      )}
    </button>
  );
}

export function InvoiceTable({ invoices = [], loading, title = "Outstanding Invoices" }) {
  const [sort, setSort] = useState({ key: 'due_date', direction: 'asc' });

  const handleSort = (key) => {
    setSort((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const sortedInvoices = useMemo(() => {
    if (!invoices || invoices.length === 0) return [];

    return [...invoices].sort((a, b) => {
      let aVal, bVal;

      switch (sort.key) {
        case 'contact_name':
          aVal = a.contact_name || '';
          bVal = b.contact_name || '';
          break;
        case 'amount_due':
          aVal = a.amount_due || 0;
          bVal = b.amount_due || 0;
          break;
        case 'due_date':
          aVal = a.due_date ? new Date(a.due_date) : new Date();
          bVal = b.due_date ? new Date(b.due_date) : new Date();
          break;
        case 'days_overdue':
          aVal = a.days_overdue || 0;
          bVal = b.days_overdue || 0;
          break;
        default:
          aVal = a[sort.key];
          bVal = b[sort.key];
      }

      if (typeof aVal === 'string') {
        return sort.direction === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return sort.direction === 'asc' ? aVal - bVal : bVal - aVal;
    });
  }, [invoices, sort]);

  const getStatusBadge = (invoice) => {
    const daysOverdue = invoice.days_overdue || 0;

    if (daysOverdue > 30) {
      return <Badge variant="destructive">30+ days overdue</Badge>;
    }
    if (daysOverdue > 0) {
      return <Badge variant="warning">{daysOverdue}d overdue</Badge>;
    }

    const dueDate = invoice.due_date ? parseISO(invoice.due_date) : null;
    const daysUntilDue = dueDate ? differenceInDays(dueDate, new Date()) : 0;

    if (daysUntilDue <= 7 && daysUntilDue >= 0) {
      return <Badge variant="secondary">Due soon</Badge>;
    }

    return <Badge variant="outline">Current</Badge>;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!invoices || invoices.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No outstanding invoices
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
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {title}
            </CardTitle>
            <Badge variant="secondary">
              {invoices.length} invoice{invoices.length !== 1 ? 's' : ''}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="px-0 sm:px-6">
          {/* Mobile Card View */}
          <div className="sm:hidden space-y-2 px-3">
            {sortedInvoices.map((invoice, index) => (
              <motion.div
                key={invoice.invoice_number || index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/30"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-sm truncate">{invoice.contact_name}</p>
                    <p className="text-xs text-muted-foreground">{invoice.invoice_number}</p>
                  </div>
                  {getStatusBadge(invoice)}
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-mono tabular-nums font-semibold">
                    {formatCurrency(invoice.amount_due)}
                  </span>
                  <span className="text-muted-foreground text-xs">
                    {invoice.due_date
                      ? formatDistanceToNow(parseISO(invoice.due_date), { addSuffix: true })
                      : '-'}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Desktop Table View */}
          <div className="hidden sm:block overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <SortableHeader
                      label="Client"
                      sortKey="contact_name"
                      currentSort={sort}
                      onSort={handleSort}
                    />
                  </TableHead>
                  <TableHead className="text-right">
                    <SortableHeader
                      label="Amount"
                      sortKey="amount_due"
                      currentSort={sort}
                      onSort={handleSort}
                    />
                  </TableHead>
                  <TableHead>
                    <SortableHeader
                      label="Due Date"
                      sortKey="due_date"
                      currentSort={sort}
                      onSort={handleSort}
                    />
                  </TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedInvoices.map((invoice, index) => (
                  <motion.tr
                    key={invoice.invoice_number || index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="group border-b transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                  >
                    <TableCell>
                      <div>
                        <p className="font-medium">{invoice.contact_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {invoice.invoice_number}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono tabular-nums font-medium">
                        {formatCurrency(invoice.amount_due)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="text-sm">
                          {invoice.due_date
                            ? new Date(invoice.due_date).toLocaleDateString('en-GB', {
                                day: 'numeric',
                                month: 'short',
                              })
                            : '-'}
                        </p>
                        {invoice.due_date && (
                          <p className="text-xs text-muted-foreground">
                            {formatDistanceToNow(parseISO(invoice.due_date), {
                              addSuffix: true,
                            })}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(invoice)}</TableCell>
                  </motion.tr>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default InvoiceTable;
