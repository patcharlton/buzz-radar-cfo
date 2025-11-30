"""AI-powered analysis API routes."""

from datetime import datetime
from flask import Blueprint, jsonify, request

from xero import XeroClient, XeroAuth
from context import load_all_context
from ai import ClaudeClient

ai_bp = Blueprint('ai', __name__)
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


def get_financial_data():
    """Fetch current financial data from Xero."""
    return xero_client.get_dashboard_data()


@ai_bp.route('/api/ai/daily-insights')
@require_xero_connection
def daily_insights():
    """Generate AI-powered daily financial insights."""
    try:
        # Get financial data from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Generate insights using Claude
        claude = ClaudeClient()
        insights = claude.daily_insights(financial_data, context)

        return jsonify({
            'success': True,
            'insights': insights,
            'generated_at': datetime.utcnow().isoformat(),
            'data_as_of': financial_data.get('last_synced'),
        })

    except ValueError as e:
        # Missing API key
        return jsonify({
            'success': False,
            'error': str(e),
            'hint': 'Ensure ANTHROPIC_API_KEY is set in .env'
        }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/api/ai/monthly-analysis')
@require_xero_connection
def monthly_analysis():
    """Generate AI-powered monthly strategic analysis."""
    try:
        # Get financial data from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Generate analysis using Claude
        claude = ClaudeClient()
        analysis = claude.monthly_analysis(financial_data, context)

        return jsonify({
            'success': True,
            'analysis': analysis,
            'generated_at': datetime.utcnow().isoformat(),
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'hint': 'Ensure ANTHROPIC_API_KEY is set in .env'
        }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/api/ai/ask', methods=['POST'])
@require_xero_connection
def ask_question():
    """Answer a specific financial question using AI."""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400

        question = data['question'].strip()
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question cannot be empty'
            }), 400

        # Get financial data from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Get answer from Claude
        claude = ClaudeClient()
        answer = claude.answer_question(question, financial_data, context)

        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,
            'answered_at': datetime.utcnow().isoformat(),
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'hint': 'Ensure ANTHROPIC_API_KEY is set in .env'
        }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/api/ai/refresh-insights', methods=['POST'])
@require_xero_connection
def refresh_insights():
    """Sync Xero data and generate fresh insights."""
    try:
        # Force sync from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Generate fresh insights
        claude = ClaudeClient()
        insights = claude.daily_insights(financial_data, context)

        return jsonify({
            'success': True,
            'insights': insights,
            'generated_at': datetime.utcnow().isoformat(),
            'data_as_of': financial_data.get('last_synced'),
            'message': 'Data synced and insights refreshed'
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'hint': 'Ensure ANTHROPIC_API_KEY is set in .env'
        }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
