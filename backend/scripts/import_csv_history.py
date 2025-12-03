"""
Import historical invoice data from Xero CSV exports.

Usage:
    python -m backend.scripts.import_csv_history \
        --bills backend/data/imports/bills_historical.csv \
        --invoices backend/data/imports/invoices_historical.csv

Features:
    - Parse UK date format (DD/MM/YYYY)
    - Handle multiple currencies (GBP, EUR, USD)
    - Group rows by InvoiceNumber to create invoice + line items
    - Handle credit notes (Type contains "credit note")
    - Skip duplicates (upsert on invoice_number + invoice_type)
    - Log import stats
"""

import argparse
import csv
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict

# Add parent to path for imports
sys.path.insert(0, '.')

from backend.app import create_app
from backend.database import db, HistoricalInvoice, HistoricalLineItem


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
        print(f"  Warning: Could not parse date: {date_str}")
        return None


def parse_decimal(value):
    """Parse string to Decimal, handling empty strings and commas."""
    if not value or not str(value).strip():
        return Decimal('0')
    try:
        # Remove commas and whitespace
        cleaned = str(value).replace(',', '').strip()
        return Decimal(cleaned)
    except InvalidOperation:
        print(f"  Warning: Could not parse decimal: {value}")
        return Decimal('0')


def determine_invoice_type(row_type):
    """
    Determine invoice type from Xero Type field.

    Returns: (invoice_type, is_credit_note)
    """
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
        print(f"  Warning: Unknown type '{row_type}', defaulting to receivable")
        return 'receivable', False


def group_rows_by_invoice(rows):
    """
    Group CSV rows by InvoiceNumber.

    Returns dict: {invoice_number: [rows]}
    """
    grouped = defaultdict(list)
    for row in rows:
        invoice_number = row.get('InvoiceNumber', '').strip()
        if invoice_number:
            grouped[invoice_number].append(row)
    return grouped


def calculate_gbp_total(total, currency):
    """Convert amount to GBP equivalent."""
    rate = CURRENCY_RATES.get(currency, Decimal('1.0'))
    return total * rate


def import_csv(filepath, default_type='receivable', dry_run=False):
    """
    Import a single CSV file.

    Args:
        filepath: Path to CSV file
        default_type: 'receivable' for sales invoices, 'payable' for bills
        dry_run: If True, don't commit changes

    Returns:
        dict with stats
    """
    stats = {
        'total_rows': 0,
        'invoices_created': 0,
        'invoices_updated': 0,
        'invoices_skipped': 0,
        'line_items_created': 0,
        'credit_notes': 0,
        'overpayments': 0,
        'errors': [],
    }

    print(f"\nReading {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            stats['total_rows'] = len(rows)
    except FileNotFoundError:
        stats['errors'].append(f"File not found: {filepath}")
        return stats
    except Exception as e:
        stats['errors'].append(f"Error reading file: {e}")
        return stats

    print(f"  Found {stats['total_rows']} rows")

    # Group rows by invoice number
    grouped = group_rows_by_invoice(rows)
    print(f"  Grouped into {len(grouped)} unique invoices")

    for invoice_number, invoice_rows in grouped.items():
        try:
            # Use first row for invoice-level data
            first_row = invoice_rows[0]

            # Determine type from row data
            row_type = first_row.get('Type', '')
            invoice_type, is_credit_note = determine_invoice_type(row_type)

            if is_credit_note:
                stats['credit_notes'] += 1
            if invoice_type == 'overpayment':
                stats['overpayments'] += 1

            # Parse invoice data
            invoice_date = parse_uk_date(first_row.get('InvoiceDate'))
            if not invoice_date:
                stats['errors'].append(f"No valid date for invoice {invoice_number}")
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

            # Calculate GBP equivalent
            gbp_total = calculate_gbp_total(total, currency)

            # Check for existing invoice (upsert)
            existing = HistoricalInvoice.query.filter_by(
                invoice_number=invoice_number,
                invoice_type=invoice_type
            ).first()

            if existing:
                # Update existing
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

                # Delete existing line items to replace
                HistoricalLineItem.query.filter_by(invoice_id=existing.id).delete()
                invoice = existing
                stats['invoices_updated'] += 1
            else:
                # Create new
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

            # Need to flush to get invoice ID for line items
            if not dry_run:
                db.session.flush()

            # Create line items from each row
            for row in invoice_rows:
                description = row.get('Description', '').strip()
                quantity = parse_decimal(row.get('Quantity', 1))
                unit_amount = parse_decimal(row.get('UnitAmount', 0))
                line_amount = parse_decimal(row.get('LineAmount', 0))
                account_code = row.get('AccountCode', '').strip()
                tax_type = row.get('TaxType', '').strip()

                if description or line_amount:
                    line_item = HistoricalLineItem(
                        invoice_id=invoice.id if not dry_run else 0,
                        description=description,
                        quantity=quantity,
                        unit_amount=unit_amount,
                        line_amount=line_amount,
                        account_code=account_code,
                        tax_type=tax_type,
                    )
                    if not dry_run:
                        db.session.add(line_item)
                    stats['line_items_created'] += 1

        except Exception as e:
            stats['errors'].append(f"Error processing invoice {invoice_number}: {e}")
            stats['invoices_skipped'] += 1

    if not dry_run:
        db.session.commit()
        print("  Committed to database")
    else:
        print("  DRY RUN - no changes committed")

    return stats


def print_stats(stats, label):
    """Print import statistics."""
    print(f"\n{'='*50}")
    print(f"Import Results: {label}")
    print(f"{'='*50}")
    print(f"  Total CSV rows:      {stats['total_rows']}")
    print(f"  Invoices created:    {stats['invoices_created']}")
    print(f"  Invoices updated:    {stats['invoices_updated']}")
    print(f"  Invoices skipped:    {stats['invoices_skipped']}")
    print(f"  Line items created:  {stats['line_items_created']}")
    print(f"  Credit notes:        {stats['credit_notes']}")
    print(f"  Overpayments:        {stats['overpayments']}")

    if stats['errors']:
        print(f"\n  Errors ({len(stats['errors'])}):")
        for err in stats['errors'][:10]:
            print(f"    - {err}")
        if len(stats['errors']) > 10:
            print(f"    ... and {len(stats['errors']) - 10} more")


def main():
    parser = argparse.ArgumentParser(
        description='Import historical invoice data from Xero CSV exports'
    )
    parser.add_argument(
        '--bills',
        help='Path to bills CSV file'
    )
    parser.add_argument(
        '--invoices',
        help='Path to sales invoices CSV file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse and validate without committing to database'
    )

    args = parser.parse_args()

    if not args.bills and not args.invoices:
        parser.error('At least one of --bills or --invoices is required')

    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        print("="*60)
        print("Historical Invoice CSV Import")
        print("="*60)

        if args.dry_run:
            print("\n*** DRY RUN MODE - No changes will be saved ***\n")

        total_stats = {
            'invoices_created': 0,
            'invoices_updated': 0,
            'line_items_created': 0,
        }

        # Import bills (payables)
        if args.bills:
            print("\n" + "-"*40)
            print("Importing Bills (Payables)")
            print("-"*40)
            stats = import_csv(args.bills, 'payable', args.dry_run)
            print_stats(stats, "Bills")
            total_stats['invoices_created'] += stats['invoices_created']
            total_stats['invoices_updated'] += stats['invoices_updated']
            total_stats['line_items_created'] += stats['line_items_created']

        # Import invoices (receivables)
        if args.invoices:
            print("\n" + "-"*40)
            print("Importing Sales Invoices (Receivables)")
            print("-"*40)
            stats = import_csv(args.invoices, 'receivable', args.dry_run)
            print_stats(stats, "Sales Invoices")
            total_stats['invoices_created'] += stats['invoices_created']
            total_stats['invoices_updated'] += stats['invoices_updated']
            total_stats['line_items_created'] += stats['line_items_created']

        # Print totals
        print("\n" + "="*60)
        print("TOTAL IMPORT SUMMARY")
        print("="*60)
        print(f"  Total invoices created:    {total_stats['invoices_created']}")
        print(f"  Total invoices updated:    {total_stats['invoices_updated']}")
        print(f"  Total line items created:  {total_stats['line_items_created']}")

        # Verify counts
        if not args.dry_run:
            receivable_count = HistoricalInvoice.query.filter_by(invoice_type='receivable').count()
            payable_count = HistoricalInvoice.query.filter_by(invoice_type='payable').count()
            line_count = HistoricalLineItem.query.count()

            print("\n  Database counts:")
            print(f"    - Receivables in DB:     {receivable_count}")
            print(f"    - Payables in DB:        {payable_count}")
            print(f"    - Line items in DB:      {line_count}")

            # Date range check
            from sqlalchemy import func
            earliest = db.session.query(func.min(HistoricalInvoice.invoice_date)).scalar()
            latest = db.session.query(func.max(HistoricalInvoice.invoice_date)).scalar()
            print(f"\n  Date range: {earliest} to {latest}")


if __name__ == '__main__':
    main()
