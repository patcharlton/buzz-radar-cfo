"""
File Upload endpoints for importing historical data.

Supports:
- Excel bank transaction exports from Xero
- CSV invoice/bill exports (legacy)
"""
import io
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from calendar import monthrange

from flask import Blueprint, jsonify, request
import pandas as pd

from database import db, HistoricalInvoice, HistoricalLineItem, BankTransaction, MonthlyCashSnapshot

upload_bp = Blueprint('upload', __name__)

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def parse_decimal(value):
    """Parse value to Decimal, handling empty strings and various formats."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return Decimal('0')
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if not str(value).strip():
        return Decimal('0')
    try:
        cleaned = str(value).replace(',', '').strip()
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal('0')


def process_bank_transactions_excel(file_content):
    """
    Process Xero Account Transactions Excel export.

    Expected format:
    - Row 1-3: Headers (skip)
    - Row 4: Column headers
    - Data rows contain either:
      - Account header (Source column empty, Date is account name)
      - Transaction row (Source has value like "Spend Money")
      - Summary rows ("Opening Balance", "Closing Balance", etc.) - skip

    Columns after cleanup:
    - Date, Source, Description, Reference, Currency
    - Debit (source), Credit (source), Debit (GBP), Credit (GBP), Running Balance

    Returns:
        dict with import statistics
    """
    import time
    start_time = time.time()

    stats = {
        'total_rows': 0,
        'transactions_created': 0,
        'transactions_skipped': 0,
        'accounts_found': [],
        'date_range': {'earliest': None, 'latest': None},
        'errors': [],
    }

    try:
        print(f"[IMPORT] Starting Excel file processing...")

        # Read Excel, skip first 3 rows (headers)
        df = pd.read_excel(io.BytesIO(file_content), skiprows=3)
        print(f"[IMPORT] Excel loaded: {len(df)} rows in {time.time() - start_time:.2f}s")

        # Rename columns to standard names
        expected_cols = ['Date', 'Source', 'Description', 'Reference', 'Currency',
                        'Debit_Source', 'Credit_Source', 'Debit_GBP', 'Credit_GBP', 'Running_Balance']

        if len(df.columns) >= 10:
            df.columns = expected_cols[:len(df.columns)]
        else:
            stats['errors'].append(f'Expected at least 10 columns, found {len(df.columns)}')
            return stats

        stats['total_rows'] = len(df)

        # Clear existing bank transactions before import
        print(f"[IMPORT] Clearing existing transactions...")
        BankTransaction.query.delete()
        db.session.flush()
        print(f"[IMPORT] Cleared in {time.time() - start_time:.2f}s")

        # Pre-process DataFrame for faster iteration using vectorized operations
        print(f"[IMPORT] Processing transactions...")

        transactions = []
        current_account = None
        earliest_date = None
        latest_date = None

        # Convert to records for faster iteration
        records = df.to_dict('records')

        for idx, row in enumerate(records):
            date_val = row.get('Date')
            source = row.get('Source')

            # Skip header row if present
            if date_val == 'Date':
                continue

            # Account header detection: Source is empty/NaN, Date is a string (account name)
            source_is_na = source is None or (isinstance(source, float) and pd.isna(source))
            date_is_valid = date_val is not None and not (isinstance(date_val, float) and pd.isna(date_val))

            if source_is_na and date_is_valid:
                if isinstance(date_val, str):
                    # Skip summary rows
                    if date_val in ['Opening Balance', 'Closing Balance', 'Movement'] or str(date_val).startswith('Total'):
                        continue
                    # This is an account header
                    current_account = date_val.strip()
                    if current_account not in stats['accounts_found']:
                        stats['accounts_found'].append(current_account)
                continue

            # Skip rows without a source type
            if source_is_na or source == 'Source':
                continue

            # Parse transaction date
            tx_date = None
            if isinstance(date_val, str):
                # Try various date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y']:
                    try:
                        tx_date = datetime.strptime(date_val.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
            elif isinstance(date_val, datetime):
                tx_date = date_val.date()
            elif isinstance(date_val, date):
                tx_date = date_val
            elif date_is_valid:
                try:
                    tx_date = pd.to_datetime(date_val).date()
                except Exception:
                    pass

            if not tx_date:
                stats['transactions_skipped'] += 1
                continue

            if not current_account:
                stats['transactions_skipped'] += 1
                continue

            # Parse amounts
            debit_gbp = parse_decimal(row.get('Debit_GBP'))
            credit_gbp = parse_decimal(row.get('Credit_GBP'))

            # Get description and reference
            desc = row.get('Description')
            ref = row.get('Reference')
            curr = row.get('Currency')

            # Create transaction
            transaction = BankTransaction(
                transaction_date=tx_date,
                bank_account=current_account,
                source_type=str(source).strip(),
                description=str(desc).strip() if desc is not None and not (isinstance(desc, float) and pd.isna(desc)) else None,
                reference=str(ref).strip() if ref is not None and not (isinstance(ref, float) and pd.isna(ref)) else None,
                currency=str(curr).strip() if curr is not None and not (isinstance(curr, float) and pd.isna(curr)) else 'GBP',
                debit_gbp=debit_gbp,
                credit_gbp=credit_gbp,
            )
            transactions.append(transaction)

            # Track date range
            if earliest_date is None or tx_date < earliest_date:
                earliest_date = tx_date
            if latest_date is None or tx_date > latest_date:
                latest_date = tx_date

        print(f"[IMPORT] Processed {len(transactions)} transactions in {time.time() - start_time:.2f}s")

        # Bulk insert transactions in batches for better performance
        print(f"[IMPORT] Inserting transactions into database...")
        batch_size = 500
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            db.session.bulk_save_objects(batch)
            if (i + batch_size) % 1000 == 0:
                print(f"[IMPORT] Inserted {min(i + batch_size, len(transactions))}/{len(transactions)} transactions...")

        db.session.commit()
        print(f"[IMPORT] Database commit complete in {time.time() - start_time:.2f}s")

        stats['transactions_created'] = len(transactions)
        stats['date_range']['earliest'] = earliest_date
        stats['date_range']['latest'] = latest_date

        # Convert dates to strings for JSON
        if stats['date_range']['earliest']:
            stats['date_range']['earliest'] = stats['date_range']['earliest'].isoformat()
        if stats['date_range']['latest']:
            stats['date_range']['latest'] = stats['date_range']['latest'].isoformat()

        print(f"[IMPORT] Complete! {stats['transactions_created']} transactions imported in {time.time() - start_time:.2f}s")

    except Exception as e:
        db.session.rollback()
        print(f"[IMPORT] ERROR: {str(e)}")
        stats['errors'].append(f'Failed to process Excel file: {str(e)}')

    return stats


def calculate_monthly_cash_snapshots():
    """
    Calculate monthly cash snapshots from bank transactions.

    For each month with transactions:
    - Sum all debit_gbp (money in)
    - Sum all credit_gbp (money out)
    - Calculate running balance from start
    - Extract WAGES and HMRC totals

    Returns:
        dict with calculation stats
    """
    from sqlalchemy import func, extract

    stats = {
        'months_calculated': 0,
        'errors': [],
    }

    try:
        # Clear existing snapshots
        MonthlyCashSnapshot.query.delete()
        db.session.flush()

        # Get date range from transactions
        date_range = db.session.query(
            func.min(BankTransaction.transaction_date),
            func.max(BankTransaction.transaction_date)
        ).first()

        if not date_range[0] or not date_range[1]:
            stats['errors'].append('No transactions found')
            return stats

        start_date = date_range[0]
        end_date = date_range[1]

        # Initialize running balance (assume 0 at start, or calculate from Opening Balance if available)
        running_balance = Decimal('0')

        # Iterate through each month
        current_year = start_date.year
        current_month = start_date.month

        while date(current_year, current_month, 1) <= end_date:
            # Get last day of month
            last_day = monthrange(current_year, current_month)[1]
            month_start = date(current_year, current_month, 1)
            month_end = date(current_year, current_month, last_day)

            # Sum debits and credits for the month
            totals = db.session.query(
                func.coalesce(func.sum(BankTransaction.debit_gbp), 0).label('total_in'),
                func.coalesce(func.sum(BankTransaction.credit_gbp), 0).label('total_out')
            ).filter(
                BankTransaction.transaction_date >= month_start,
                BankTransaction.transaction_date <= month_end
            ).first()

            total_in = Decimal(str(totals.total_in))
            total_out = Decimal(str(totals.total_out))

            # Get WAGES payments (credit = money out, description = 'WAGES')
            wages_result = db.session.query(
                func.coalesce(func.sum(BankTransaction.credit_gbp), 0)
            ).filter(
                BankTransaction.transaction_date >= month_start,
                BankTransaction.transaction_date <= month_end,
                BankTransaction.description == 'WAGES'
            ).scalar()
            wages_paid = Decimal(str(wages_result))

            # Get HMRC payments
            hmrc_result = db.session.query(
                func.coalesce(func.sum(BankTransaction.credit_gbp), 0)
            ).filter(
                BankTransaction.transaction_date >= month_start,
                BankTransaction.transaction_date <= month_end,
                BankTransaction.description == 'HMRC'
            ).scalar()
            hmrc_paid = Decimal(str(hmrc_result))

            # Calculate closing balance
            opening_balance = running_balance
            closing_balance = opening_balance + total_in - total_out

            # Only create snapshot if there's activity or a balance
            if total_in > 0 or total_out > 0 or opening_balance != 0:
                snapshot = MonthlyCashSnapshot(
                    snapshot_date=month_end,
                    opening_balance=opening_balance,
                    total_in=total_in,
                    total_out=total_out,
                    closing_balance=closing_balance,
                    wages_paid=wages_paid,
                    hmrc_paid=hmrc_paid,
                )
                db.session.add(snapshot)
                stats['months_calculated'] += 1

            # Update running balance for next month
            running_balance = closing_balance

            # Move to next month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        stats['errors'].append(f'Failed to calculate snapshots: {str(e)}')

    return stats


@upload_bp.route('/api/upload/bank-transactions', methods=['POST'])
def upload_bank_transactions():
    """
    Upload an Excel file with bank transactions.

    Form data:
        file: The Excel file (.xlsx)
    """
    import time
    request_start = time.time()
    print(f"[UPLOAD] Bank transactions upload request received")

    try:
        if 'file' not in request.files:
            print(f"[UPLOAD] ERROR: No file in request")
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        print(f"[UPLOAD] File received: {file.filename}")

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'error': 'File must be an Excel file (.xlsx or .xls)'
            }), 400

        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        print(f"[UPLOAD] File size: {size / 1024:.1f} KB")

        if size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400

        # Read file content
        content = file.read()
        print(f"[UPLOAD] File content read in {time.time() - request_start:.2f}s")

        # Process the Excel file
        import_stats = process_bank_transactions_excel(content)

        if import_stats['errors']:
            print(f"[UPLOAD] Import failed with errors: {import_stats['errors']}")
            return jsonify({
                'success': False,
                'error': import_stats['errors'][0],
                'stats': import_stats
            }), 400

        # Calculate monthly snapshots
        print(f"[UPLOAD] Calculating monthly snapshots...")
        snapshot_stats = calculate_monthly_cash_snapshots()
        print(f"[UPLOAD] Snapshots calculated in {time.time() - request_start:.2f}s")

        # Get total counts
        transaction_count = BankTransaction.query.count()
        snapshot_count = MonthlyCashSnapshot.query.count()

        print(f"[UPLOAD] COMPLETE! Total time: {time.time() - request_start:.2f}s")
        print(f"[UPLOAD] Stats: {transaction_count} transactions, {snapshot_count} snapshots")

        return jsonify({
            'success': True,
            'stats': {
                **import_stats,
                'snapshots_calculated': snapshot_stats['months_calculated'],
            },
            'totals': {
                'transactions': transaction_count,
                'monthly_snapshots': snapshot_count,
            },
            'message': f"Imported {import_stats['transactions_created']} transactions from {len(import_stats['accounts_found'])} accounts, calculated {snapshot_stats['months_calculated']} monthly snapshots"
        })

    except Exception as e:
        print(f"[UPLOAD] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upload_bp.route('/api/upload/bank-transactions/preview', methods=['POST'])
def preview_bank_transactions():
    """
    Preview an Excel file with bank transactions without importing.
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'error': 'File must be an Excel file (.xlsx or .xls)'
            }), 400

        # Read file content
        content = file.read()
        df = pd.read_excel(io.BytesIO(content), skiprows=3)

        # Rename columns
        expected_cols = ['Date', 'Source', 'Description', 'Reference', 'Currency',
                        'Debit_Source', 'Credit_Source', 'Debit_GBP', 'Credit_GBP', 'Running_Balance']

        if len(df.columns) >= 10:
            df.columns = expected_cols[:len(df.columns)]

        # Count transactions (rows with Source value)
        transaction_rows = df[df['Source'].notna() & (df['Source'] != 'Source')]

        # Find accounts
        accounts = []
        for idx, row in df.iterrows():
            date_val = row.get('Date')
            source = row.get('Source')
            if pd.isna(source) and pd.notna(date_val) and isinstance(date_val, str):
                if date_val not in ['Opening Balance', 'Closing Balance', 'Movement', 'Date'] and not date_val.startswith('Total'):
                    accounts.append(date_val)

        # Get date range
        dates = []
        for idx, row in df.iterrows():
            date_val = row.get('Date')
            source = row.get('Source')
            if pd.notna(source) and source != 'Source':
                try:
                    if isinstance(date_val, (datetime, date)):
                        dates.append(date_val if isinstance(date_val, date) else date_val.date())
                    elif isinstance(date_val, str):
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y']:
                            try:
                                dates.append(datetime.strptime(date_val, fmt).date())
                                break
                            except ValueError:
                                continue
                except Exception:
                    pass

        date_range = None
        if dates:
            date_range = {
                'earliest': min(dates).isoformat(),
                'latest': max(dates).isoformat(),
            }

        # Sample transactions
        sample_rows = []
        count = 0
        for idx, row in df.iterrows():
            if pd.notna(row.get('Source')) and row.get('Source') != 'Source' and count < 5:
                sample_rows.append({
                    'date': str(row.get('Date', ''))[:10],
                    'source': row.get('Source', ''),
                    'description': str(row.get('Description', ''))[:50] if pd.notna(row.get('Description')) else '',
                    'debit_gbp': float(row.get('Debit_GBP', 0)) if pd.notna(row.get('Debit_GBP')) else 0,
                    'credit_gbp': float(row.get('Credit_GBP', 0)) if pd.notna(row.get('Credit_GBP')) else 0,
                })
                count += 1

        return jsonify({
            'success': True,
            'preview': {
                'total_rows': len(df),
                'transaction_rows': len(transaction_rows),
                'accounts': accounts,
                'date_range': date_range,
                'sample_rows': sample_rows,
                'columns': list(df.columns),
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upload_bp.route('/api/upload/bank-transactions/stats', methods=['GET'])
def get_bank_transaction_stats():
    """Get statistics about imported bank transactions."""
    try:
        from sqlalchemy import func

        # Total transactions
        transaction_count = BankTransaction.query.count()

        # Date range
        date_range = db.session.query(
            func.min(BankTransaction.transaction_date),
            func.max(BankTransaction.transaction_date)
        ).first()

        # Totals
        totals = db.session.query(
            func.sum(BankTransaction.debit_gbp).label('total_in'),
            func.sum(BankTransaction.credit_gbp).label('total_out')
        ).first()

        # Accounts
        accounts = db.session.query(
            BankTransaction.bank_account,
            func.count(BankTransaction.id).label('count')
        ).group_by(BankTransaction.bank_account).all()

        # Source types
        source_types = db.session.query(
            BankTransaction.source_type,
            func.count(BankTransaction.id).label('count')
        ).group_by(BankTransaction.source_type).all()

        # Monthly snapshots
        snapshot_count = MonthlyCashSnapshot.query.count()

        return jsonify({
            'success': True,
            'stats': {
                'transaction_count': transaction_count,
                'snapshot_count': snapshot_count,
                'date_range': {
                    'earliest': date_range[0].isoformat() if date_range[0] else None,
                    'latest': date_range[1].isoformat() if date_range[1] else None,
                },
                'totals': {
                    'total_in': float(totals.total_in or 0),
                    'total_out': float(totals.total_out or 0),
                    'net': float((totals.total_in or 0) - (totals.total_out or 0)),
                },
                'accounts': [{'name': a.bank_account, 'count': a.count} for a in accounts],
                'source_types': [{'name': s.source_type, 'count': s.count} for s in source_types],
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upload_bp.route('/api/upload/clear-all', methods=['POST'])
def clear_all_historical_data():
    """
    Clear ALL historical data (invoices AND bank transactions).

    Body:
        confirm: Must be true to proceed
    """
    try:
        data = request.get_json() or {}

        if not data.get('confirm'):
            return jsonify({
                'success': False,
                'error': 'Must confirm deletion'
            }), 400

        deleted = {
            'invoices': 0,
            'line_items': 0,
            'bank_transactions': 0,
            'cash_snapshots': 0,
        }

        # Clear bank transactions and snapshots
        deleted['cash_snapshots'] = MonthlyCashSnapshot.query.delete()
        deleted['bank_transactions'] = BankTransaction.query.delete()

        # Clear invoices and line items
        deleted['line_items'] = HistoricalLineItem.query.delete()
        deleted['invoices'] = HistoricalInvoice.query.delete()

        db.session.commit()

        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': f"Cleared {deleted['bank_transactions']} transactions, {deleted['cash_snapshots']} snapshots, {deleted['invoices']} invoices"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upload_bp.route('/api/upload/recalculate-snapshots', methods=['POST'])
def recalculate_snapshots():
    """Recalculate monthly cash snapshots from existing bank transactions."""
    try:
        stats = calculate_monthly_cash_snapshots()

        return jsonify({
            'success': True,
            'stats': stats,
            'message': f"Calculated {stats['months_calculated']} monthly snapshots"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
