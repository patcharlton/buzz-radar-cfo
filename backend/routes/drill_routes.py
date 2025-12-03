"""
Drill-down API endpoints for transaction-level views.

These endpoints support the DrillDownDrawer component for viewing
detailed transactions behind summary numbers.
"""
from datetime import date, datetime, timedelta
from flask import Blueprint, jsonify, request

from xero import XeroClient, XeroAuth

drill_bp = Blueprint('drill', __name__)
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


def parse_date(date_str, default=None):
    """Parse ISO date string to date object.

    Special values:
        'all' - Returns a date 10 years in the past for max history
    """
    if not date_str:
        return default

    # Handle 'all' for fetching all history
    if isinstance(date_str, str) and date_str.lower() == 'all':
        return date(date.today().year - 10, 1, 1)

    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return default


# =============================================================================
# CASH DRILL-DOWN
# =============================================================================

@drill_bp.route('/api/drill/cash')
@require_xero_connection
def drill_cash():
    """
    Get bank transactions for drill-down view.

    Query params:
        from_date: Start date (ISO format, default: 90 days ago, use 'all' for all history)
        to_date: End date (ISO format, default: today)
        account_id: Optional bank account ID to filter
        page: Page number (default: 1)
        page_size: Results per page (default: 50, max: 100)
    """
    try:
        today = date.today()
        from_date = parse_date(request.args.get('from_date'), today - timedelta(days=90))
        to_date = parse_date(request.args.get('to_date'), today)
        account_id = request.args.get('account_id')
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        data = xero_client.get_bank_transactions(
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
            page=page,
            page_size=page_size,
        )

        # Calculate running balance if single account
        transactions = data.get('transactions', [])
        if transactions:
            # Calculate totals
            total_in = sum(t['amount'] for t in transactions if t['amount'] > 0)
            total_out = sum(t['amount'] for t in transactions if t['amount'] < 0)
            net_change = total_in + total_out

            data['summary'] = {
                'total_in': total_in,
                'total_out': total_out,
                'net_change': net_change,
                'transaction_count': len(transactions),
            }

        return jsonify({
            'success': True,
            **data,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@drill_bp.route('/api/drill/cash/accounts')
@require_xero_connection
def drill_cash_accounts():
    """Get list of bank accounts for filtering."""
    try:
        accounts = xero_client.get_bank_accounts()
        return jsonify({
            'success': True,
            'accounts': accounts,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# RECEIVABLES DRILL-DOWN
# =============================================================================

@drill_bp.route('/api/drill/receivables')
@require_xero_connection
def drill_receivables():
    """
    Get outstanding receivables (invoices) for drill-down view.

    Query params:
        from_date: Optional issue date start
        to_date: Optional issue date end
        status: Filter by status (AUTHORISED, PAID, etc.)
        overdue_only: If 'true', only show overdue invoices
        page: Page number (default: 1)
        page_size: Results per page (default: 50, max: 100)
    """
    try:
        from_date = parse_date(request.args.get('from_date'))
        to_date = parse_date(request.args.get('to_date'))
        status = request.args.get('status', 'AUTHORISED')
        overdue_only = request.args.get('overdue_only', '').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        data = xero_client.get_invoices_detailed(
            invoice_type='ACCREC',
            status=status if status else None,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        invoices = data.get('invoices', [])

        # Filter to overdue only if requested
        if overdue_only:
            invoices = [inv for inv in invoices if inv.get('is_overdue')]
            data['invoices'] = invoices

        # Calculate summary
        total_outstanding = sum(inv['amount_due'] for inv in invoices)
        total_overdue = sum(inv['amount_due'] for inv in invoices if inv['is_overdue'])
        overdue_count = len([inv for inv in invoices if inv['is_overdue']])

        data['summary'] = {
            'total_outstanding': total_outstanding,
            'total_overdue': total_overdue,
            'invoice_count': len(invoices),
            'overdue_count': overdue_count,
        }

        return jsonify({
            'success': True,
            **data,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@drill_bp.route('/api/drill/receivables/<invoice_id>')
@require_xero_connection
def drill_receivables_detail(invoice_id):
    """
    Get full invoice details including line items.

    Path params:
        invoice_id: The Xero invoice ID
    """
    try:
        invoice = xero_client.get_invoice_details(invoice_id)

        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404

        return jsonify({
            'success': True,
            'invoice': invoice,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# PAYABLES DRILL-DOWN
# =============================================================================

@drill_bp.route('/api/drill/payables')
@require_xero_connection
def drill_payables():
    """
    Get outstanding payables (bills) for drill-down view.

    Query params:
        from_date: Optional issue date start
        to_date: Optional issue date end
        status: Filter by status (AUTHORISED, PAID, etc.)
        overdue_only: If 'true', only show overdue bills
        page: Page number (default: 1)
        page_size: Results per page (default: 50, max: 100)
    """
    try:
        from_date = parse_date(request.args.get('from_date'))
        to_date = parse_date(request.args.get('to_date'))
        status = request.args.get('status', 'AUTHORISED')
        overdue_only = request.args.get('overdue_only', '').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        data = xero_client.get_invoices_detailed(
            invoice_type='ACCPAY',
            status=status if status else None,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        invoices = data.get('invoices', [])

        # Filter to overdue only if requested
        if overdue_only:
            invoices = [inv for inv in invoices if inv.get('is_overdue')]
            data['invoices'] = invoices

        # Calculate summary
        total_outstanding = sum(inv['amount_due'] for inv in invoices)
        total_overdue = sum(inv['amount_due'] for inv in invoices if inv['is_overdue'])
        overdue_count = len([inv for inv in invoices if inv['is_overdue']])

        data['summary'] = {
            'total_outstanding': total_outstanding,
            'total_overdue': total_overdue,
            'bill_count': len(invoices),
            'overdue_count': overdue_count,
        }

        return jsonify({
            'success': True,
            **data,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@drill_bp.route('/api/drill/payables/<invoice_id>')
@require_xero_connection
def drill_payables_detail(invoice_id):
    """
    Get full bill details including line items.

    Path params:
        invoice_id: The Xero invoice/bill ID
    """
    try:
        invoice = xero_client.get_invoice_details(invoice_id)

        if not invoice:
            return jsonify({'success': False, 'error': 'Bill not found'}), 404

        return jsonify({
            'success': True,
            'invoice': invoice,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# P&L DRILL-DOWN
# =============================================================================

@drill_bp.route('/api/drill/pnl')
@require_xero_connection
def drill_pnl():
    """
    Get P&L categories for drill-down view.

    Query params:
        from_date: Start of period (default: start of current month)
        to_date: End of period (default: today)
    """
    try:
        today = date.today()
        from_date = parse_date(
            request.args.get('from_date'),
            date(today.year, today.month, 1)
        )
        to_date = parse_date(request.args.get('to_date'), today)

        data = xero_client.get_profit_and_loss_detailed(
            from_date=from_date,
            to_date=to_date,
        )

        # Calculate totals
        categories = data.get('categories', [])
        total_revenue = sum(
            cat['total'] for cat in categories
            if 'income' in cat['category'].lower() or 'revenue' in cat['category'].lower()
        )
        total_expenses = sum(
            abs(cat['total']) for cat in categories
            if 'expense' in cat['category'].lower() or 'cost' in cat['category'].lower()
        )

        data['summary'] = {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': total_revenue - total_expenses,
            'category_count': len(categories),
        }

        return jsonify({
            'success': True,
            **data,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@drill_bp.route('/api/drill/pnl/account/<account_id>')
@require_xero_connection
def drill_pnl_account(account_id):
    """
    Get journal entries for a specific P&L account.

    Path params:
        account_id: The Xero account ID

    Query params:
        from_date: Start of period
        to_date: End of period
        page: Page number
    """
    try:
        today = date.today()
        from_date = parse_date(
            request.args.get('from_date'),
            date(today.year, today.month, 1)
        )
        to_date = parse_date(request.args.get('to_date'), today)
        page = request.args.get('page', 1, type=int)

        data = xero_client.get_journals(
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
            page=page,
        )

        # Calculate totals
        journals = data.get('journals', [])
        total_debits = sum(j['debit'] for j in journals)
        total_credits = sum(j['credit'] for j in journals)

        data['summary'] = {
            'total_debits': total_debits,
            'total_credits': total_credits,
            'net_amount': total_debits - total_credits,
            'entry_count': len(journals),
        }

        return jsonify({
            'success': True,
            **data,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# SEARCH
# =============================================================================

@drill_bp.route('/api/drill/search')
@require_xero_connection
def drill_search():
    """
    Search across transactions.

    Query params:
        q: Search query (required)
        type: Transaction type to search (cash, receivables, payables, all)
        from_date: Start date (default: 90 days ago)
        to_date: End date (default: today)
        page: Page number
        page_size: Results per page
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400

        today = date.today()
        from_date = parse_date(request.args.get('from_date'), today - timedelta(days=90))
        to_date = parse_date(request.args.get('to_date'), today)
        search_type = request.args.get('type', 'all')
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        data = xero_client.search_transactions(
            query=query,
            search_type=search_type,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        return jsonify({
            'success': True,
            **data,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ACCOUNT CODES
# =============================================================================

@drill_bp.route('/api/drill/accounts')
@require_xero_connection
def drill_accounts():
    """
    Get all account codes (for filters and lookups).

    Query params:
        refresh: If 'true', force cache refresh
    """
    try:
        force_refresh = request.args.get('refresh', '').lower() == 'true'
        accounts = xero_client.get_account_codes(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'accounts': accounts,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
