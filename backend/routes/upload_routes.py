"""
CSV Upload endpoints for importing historical data.

Allows direct upload of Xero CSV exports through the web UI.
"""
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict

from flask import Blueprint, jsonify, request

from database import db, HistoricalInvoice, HistoricalLineItem

upload_bp = Blueprint('upload', __name__)

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Currency conversion rates to GBP (approximate historical rates)
CURRENCY_RATES = {
    'GBP': Decimal('1.0'),
    'EUR': Decimal('0.85'),
    'USD': Decimal('0.79'),
}


def parse_uk_date(date_str):
    """Parse UK date format (DD/MM/YYYY) to date object."""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
    except ValueError:
        # Try alternative formats
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None


def parse_decimal(value):
    """Parse string to Decimal, handling empty strings and commas."""
    if not value or not str(value).strip():
        return Decimal('0')
    try:
        cleaned = str(value).replace(',', '').strip()
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal('0')


def determine_invoice_type(row_type):
    """Determine invoice type from Xero Type field."""
    row_type = (row_type or '').lower().strip()

    if 'bill credit note' in row_type:
        return 'payable', True
    elif 'sales credit note' in row_type:
        return 'receivable', True
    elif 'sales overpayment' in row_type:
        return 'overpayment', False
    elif 'bill' in row_type:
        return 'payable', False
    elif 'sales invoice' in row_type or 'invoice' in row_type:
        return 'receivable', False
    else:
        return 'receivable', False


def calculate_gbp_total(total, currency):
    """Convert amount to GBP equivalent."""
    rate = CURRENCY_RATES.get(currency, Decimal('1.0'))
    return total * rate


def process_csv_content(content, default_type='receivable'):
    """
    Process CSV content and import into database.

    Args:
        content: CSV file content as string
        default_type: 'receivable' or 'payable'

    Returns:
        dict with import statistics
    """
    stats = {
        'total_rows': 0,
        'invoices_created': 0,
        'invoices_updated': 0,
        'invoices_skipped': 0,
        'line_items_created': 0,
        'credit_notes': 0,
        'errors': [],
    }

    try:
        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        stats['total_rows'] = len(rows)

        if not rows:
            stats['errors'].append('CSV file is empty')
            return stats

        # Check for required columns
        required_cols = ['InvoiceNumber', 'InvoiceDate']
        first_row = rows[0]
        missing_cols = [col for col in required_cols if col not in first_row]
        if missing_cols:
            stats['errors'].append(f'Missing required columns: {", ".join(missing_cols)}')
            return stats

    except Exception as e:
        stats['errors'].append(f'Failed to parse CSV: {str(e)}')
        return stats

    # Group rows by invoice number
    grouped = defaultdict(list)
    for row in rows:
        invoice_number = row.get('InvoiceNumber', '').strip()
        if invoice_number:
            grouped[invoice_number].append(row)

    # Process each invoice
    for invoice_number, invoice_rows in grouped.items():
        try:
            first_row = invoice_rows[0]

            # Determine type from row data
            row_type = first_row.get('Type', '')
            invoice_type, is_credit_note = determine_invoice_type(row_type)

            if is_credit_note:
                stats['credit_notes'] += 1

            # Parse invoice data
            invoice_date = parse_uk_date(first_row.get('InvoiceDate'))
            if not invoice_date:
                stats['errors'].append(f'No valid date for invoice {invoice_number}')
                stats['invoices_skipped'] += 1
                continue

            due_date = parse_uk_date(first_row.get('DueDate'))
            total = parse_decimal(first_row.get('Total', 0))
            tax_total = parse_decimal(first_row.get('TaxTotal', 0))
            amount_paid = parse_decimal(first_row.get('InvoiceAmountPaid', 0))
            amount_due = parse_decimal(first_row.get('InvoiceAmountDue', 0))
            currency = first_row.get('Currency', 'GBP').strip().upper()
            status = first_row.get('Status', '').strip()
            contact_name = first_row.get('ContactName', '').strip()

            gbp_total = calculate_gbp_total(total, currency)

            # Check for existing invoice (upsert)
            existing = HistoricalInvoice.query.filter_by(
                invoice_number=invoice_number,
                invoice_type=invoice_type
            ).first()

            if existing:
                existing.contact_name = contact_name
                existing.invoice_date = invoice_date
                existing.due_date = due_date
                existing.total = total
                existing.tax_total = tax_total
                existing.amount_paid = amount_paid
                existing.amount_due = amount_due
                existing.currency = currency
                existing.gbp_total = gbp_total
                existing.status = status
                existing.is_credit_note = is_credit_note

                # Delete existing line items
                HistoricalLineItem.query.filter_by(invoice_id=existing.id).delete()
                invoice = existing
                stats['invoices_updated'] += 1
            else:
                invoice = HistoricalInvoice(
                    invoice_number=invoice_number,
                    invoice_type=invoice_type,
                    is_credit_note=is_credit_note,
                    contact_name=contact_name,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    total=total,
                    tax_total=tax_total,
                    amount_paid=amount_paid,
                    amount_due=amount_due,
                    currency=currency,
                    gbp_total=gbp_total,
                    status=status,
                    source='csv_import',
                )
                db.session.add(invoice)
                stats['invoices_created'] += 1

            db.session.flush()

            # Create line items
            for row in invoice_rows:
                description = row.get('Description', '').strip()
                quantity = parse_decimal(row.get('Quantity', 1))
                unit_amount = parse_decimal(row.get('UnitAmount', 0))
                line_amount = parse_decimal(row.get('LineAmount', 0))
                account_code = row.get('AccountCode', '').strip()
                tax_type = row.get('TaxType', '').strip()

                if description or line_amount:
                    line_item = HistoricalLineItem(
                        invoice_id=invoice.id,
                        description=description,
                        quantity=quantity,
                        unit_amount=unit_amount,
                        line_amount=line_amount,
                        account_code=account_code,
                        tax_type=tax_type,
                    )
                    db.session.add(line_item)
                    stats['line_items_created'] += 1

        except Exception as e:
            stats['errors'].append(f'Error processing invoice {invoice_number}: {str(e)}')
            stats['invoices_skipped'] += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        stats['errors'].append(f'Database error: {str(e)}')

    return stats


@upload_bp.route('/api/upload/csv', methods=['POST'])
def upload_csv():
    """
    Upload a CSV file for import.

    Form data:
        file: The CSV file
        type: 'invoices' or 'bills' (determines default invoice type)
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not file.filename.lower().endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'File must be a CSV'
            }), 400

        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Seek back to start

        if size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400

        # Read file content
        try:
            content = file.read().decode('utf-8-sig')  # Handle BOM
        except UnicodeDecodeError:
            try:
                file.seek(0)
                content = file.read().decode('latin-1')
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to read file: {str(e)}'
                }), 400

        # Get import type
        import_type = request.form.get('type', 'invoices')
        default_type = 'receivable' if import_type == 'invoices' else 'payable'

        # Process the CSV
        stats = process_csv_content(content, default_type)

        # Get updated totals
        from sqlalchemy import func
        receivables_count = HistoricalInvoice.query.filter_by(invoice_type='receivable').count()
        payables_count = HistoricalInvoice.query.filter_by(invoice_type='payable').count()

        return jsonify({
            'success': True,
            'stats': stats,
            'totals': {
                'receivables': receivables_count,
                'payables': payables_count,
            },
            'message': f"Imported {stats['invoices_created']} new invoices, updated {stats['invoices_updated']}"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upload_bp.route('/api/upload/preview', methods=['POST'])
def preview_csv():
    """
    Preview a CSV file without importing.

    Returns sample rows and validation info.
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if not file.filename.lower().endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'File must be a CSV'
            }), 400

        # Read file content
        try:
            content = file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            file.seek(0)
            content = file.read().decode('latin-1')

        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        if not rows:
            return jsonify({
                'success': False,
                'error': 'CSV file is empty'
            }), 400

        # Get columns
        columns = list(rows[0].keys())

        # Check for required columns
        required_cols = ['InvoiceNumber', 'InvoiceDate', 'Total']
        missing_cols = [col for col in required_cols if col not in columns]

        # Count unique invoices
        invoice_numbers = set(row.get('InvoiceNumber', '') for row in rows)
        invoice_numbers.discard('')

        # Get date range
        dates = []
        for row in rows:
            d = parse_uk_date(row.get('InvoiceDate'))
            if d:
                dates.append(d)

        date_range = None
        if dates:
            date_range = {
                'earliest': min(dates).isoformat(),
                'latest': max(dates).isoformat(),
            }

        # Get sample rows (first 5)
        sample_rows = []
        for row in rows[:5]:
            sample_rows.append({
                'invoice_number': row.get('InvoiceNumber', ''),
                'contact': row.get('ContactName', ''),
                'date': row.get('InvoiceDate', ''),
                'total': row.get('Total', ''),
                'type': row.get('Type', ''),
            })

        return jsonify({
            'success': True,
            'preview': {
                'total_rows': len(rows),
                'unique_invoices': len(invoice_numbers),
                'columns': columns,
                'missing_columns': missing_cols,
                'date_range': date_range,
                'sample_rows': sample_rows,
                'is_valid': len(missing_cols) == 0,
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upload_bp.route('/api/upload/clear', methods=['POST'])
def clear_historical_data():
    """
    Clear all historical data (for re-importing).

    Body:
        type: 'all', 'receivables', or 'payables'
        confirm: Must be true to proceed
    """
    try:
        data = request.get_json() or {}

        if not data.get('confirm'):
            return jsonify({
                'success': False,
                'error': 'Must confirm deletion'
            }), 400

        clear_type = data.get('type', 'all')

        deleted_invoices = 0
        deleted_line_items = 0

        if clear_type in ['all', 'receivables']:
            # Get receivable invoice IDs
            invoice_ids = [inv.id for inv in HistoricalInvoice.query.filter_by(invoice_type='receivable').all()]
            if invoice_ids:
                deleted_line_items += HistoricalLineItem.query.filter(
                    HistoricalLineItem.invoice_id.in_(invoice_ids)
                ).delete(synchronize_session=False)
                deleted_invoices += HistoricalInvoice.query.filter_by(invoice_type='receivable').delete()

        if clear_type in ['all', 'payables']:
            invoice_ids = [inv.id for inv in HistoricalInvoice.query.filter_by(invoice_type='payable').all()]
            if invoice_ids:
                deleted_line_items += HistoricalLineItem.query.filter(
                    HistoricalLineItem.invoice_id.in_(invoice_ids)
                ).delete(synchronize_session=False)
                deleted_invoices += HistoricalInvoice.query.filter_by(invoice_type='payable').delete()

        db.session.commit()

        return jsonify({
            'success': True,
            'deleted': {
                'invoices': deleted_invoices,
                'line_items': deleted_line_items,
            },
            'message': f'Deleted {deleted_invoices} invoices and {deleted_line_items} line items'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upload_bp.route('/api/upload/dedupe', methods=['POST'])
def dedupe_historical_data():
    """
    Remove duplicate invoices, keeping only the most recent version.

    Duplicates are identified by invoice_number + invoice_type.
    """
    try:
        from sqlalchemy import func

        stats = {
            'duplicates_found': 0,
            'invoices_removed': 0,
            'line_items_removed': 0,
        }

        # Find duplicate invoice_number + invoice_type combinations
        duplicates = db.session.query(
            HistoricalInvoice.invoice_number,
            HistoricalInvoice.invoice_type,
            func.count(HistoricalInvoice.id).label('count')
        ).group_by(
            HistoricalInvoice.invoice_number,
            HistoricalInvoice.invoice_type
        ).having(
            func.count(HistoricalInvoice.id) > 1
        ).all()

        stats['duplicates_found'] = len(duplicates)

        for invoice_number, invoice_type, count in duplicates:
            # Get all invoices with this number/type, ordered by id (keep highest = most recent)
            invoices = HistoricalInvoice.query.filter_by(
                invoice_number=invoice_number,
                invoice_type=invoice_type
            ).order_by(HistoricalInvoice.id.desc()).all()

            # Keep the first one (highest id), delete the rest
            to_delete = invoices[1:]

            for inv in to_delete:
                # Delete line items first
                deleted_items = HistoricalLineItem.query.filter_by(
                    invoice_id=inv.id
                ).delete()
                stats['line_items_removed'] += deleted_items

                # Delete the invoice
                db.session.delete(inv)
                stats['invoices_removed'] += 1

        db.session.commit()

        # Get updated counts
        receivables_count = HistoricalInvoice.query.filter_by(invoice_type='receivable').count()
        payables_count = HistoricalInvoice.query.filter_by(invoice_type='payable').count()

        return jsonify({
            'success': True,
            'stats': stats,
            'totals': {
                'receivables': receivables_count,
                'payables': payables_count,
            },
            'message': f"Removed {stats['invoices_removed']} duplicate invoices"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
