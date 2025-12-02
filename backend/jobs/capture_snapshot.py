#!/usr/bin/env python3
"""
Capture current financial snapshot.

Captures current cash position, receivables, payables, and MTD revenue/expenses/profit.
Designed to run via cron or Render scheduled job on the 1st of each month.

Usage:
    python -m backend.jobs.capture_snapshot
    python -m backend.jobs.capture_snapshot --dry-run
"""

import argparse
import sys
from datetime import date, datetime
from decimal import Decimal

# Add parent directory to path for imports when running as script
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app
from backend.database.db import db
from backend.database.models import MonthlySnapshot, AccountBalanceHistory
from backend.xero.client import XeroClient
from backend.xero.auth import XeroAuth


def capture_snapshot(dry_run: bool = False) -> dict:
    """
    Capture a snapshot of current financial state.

    For monthly snapshots, uses the first of the current month as the snapshot_date.
    Updates existing snapshot if one exists for this month (upsert logic).

    Args:
        dry_run: If True, don't actually save to database

    Returns:
        Dict with snapshot data and status
    """
    app = create_app()

    with app.app_context():
        # Check Xero connection
        xero_auth = XeroAuth()
        if not xero_auth.is_connected():
            print("ERROR: Not connected to Xero. Please connect first via the web interface.")
            return {'success': False, 'error': 'Not connected to Xero'}

        xero_client = XeroClient()
        today = date.today()

        # Use first of month as snapshot date
        snapshot_date = date(today.year, today.month, 1)
        print(f"Capturing snapshot for {snapshot_date.strftime('%B %Y')}...")

        try:
            # Get current data from Xero
            print("  Fetching bank summary...")
            bank_summary = xero_client.get_bank_summary()

            print("  Fetching receivables...")
            receivables = xero_client.get_receivables_summary()

            print("  Fetching payables...")
            payables = xero_client.get_payables_summary()

            print("  Fetching P&L...")
            pnl = xero_client.get_profit_and_loss()

            # Prepare snapshot data
            snapshot_data = {
                'snapshot_date': snapshot_date,
                'cash_position': Decimal(str(bank_summary.get('total_balance', 0))),
                'receivables_total': Decimal(str(receivables.get('total', 0))),
                'receivables_overdue': Decimal(str(receivables.get('overdue', 0))),
                'payables_total': Decimal(str(payables.get('total', 0))),
                'payables_overdue': Decimal(str(payables.get('overdue', 0))),
                'revenue': Decimal(str(pnl.get('revenue', 0))),
                'expenses': Decimal(str(pnl.get('expenses', 0))),
                'net_profit': Decimal(str(pnl.get('net_profit', 0))),
            }

            if dry_run:
                print(f"\n[DRY RUN] Would save snapshot:")
                print(f"  Cash Position: {snapshot_data['cash_position']:.2f}")
                print(f"  Receivables: {snapshot_data['receivables_total']:.2f} "
                      f"(overdue: {snapshot_data['receivables_overdue']:.2f})")
                print(f"  Payables: {snapshot_data['payables_total']:.2f} "
                      f"(overdue: {snapshot_data['payables_overdue']:.2f})")
                print(f"  Revenue: {snapshot_data['revenue']:.2f}")
                print(f"  Expenses: {snapshot_data['expenses']:.2f}")
                print(f"  Net Profit: {snapshot_data['net_profit']:.2f}")
                return {'success': True, 'dry_run': True, 'data': snapshot_data}

            # Check if snapshot exists for this month (upsert)
            existing = MonthlySnapshot.query.filter_by(snapshot_date=snapshot_date).first()

            if existing:
                print(f"  Updating existing snapshot for {snapshot_date.strftime('%B %Y')}...")
                for key, value in snapshot_data.items():
                    if key != 'snapshot_date':
                        setattr(existing, key, value)
                snapshot = existing
            else:
                print(f"  Creating new snapshot for {snapshot_date.strftime('%B %Y')}...")
                snapshot = MonthlySnapshot(**snapshot_data)
                db.session.add(snapshot)

            # Also capture individual account balances for detailed history
            print("  Saving account balances...")
            accounts = bank_summary.get('accounts', [])
            for account in accounts:
                account_name = account.get('name', 'Unknown')
                balance = Decimal(str(account.get('balance', 0)))

                # Use account name as ID since Xero bank summary doesn't include IDs
                account_id = account_name.replace(' ', '_').lower()

                # Check for existing balance record
                existing_balance = AccountBalanceHistory.query.filter_by(
                    snapshot_date=snapshot_date,
                    account_id=account_id
                ).first()

                if existing_balance:
                    existing_balance.balance = balance
                    existing_balance.account_name = account_name
                else:
                    new_balance = AccountBalanceHistory(
                        snapshot_date=snapshot_date,
                        account_id=account_id,
                        account_name=account_name,
                        balance=balance
                    )
                    db.session.add(new_balance)

            db.session.commit()

            print(f"\nSnapshot captured successfully!")
            print(f"  Cash Position: {snapshot_data['cash_position']:.2f}")
            print(f"  Receivables: {snapshot_data['receivables_total']:.2f} "
                  f"(overdue: {snapshot_data['receivables_overdue']:.2f})")
            print(f"  Payables: {snapshot_data['payables_total']:.2f} "
                  f"(overdue: {snapshot_data['payables_overdue']:.2f})")
            print(f"  Revenue: {snapshot_data['revenue']:.2f}")
            print(f"  Expenses: {snapshot_data['expenses']:.2f}")
            print(f"  Net Profit: {snapshot_data['net_profit']:.2f}")

            return {'success': True, 'data': snapshot.to_dict()}

        except Exception as e:
            print(f"ERROR: Failed to capture snapshot: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(
        description='Capture current financial snapshot'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Dry run - show what would be captured without saving'
    )

    args = parser.parse_args()
    result = capture_snapshot(dry_run=args.dry_run)

    if not result.get('success'):
        sys.exit(1)


if __name__ == '__main__':
    main()
