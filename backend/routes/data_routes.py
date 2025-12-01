from flask import Blueprint, jsonify

from xero import XeroClient, XeroAuth
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
        data = xero_client.get_dashboard_data()
        return jsonify(data)
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
        return jsonify({
            'success': True,
            'message': 'Data synced successfully',
            'data': data,
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
