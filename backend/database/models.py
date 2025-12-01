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
