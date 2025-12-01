"""AI-powered analysis API routes."""

from datetime import datetime
from flask import Blueprint, jsonify, request

from xero import XeroClient, XeroAuth
from context import load_all_context
from ai import ClaudeClient
from ai.cache import cache_key, get_cached, set_cached, clear_cache, get_cache_stats, DEFAULT_TTL

ai_bp = Blueprint('ai', __name__)
xero_client = XeroClient()
xero_auth = XeroAuth()

# Cache TTL in seconds (uses DEFAULT_TTL from cache module, default 4 hours)
CACHE_TTL = DEFAULT_TTL


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
        # Check cache first
        cache_id = cache_key('daily_insights')
        cached_result = get_cached(cache_id, cache_type='daily_insights')
        if cached_result:
            return jsonify({
                **cached_result,
                'cached': True
            })

        # Get financial data from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Generate insights using Claude
        claude = ClaudeClient()
        insights = claude.daily_insights(financial_data, context)

        result = {
            'success': True,
            'insights': insights,
            'generated_at': datetime.utcnow().isoformat(),
            'data_as_of': financial_data.get('last_synced'),
        }

        # Cache the result in Postgres
        set_cached(cache_id, result, CACHE_TTL, cache_type='daily_insights')

        return jsonify({**result, 'cached': False})

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
        # Check cache first
        cache_id = cache_key('monthly_analysis')
        cached_result = get_cached(cache_id, cache_type='monthly_analysis')
        if cached_result:
            return jsonify({
                **cached_result,
                'cached': True
            })

        # Get financial data from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Generate analysis using Claude
        claude = ClaudeClient()
        analysis = claude.monthly_analysis(financial_data, context)

        result = {
            'success': True,
            'analysis': analysis,
            'generated_at': datetime.utcnow().isoformat(),
        }

        # Cache the result in Postgres
        set_cached(cache_id, result, CACHE_TTL, cache_type='monthly_analysis')

        return jsonify({**result, 'cached': False})

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
        # Clear daily insights cache to force fresh generation
        clear_cache(cache_type='daily_insights')

        # Force sync from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Generate fresh insights
        claude = ClaudeClient()
        insights = claude.daily_insights(financial_data, context)

        result = {
            'success': True,
            'insights': insights,
            'generated_at': datetime.utcnow().isoformat(),
            'data_as_of': financial_data.get('last_synced'),
            'message': 'Cache cleared, data synced and insights refreshed'
        }

        # Cache the fresh result in Postgres
        cache_id = cache_key('daily_insights')
        set_cached(cache_id, result, CACHE_TTL, cache_type='daily_insights')

        return jsonify({**result, 'cached': False})

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


@ai_bp.route('/api/ai/forecast')
@require_xero_connection
def cash_forecast():
    """Generate 4-week cash flow forecast."""
    try:
        # Check cache first
        cache_id = cache_key('cash_forecast')
        cached_result = get_cached(cache_id, cache_type='forecast')
        if cached_result:
            return jsonify({
                **cached_result,
                'cached': True
            })

        # Get financial data from Xero (including historical monthly expenses for burn rate)
        financial_data = xero_client.get_forecast_data()

        # Load business context
        context = load_all_context()

        # Generate forecast using Claude
        claude = ClaudeClient()
        forecast = claude.cash_forecast(financial_data, context)

        result = {
            'success': True,
            'forecast': forecast,
            'generated_at': datetime.utcnow().isoformat(),
            'data_as_of': financial_data.get('last_synced'),
        }

        # Cache the result in Postgres
        set_cached(cache_id, result, CACHE_TTL, cache_type='forecast')

        return jsonify({**result, 'cached': False})

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


@ai_bp.route('/api/ai/anomalies')
@require_xero_connection
def detect_anomalies():
    """Detect financial anomalies and risks."""
    try:
        # Check cache first
        cache_id = cache_key('anomalies')
        cached_result = get_cached(cache_id, cache_type='anomalies')
        if cached_result:
            return jsonify({
                **cached_result,
                'cached': True
            })

        # Get financial data from Xero
        financial_data = get_financial_data()

        # Load business context
        context = load_all_context()

        # Detect anomalies using Claude
        claude = ClaudeClient()
        anomalies = claude.detect_anomalies(financial_data, context)

        result = {
            'success': True,
            'anomalies': anomalies,
            'generated_at': datetime.utcnow().isoformat(),
            'data_as_of': financial_data.get('last_synced'),
        }

        # Cache the result in Postgres
        set_cached(cache_id, result, CACHE_TTL, cache_type='anomalies')

        return jsonify({**result, 'cached': False})

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


@ai_bp.route('/api/ai/cache-stats')
def cache_stats():
    """Get cache statistics."""
    stats = get_cache_stats()
    return jsonify({
        'success': True,
        'stats': stats
    })
