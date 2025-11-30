from flask import Blueprint, jsonify

from xero import XeroClient, XeroAuth

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
