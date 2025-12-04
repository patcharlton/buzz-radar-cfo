from flask import Blueprint, jsonify, request
from datetime import date, timedelta
from sqlalchemy import func

from xero import XeroClient, XeroAuth
from database.db import db
from database.models import BankTransaction
from ai.cache import cache_key, get_cached, set_cached
from context.loader import (
    load_all_context,
    load_pipeline,
    get_deals_by_stage,
    get_overdue_deals,
    get_deals_closing_this_month,
    calculate_weighted_pipeline,
    get_at_risk_clients,
    get_active_clients,
    get_critical_risks,
    get_current_metrics,
    get_q1_goals,
    get_transition_status,
)

# Dashboard cache TTL: 5 minutes (Xero data doesn't change frequently)
DASHBOARD_CACHE_TTL = 300

data_bp = Blueprint('data', __name__)
xero_client = XeroClient()
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


@data_bp.route('/api/dashboard')
@require_xero_connection
def dashboard():
    """Get all dashboard data in a single call."""
    try:
        # Check cache first
        cache_id = cache_key('dashboard')
        cached_result = get_cached(cache_id, cache_type='dashboard')
        if cached_result:
            return jsonify({**cached_result, 'cached': True})

        # Fetch fresh data
        data = xero_client.get_dashboard_data()

        # Cache the result
        set_cached(cache_id, data, DASHBOARD_CACHE_TTL, cache_type='dashboard')

        return jsonify({**data, 'cached': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/api/cash-position')
@require_xero_connection
def cash_position():
    """Get current cash position across all bank accounts."""
    try:
        data = xero_client.get_bank_summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/api/receivables')
@require_xero_connection
def receivables():
    """Get outstanding receivables (invoices owed to us)."""
    try:
        data = xero_client.get_receivables_summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/api/payables')
@require_xero_connection
def payables():
    """Get outstanding payables (bills we owe)."""
    try:
        data = xero_client.get_payables_summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/api/pnl')
@require_xero_connection
def profit_and_loss():
    """Get Profit & Loss summary for current month."""
    try:
        data = xero_client.get_profit_and_loss()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/api/sync', methods=['POST'])
@require_xero_connection
def sync():
    """Manually trigger a full data refresh from Xero."""
    try:
        # Force refresh by getting all dashboard data
        data = xero_client.get_dashboard_data()

        # Also sync historical data from Xero
        from services.history_sync import sync_all_from_xero
        history_sync_result = sync_all_from_xero(xero_client, days_back=90)

        return jsonify({
            'success': True,
            'message': 'Data synced successfully',
            'data': data,
            'history_sync': {
                'bank_transactions': {
                    'created': history_sync_result.get('bank_transactions', {}).get('created', 0),
                    'updated': history_sync_result.get('bank_transactions', {}).get('updated', 0),
                },
                'invoices': {
                    'created': history_sync_result.get('invoices', {}).get('created', 0),
                    'updated': history_sync_result.get('invoices', {}).get('updated', 0),
                },
            },
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/recurring-costs')
@require_xero_connection
def recurring_costs():
    """Get recurring costs analysis and future predictions."""
    try:
        from flask import request
        months = request.args.get('months', 6, type=int)
        months = min(max(months, 3), 12)  # Clamp between 3-12 months

        data = xero_client.get_recurring_costs_analysis(months=months)
        return jsonify({
            'success': True,
            **data,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# CONTEXT DATA ENDPOINTS (Pipeline, Clients, Risks, Metrics)
# =============================================================================

@data_bp.route('/api/context/pipeline')
def get_pipeline():
    """Get full sales pipeline data."""
    try:
        pipeline = load_pipeline()
        overdue = get_overdue_deals()
        closing_this_month = get_deals_closing_this_month()
        weighted = calculate_weighted_pipeline()

        return jsonify({
            'success': True,
            'pipeline': pipeline,
            'summary': {
                'total_deals': len(pipeline.get('deals', [])),
                'total_value': sum(d.get('deal_value', 0) for d in pipeline.get('deals', [])),
                'weighted_value': weighted,
                'overdue_count': len(overdue),
                'closing_this_month_count': len(closing_this_month),
            },
            'overdue_deals': overdue,
            'closing_this_month': closing_this_month,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/context/clients')
def get_clients():
    """Get client portfolio data."""
    try:
        context = load_all_context()
        clients_data = context.get('clients', {})
        at_risk = get_at_risk_clients()
        active = get_active_clients()

        return jsonify({
            'success': True,
            'clients': clients_data.get('clients', []),
            'summary': clients_data.get('summary', {}),
            'at_risk_clients': at_risk,
            'active_clients': active,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/context/risks')
def get_risks():
    """Get risk management data."""
    try:
        critical_risks = get_critical_risks()
        context = load_all_context()
        all_risks = context.get('risks', {}).get('risks', [])

        return jsonify({
            'success': True,
            'critical_risks': critical_risks,
            'all_risks': all_risks,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/context/metrics')
def get_metrics():
    """Get current business metrics."""
    try:
        metrics = get_current_metrics()
        context = load_all_context()
        all_metrics = context.get('metrics', {})

        return jsonify({
            'success': True,
            'current': metrics,
            'definitions': all_metrics,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/context/goals')
def get_goals():
    """Get strategic goals and milestones."""
    try:
        q1_goals = get_q1_goals()
        context = load_all_context()
        all_goals = context.get('goals', {})

        return jsonify({
            'success': True,
            'q1_2026': q1_goals,
            'all_goals': all_goals,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/context/transition')
def get_transition():
    """Get services-to-platform transition status."""
    try:
        transition = get_transition_status()

        return jsonify({
            'success': True,
            'transition': transition,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/context/summary')
def get_context_summary():
    """Get a comprehensive summary of all context data for the dashboard."""
    try:
        # Load all context
        context = load_all_context()
        pipeline = load_pipeline()
        overdue = get_overdue_deals()
        closing_this_month = get_deals_closing_this_month()
        weighted = calculate_weighted_pipeline()
        at_risk_clients = get_at_risk_clients()
        critical_risks = get_critical_risks()
        metrics = get_current_metrics()
        q1_goals = get_q1_goals()
        transition = get_transition_status()

        # Build summary
        deals = pipeline.get('deals', [])
        won_deals = [d for d in deals if d.get('stage') == 'Won']
        high_confidence = [d for d in deals if d.get('likelihood', 0) >= 8 and d.get('stage') != 'Won']

        return jsonify({
            'success': True,
            'pipeline_summary': {
                'total_value': sum(d.get('deal_value', 0) for d in deals),
                'weighted_value': weighted.get('weighted_total', 0),
                'deal_count': len(deals),
                'won_value': sum(d.get('deal_value', 0) for d in won_deals),
                'high_confidence_value': sum(d.get('deal_value', 0) for d in high_confidence),
                'overdue_deals': [{
                    'name': d.get('name'),
                    'client': d.get('client'),
                    'value': d.get('deal_value'),
                    'days_overdue': d.get('days_overdue'),
                    'decision_maker': d.get('decision_maker'),
                } for d in overdue],
                'closing_this_month': [{
                    'name': d.get('name'),
                    'client': d.get('client'),
                    'value': d.get('deal_value'),
                    'likelihood': d.get('likelihood'),
                    'expected_close': d.get('expected_close'),
                } for d in closing_this_month],
            },
            'client_summary': {
                'at_risk_count': len(at_risk_clients),
                'at_risk_value': sum(c.get('contract_value', 0) for c in at_risk_clients),
                'at_risk_clients': at_risk_clients,
            },
            'risk_summary': {
                'critical_count': len([r for r in critical_risks if r.get('severity') == 'Critical']),
                'high_count': len([r for r in critical_risks if r.get('severity') == 'High']),
                'top_risks': critical_risks[:3],
            },
            'financial_summary': {
                'annual_revenue': metrics.get('annual_revenue'),
                'gross_margin': metrics.get('gross_margin'),
                'net_margin': metrics.get('net_margin'),
                'yoy_growth': metrics.get('yoy_growth'),
            },
            'transition_summary': {
                'current_state': transition.get('current_state'),
                'revenue_mix': transition.get('revenue_mix', {}).get('current', {}),
                'target_2026': transition.get('revenue_mix', {}).get('target_end_2026', {}),
            },
            'q1_goals': q1_goals,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/api/metrics/cash-concentration')
def get_cash_concentration():
    """
    Calculate cash concentration risk based on revenue dependency on top clients.

    Analyzes receivable payments over the last 12 months to determine
    concentration risk from client dependency.

    Risk levels:
    - HIGH: Top 1 client > 40% of total
    - MEDIUM: Top 3 clients > 70% of total
    - LOW: Otherwise

    Returns:
        Client concentration data with risk assessment
    """
    try:
        # Get date range for last 12 months
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        # Query receivable payments from bank_transactions
        # Use 'Receivable Payment' which represents client invoice payments
        payments = db.session.query(
            BankTransaction.description,
            func.sum(BankTransaction.debit_gbp).label('total_amount')
        ).filter(
            BankTransaction.source_type == 'Receivable Payment',
            BankTransaction.transaction_date >= start_date,
            BankTransaction.transaction_date <= end_date,
            BankTransaction.debit_gbp > 0
        ).group_by(
            BankTransaction.description
        ).all()

        # Extract client names and aggregate by client
        client_totals = {}

        def normalize_client_name(name):
            """Normalize client names to group related entities together."""
            name = name.strip()
            # Common suffixes to remove for grouping
            suffixes = [' Limited', ' Ltd', ' Ltd.', ' UK Limited', ' Company', ' Inc', ' Inc.', ' PLC', ' plc']
            normalized = name
            for suffix in suffixes:
                if normalized.endswith(suffix):
                    normalized = normalized[:-len(suffix)]
            return normalized

        for payment in payments:
            description = payment.description or ''
            amount = float(payment.total_amount or 0)

            # Extract client name from description
            # Format: "Payment: Client Name" or just the description
            if description.startswith('Payment: '):
                client_name = description[9:].strip()
            elif description.startswith('Payment from '):
                client_name = description[13:].strip()
            else:
                client_name = description.strip()

            # Skip empty or generic descriptions
            if not client_name or client_name.lower() in ['', 'payment', 'transfer']:
                continue

            # Normalize client name for grouping (but keep original for display)
            normalized = normalize_client_name(client_name)

            # Aggregate by normalized name
            if normalized in client_totals:
                client_totals[normalized]['amount'] += amount
                # Keep the most complete name for display
                if len(client_name) > len(client_totals[normalized]['display_name']):
                    client_totals[normalized]['display_name'] = client_name
            else:
                client_totals[normalized] = {
                    'amount': amount,
                    'display_name': client_name
                }

        # Calculate total received
        total_received = sum(c['amount'] for c in client_totals.values())

        if total_received == 0:
            return jsonify({
                'success': True,
                'period': 'Last 12 months',
                'total_received': 0,
                'top_1_percent': 0,
                'top_3_percent': 0,
                'top_5_percent': 0,
                'concentration_risk': 'LOW',
                'client_count': 0,
                'clients': []
            })

        # Sort clients by amount descending
        sorted_clients = sorted(
            client_totals.items(),
            key=lambda x: x[1]['amount'],
            reverse=True
        )

        # Calculate percentages and cumulative percentages
        clients_data = []
        cumulative = 0
        for normalized_name, client_info in sorted_clients:
            amount = client_info['amount']
            display_name = client_info['display_name']
            percent = (amount / total_received) * 100
            cumulative += percent
            clients_data.append({
                'client': display_name,
                'amount': round(amount, 2),
                'percent': round(percent, 1),
                'cumulative_percent': round(cumulative, 1)
            })

        # Calculate concentration metrics
        top_1_percent = clients_data[0]['percent'] if len(clients_data) >= 1 else 0
        top_3_percent = clients_data[2]['cumulative_percent'] if len(clients_data) >= 3 else (
            clients_data[-1]['cumulative_percent'] if clients_data else 0
        )
        top_5_percent = clients_data[4]['cumulative_percent'] if len(clients_data) >= 5 else (
            clients_data[-1]['cumulative_percent'] if clients_data else 0
        )

        # Determine risk level
        if top_1_percent > 40:
            concentration_risk = 'HIGH'
        elif top_3_percent > 70:
            concentration_risk = 'MEDIUM'
        else:
            concentration_risk = 'LOW'

        return jsonify({
            'success': True,
            'period': 'Last 12 months',
            'total_received': round(total_received, 2),
            'top_1_percent': round(top_1_percent, 1),
            'top_3_percent': round(top_3_percent, 1),
            'top_5_percent': round(top_5_percent, 1),
            'concentration_risk': concentration_risk,
            'client_count': len(clients_data),
            'clients': clients_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
