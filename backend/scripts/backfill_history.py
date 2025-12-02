#!/usr/bin/env python3
"""
Backfill historical financial data from Xero.

Pulls P&L reports from Xero for the last 60 months (5 years) and populates
the monthly_snapshots table.

Usage:
    python -m backend.scripts.backfill_history
    python -m backend.scripts.backfill_history --months 24
    python -m backend.scripts.backfill_history --dry-run
"""

import argparse
import sys
import time
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add parent directory to path for imports when running as script
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app
from backend.database.db import db
from backend.database.models import MonthlySnapshot
from backend.xero.client import XeroClient
from backend.xero.auth import XeroAuth


# Xero API rate limit: 60 calls per minute
RATE_LIMIT_CALLS = 60
RATE_LIMIT_WINDOW = 60  # seconds
DELAY_BETWEEN_CALLS = 1.1  # seconds (slightly over 1 to be safe)


def get_month_boundaries(year: int, month: int) -> tuple[date, date]:
    """Get the first and last day of a given month."""
    first_day = date(year, month, 1)

    # Last day of month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    return first_day, last_day


def generate_month_list(num_months: int) -> list[tuple[int, int]]:
    """Generate a list of (year, month) tuples going back num_months from today."""
    today = date.today()
    months = []

    for i in range(num_months):
        # Go back i months from current month
        year = today.year
        month = today.month - i

        while month <= 0:
            month += 12
            year -= 1

        months.append((year, month))

    return months


def backfill_month(xero_client: XeroClient, year: int, month: int, dry_run: bool = False) -> dict:
    """
    Backfill data for a single month.

    Returns a dict with the snapshot data or None if failed.
    """
    first_day, last_day = get_month_boundaries(year, month)
    month_str = first_day.strftime('%B %Y')

    print(f"  Processing {month_str}...")

    # Check if already exists
    existing = MonthlySnapshot.query.filter_by(snapshot_date=first_day).first()
    if existing:
        print(f"    Skipping {month_str} - already exists")
        return {'status': 'skipped', 'month': month_str}

    try:
        # Get P&L for this month
        pnl = xero_client.get_profit_and_loss(from_date=first_day, to_date=last_day)

        snapshot_data = {
            'snapshot_date': first_day,
            'revenue': Decimal(str(pnl.get('revenue', 0))),
            'expenses': Decimal(str(pnl.get('expenses', 0))),
            'net_profit': Decimal(str(pnl.get('net_profit', 0))),
            # Cash position, receivables, payables not available historically from Xero
            'cash_position': None,
            'receivables_total': None,
            'receivables_overdue': None,
            'payables_total': None,
            'payables_overdue': None,
        }

        if dry_run:
            print(f"    [DRY RUN] Would save: Revenue={pnl.get('revenue', 0):.2f}, "
                  f"Expenses={pnl.get('expenses', 0):.2f}, "
                  f"Net Profit={pnl.get('net_profit', 0):.2f}")
            return {'status': 'dry_run', 'month': month_str, 'data': snapshot_data}

        # Create and save snapshot
        snapshot = MonthlySnapshot(**snapshot_data)
        db.session.add(snapshot)
        db.session.commit()

        print(f"    Saved: Revenue={pnl.get('revenue', 0):.2f}, "
              f"Expenses={pnl.get('expenses', 0):.2f}, "
              f"Net Profit={pnl.get('net_profit', 0):.2f}")

        return {'status': 'success', 'month': month_str, 'data': snapshot_data}

    except Exception as e:
        print(f"    Error processing {month_str}: {str(e)}")
        db.session.rollback()
        return {'status': 'error', 'month': month_str, 'error': str(e)}


def run_backfill(num_months: int = 60, dry_run: bool = False) -> dict:
    """
    Run the full backfill process.

    Args:
        num_months: Number of months to backfill (default 60 = 5 years)
        dry_run: If True, don't actually save to database

    Returns:
        Summary dict with success/failure counts
    """
    app = create_app()

    with app.app_context():
        # Check Xero connection
        xero_auth = XeroAuth()
        if not xero_auth.is_connected():
            print("ERROR: Not connected to Xero. Please connect first via the web interface.")
            return {'error': 'Not connected to Xero'}

        print(f"\nStarting backfill for {num_months} months...")
        if dry_run:
            print("DRY RUN MODE - no data will be saved\n")

        xero_client = XeroClient()
        months = generate_month_list(num_months)

        results = {
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'dry_run': 0,
            'details': []
        }

        for i, (year, month) in enumerate(months):
            result = backfill_month(xero_client, year, month, dry_run)
            results['details'].append(result)

            if result['status'] == 'success':
                results['success'] += 1
            elif result['status'] == 'skipped':
                results['skipped'] += 1
            elif result['status'] == 'dry_run':
                results['dry_run'] += 1
            else:
                results['errors'] += 1

            # Rate limiting - wait between API calls
            if i < len(months) - 1 and result['status'] not in ('skipped',):
                time.sleep(DELAY_BETWEEN_CALLS)

        print(f"\nBackfill complete!")
        print(f"  Success: {results['success']}")
        print(f"  Skipped (already exists): {results['skipped']}")
        print(f"  Errors: {results['errors']}")
        if dry_run:
            print(f"  Dry run: {results['dry_run']}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description='Backfill historical financial data from Xero'
    )
    parser.add_argument(
        '--months', '-m',
        type=int,
        default=60,
        help='Number of months to backfill (default: 60 = 5 years)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Dry run - show what would be done without saving'
    )

    args = parser.parse_args()

    run_backfill(num_months=args.months, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
