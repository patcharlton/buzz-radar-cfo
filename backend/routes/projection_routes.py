"""API routes for financial projections."""

from datetime import datetime
from flask import Blueprint, jsonify, request

from xero import XeroClient, XeroAuth
from context import load_all_context
from services.scenarios import calculate_scenarios
from services.costs import get_historical_costs
from services.categoriser import get_category_breakdown
from services.gap_analysis import analyse_gap

projection_bp = Blueprint('projections', __name__)
xero_client = XeroClient()
xero_auth = XeroAuth()

# Default Q1 target from goals.yaml
DEFAULT_Q1_TARGET = 375000


def require_xero_connection(f):
    """Decorator to ensure Xero connection before API calls."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not xero_auth.is_connected():
            return jsonify({'error': 'Not connected to Xero'}), 401
        return f(*args, **kwargs)
    return decorated


def get_target_from_goals(context: dict) -> float:
    """Extract Q1 target from goals context."""
    goals = context.get('goals', {})
    operational = goals.get('operational_goals', {})
    q1_goals = operational.get('q1_2026', [])

    # Sum up goal values
    total = 0
    for goal in q1_goals:
        value = goal.get('value') or goal.get('value_if_success', 0)
        if value:
            total += value

    return total if total > 0 else DEFAULT_Q1_TARGET


@projection_bp.route('/api/projections')
@require_xero_connection
def get_projections():
    """
    Get full 3-month financial projection.

    Query params:
        months: Number of months to project (default: 3)

    Returns:
        dict: Complete projection with scenarios, costs, and gap analysis
    """
    try:
        months = request.args.get('months', 3, type=int)
        months = max(1, min(months, 6))  # Limit to 1-6 months

        # Load context
        context = load_all_context()
        pipeline = context.get('pipeline', {}).get('deals', [])

        # Calculate revenue scenarios
        scenarios = calculate_scenarios(pipeline, months)

        # Get historical costs
        try:
            costs = get_historical_costs(months, xero_client)
        except Exception as e:
            costs = {
                'error': str(e),
                'months': [],
                'average_monthly_expenses': 0,
            }

        # Get cost breakdown
        avg_expenses = costs.get('average_monthly_expenses', 0)
        cost_breakdown = get_category_breakdown(avg_expenses)

        # Get target and calculate gap
        target = get_target_from_goals(context)
        base_projection = scenarios.get('totals', {}).get('base', 0)
        gap_analysis = analyse_gap(base_projection, target, pipeline)

        return jsonify({
            'success': True,
            'revenue': scenarios,
            'costs': costs,
            'cost_breakdown': cost_breakdown,
            'gap_analysis': gap_analysis,
            'target': target,
            'generated_at': datetime.utcnow().isoformat(),
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@projection_bp.route('/api/projections/costs')
@require_xero_connection
def get_costs_only():
    """
    Get cost breakdown only.

    Query params:
        months: Number of months to fetch (default: 3)

    Returns:
        dict: Historical costs with category breakdown
    """
    try:
        months = request.args.get('months', 3, type=int)
        months = max(1, min(months, 6))

        # Get historical costs
        costs = get_historical_costs(months, xero_client)

        # Get category breakdown
        avg_expenses = costs.get('average_monthly_expenses', 0)
        cost_breakdown = get_category_breakdown(avg_expenses)

        return jsonify({
            'success': True,
            'costs': costs,
            'cost_breakdown': cost_breakdown,
            'generated_at': datetime.utcnow().isoformat(),
        })

    except Exception as e:
        # Return cached data if available
        try:
            from services.costs import _costs_cache
            if _costs_cache.get('data'):
                return jsonify({
                    'success': True,
                    'costs': _costs_cache['data'],
                    'cost_breakdown': get_category_breakdown(
                        _costs_cache['data'].get('average_monthly_expenses', 0)
                    ),
                    'cached': True,
                    'warning': f'Using cached data: {str(e)}',
                    'generated_at': datetime.utcnow().isoformat(),
                })
        except Exception:
            pass

        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@projection_bp.route('/api/projections/gap')
@require_xero_connection
def get_gap_only():
    """
    Get gap analysis only.

    Query params:
        months: Number of months to project (default: 3)
        target: Override target amount (optional)

    Returns:
        dict: Gap analysis with recommendations
    """
    try:
        months = request.args.get('months', 3, type=int)
        months = max(1, min(months, 6))

        # Load context
        context = load_all_context()
        pipeline = context.get('pipeline', {}).get('deals', [])

        # Calculate scenarios
        scenarios = calculate_scenarios(pipeline, months)
        base_projection = scenarios.get('totals', {}).get('base', 0)

        # Get target (allow override via query param)
        target = request.args.get('target', type=float)
        if target is None:
            target = get_target_from_goals(context)

        # Calculate gap
        gap_analysis = analyse_gap(base_projection, target, pipeline)

        return jsonify({
            'success': True,
            'gap_analysis': gap_analysis,
            'scenarios': scenarios.get('totals'),
            'target': target,
            'generated_at': datetime.utcnow().isoformat(),
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@projection_bp.route('/api/projections/scenarios')
def get_scenarios_only():
    """
    Get revenue scenarios only (no Xero auth required).

    Query params:
        months: Number of months to project (default: 3)

    Returns:
        dict: Revenue scenarios from pipeline
    """
    try:
        months = request.args.get('months', 3, type=int)
        months = max(1, min(months, 6))

        # Load context
        context = load_all_context()
        pipeline = context.get('pipeline', {}).get('deals', [])

        if not pipeline:
            return jsonify({
                'success': False,
                'error': 'No pipeline data available',
                'hint': 'Check that pipeline.yaml exists in context directory',
            }), 404

        # Calculate scenarios
        scenarios = calculate_scenarios(pipeline, months)

        return jsonify({
            'success': True,
            'scenarios': scenarios,
            'generated_at': datetime.utcnow().isoformat(),
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
