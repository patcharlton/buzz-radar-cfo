from datetime import datetime
from .db import db
from cryptography.fernet import Fernet
import os
import base64


def get_encryption_key():
    """Get or generate encryption key for token storage."""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        # In production, this should be a persistent key stored securely
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return key.encode() if isinstance(key, str) else key


class XeroToken(db.Model):
    """Store OAuth tokens for Xero API access."""

    __tablename__ = 'xero_tokens'

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    token_type = db.Column(db.String(50), default='Bearer')
    expires_at = db.Column(db.DateTime, nullable=False)
    tenant_id = db.Column(db.String(100))
    tenant_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def encrypt_token(token):
        """Encrypt a token for secure storage."""
        f = Fernet(get_encryption_key())
        return f.encrypt(token.encode()).decode()

    @staticmethod
    def decrypt_token(encrypted_token):
        """Decrypt a stored token."""
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_token.encode()).decode()

    def set_access_token(self, token):
        """Set and encrypt the access token."""
        self.access_token = self.encrypt_token(token)

    def get_access_token(self):
        """Get and decrypt the access token."""
        return self.decrypt_token(self.access_token)

    def set_refresh_token(self, token):
        """Set and encrypt the refresh token."""
        self.refresh_token = self.encrypt_token(token)

    def get_refresh_token(self):
        """Get and decrypt the refresh token."""
        return self.decrypt_token(self.refresh_token)

    def is_expired(self):
        """Check if the access token is expired."""
        return datetime.utcnow() >= self.expires_at

    def to_dict(self):
        """Convert to dictionary for API responses (excluding sensitive data)."""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant_name,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FinancialSnapshot(db.Model):
    """Cache financial snapshots for quick access."""

    __tablename__ = 'financial_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    snapshot_date = db.Column(db.Date, nullable=False)
    cash_balance = db.Column(db.Numeric(12, 2))
    receivables_total = db.Column(db.Numeric(12, 2))
    receivables_overdue = db.Column(db.Numeric(12, 2))
    payables_total = db.Column(db.Numeric(12, 2))
    payables_overdue = db.Column(db.Numeric(12, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'cash_balance': float(self.cash_balance) if self.cash_balance else 0,
            'receivables_total': float(self.receivables_total) if self.receivables_total else 0,
            'receivables_overdue': float(self.receivables_overdue) if self.receivables_overdue else 0,
            'payables_total': float(self.payables_total) if self.payables_total else 0,
            'payables_overdue': float(self.payables_overdue) if self.payables_overdue else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class InvoiceCache(db.Model):
    """Cache invoice data from Xero."""

    __tablename__ = 'invoices_cache'

    id = db.Column(db.Integer, primary_key=True)
    xero_invoice_id = db.Column(db.String(100), unique=True, nullable=False)
    invoice_number = db.Column(db.String(100))
    contact_name = db.Column(db.String(200))
    invoice_type = db.Column(db.String(20))  # ACCREC or ACCPAY
    status = db.Column(db.String(50))
    amount_due = db.Column(db.Numeric(12, 2))
    total = db.Column(db.Numeric(12, 2))
    due_date = db.Column(db.Date)
    issue_date = db.Column(db.Date)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'xero_invoice_id': self.xero_invoice_id,
            'invoice_number': self.invoice_number,
            'contact_name': self.contact_name,
            'invoice_type': self.invoice_type,
            'status': self.status,
            'amount_due': float(self.amount_due) if self.amount_due else 0,
            'total': float(self.total) if self.total else 0,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def days_until_due(self):
        """Calculate days until due (negative if overdue)."""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow().date()
        return delta.days

    def is_overdue(self):
        """Check if the invoice is overdue."""
        days = self.days_until_due()
        return days is not None and days < 0


class AICache(db.Model):
    """Persistent cache for AI-generated responses."""

    __tablename__ = 'ai_cache'

    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    cache_type = db.Column(db.String(50), nullable=False)  # daily_insights, monthly_analysis, forecast, etc.
    value = db.Column(db.Text, nullable=False)  # JSON-encoded response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_expired(self):
        """Check if the cache entry is expired."""
        return datetime.utcnow() >= self.expires_at

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'cache_type': self.cache_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
        }


class MonthlySnapshot(db.Model):
    """Store monthly financial snapshots for historical analysis."""

    __tablename__ = 'monthly_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    snapshot_date = db.Column(db.Date, nullable=False, unique=True, index=True)  # First of month
    cash_position = db.Column(db.Numeric(14, 2))
    receivables_total = db.Column(db.Numeric(14, 2))
    receivables_overdue = db.Column(db.Numeric(14, 2))
    payables_total = db.Column(db.Numeric(14, 2))
    payables_overdue = db.Column(db.Numeric(14, 2))
    revenue = db.Column(db.Numeric(14, 2))
    expenses = db.Column(db.Numeric(14, 2))
    net_profit = db.Column(db.Numeric(14, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'cash_position': float(self.cash_position) if self.cash_position else 0,
            'receivables_total': float(self.receivables_total) if self.receivables_total else 0,
            'receivables_overdue': float(self.receivables_overdue) if self.receivables_overdue else 0,
            'payables_total': float(self.payables_total) if self.payables_total else 0,
            'payables_overdue': float(self.payables_overdue) if self.payables_overdue else 0,
            'revenue': float(self.revenue) if self.revenue else 0,
            'expenses': float(self.expenses) if self.expenses else 0,
            'net_profit': float(self.net_profit) if self.net_profit else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_or_create(cls, snapshot_date):
        """Get existing snapshot or create new one (upsert logic)."""
        existing = cls.query.filter_by(snapshot_date=snapshot_date).first()
        if existing:
            return existing, False
        new_snapshot = cls(snapshot_date=snapshot_date)
        return new_snapshot, True


class AccountBalanceHistory(db.Model):
    """Store historical account balances for trend analysis."""

    __tablename__ = 'account_balances_history'

    id = db.Column(db.Integer, primary_key=True)
    snapshot_date = db.Column(db.Date, nullable=False, index=True)
    account_id = db.Column(db.String(100), nullable=False)
    account_name = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Numeric(14, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('snapshot_date', 'account_id', name='unique_account_snapshot'),
    )

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'balance': float(self.balance) if self.balance else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class HistoricalInvoice(db.Model):
    """Store historical invoice data imported from CSV exports."""

    __tablename__ = 'historical_invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), nullable=False, index=True)
    invoice_type = db.Column(db.String(20), nullable=False)  # receivable, payable, overpayment
    is_credit_note = db.Column(db.Boolean, default=False)
    contact_name = db.Column(db.String(300))
    invoice_date = db.Column(db.Date, nullable=False, index=True)
    due_date = db.Column(db.Date)
    total = db.Column(db.Numeric(14, 2))  # Always positive, sign determined by type/is_credit_note
    tax_total = db.Column(db.Numeric(14, 2))
    amount_paid = db.Column(db.Numeric(14, 2))
    amount_due = db.Column(db.Numeric(14, 2))
    currency = db.Column(db.String(10), default='GBP')
    gbp_total = db.Column(db.Numeric(14, 2))  # Converted to GBP for reporting
    status = db.Column(db.String(50))  # Paid, Awaiting Payment
    source = db.Column(db.String(20), default='csv_import')  # csv_import, xero_api
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    line_items = db.relationship('HistoricalLineItem', backref='invoice', lazy='dynamic',
                                 cascade='all, delete-orphan')

    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('invoice_number', 'invoice_type', name='unique_invoice_number_type'),
    )

    # Approximate currency conversion rates to GBP
    CURRENCY_RATES = {
        'GBP': 1.0,
        'EUR': 0.85,
        'USD': 0.79,
    }

    def calculate_gbp_total(self):
        """Calculate GBP equivalent of total."""
        rate = self.CURRENCY_RATES.get(self.currency, 1.0)
        return float(self.total or 0) * rate

    def signed_total(self):
        """Get total with correct sign (negative for credit notes)."""
        total = float(self.total or 0)
        return -total if self.is_credit_note else total

    def signed_gbp_total(self):
        """Get GBP total with correct sign."""
        total = float(self.gbp_total or 0)
        return -total if self.is_credit_note else total

    def net_total(self):
        """Get total excluding tax."""
        return float(self.total or 0) - float(self.tax_total or 0)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_type': self.invoice_type,
            'is_credit_note': self.is_credit_note,
            'contact_name': self.contact_name,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'total': float(self.total) if self.total else 0,
            'tax_total': float(self.tax_total) if self.tax_total else 0,
            'amount_paid': float(self.amount_paid) if self.amount_paid else 0,
            'amount_due': float(self.amount_due) if self.amount_due else 0,
            'currency': self.currency,
            'gbp_total': float(self.gbp_total) if self.gbp_total else 0,
            'status': self.status,
            'source': self.source,
            'is_overdue': self.is_overdue(),
            'days_overdue': self.days_overdue(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def is_overdue(self):
        """Check if invoice is overdue (unpaid and past due date)."""
        if self.status == 'Paid' or not self.due_date:
            return False
        return self.due_date < datetime.utcnow().date()

    def days_overdue(self):
        """Calculate days overdue (0 if not overdue)."""
        if not self.is_overdue():
            return 0
        delta = datetime.utcnow().date() - self.due_date
        return delta.days


class HistoricalLineItem(db.Model):
    """Store line items for historical invoices."""

    __tablename__ = 'historical_line_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('historical_invoices.id'), nullable=False, index=True)
    description = db.Column(db.Text)
    quantity = db.Column(db.Numeric(14, 4))
    unit_amount = db.Column(db.Numeric(14, 4))
    line_amount = db.Column(db.Numeric(14, 2))
    account_code = db.Column(db.String(20))
    tax_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'description': self.description,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit_amount': float(self.unit_amount) if self.unit_amount else 0,
            'line_amount': float(self.line_amount) if self.line_amount else 0,
            'account_code': self.account_code,
            'tax_type': self.tax_type,
        }


class BankTransaction(db.Model):
    """Store historical bank transactions imported from Xero exports."""

    __tablename__ = 'bank_transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    bank_account = db.Column(db.String(100), nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=False, index=True)  # Spend Money, Receivable Payment, etc.
    description = db.Column(db.Text)
    reference = db.Column(db.String(100))
    currency = db.Column(db.String(10), default='GBP')
    debit_gbp = db.Column(db.Numeric(12, 2), default=0)   # Money IN
    credit_gbp = db.Column(db.Numeric(12, 2), default=0)  # Money OUT
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def net_amount(self):
        """Get net amount (positive = money in, negative = money out)."""
        return float(self.debit_gbp or 0) - float(self.credit_gbp or 0)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'bank_account': self.bank_account,
            'source_type': self.source_type,
            'description': self.description,
            'reference': self.reference,
            'currency': self.currency,
            'debit_gbp': float(self.debit_gbp) if self.debit_gbp else 0,
            'credit_gbp': float(self.credit_gbp) if self.credit_gbp else 0,
            'net_amount': self.net_amount(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class MonthlyCashSnapshot(db.Model):
    """Store monthly cash flow snapshots calculated from bank transactions."""

    __tablename__ = 'monthly_cash_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    snapshot_date = db.Column(db.Date, nullable=False, unique=True, index=True)  # Last day of month
    opening_balance = db.Column(db.Numeric(12, 2))
    total_in = db.Column(db.Numeric(12, 2))
    total_out = db.Column(db.Numeric(12, 2))
    closing_balance = db.Column(db.Numeric(12, 2))
    wages_paid = db.Column(db.Numeric(12, 2))      # WAGES transactions
    hmrc_paid = db.Column(db.Numeric(12, 2))       # HMRC transactions (PAYE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def net_change(self):
        """Get net change for the month."""
        return float(self.total_in or 0) - float(self.total_out or 0)

    def total_payroll(self):
        """Get total payroll (wages + HMRC)."""
        return float(self.wages_paid or 0) + float(self.hmrc_paid or 0)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'month': self.snapshot_date.strftime('%Y-%m') if self.snapshot_date else None,
            'opening_balance': float(self.opening_balance) if self.opening_balance else 0,
            'total_in': float(self.total_in) if self.total_in else 0,
            'total_out': float(self.total_out) if self.total_out else 0,
            'closing_balance': float(self.closing_balance) if self.closing_balance else 0,
            'net_change': self.net_change(),
            'wages_paid': float(self.wages_paid) if self.wages_paid else 0,
            'hmrc_paid': float(self.hmrc_paid) if self.hmrc_paid else 0,
            'total_payroll': self.total_payroll(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
