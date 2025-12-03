"""
Service to sync historical data from Xero API.

This ensures that the historical tables stay up-to-date with new transactions
and invoices from Xero, supplementing the initial Excel import.
"""
from datetime import date, datetime, timedelta
from sqlalchemy import and_
from backend.database import db
from backend.database.models import BankTransaction, HistoricalInvoice, MonthlyCashSnapshot


# Map Xero transaction types to our source types
XERO_TYPE_MAP = {
    'SPEND': 'Spend Money',
    'RECEIVE': 'Receive Money',
    'RECEIVE-OVERPAYMENT': 'Overpayment',
    'RECEIVE-PREPAYMENT': 'Prepayment',
    'SPEND-OVERPAYMENT': 'Spend Overpayment',
    'SPEND-PREPAYMENT': 'Spend Prepayment',
}


def sync_bank_transactions_from_xero(xero_client, days_back=90):
    """
    Sync bank transactions from Xero API to historical database.

    Args:
        xero_client: Authenticated Xero client
        days_back: Number of days to fetch (default 90)

    Returns:
        dict: Statistics about the sync operation
    """
    from_date = date.today() - timedelta(days=days_back)
    to_date = date.today()

    stats = {
        'fetched': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': [],
    }

    try:
        # Fetch all pages of transactions
        page = 1
        all_transactions = []

        while True:
            result = xero_client.get_bank_transactions(
                from_date=from_date,
                to_date=to_date,
                page=page,
                page_size=100
            )

            transactions = result.get('transactions', [])
            all_transactions.extend(transactions)
            stats['fetched'] += len(transactions)

            if not result.get('has_more', False) or len(transactions) == 0:
                break
            page += 1

            # Safety limit
            if page > 50:
                break

        # Process each transaction
        for txn in all_transactions:
            try:
                txn_date_str = txn.get('date')
                if not txn_date_str:
                    stats['skipped'] += 1
                    continue

                txn_date = datetime.strptime(txn_date_str[:10], '%Y-%m-%d').date()

                # Check if transaction already exists (by date + description + amount)
                # We use a composite check since Xero transaction IDs aren't stored in historical
                amount = txn.get('amount', 0)
                description = txn.get('description') or txn.get('contact_name') or ''
                bank_account = txn.get('bank_account_name', '')

                existing = BankTransaction.query.filter(
                    and_(
                        BankTransaction.transaction_date == txn_date,
                        BankTransaction.description == description,
                        BankTransaction.bank_account == bank_account,
                    )
                ).first()

                # Calculate debit/credit from amount
                if amount >= 0:
                    debit_gbp = amount
                    credit_gbp = 0
                else:
                    debit_gbp = 0
                    credit_gbp = abs(amount)

                # Map Xero type to our source type
                xero_type = txn.get('type', '')
                source_type = XERO_TYPE_MAP.get(xero_type, xero_type)

                if existing:
                    # Update existing record
                    existing.debit_gbp = debit_gbp
                    existing.credit_gbp = credit_gbp
                    existing.source_type = source_type
                    existing.reference = txn.get('reference', '')
                    stats['updated'] += 1
                else:
                    # Create new record
                    new_txn = BankTransaction(
                        transaction_date=txn_date,
                        bank_account=bank_account,
                        source_type=source_type,
                        description=description,
                        reference=txn.get('reference', ''),
                        currency='GBP',  # Xero API returns in account currency
                        debit_gbp=debit_gbp,
                        credit_gbp=credit_gbp,
                    )
                    db.session.add(new_txn)
                    stats['created'] += 1

            except Exception as e:
                stats['errors'].append(f"Transaction error: {str(e)}")
                stats['skipped'] += 1

        db.session.commit()

        # Recalculate monthly snapshots for affected months
        if stats['created'] > 0 or stats['updated'] > 0:
            recalculate_monthly_snapshots(from_date, to_date)

    except Exception as e:
        db.session.rollback()
        stats['errors'].append(f"Sync error: {str(e)}")

    return stats


def sync_invoices_from_xero(xero_client, days_back=90):
    """
    Sync invoices (receivables and payables) from Xero API to historical database.

    Args:
        xero_client: Authenticated Xero client
        days_back: Number of days to fetch (default 90)

    Returns:
        dict: Statistics about the sync operation
    """
    from_date = date.today() - timedelta(days=days_back)
    to_date = date.today()

    stats = {
        'receivables_fetched': 0,
        'payables_fetched': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': [],
    }

    try:
        # Fetch receivables (ACCREC)
        recv_invoices = _fetch_all_invoices(xero_client, 'ACCREC', from_date, to_date)
        stats['receivables_fetched'] = len(recv_invoices)

        # Fetch payables (ACCPAY)
        pay_invoices = _fetch_all_invoices(xero_client, 'ACCPAY', from_date, to_date)
        stats['payables_fetched'] = len(pay_invoices)

        # Process receivables
        for inv in recv_invoices:
            result = _upsert_invoice(inv, 'receivable')
            if result == 'created':
                stats['created'] += 1
            elif result == 'updated':
                stats['updated'] += 1
            else:
                stats['skipped'] += 1

        # Process payables
        for inv in pay_invoices:
            result = _upsert_invoice(inv, 'payable')
            if result == 'created':
                stats['created'] += 1
            elif result == 'updated':
                stats['updated'] += 1
            else:
                stats['skipped'] += 1

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        stats['errors'].append(f"Sync error: {str(e)}")

    return stats


def _fetch_all_invoices(xero_client, invoice_type, from_date, to_date):
    """Fetch all pages of invoices from Xero."""
    all_invoices = []
    page = 1

    while True:
        result = xero_client.get_invoices_detailed(
            invoice_type=invoice_type,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=100
        )

        invoices = result.get('invoices', [])
        all_invoices.extend(invoices)

        if not result.get('has_more', False) or len(invoices) == 0:
            break
        page += 1

        # Safety limit
        if page > 50:
            break

    return all_invoices


def _upsert_invoice(inv, invoice_type):
    """
    Insert or update an invoice in the historical table.

    Returns: 'created', 'updated', or 'skipped'
    """
    invoice_number = inv.get('invoice_number')
    if not invoice_number:
        return 'skipped'

    # Parse dates
    issue_date_str = inv.get('issue_date')
    due_date_str = inv.get('due_date')

    if not issue_date_str:
        return 'skipped'

    try:
        issue_date = datetime.strptime(issue_date_str[:10], '%Y-%m-%d').date()
        due_date = datetime.strptime(due_date_str[:10], '%Y-%m-%d').date() if due_date_str else None
    except ValueError:
        return 'skipped'

    # Check if invoice already exists
    existing = HistoricalInvoice.query.filter_by(
        invoice_number=invoice_number,
        invoice_type=invoice_type
    ).first()

    # Map Xero status to our status
    xero_status = inv.get('status', '')
    if xero_status == 'PAID':
        status = 'Paid'
    elif xero_status in ['AUTHORISED', 'SUBMITTED']:
        status = 'Awaiting Payment'
    else:
        status = xero_status

    total = float(inv.get('total', 0))
    amount_paid = float(inv.get('amount_paid', 0))
    amount_due = float(inv.get('amount_due', 0))
    currency = inv.get('currency_code', 'GBP')

    # Calculate GBP total
    rates = {'GBP': 1.0, 'EUR': 0.85, 'USD': 0.79}
    gbp_total = total * rates.get(currency, 1.0)

    if existing:
        # Update existing record
        existing.contact_name = inv.get('contact_name', '')
        existing.invoice_date = issue_date
        existing.due_date = due_date
        existing.total = total
        existing.amount_paid = amount_paid
        existing.amount_due = amount_due
        existing.currency = currency
        existing.gbp_total = gbp_total
        existing.status = status
        existing.source = 'xero_api'
        return 'updated'
    else:
        # Create new record
        new_inv = HistoricalInvoice(
            invoice_number=invoice_number,
            invoice_type=invoice_type,
            is_credit_note=False,  # Credit notes have different invoice numbers in Xero
            contact_name=inv.get('contact_name', ''),
            invoice_date=issue_date,
            due_date=due_date,
            total=total,
            tax_total=0,  # Not available in basic API response
            amount_paid=amount_paid,
            amount_due=amount_due,
            currency=currency,
            gbp_total=gbp_total,
            status=status,
            source='xero_api',
        )
        db.session.add(new_inv)
        return 'created'


def recalculate_monthly_snapshots(from_date, to_date):
    """
    Recalculate monthly cash snapshots for affected months.

    This ensures the snapshots stay accurate after new transactions are added.
    """
    from sqlalchemy import func, extract

    # Get all months between from_date and to_date
    current = date(from_date.year, from_date.month, 1)
    end = date(to_date.year, to_date.month, 1)

    while current <= end:
        # Calculate snapshot for this month
        month_start = current
        if current.month == 12:
            month_end = date(current.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)

        # Get totals for the month
        totals = db.session.query(
            func.sum(BankTransaction.debit_gbp).label('total_in'),
            func.sum(BankTransaction.credit_gbp).label('total_out'),
        ).filter(
            BankTransaction.transaction_date >= month_start,
            BankTransaction.transaction_date <= month_end
        ).first()

        total_in = float(totals.total_in or 0)
        total_out = float(totals.total_out or 0)

        # Get wages and HMRC specifically
        wages = db.session.query(
            func.sum(BankTransaction.credit_gbp)
        ).filter(
            BankTransaction.transaction_date >= month_start,
            BankTransaction.transaction_date <= month_end,
            BankTransaction.description.ilike('%WAGES%')
        ).scalar() or 0

        hmrc = db.session.query(
            func.sum(BankTransaction.credit_gbp)
        ).filter(
            BankTransaction.transaction_date >= month_start,
            BankTransaction.transaction_date <= month_end,
            BankTransaction.description.ilike('%HMRC%')
        ).scalar() or 0

        # Upsert the snapshot
        existing = MonthlyCashSnapshot.query.filter_by(snapshot_date=month_end).first()

        if existing:
            existing.total_in = total_in
            existing.total_out = total_out
            existing.wages_paid = float(wages)
            existing.hmrc_paid = float(hmrc)
        else:
            snapshot = MonthlyCashSnapshot(
                snapshot_date=month_end,
                total_in=total_in,
                total_out=total_out,
                wages_paid=float(wages),
                hmrc_paid=float(hmrc),
            )
            db.session.add(snapshot)

        # Move to next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    db.session.commit()


def sync_all_from_xero(xero_client, days_back=90):
    """
    Sync all historical data from Xero API.

    This is the main entry point for the sync process.

    Args:
        xero_client: Authenticated Xero client
        days_back: Number of days to fetch (default 90)

    Returns:
        dict: Combined statistics from all sync operations
    """
    results = {
        'bank_transactions': {},
        'invoices': {},
        'success': True,
        'errors': [],
    }

    try:
        # Sync bank transactions
        results['bank_transactions'] = sync_bank_transactions_from_xero(xero_client, days_back)

        # Sync invoices
        results['invoices'] = sync_invoices_from_xero(xero_client, days_back)

        # Collect any errors
        if results['bank_transactions'].get('errors'):
            results['errors'].extend(results['bank_transactions']['errors'])
        if results['invoices'].get('errors'):
            results['errors'].extend(results['invoices']['errors'])

        if results['errors']:
            results['success'] = False

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))

    return results
