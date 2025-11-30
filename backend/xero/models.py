"""Data models for Xero entities - used for type hints and data transformation."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List


@dataclass
class BankAccount:
    """Represents a Xero bank account."""
    account_id: str
    name: str
    code: Optional[str]
    balance: float
    currency_code: str = 'GBP'


@dataclass
class Invoice:
    """Represents a Xero invoice."""
    invoice_id: str
    invoice_number: str
    contact_name: str
    invoice_type: str  # ACCREC or ACCPAY
    status: str
    amount_due: float
    total: float
    due_date: Optional[date]
    issue_date: Optional[date]

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return self.due_date < date.today()

    @property
    def days_until_due(self) -> Optional[int]:
        if not self.due_date:
            return None
        return (self.due_date - date.today()).days


@dataclass
class CashPosition:
    """Summary of cash position across all bank accounts."""
    total_balance: float
    accounts: List[BankAccount]
    as_of_date: date


@dataclass
class ReceivablesSummary:
    """Summary of accounts receivable."""
    total: float
    overdue: float
    count: int
    overdue_count: int
    invoices: List[Invoice]


@dataclass
class PayablesSummary:
    """Summary of accounts payable."""
    total: float
    overdue: float
    count: int
    overdue_count: int
    invoices: List[Invoice]


@dataclass
class ProfitLossSummary:
    """Summary of profit and loss for a period."""
    revenue: float
    expenses: float
    net_profit: float
    from_date: date
    to_date: date
    period: str


@dataclass
class DashboardData:
    """Complete dashboard data structure."""
    cash_position: CashPosition
    receivables: ReceivablesSummary
    payables: PayablesSummary
    profit_loss: ProfitLossSummary
    last_synced: datetime
