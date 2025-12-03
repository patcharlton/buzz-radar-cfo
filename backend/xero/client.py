from datetime import datetime, date, timedelta
import requests
import re
from functools import lru_cache

from .auth import XeroAuth

# Module-level cache for account codes (refreshed daily)
_account_codes_cache = None
_account_codes_cache_time = None


class XeroClient:
    """Wrapper for Xero API operations using direct REST calls."""

    BASE_URL = 'https://api.xero.com/api.xro/2.0'
    FINANCE_URL = 'https://api.xero.com/finance.xro/1.0'

    def __init__(self):
        self.auth = XeroAuth()

    def _get_headers(self):
        """Get headers with valid access token."""
        access_token = self.auth.get_valid_token()
        if not access_token:
            raise Exception("Not connected to Xero")

        tenant_id = self.auth.get_tenant_id()
        if not tenant_id:
            raise Exception("No Xero tenant selected")

        return {
            'Authorization': f'Bearer {access_token}',
            'Xero-Tenant-Id': tenant_id,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _get(self, endpoint, params=None):
        """Make a GET request to Xero API."""
        headers = self._get_headers()
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Xero API error: {response.status_code} - {response.text}")

        return response.json()

    def _get_finance(self, endpoint, params=None):
        """Make a GET request to Xero Finance API."""
        headers = self._get_headers()
        url = f"{self.FINANCE_URL}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Xero Finance API error: {response.status_code} - {response.text}")

        return response.json()

    def get_bank_accounts(self):
        """Get all bank accounts with balances."""
        data = self._get('Accounts', params={'where': 'Type=="BANK"'})

        accounts = []
        for account in data.get('Accounts', []):
            accounts.append({
                'account_id': account.get('AccountID'),
                'name': account.get('Name'),
                'code': account.get('Code'),
                'type': account.get('Type'),
                'bank_account_number': account.get('BankAccountNumber'),
                'currency_code': account.get('CurrencyCode', 'GBP'),
            })

        return accounts

    def get_bank_summary(self):
        """Get bank summary report with current balances."""
        today = date.today()
        params = {
            'fromDate': date(today.year, 1, 1).isoformat(),
            'toDate': today.isoformat(),
        }

        data = self._get('Reports/BankSummary', params=params)

        total_balance = 0
        bank_accounts = []

        reports = data.get('Reports', [])
        if reports:
            report = reports[0]
            rows = report.get('Rows', [])

            for section in rows:
                if section.get('RowType') == 'Section':
                    for row in section.get('Rows', []):
                        if row.get('RowType') == 'Row':
                            cells = row.get('Cells', [])
                            if len(cells) >= 2:
                                account_name = cells[0].get('Value', '')
                                balance_str = cells[-1].get('Value', '0')
                                try:
                                    balance = float(balance_str) if balance_str else 0
                                except ValueError:
                                    balance = 0

                                if account_name and account_name != 'Total':
                                    bank_accounts.append({
                                        'name': account_name,
                                        'balance': balance,
                                    })
                                    total_balance += balance

        return {
            'total_balance': total_balance,
            'accounts': bank_accounts,
            'as_of_date': today.isoformat(),
        }

    def get_invoices(self, invoice_type='ACCREC', status='AUTHORISED'):
        """Get invoices filtered by type and status."""
        params = {
            'where': f'Type=="{invoice_type}" AND Status=="{status}"',
        }

        data = self._get('Invoices', params=params)

        invoices = []
        for inv in data.get('Invoices', []):
            due_date_str = inv.get('DueDateString')
            issue_date_str = inv.get('DateString')

            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            issue_date = None
            if issue_date_str:
                try:
                    issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            contact = inv.get('Contact', {})

            invoices.append({
                'invoice_id': inv.get('InvoiceID'),
                'invoice_number': inv.get('InvoiceNumber'),
                'contact_name': contact.get('Name', 'Unknown'),
                'invoice_type': inv.get('Type'),
                'status': inv.get('Status'),
                'amount_due': float(inv.get('AmountDue', 0)),
                'total': float(inv.get('Total', 0)),
                'due_date': due_date.isoformat() if due_date else None,
                'issue_date': issue_date.isoformat() if issue_date else None,
                'is_overdue': due_date < date.today() if due_date else False,
                'days_until_due': (due_date - date.today()).days if due_date else None,
            })

        return sorted(invoices, key=lambda x: x['due_date'] or '9999-12-31')

    def get_receivables(self):
        """Get all outstanding receivables (invoices owed to us)."""
        return self.get_invoices(invoice_type='ACCREC', status='AUTHORISED')

    def get_payables(self):
        """Get all outstanding payables (bills we owe)."""
        return self.get_invoices(invoice_type='ACCPAY', status='AUTHORISED')

    def get_receivables_summary(self):
        """Get summary of receivables with totals."""
        invoices = self.get_receivables()

        total = sum(inv['amount_due'] for inv in invoices)
        overdue = sum(inv['amount_due'] for inv in invoices if inv['is_overdue'])
        count = len(invoices)
        overdue_count = len([inv for inv in invoices if inv['is_overdue']])

        return {
            'total': total,
            'overdue': overdue,
            'count': count,
            'overdue_count': overdue_count,
            'invoices': invoices,
        }

    def get_payables_summary(self):
        """Get summary of payables with totals."""
        invoices = self.get_payables()

        total = sum(inv['amount_due'] for inv in invoices)
        overdue = sum(inv['amount_due'] for inv in invoices if inv['is_overdue'])
        count = len(invoices)
        overdue_count = len([inv for inv in invoices if inv['is_overdue']])

        return {
            'total': total,
            'overdue': overdue,
            'count': count,
            'overdue_count': overdue_count,
            'invoices': invoices,
        }

    def get_profit_and_loss(self, from_date=None, to_date=None):
        """Get Profit & Loss report."""
        today = date.today()

        if from_date is None:
            from_date = date(today.year, today.month, 1)
        if to_date is None:
            to_date = today

        params = {
            'fromDate': from_date.isoformat(),
            'toDate': to_date.isoformat(),
        }

        data = self._get('Reports/ProfitAndLoss', params=params)

        revenue = 0
        expenses = 0
        net_profit = 0
        gross_profit = 0

        # Income section titles
        income_titles = ['Income', 'Revenue', 'Sales', 'Trading Income', 'Other Income']
        # Expense section titles (Xero uses various names)
        expense_titles = [
            'Expense', 'Expenses', 'Operating Expenses', 'Overheads',
            'Direct Costs', 'Cost of Sales', 'Cost of Goods Sold',
            'Administrative Expenses', 'Other Expenses', 'Less Cost of Sales',
            'Less Operating Expenses'
        ]

        reports = data.get('Reports', [])
        if reports:
            report = reports[0]
            rows = report.get('Rows', [])

            for section in rows:
                row_type = section.get('RowType')
                title = section.get('Title', '').strip()

                if row_type == 'Section':
                    for row in section.get('Rows', []):
                        if row.get('RowType') == 'SummaryRow':
                            cells = row.get('Cells', [])
                            if cells:
                                value_str = cells[-1].get('Value', '0')
                                try:
                                    value = float(value_str) if value_str else 0
                                except ValueError:
                                    value = 0

                                # Check if this is an income section
                                is_income = any(inc.lower() in title.lower() for inc in income_titles)
                                # Check if this is an expense section
                                is_expense = any(exp.lower() in title.lower() for exp in expense_titles)

                                if is_income and not is_expense:
                                    revenue += value
                                elif is_expense:
                                    # Expenses are sometimes negative in Xero, take absolute value
                                    expenses += abs(value)

                elif row_type == 'Row':
                    cells = section.get('Cells', [])
                    if cells:
                        label = str(cells[0].get('Value', '')).strip()
                        value_str = cells[-1].get('Value', '0')
                        try:
                            value = float(value_str) if value_str else 0
                        except ValueError:
                            value = 0

                        if 'Net Profit' in label or 'Net Loss' in label:
                            net_profit = value
                        elif 'Gross Profit' in label:
                            gross_profit = value

        # If we got gross profit but no expenses calculated, derive expenses
        # Gross Profit = Revenue - Cost of Sales
        # So if we have revenue and gross profit, Cost of Sales = Revenue - Gross Profit
        if gross_profit > 0 and expenses == 0 and revenue > 0:
            # This means we missed parsing expenses - use net profit to derive
            if net_profit != 0:
                expenses = revenue - net_profit

        # Fallback: calculate net profit from revenue - expenses
        if net_profit == 0 and (revenue > 0 or expenses > 0):
            net_profit = revenue - expenses

        return {
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': net_profit,
            'gross_profit': gross_profit,
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
            'period': f"{from_date.strftime('%B %Y')}",
        }

    def get_monthly_expenses(self, num_months=3):
        """
        Get expenses for the last N months to calculate average burn rate.

        Args:
            num_months: Number of months to fetch (default: 3)

        Returns:
            dict: Monthly expenses and calculated average
        """
        today = date.today()
        monthly_data = []

        for i in range(num_months):
            # Calculate month boundaries (going backwards)
            if i == 0:
                # Current month (partial)
                month_start = date(today.year, today.month, 1)
                month_end = today
            else:
                # Previous complete months
                year = today.year
                month = today.month - i
                while month <= 0:
                    month += 12
                    year -= 1

                month_start = date(year, month, 1)
                # Last day of the month
                if month == 12:
                    month_end = date(year + 1, 1, 1)
                else:
                    month_end = date(year, month + 1, 1)
                from datetime import timedelta
                month_end = month_end - timedelta(days=1)

            pnl = self.get_profit_and_loss(from_date=month_start, to_date=month_end)
            monthly_data.append({
                'month': month_start.strftime('%B %Y'),
                'expenses': pnl.get('expenses', 0),
                'revenue': pnl.get('revenue', 0),
                'net_profit': pnl.get('net_profit', 0),
                'is_partial': i == 0,  # Current month is partial
            })

        # Calculate average from complete months only (exclude current partial month)
        complete_months = [m for m in monthly_data if not m['is_partial']]
        if complete_months:
            avg_expenses = sum(m['expenses'] for m in complete_months) / len(complete_months)
        else:
            # Fall back to current month if no complete months
            avg_expenses = monthly_data[0]['expenses'] if monthly_data else 0

        return {
            'months': monthly_data,
            'average_monthly_expenses': avg_expenses,
            'num_complete_months': len(complete_months),
        }

    def get_dashboard_data(self):
        """Get all data needed for the dashboard in a single call."""
        bank_summary = self.get_bank_summary()
        receivables = self.get_receivables_summary()
        payables = self.get_payables_summary()
        pnl = self.get_profit_and_loss()

        return {
            'cash_position': bank_summary,
            'receivables': receivables,
            'payables': payables,
            'profit_loss': pnl,
            'last_synced': datetime.utcnow().isoformat(),
        }

    def get_forecast_data(self):
        """Get all data needed for cash flow forecasting, including historical burn rate."""
        bank_summary = self.get_bank_summary()
        receivables = self.get_receivables_summary()
        payables = self.get_payables_summary()
        pnl = self.get_profit_and_loss()
        monthly_expenses = self.get_monthly_expenses(num_months=3)

        return {
            'cash_position': bank_summary,
            'receivables': receivables,
            'payables': payables,
            'profit_loss': pnl,
            'monthly_expenses': monthly_expenses,
            'last_synced': datetime.utcnow().isoformat(),
        }

    def get_paid_bills(self, months=6):
        """
        Get paid bills from the last N months for recurring cost analysis.

        Args:
            months: Number of months to look back (default: 6)

        Returns:
            list: Paid bills with vendor, amount, date, and line items
        """
        from datetime import timedelta
        import re

        today = date.today()
        start_date = today - timedelta(days=months * 30)

        # Fetch paid bills (ACCPAY with PAID status)
        params = {
            'where': f'Type=="ACCPAY" AND Status=="PAID" AND Date>=DateTime({start_date.year},{start_date.month},{start_date.day})',
        }

        data = self._get('Invoices', params=params)

        def parse_xero_date(date_value):
            """Parse Xero date which can be in multiple formats."""
            if not date_value:
                return None

            # Handle Microsoft JSON date format: /Date(1751241600000+0000)/
            if isinstance(date_value, str) and date_value.startswith('/Date('):
                match = re.search(r'/Date\((\d+)', date_value)
                if match:
                    timestamp_ms = int(match.group(1))
                    return datetime.utcfromtimestamp(timestamp_ms / 1000).date()

            # Handle ISO format with time: 2025-06-23T00:00:00
            if isinstance(date_value, str):
                try:
                    if 'T' in date_value:
                        return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
                    else:
                        return datetime.strptime(date_value[:10], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass

            return None

        bills = []
        for inv in data.get('Invoices', []):
            # Try FullyPaidOnDate first, then fall back to DateString
            paid_date = parse_xero_date(inv.get('FullyPaidOnDate'))
            if not paid_date:
                paid_date = parse_xero_date(inv.get('DateString'))

            contact = inv.get('Contact', {})

            bills.append({
                'invoice_id': inv.get('InvoiceID'),
                'invoice_number': inv.get('InvoiceNumber'),
                'vendor': contact.get('Name', 'Unknown'),
                'contact_id': contact.get('ContactID'),
                'total': float(inv.get('Total', 0)),
                'paid_date': paid_date.isoformat() if paid_date else None,
                'month_key': paid_date.strftime('%Y-%m') if paid_date else None,
                'reference': inv.get('Reference', ''),
            })

        return bills

    def get_recurring_costs_analysis(self, months=6):
        """
        Analyze paid bills and P&L to identify recurring costs and predict future expenses.

        Uses P&L data for accurate total expense predictions, combined with paid bills
        for vendor-level breakdown of trackable supplier costs.

        Args:
            months: Number of months to analyze (default: 6)

        Returns:
            dict: Recurring costs breakdown with predictions
        """
        from collections import defaultdict
        from datetime import timedelta

        bills = self.get_paid_bills(months=months)
        today = date.today()

        # Get actual P&L expenses for accurate monthly totals
        monthly_expenses = self.get_monthly_expenses(num_months=months)
        avg_monthly_from_pnl = monthly_expenses.get('average_monthly_expenses', 0)

        # Group bills by vendor
        vendor_bills = defaultdict(list)
        for bill in bills:
            vendor_bills[bill['vendor']].append(bill)

        recurring_costs = []
        total_vendor_monthly_avg = 0

        for vendor, vendor_bill_list in vendor_bills.items():
            # Calculate stats for this vendor
            amounts = [b['total'] for b in vendor_bill_list]
            months_with_bills = len(set(b['month_key'] for b in vendor_bill_list if b['month_key']))

            avg_amount = sum(amounts) / len(amounts) if amounts else 0
            total_spent = sum(amounts)
            frequency = months_with_bills / months if months > 0 else 0

            # Determine if this is a recurring cost (appears in 50%+ of months)
            is_recurring = frequency >= 0.5

            # Calculate variance (consistency of amounts)
            if len(amounts) > 1:
                mean = avg_amount
                variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
                std_dev = variance ** 0.5
                consistency = 1 - (std_dev / mean if mean > 0 else 0)
                consistency = max(0, min(1, consistency))  # Clamp to 0-1
            else:
                consistency = 1.0

            # Predicted monthly cost (weighted by frequency)
            predicted_monthly = avg_amount * frequency

            if is_recurring or total_spent > 1000:  # Include significant one-offs too
                recurring_costs.append({
                    'vendor': vendor,
                    'occurrences': len(vendor_bill_list),
                    'months_active': months_with_bills,
                    'average_amount': round(avg_amount, 2),
                    'total_spent': round(total_spent, 2),
                    'frequency': round(frequency, 2),
                    'is_recurring': is_recurring,
                    'consistency': round(consistency, 2),
                    'predicted_monthly': round(predicted_monthly, 2),
                    'last_bill_date': max((b['paid_date'] for b in vendor_bill_list if b['paid_date']), default=None),
                })
                total_vendor_monthly_avg += predicted_monthly

        # Sort by predicted monthly cost (highest first)
        recurring_costs.sort(key=lambda x: x['predicted_monthly'], reverse=True)

        # Calculate the "other costs" that aren't captured in vendor bills
        # This includes PAYE, salaries, direct debits, etc.
        other_costs = max(0, avg_monthly_from_pnl - total_vendor_monthly_avg)

        # Generate next 3 month predictions using P&L-based totals
        predictions = []
        for i in range(3):
            month = today.month + i + 1
            year = today.year
            while month > 12:
                month -= 12
                year += 1

            month_name = date(year, month, 1).strftime('%B %Y')

            # Predict costs for this month - use P&L average as the base
            month_costs = []

            # Add "Salaries & PAYE" as a synthetic entry for the non-vendor costs
            if other_costs > 1000:
                month_costs.append({
                    'vendor': 'Salaries, PAYE & Other',
                    'predicted_amount': round(other_costs, 2),
                    'confidence': 0.95,  # Very predictable
                    'is_fixed': True,
                })

            # Add recurring vendor costs
            for cost in recurring_costs:
                if cost['is_recurring']:
                    # Predict this vendor will bill
                    expected = cost['average_amount'] * cost['frequency']
                    if expected > 100:  # Only include significant predictions
                        month_costs.append({
                            'vendor': cost['vendor'],
                            'predicted_amount': round(cost['average_amount'], 2),
                            'confidence': round(cost['frequency'] * cost['consistency'], 2),
                            'is_fixed': False,
                        })

            # Use P&L average for the total prediction (more accurate than summing vendors)
            predictions.append({
                'month': month_name,
                'month_key': f"{year}-{month:02d}",
                'predicted_total': round(avg_monthly_from_pnl, 2),
                'top_costs': month_costs[:6],  # Top 6 expected costs (including salaries)
            })

        return {
            'analysis_period_months': months,
            'total_bills_analyzed': len(bills),
            'unique_vendors': len(vendor_bills),
            'recurring_costs': recurring_costs[:15],  # Top 15 vendors
            'average_monthly_spend': round(avg_monthly_from_pnl, 2),  # Use P&L figure
            'vendor_costs_monthly': round(total_vendor_monthly_avg, 2),
            'other_costs_monthly': round(other_costs, 2),  # PAYE, salaries, etc.
            'predictions': predictions,
            'pnl_based': True,  # Flag to indicate this uses P&L data
        }

    # ==================== DRILL-DOWN METHODS ====================

    def get_account_codes(self, force_refresh=False):
        """
        Get all account codes from Xero. Cached for 24 hours.

        Returns:
            list: Account codes with name, type, and class
        """
        global _account_codes_cache, _account_codes_cache_time

        # Check cache
        if not force_refresh and _account_codes_cache is not None:
            if _account_codes_cache_time and (datetime.utcnow() - _account_codes_cache_time).seconds < 86400:
                return _account_codes_cache

        data = self._get('Accounts')

        accounts = []
        for acct in data.get('Accounts', []):
            accounts.append({
                'account_id': acct.get('AccountID'),
                'account_code': acct.get('Code'),
                'name': acct.get('Name'),
                'type': acct.get('Type'),
                'class': acct.get('Class'),  # REVENUE, EXPENSE, ASSET, LIABILITY, EQUITY
                'status': acct.get('Status'),
                'tax_type': acct.get('TaxType'),
            })

        # Update cache
        _account_codes_cache = accounts
        _account_codes_cache_time = datetime.utcnow()

        return accounts

    def get_bank_transactions(self, from_date=None, to_date=None, account_id=None, page=1, page_size=100):
        """
        Get bank transactions for a date range.

        Args:
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: today)
            account_id: Optional bank account ID to filter by
            page: Page number (1-indexed)
            page_size: Results per page (max 100)

        Returns:
            dict: Transactions with pagination info
        """
        today = date.today()
        if from_date is None:
            from_date = today - timedelta(days=30)
        if to_date is None:
            to_date = today

        # Build where clause
        where_parts = [
            f'Date>=DateTime({from_date.year},{from_date.month},{from_date.day})',
            f'Date<=DateTime({to_date.year},{to_date.month},{to_date.day})',
        ]

        if account_id:
            where_parts.append(f'BankAccount.AccountID==Guid("{account_id}")')

        params = {
            'where': ' AND '.join(where_parts),
            'page': page,
            'order': 'Date DESC',
        }

        data = self._get('BankTransactions', params=params)

        transactions = []
        for txn in data.get('BankTransactions', []):
            txn_date = self._parse_xero_date(txn.get('DateString') or txn.get('Date'))
            contact = txn.get('Contact', {})
            bank_account = txn.get('BankAccount', {})

            # Calculate amount (positive for money in, negative for money out)
            txn_type = txn.get('Type', '')
            total = float(txn.get('Total', 0))
            if txn_type in ['SPEND', 'SPEND-OVERPAYMENT', 'SPEND-PREPAYMENT']:
                amount = -total
            else:
                amount = total

            transactions.append({
                'transaction_id': txn.get('BankTransactionID'),
                'date': txn_date.isoformat() if txn_date else None,
                'type': txn_type,
                'description': txn.get('Reference') or self._get_line_description(txn),
                'reference': txn.get('Reference', ''),
                'amount': amount,
                'contact_name': contact.get('Name', ''),
                'contact_id': contact.get('ContactID'),
                'is_reconciled': txn.get('IsReconciled', False),
                'bank_account_name': bank_account.get('Name', ''),
                'bank_account_id': bank_account.get('AccountID'),
                'status': txn.get('Status'),
            })

        return {
            'transactions': transactions,
            'page': page,
            'page_size': page_size,
            'has_more': len(transactions) == page_size,
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
        }

    def _get_line_description(self, txn):
        """Extract description from first line item."""
        line_items = txn.get('LineItems', [])
        if line_items:
            return line_items[0].get('Description', '')
        return ''

    def _parse_xero_date(self, date_value):
        """Parse Xero date which can be in multiple formats."""
        if not date_value:
            return None

        # Handle Microsoft JSON date format: /Date(1751241600000+0000)/
        if isinstance(date_value, str) and date_value.startswith('/Date('):
            match = re.search(r'/Date\((\d+)', date_value)
            if match:
                timestamp_ms = int(match.group(1))
                return datetime.utcfromtimestamp(timestamp_ms / 1000).date()

        # Handle ISO format with time: 2025-06-23T00:00:00
        if isinstance(date_value, str):
            try:
                if 'T' in date_value:
                    return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
                else:
                    return datetime.strptime(date_value[:10], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        return None

    def get_invoice_details(self, invoice_id):
        """
        Get full invoice details including line items.

        Args:
            invoice_id: The Xero invoice ID

        Returns:
            dict: Invoice with line items
        """
        data = self._get(f'Invoices/{invoice_id}')

        invoices = data.get('Invoices', [])
        if not invoices:
            return None

        inv = invoices[0]
        contact = inv.get('Contact', {})

        line_items = []
        for item in inv.get('LineItems', []):
            line_items.append({
                'line_item_id': item.get('LineItemID'),
                'description': item.get('Description', ''),
                'quantity': float(item.get('Quantity', 0)),
                'unit_price': float(item.get('UnitAmount', 0)),
                'amount': float(item.get('LineAmount', 0)),
                'account_code': item.get('AccountCode'),
                'tax_type': item.get('TaxType'),
                'tax_amount': float(item.get('TaxAmount', 0)),
            })

        due_date = self._parse_xero_date(inv.get('DueDateString') or inv.get('DueDate'))
        issue_date = self._parse_xero_date(inv.get('DateString') or inv.get('Date'))

        return {
            'invoice_id': inv.get('InvoiceID'),
            'invoice_number': inv.get('InvoiceNumber'),
            'type': inv.get('Type'),
            'status': inv.get('Status'),
            'contact_name': contact.get('Name', ''),
            'contact_id': contact.get('ContactID'),
            'issue_date': issue_date.isoformat() if issue_date else None,
            'due_date': due_date.isoformat() if due_date else None,
            'subtotal': float(inv.get('SubTotal', 0)),
            'tax': float(inv.get('TotalTax', 0)),
            'total': float(inv.get('Total', 0)),
            'amount_due': float(inv.get('AmountDue', 0)),
            'amount_paid': float(inv.get('AmountPaid', 0)),
            'reference': inv.get('Reference', ''),
            'line_items': line_items,
            'currency_code': inv.get('CurrencyCode', 'GBP'),
        }

    def get_invoices_detailed(self, invoice_type='ACCREC', status=None, from_date=None, to_date=None, page=1, page_size=100):
        """
        Get invoices with more details for drill-down view.

        Args:
            invoice_type: 'ACCREC' for receivables, 'ACCPAY' for payables
            status: Optional status filter ('AUTHORISED', 'PAID', 'DRAFT', etc.)
            from_date: Optional start date filter
            to_date: Optional end date filter
            page: Page number
            page_size: Results per page

        Returns:
            dict: Invoices with pagination info
        """
        where_parts = [f'Type=="{invoice_type}"']

        if status:
            where_parts.append(f'Status=="{status}"')

        if from_date:
            where_parts.append(f'Date>=DateTime({from_date.year},{from_date.month},{from_date.day})')

        if to_date:
            where_parts.append(f'Date<=DateTime({to_date.year},{to_date.month},{to_date.day})')

        params = {
            'where': ' AND '.join(where_parts),
            'page': page,
            'order': 'DueDate ASC',
        }

        data = self._get('Invoices', params=params)

        invoices = []
        today = date.today()

        for inv in data.get('Invoices', []):
            due_date = self._parse_xero_date(inv.get('DueDateString') or inv.get('DueDate'))
            issue_date = self._parse_xero_date(inv.get('DateString') or inv.get('Date'))
            contact = inv.get('Contact', {})

            is_overdue = due_date < today if due_date else False
            days_overdue = (today - due_date).days if due_date and is_overdue else 0

            invoices.append({
                'invoice_id': inv.get('InvoiceID'),
                'invoice_number': inv.get('InvoiceNumber'),
                'type': inv.get('Type'),
                'status': inv.get('Status'),
                'contact_name': contact.get('Name', ''),
                'contact_id': contact.get('ContactID'),
                'issue_date': issue_date.isoformat() if issue_date else None,
                'due_date': due_date.isoformat() if due_date else None,
                'total': float(inv.get('Total', 0)),
                'amount_due': float(inv.get('AmountDue', 0)),
                'amount_paid': float(inv.get('AmountPaid', 0)),
                'is_overdue': is_overdue,
                'days_overdue': days_overdue,
                'reference': inv.get('Reference', ''),
                'currency_code': inv.get('CurrencyCode', 'GBP'),
            })

        return {
            'invoices': invoices,
            'page': page,
            'page_size': page_size,
            'has_more': len(invoices) == page_size,
            'type': invoice_type,
        }

    def get_profit_and_loss_detailed(self, from_date=None, to_date=None):
        """
        Get P&L report with account-level detail for drill-down.

        Returns categories with their accounts and totals.
        """
        today = date.today()
        if from_date is None:
            from_date = date(today.year, today.month, 1)
        if to_date is None:
            to_date = today

        params = {
            'fromDate': from_date.isoformat(),
            'toDate': to_date.isoformat(),
        }

        data = self._get('Reports/ProfitAndLoss', params=params)

        categories = []

        reports = data.get('Reports', [])
        if reports:
            report = reports[0]
            rows = report.get('Rows', [])

            for section in rows:
                if section.get('RowType') == 'Section':
                    title = section.get('Title', '').strip()
                    if not title:
                        continue

                    accounts = []
                    section_total = 0

                    for row in section.get('Rows', []):
                        row_type = row.get('RowType')
                        cells = row.get('Cells', [])

                        if row_type == 'Row' and len(cells) >= 2:
                            account_name = cells[0].get('Value', '')
                            account_id = cells[0].get('Attributes', [{}])[0].get('Value') if cells[0].get('Attributes') else None
                            value_str = cells[-1].get('Value', '0')

                            try:
                                value = float(value_str) if value_str else 0
                            except ValueError:
                                value = 0

                            if account_name and value != 0:
                                accounts.append({
                                    'account_name': account_name,
                                    'account_id': account_id,
                                    'amount': value,
                                })

                        elif row_type == 'SummaryRow':
                            value_str = cells[-1].get('Value', '0') if cells else '0'
                            try:
                                section_total = float(value_str) if value_str else 0
                            except ValueError:
                                section_total = 0

                    if accounts or section_total != 0:
                        categories.append({
                            'category': title,
                            'total': section_total,
                            'accounts': accounts,
                        })

        return {
            'categories': categories,
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
        }

    def get_journals(self, from_date=None, to_date=None, account_id=None, page=1):
        """
        Get journal entries, optionally filtered by account.

        Note: Xero's Journals endpoint doesn't filter by account server-side,
        so we fetch all journals and filter client-side if account_id is provided.

        Args:
            from_date: Start date
            to_date: End date
            account_id: Optional account ID to filter by
            page: Page number (Xero uses offset, 100 per page)

        Returns:
            dict: Journal entries with lines
        """
        today = date.today()
        if from_date is None:
            from_date = date(today.year, today.month, 1)
        if to_date is None:
            to_date = today

        # Xero uses offset-based pagination for journals
        offset = (page - 1) * 100

        params = {
            'offset': offset,
        }

        # Add date filter if supported (check Xero API docs)
        # For now, we'll filter client-side

        data = self._get('Journals', params=params)

        journals = []
        for journal in data.get('Journals', []):
            journal_date = self._parse_xero_date(journal.get('JournalDate'))

            # Skip if outside date range
            if journal_date:
                if journal_date < from_date or journal_date > to_date:
                    continue

            source_id = journal.get('SourceID')
            source_type = journal.get('SourceType', '')

            for line in journal.get('JournalLines', []):
                line_account_id = line.get('AccountID')

                # Filter by account if specified
                if account_id and line_account_id != account_id:
                    continue

                gross = float(line.get('GrossAmount', 0))
                net = float(line.get('NetAmount', 0))

                journals.append({
                    'journal_id': journal.get('JournalID'),
                    'journal_number': journal.get('JournalNumber'),
                    'date': journal_date.isoformat() if journal_date else None,
                    'description': line.get('Description', ''),
                    'reference': journal.get('Reference', ''),
                    'account_id': line_account_id,
                    'account_name': line.get('AccountName', ''),
                    'account_code': line.get('AccountCode', ''),
                    'debit': gross if gross > 0 else 0,
                    'credit': abs(gross) if gross < 0 else 0,
                    'net_amount': net,
                    'source_type': source_type,
                    'source_id': source_id,
                })

        return {
            'journals': journals,
            'page': page,
            'has_more': len(data.get('Journals', [])) == 100,
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
        }

    def search_transactions(self, query, search_type='all', from_date=None, to_date=None, page=1, page_size=50):
        """
        Search across transactions by description, reference, or contact name.

        Args:
            query: Search term
            search_type: 'cash', 'receivables', 'payables', 'pnl', or 'all'
            from_date: Start date
            to_date: End date
            page: Page number
            page_size: Results per page

        Returns:
            dict: Matching transactions grouped by type
        """
        today = date.today()
        if from_date is None:
            from_date = today - timedelta(days=90)
        if to_date is None:
            to_date = today

        query_lower = query.lower()
        results = {
            'query': query,
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
            'results': [],
        }

        def matches(text):
            return query_lower in (text or '').lower()

        # Search bank transactions
        if search_type in ['cash', 'all']:
            bank_data = self.get_bank_transactions(from_date, to_date, page=1, page_size=500)
            for txn in bank_data.get('transactions', []):
                if matches(txn['description']) or matches(txn['reference']) or matches(txn['contact_name']):
                    txn['result_type'] = 'cash'
                    results['results'].append(txn)

        # Search receivables
        if search_type in ['receivables', 'all']:
            recv_data = self.get_invoices_detailed('ACCREC', from_date=from_date, to_date=to_date, page=1, page_size=500)
            for inv in recv_data.get('invoices', []):
                if matches(inv['invoice_number']) or matches(inv['reference']) or matches(inv['contact_name']):
                    inv['result_type'] = 'receivables'
                    results['results'].append(inv)

        # Search payables
        if search_type in ['payables', 'all']:
            pay_data = self.get_invoices_detailed('ACCPAY', from_date=from_date, to_date=to_date, page=1, page_size=500)
            for inv in pay_data.get('invoices', []):
                if matches(inv['invoice_number']) or matches(inv['reference']) or matches(inv['contact_name']):
                    inv['result_type'] = 'payables'
                    results['results'].append(inv)

        # Paginate results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        results['total_results'] = len(results['results'])
        results['results'] = results['results'][start_idx:end_idx]
        results['page'] = page
        results['page_size'] = page_size
        results['has_more'] = end_idx < results['total_results']

        return results

    # ==================== FINANCE API METHODS ====================

    def get_bank_statement_accounting(self, bank_account_id, from_date=None, to_date=None, summary_only=False):
        """
        Get bank statement data with accounting details using the Finance API.

        This endpoint provides access to actual bank statement data (from bank feeds)
        along with reconciled accounting data, unlike the BankTransactions endpoint
        which only shows manually created transactions.

        Args:
            bank_account_id: The Xero bank account ID (GUID)
            from_date: Start date (default: 1 year ago)
            to_date: End date (default: today)
            summary_only: If True, returns only summary data

        Returns:
            dict: Bank statement data with transactions
        """
        today = date.today()
        if from_date is None:
            from_date = date(today.year - 1, today.month, today.day)
        if to_date is None:
            to_date = today

        params = {
            'fromDate': from_date.isoformat(),
            'toDate': to_date.isoformat(),
            'summaryOnly': 'true' if summary_only else 'false',
        }

        endpoint = f'BankStatementsPlus/BankStatementAccounting/{bank_account_id}'
        data = self._get_finance(endpoint, params=params)

        return data

    def get_bank_statements_plus(self, from_date=None, to_date=None, page=1, page_size=50):
        """
        Get bank statement transactions from all accounts using Finance API.

        This method fetches data from all bank accounts and combines them,
        providing historical bank feed data that BankTransactions doesn't have.

        Args:
            from_date: Start date (default: 1 year ago)
            to_date: End date (default: today)
            page: Page number for pagination
            page_size: Number of results per page

        Returns:
            dict: Combined bank statement transactions from all accounts
        """
        today = date.today()
        if from_date is None:
            from_date = date(today.year - 1, today.month, today.day)
        if to_date is None:
            to_date = today

        # Get all bank accounts
        bank_accounts = self.get_bank_accounts()

        all_transactions = []

        for account in bank_accounts:
            account_id = account.get('account_id')
            if not account_id:
                continue

            try:
                data = self.get_bank_statement_accounting(
                    bank_account_id=account_id,
                    from_date=from_date,
                    to_date=to_date,
                    summary_only=False,
                )

                # Extract statement data
                statement = data.get('statement', {})
                statement_lines = statement.get('statementLines', [])

                for line in statement_lines:
                    posted_date = self._parse_xero_date(line.get('postedDate'))
                    amount = float(line.get('amount', 0))

                    all_transactions.append({
                        'transaction_id': line.get('statementLineId'),
                        'date': posted_date.isoformat() if posted_date else None,
                        'type': 'CREDIT' if amount >= 0 else 'DEBIT',
                        'description': line.get('description', ''),
                        'reference': line.get('reference', ''),
                        'amount': amount,
                        'cheque_number': line.get('chequeNumber', ''),
                        'is_reconciled': line.get('isReconciled', False),
                        'bank_account_name': account.get('name', ''),
                        'bank_account_id': account_id,
                        'payee_name': line.get('payeeName', ''),
                        # Include accounting data if available
                        'accounting': line.get('accounting', {}),
                    })

            except Exception as e:
                # Log error but continue with other accounts
                print(f"Error fetching bank statements for account {account_id}: {e}")
                continue

        # Sort by date descending
        all_transactions.sort(key=lambda x: x['date'] or '', reverse=True)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = all_transactions[start_idx:end_idx]

        # Calculate summary
        total_in = sum(t['amount'] for t in paginated if t['amount'] > 0)
        total_out = sum(t['amount'] for t in paginated if t['amount'] < 0)

        return {
            'transactions': paginated,
            'page': page,
            'page_size': page_size,
            'total_count': len(all_transactions),
            'has_more': end_idx < len(all_transactions),
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
            'summary': {
                'total_in': total_in,
                'total_out': total_out,
                'net_change': total_in + total_out,
                'transaction_count': len(paginated),
            },
        }
