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
