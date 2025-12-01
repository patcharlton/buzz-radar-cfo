from datetime import datetime, date
import requests

from .auth import XeroAuth


class XeroClient:
    """Wrapper for Xero API operations using direct REST calls."""

    BASE_URL = 'https://api.xero.com/api.xro/2.0'

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

        reports = data.get('Reports', [])
        if reports:
            report = reports[0]
            rows = report.get('Rows', [])

            for section in rows:
                row_type = section.get('RowType')
                title = section.get('Title', '')

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

                                if 'Income' in title or 'Revenue' in title:
                                    revenue = value
                                elif 'Expense' in title or 'Operating' in title:
                                    expenses = abs(value)

                elif row_type == 'Row':
                    cells = section.get('Cells', [])
                    if cells and 'Net Profit' in str(cells[0].get('Value', '')):
                        value_str = cells[-1].get('Value', '0')
                        try:
                            net_profit = float(value_str) if value_str else 0
                        except ValueError:
                            net_profit = 0

        if net_profit == 0:
            net_profit = revenue - expenses

        return {
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': net_profit,
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
        Analyze paid bills to identify recurring costs and predict future expenses.

        Args:
            months: Number of months to analyze (default: 6)

        Returns:
            dict: Recurring costs breakdown with predictions
        """
        from collections import defaultdict
        from datetime import timedelta

        bills = self.get_paid_bills(months=months)
        today = date.today()

        # Group bills by vendor
        vendor_bills = defaultdict(list)
        for bill in bills:
            vendor_bills[bill['vendor']].append(bill)

        recurring_costs = []
        total_monthly_avg = 0

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
                total_monthly_avg += predicted_monthly

        # Sort by predicted monthly cost (highest first)
        recurring_costs.sort(key=lambda x: x['predicted_monthly'], reverse=True)

        # Generate next 3 month predictions
        predictions = []
        for i in range(3):
            month = today.month + i + 1
            year = today.year
            while month > 12:
                month -= 12
                year += 1

            month_name = date(year, month, 1).strftime('%B %Y')

            # Predict costs for this month
            month_costs = []
            for cost in recurring_costs:
                if cost['is_recurring']:
                    # Predict this vendor will bill
                    expected = cost['average_amount'] * cost['frequency']
                    if expected > 100:  # Only include significant predictions
                        month_costs.append({
                            'vendor': cost['vendor'],
                            'predicted_amount': round(cost['average_amount'], 2),
                            'confidence': round(cost['frequency'] * cost['consistency'], 2),
                        })

            predictions.append({
                'month': month_name,
                'month_key': f"{year}-{month:02d}",
                'predicted_total': round(sum(c['predicted_amount'] for c in month_costs), 2),
                'top_costs': month_costs[:5],  # Top 5 expected costs
            })

        return {
            'analysis_period_months': months,
            'total_bills_analyzed': len(bills),
            'unique_vendors': len(vendor_bills),
            'recurring_costs': recurring_costs[:15],  # Top 15 vendors
            'average_monthly_spend': round(total_monthly_avg, 2),
            'predictions': predictions,
        }
