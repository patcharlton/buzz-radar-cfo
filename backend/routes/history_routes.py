"""
History and metrics API routes.

Provides endpoints for historical financial data and calculated metrics.
"""

from flask import Blueprint, jsonify, request
from datetime import date, datetime
from decimal import Decimal

from database.db import db
from database.models import MonthlySnapshot, AccountBalanceHistory
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
    Calculate cash runway based on recent burn rate.

    Uses last 6 complete months of data to calculate average monthly burn.
    Burn = expenses - revenue (positive = losing money, negative = profitable)

    Returns:
        runway_months: Months of runway at current burn rate (null if cash flow positive)
        avg_monthly_burn: Average monthly burn rate
        current_cash: Current cash position
    """
    try:
        xero_client = XeroClient()

        # Get current cash position
        bank_summary = xero_client.get_bank_summary()
        current_cash = float(bank_summary.get('total_balance', 0))

        # Get last 6 months of snapshots for burn calculation
        snapshots = MonthlySnapshot.query.filter(
            MonthlySnapshot.revenue.isnot(None),
            MonthlySnapshot.expenses.isnot(None)
        ).order_by(
            MonthlySnapshot.snapshot_date.desc()
        ).limit(6).all()

        if not snapshots:
            # Fall back to live Xero data
            monthly_data = xero_client.get_monthly_expenses(num_months=6)
            months = monthly_data.get('months', [])
            complete_months = [m for m in months if not m.get('is_partial', False)]

            if complete_months:
                burns = [m['expenses'] - m['revenue'] for m in complete_months]
                avg_monthly_burn = sum(burns) / len(burns)
            else:
                avg_monthly_burn = 0
        else:
            burns = []
            for s in snapshots:
                expenses = float(s.expenses) if s.expenses else 0
                revenue = float(s.revenue) if s.revenue else 0
                burns.append(expenses - revenue)

            avg_monthly_burn = sum(burns) / len(burns) if burns else 0

        # Calculate runway
        if avg_monthly_burn <= 0:
            # Cash flow positive - infinite runway
            runway_months = None
            runway_status = 'positive_cash_flow'
        elif current_cash <= 0:
            runway_months = 0
            runway_status = 'no_cash'
        else:
            runway_months = current_cash / avg_monthly_burn
            runway_status = 'calculated'

        return jsonify({
            'success': True,
            'runway_months': round(runway_months, 1) if runway_months is not None else None,
            'avg_monthly_burn': round(avg_monthly_burn, 2),
            'current_cash': round(current_cash, 2),
            'runway_status': runway_status,
            'months_analyzed': len(snapshots) if snapshots else len(complete_months) if 'complete_months' in dir() else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/history/backfill', methods=['POST'])
@require_xero_connection
def trigger_backfill():
    """
    Trigger historical data backfill from Xero.

    This runs synchronously for now. For production, consider using
    a background task queue like Celery or RQ.

    Request body:
        months: Number of months to backfill (default 60)
        dry_run: If true, don't actually save (default false)
    """
    try:
        from scripts.backfill_history import run_backfill

        data = request.get_json() or {}
        months = data.get('months', 60)
        dry_run = data.get('dry_run', False)

        months = min(max(months, 1), 120)

        result = run_backfill(num_months=months, dry_run=dry_run)

        return jsonify({
            'success': True,
            'result': result
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
