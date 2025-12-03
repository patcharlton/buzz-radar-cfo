"""
History and metrics API routes.

Provides endpoints for historical financial data and calculated metrics.
"""

from flask import Blueprint, jsonify, request
from datetime import date, datetime
from decimal import Decimal

from database.db import db
from database.models import MonthlySnapshot, AccountBalanceHistory, BankTransaction, MonthlyCashSnapshot
from xero import XeroClient, XeroAuth

history_bp = Blueprint('history', __name__)
xero_auth = XeroAuth()


def require_xero_connection(f):
    """Decorator to ensure Xero connection before API calls."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not xero_auth.is_connected():
            return jsonify({'error': 'Not connected to Xero'}), 401
        return f(*args, **kwargs)
    return decorated


@history_bp.route('/api/history/snapshots')
def get_snapshots():
    """
    Get historical monthly snapshots.

    Query params:
        months: Number of months to return (default 60)

    Returns:
        List of monthly snapshots sorted by date descending
    """
    try:
        months = request.args.get('months', 60, type=int)
        months = min(max(months, 1), 120)  # Clamp between 1-120

        snapshots = MonthlySnapshot.query.order_by(
            MonthlySnapshot.snapshot_date.desc()
        ).limit(months).all()

        return jsonify({
            'success': True,
            'count': len(snapshots),
            'snapshots': [s.to_dict() for s in snapshots]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/cash')
def get_cash_history():
    """
    Get cash position trend.

    Query params:
        months: Number of months to return (default 12)

    Returns:
        Cash position history with dates
    """
    try:
        months = request.args.get('months', 12, type=int)
        months = min(max(months, 1), 120)

        snapshots = MonthlySnapshot.query.filter(
            MonthlySnapshot.cash_position.isnot(None)
        ).order_by(
            MonthlySnapshot.snapshot_date.desc()
        ).limit(months).all()

        # Reverse to get chronological order
        snapshots = list(reversed(snapshots))

        data = [{
            'date': s.snapshot_date.isoformat(),
            'month': s.snapshot_date.strftime('%b %Y'),
            'cash_position': float(s.cash_position) if s.cash_position else 0
        } for s in snapshots]

        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/revenue')
def get_revenue_history():
    """
    Get revenue history with MoM% and YoY% calculations.

    Query params:
        months: Number of months to return (default 12)

    Returns:
        Revenue history with growth rates
    """
    try:
        months = request.args.get('months', 12, type=int)
        months = min(max(months, 1), 120)

        # Get extra months for YoY calculation
        fetch_months = months + 12

        snapshots = MonthlySnapshot.query.filter(
            MonthlySnapshot.revenue.isnot(None)
        ).order_by(
            MonthlySnapshot.snapshot_date.desc()
        ).limit(fetch_months).all()

        # Create lookup by date
        snapshot_lookup = {s.snapshot_date: s for s in snapshots}

        # Process only the requested months
        recent_snapshots = list(reversed(snapshots[:months]))

        data = []
        for s in recent_snapshots:
            revenue = float(s.revenue) if s.revenue else 0

            # Calculate MoM%
            prev_month = date(
                s.snapshot_date.year if s.snapshot_date.month > 1 else s.snapshot_date.year - 1,
                s.snapshot_date.month - 1 if s.snapshot_date.month > 1 else 12,
                1
            )
            prev_snapshot = snapshot_lookup.get(prev_month)
            if prev_snapshot and prev_snapshot.revenue and float(prev_snapshot.revenue) > 0:
                mom_pct = ((revenue - float(prev_snapshot.revenue)) / float(prev_snapshot.revenue)) * 100
            else:
                mom_pct = None

            # Calculate YoY%
            prev_year = date(s.snapshot_date.year - 1, s.snapshot_date.month, 1)
            yoy_snapshot = snapshot_lookup.get(prev_year)
            if yoy_snapshot and yoy_snapshot.revenue and float(yoy_snapshot.revenue) > 0:
                yoy_pct = ((revenue - float(yoy_snapshot.revenue)) / float(yoy_snapshot.revenue)) * 100
            else:
                yoy_pct = None

            data.append({
                'date': s.snapshot_date.isoformat(),
                'month': s.snapshot_date.strftime('%b %Y'),
                'revenue': revenue,
                'expenses': float(s.expenses) if s.expenses else 0,
                'net_profit': float(s.net_profit) if s.net_profit else 0,
                'mom_pct': round(mom_pct, 1) if mom_pct is not None else None,
                'yoy_pct': round(yoy_pct, 1) if yoy_pct is not None else None,
            })

        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/metrics/runway')
@require_xero_connection
def get_runway():
    """
    Calculate cash runway based on P&L expense average.

    Uses get_monthly_expenses() to get accurate expense data from P&L reports,
    which includes ALL expenses: PAYE, salaries, direct debits, and vendor bills.

    Runway is calculated as: current_cash / avg_monthly_expenses
    This shows how long cash would last if revenue stopped completely.

    Returns:
        runway_months: Months cash would last at current expense rate
        avg_monthly_expenses: Average monthly expenses from P&L
        avg_monthly_revenue: Average monthly revenue
        current_cash: Current cash position
        is_profitable: True if revenue exceeds expenses
        calculation_basis: Description of calculation method
    """
    try:
        xero_client = XeroClient()

        # Get current cash position
        bank_summary = xero_client.get_bank_summary()
        current_cash = float(bank_summary.get('total_balance', 0))

        # Get 6-month P&L data - this includes ALL expenses (PAYE, salaries, etc.)
        monthly_data = xero_client.get_monthly_expenses(num_months=6)
        months = monthly_data.get('months', [])

        # Use only complete months (exclude current partial month)
        complete_months = [m for m in months if not m.get('is_partial', False)]
        months_analyzed = len(complete_months)

        if complete_months:
            # Use P&L average expenses - this is the accurate figure
            avg_monthly_expenses = monthly_data.get('average_monthly_expenses', 0)

            # Calculate average revenue
            avg_monthly_revenue = sum(m['revenue'] for m in complete_months) / len(complete_months)
            is_profitable = avg_monthly_revenue >= avg_monthly_expenses
        else:
            # No complete months - use current month data
            if months:
                avg_monthly_expenses = months[0].get('expenses', 0)
                avg_monthly_revenue = months[0].get('revenue', 0)
                is_profitable = avg_monthly_revenue >= avg_monthly_expenses
                months_analyzed = 1
            else:
                avg_monthly_expenses = 0
                avg_monthly_revenue = 0
                is_profitable = True
                months_analyzed = 0

        # Calculate runway based on TOTAL expenses (not net burn)
        # This answers: "How long would cash last if revenue stopped?"
        if avg_monthly_expenses <= 0:
            runway_months = None  # No expenses = infinite runway
        elif current_cash <= 0:
            runway_months = 0
        else:
            runway_months = current_cash / avg_monthly_expenses

        return jsonify({
            'success': True,
            'runway_months': round(runway_months, 1) if runway_months is not None else None,
            'avg_monthly_burn': round(avg_monthly_expenses, 2),
            'avg_monthly_revenue': round(avg_monthly_revenue, 2),
            'current_cash': round(current_cash, 2),
            'is_profitable': is_profitable,
            'calculation_basis': f'{months_analyzed}-month P&L average',
            'months_analyzed': months_analyzed
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/backfill', methods=['POST'])
@require_xero_connection
def trigger_backfill():
    """
    Trigger historical data backfill from Xero.

    Request body:
        months: Number of months to backfill (default 60)
        dry_run: If true, don't actually save (default false)
    """
    import time
    from datetime import timedelta

    try:
        data = request.get_json() or {}
        num_months = data.get('months', 60)
        dry_run = data.get('dry_run', False)
        num_months = min(max(num_months, 1), 120)

        xero_client = XeroClient()

        # Generate list of months to backfill
        today = date.today()
        months_list = []
        for i in range(num_months):
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1
            months_list.append((year, month))

        results = {
            'success': 0,
            'skipped': 0,
            'errors': 0,
        }

        for year, month in months_list:
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            # Check if already exists
            existing = MonthlySnapshot.query.filter_by(snapshot_date=first_day).first()
            if existing:
                results['skipped'] += 1
                continue

            try:
                # Get P&L for this month
                pnl = xero_client.get_profit_and_loss(from_date=first_day, to_date=last_day)

                if not dry_run:
                    snapshot = MonthlySnapshot(
                        snapshot_date=first_day,
                        revenue=Decimal(str(pnl.get('revenue', 0))),
                        expenses=Decimal(str(pnl.get('expenses', 0))),
                        net_profit=Decimal(str(pnl.get('net_profit', 0))),
                    )
                    db.session.add(snapshot)
                    db.session.commit()

                results['success'] += 1

                # Rate limiting - 1.1s between API calls
                time.sleep(1.1)

            except Exception as e:
                results['errors'] += 1
                db.session.rollback()

        return jsonify({
            'success': True,
            'result': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/snapshot', methods=['POST'])
@require_xero_connection
def trigger_snapshot():
    """
    Manually trigger a snapshot capture.

    Request body:
        dry_run: If true, don't actually save (default false)
    """
    try:
        from jobs.capture_snapshot import capture_snapshot

        data = request.get_json() or {}
        dry_run = data.get('dry_run', False)

        result = capture_snapshot(dry_run=dry_run)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/trends')
def get_trends():
    """
    Get combined trends for dashboard sparklines.

    Returns last 12 months of:
    - Cash position (where available)
    - Revenue
    - Receivables
    - Payables

    Useful for populating multiple sparklines in a single call.
    """
    try:
        months = request.args.get('months', 12, type=int)
        months = min(max(months, 1), 60)

        snapshots = MonthlySnapshot.query.order_by(
            MonthlySnapshot.snapshot_date.desc()
        ).limit(months).all()

        # Reverse to get chronological order
        snapshots = list(reversed(snapshots))

        # Build response
        cash_data = []
        revenue_data = []
        receivables_data = []
        payables_data = []

        for s in snapshots:
            month_label = s.snapshot_date.strftime('%b')

            if s.cash_position is not None:
                cash_data.append({
                    'month': month_label,
                    'value': float(s.cash_position)
                })

            if s.revenue is not None:
                revenue_data.append({
                    'month': month_label,
                    'value': float(s.revenue)
                })

            if s.receivables_total is not None:
                receivables_data.append({
                    'month': month_label,
                    'value': float(s.receivables_total)
                })

            if s.payables_total is not None:
                payables_data.append({
                    'month': month_label,
                    'value': float(s.payables_total)
                })

        # Calculate YoY comparison for the current/latest snapshot
        yoy_comparisons = {}
        if snapshots:
            latest = snapshots[-1]
            latest_date = latest.snapshot_date

            # Find same month last year
            try:
                prev_year_date = date(latest_date.year - 1, latest_date.month, 1)
                prev_year_snapshot = MonthlySnapshot.query.filter_by(
                    snapshot_date=prev_year_date
                ).first()

                if prev_year_snapshot:
                    def calc_yoy(current, previous):
                        if previous and float(previous) > 0 and current:
                            return round(((float(current) - float(previous)) / float(previous)) * 100, 1)
                        return None

                    yoy_comparisons = {
                        'cash_position': calc_yoy(latest.cash_position, prev_year_snapshot.cash_position),
                        'revenue': calc_yoy(latest.revenue, prev_year_snapshot.revenue),
                        'receivables': calc_yoy(latest.receivables_total, prev_year_snapshot.receivables_total),
                        'payables': calc_yoy(latest.payables_total, prev_year_snapshot.payables_total),
                        'comparison_month': prev_year_snapshot.snapshot_date.strftime('%b %Y')
                    }
            except Exception:
                pass

        return jsonify({
            'success': True,
            'trends': {
                'cash': cash_data,
                'revenue': revenue_data,
                'receivables': receivables_data,
                'payables': payables_data
            },
            'yoy_comparisons': yoy_comparisons,
            'latest_month': snapshots[-1].snapshot_date.strftime('%b %Y') if snapshots else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# BANK TRANSACTION HISTORY ENDPOINTS
# =============================================================================

@history_bp.route('/api/history/cash-position')
def get_cash_position_history():
    """
    Get monthly cash position history from bank transactions.

    Query params:
        months: Number of months to return (default 60)

    Returns:
        Monthly cash flow data including opening/closing balances
    """
    try:
        months = request.args.get('months', 60, type=int)
        months = min(max(months, 1), 120)

        snapshots = MonthlyCashSnapshot.query.order_by(
            MonthlyCashSnapshot.snapshot_date.desc()
        ).limit(months).all()

        # Reverse to chronological order
        snapshots = list(reversed(snapshots))

        # Get date range
        if snapshots:
            earliest = snapshots[0].snapshot_date.strftime('%Y-%m')
            latest = snapshots[-1].snapshot_date.strftime('%Y-%m')
        else:
            earliest = None
            latest = None

        return jsonify({
            'success': True,
            'months': [s.to_dict() for s in snapshots],
            'earliest_month': earliest,
            'latest_month': latest,
            'count': len(snapshots)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/cash-trend')
def get_cash_trend():
    """
    Get simplified cash trend for sparklines.

    Query params:
        months: Number of months to return (default 12)

    Returns:
        Arrays of values and labels for easy charting
    """
    try:
        months = request.args.get('months', 12, type=int)
        months = min(max(months, 1), 60)

        snapshots = MonthlyCashSnapshot.query.order_by(
            MonthlyCashSnapshot.snapshot_date.desc()
        ).limit(months).all()

        # Reverse to chronological order
        snapshots = list(reversed(snapshots))

        values = [float(s.closing_balance or 0) for s in snapshots]
        labels = [s.snapshot_date.strftime('%b %y') for s in snapshots]

        # Calculate YoY change
        yoy_change = None
        if len(snapshots) >= 12:
            current = float(snapshots[-1].closing_balance or 0)
            year_ago = float(snapshots[-12].closing_balance or 0)
            if year_ago != 0:
                yoy_change = round(((current - year_ago) / abs(year_ago)) * 100, 1)

        return jsonify({
            'success': True,
            'values': values,
            'labels': labels,
            'yoy_change_percent': yoy_change,
            'latest_balance': values[-1] if values else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/payroll')
def get_payroll_history():
    """
    Get monthly payroll/PAYE cash payments.

    Query params:
        months: Number of months to return (default 12)

    Returns:
        Monthly payroll breakdown (wages + HMRC)
    """
    try:
        months = request.args.get('months', 12, type=int)
        months = min(max(months, 1), 60)

        snapshots = MonthlyCashSnapshot.query.order_by(
            MonthlyCashSnapshot.snapshot_date.desc()
        ).limit(months).all()

        # Reverse to chronological order
        snapshots = list(reversed(snapshots))

        # Build response
        payroll_data = []
        total_wages = 0
        total_hmrc = 0

        for s in snapshots:
            wages = float(s.wages_paid or 0)
            hmrc = float(s.hmrc_paid or 0)
            total_wages += wages
            total_hmrc += hmrc

            payroll_data.append({
                'month': s.snapshot_date.strftime('%Y-%m'),
                'month_label': s.snapshot_date.strftime('%b %Y'),
                'wages': wages,
                'hmrc': hmrc,
                'total_payroll': wages + hmrc
            })

        # Calculate average
        if snapshots:
            avg_monthly = (total_wages + total_hmrc) / len(snapshots)
        else:
            avg_monthly = 0

        return jsonify({
            'success': True,
            'months': payroll_data,
            'average_monthly': round(avg_monthly, 2),
            'total_wages': round(total_wages, 2),
            'total_hmrc': round(total_hmrc, 2),
            'count': len(snapshots)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/drill/bank-transactions')
def drill_bank_transactions():
    """
    Get bank transactions for drill-down view.

    Query params:
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        account: Filter by bank account name
        source_type: Filter by transaction type (Spend Money, etc.)
        search: Search in description field
        page: Page number (default 1)
        page_size: Results per page (default 50, max 100)

    Returns:
        Paginated transaction list with summary
    """
    from sqlalchemy import func

    try:
        # Parse params
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        account = request.args.get('account')
        source_type = request.args.get('source_type')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        # Build query
        query = BankTransaction.query

        if from_date_str:
            try:
                from_date = datetime.strptime(from_date_str[:10], '%Y-%m-%d').date()
                query = query.filter(BankTransaction.transaction_date >= from_date)
            except ValueError:
                pass

        if to_date_str:
            try:
                to_date = datetime.strptime(to_date_str[:10], '%Y-%m-%d').date()
                query = query.filter(BankTransaction.transaction_date <= to_date)
            except ValueError:
                pass

        if account:
            query = query.filter(BankTransaction.bank_account == account)

        if source_type:
            query = query.filter(BankTransaction.source_type == source_type)

        if search:
            query = query.filter(BankTransaction.description.ilike(f'%{search}%'))

        # Get totals before pagination
        totals_query = db.session.query(
            func.sum(BankTransaction.debit_gbp).label('total_in'),
            func.sum(BankTransaction.credit_gbp).label('total_out'),
            func.count(BankTransaction.id).label('count')
        )

        # Apply same filters
        if from_date_str:
            try:
                totals_query = totals_query.filter(BankTransaction.transaction_date >= from_date)
            except NameError:
                pass
        if to_date_str:
            try:
                totals_query = totals_query.filter(BankTransaction.transaction_date <= to_date)
            except NameError:
                pass
        if account:
            totals_query = totals_query.filter(BankTransaction.bank_account == account)
        if source_type:
            totals_query = totals_query.filter(BankTransaction.source_type == source_type)
        if search:
            totals_query = totals_query.filter(BankTransaction.description.ilike(f'%{search}%'))

        totals = totals_query.first()

        # Paginate
        total_count = query.count()
        offset = (page - 1) * page_size
        transactions = query.order_by(
            BankTransaction.transaction_date.desc()
        ).offset(offset).limit(page_size).all()

        return jsonify({
            'success': True,
            'transactions': [t.to_dict() for t in transactions],
            'summary': {
                'total_in': float(totals.total_in or 0),
                'total_out': float(totals.total_out or 0),
                'net_change': float((totals.total_in or 0) - (totals.total_out or 0)),
                'transaction_count': totals.count or 0
            },
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'has_more': offset + len(transactions) < total_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/drill/bank-transactions/accounts')
def get_bank_accounts():
    """Get list of bank accounts from imported transactions."""
    from sqlalchemy import func

    try:
        accounts = db.session.query(
            BankTransaction.bank_account,
            func.count(BankTransaction.id).label('count'),
            func.sum(BankTransaction.debit_gbp).label('total_in'),
            func.sum(BankTransaction.credit_gbp).label('total_out')
        ).group_by(BankTransaction.bank_account).all()

        return jsonify({
            'success': True,
            'accounts': [{
                'name': a.bank_account,
                'transaction_count': a.count,
                'total_in': float(a.total_in or 0),
                'total_out': float(a.total_out or 0)
            } for a in accounts]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/drill/bank-transactions/source-types')
def get_source_types():
    """Get list of transaction source types."""
    from sqlalchemy import func

    try:
        types = db.session.query(
            BankTransaction.source_type,
            func.count(BankTransaction.id).label('count')
        ).group_by(BankTransaction.source_type).order_by(
            func.count(BankTransaction.id).desc()
        ).all()

        return jsonify({
            'success': True,
            'source_types': [{
                'name': t.source_type,
                'count': t.count
            } for t in types]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/metrics/runway-historical')
def get_runway_historical():
    """
    Calculate cash runway based on actual historical cash burn.

    Uses bank transaction data to calculate average monthly cash flow,
    which is more accurate than P&L-based estimates.

    Returns:
        runway_months: Months cash would last at current burn rate
        avg_monthly_burn: Average monthly cash out
        is_profitable: True if avg cash in exceeds cash out
        calculation_basis: Description of calculation method
    """
    try:
        from sqlalchemy import func

        # Get last 6 complete months (excluding current month)
        today = date.today()
        current_month_start = date(today.year, today.month, 1)

        snapshots = MonthlyCashSnapshot.query.filter(
            MonthlyCashSnapshot.snapshot_date < current_month_start
        ).order_by(
            MonthlyCashSnapshot.snapshot_date.desc()
        ).limit(6).all()

        if len(snapshots) < 3:
            return jsonify({
                'success': True,
                'runway_months': None,
                'avg_monthly_burn': None,
                'is_profitable': None,
                'calculation_basis': 'Insufficient history (need at least 3 months)',
                'months_analyzed': len(snapshots)
            })

        # Calculate averages from historical data
        total_in = sum(float(s.total_in or 0) for s in snapshots)
        total_out = sum(float(s.total_out or 0) for s in snapshots)
        num_months = len(snapshots)

        avg_monthly_in = total_in / num_months
        avg_monthly_out = total_out / num_months
        avg_net_change = avg_monthly_in - avg_monthly_out

        # Get current cash position from Xero (if connected) or latest snapshot
        try:
            if xero_auth.is_connected():
                xero_client = XeroClient()
                bank_summary = xero_client.get_bank_summary()
                current_cash = float(bank_summary.get('total_balance', 0))
            else:
                # Use latest closing balance
                latest = MonthlyCashSnapshot.query.order_by(
                    MonthlyCashSnapshot.snapshot_date.desc()
                ).first()
                current_cash = float(latest.closing_balance) if latest else 0
        except Exception:
            latest = MonthlyCashSnapshot.query.order_by(
                MonthlyCashSnapshot.snapshot_date.desc()
            ).first()
            current_cash = float(latest.closing_balance) if latest else 0

        is_profitable = avg_net_change >= 0

        # Calculate runway based on expense rate
        if avg_monthly_out <= 0:
            runway_months = None  # No expenses
        elif current_cash <= 0:
            runway_months = 0
        else:
            # Runway = how long until cash runs out at current burn rate
            # If profitable, runway is technically infinite, but we still show
            # how long cash would last if revenue stopped
            runway_months = current_cash / avg_monthly_out

        return jsonify({
            'success': True,
            'runway_months': round(runway_months, 1) if runway_months is not None else None,
            'avg_monthly_burn': round(avg_monthly_out, 2),
            'avg_monthly_revenue': round(avg_monthly_in, 2),
            'avg_net_change': round(avg_net_change, 2),
            'current_cash': round(current_cash, 2),
            'is_profitable': is_profitable,
            'calculation_basis': f'{num_months}-month cash flow average',
            'months_analyzed': num_months
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
