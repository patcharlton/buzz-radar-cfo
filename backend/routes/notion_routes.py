"""API routes for Notion integration."""

import os
from flask import Blueprint, jsonify

notion_bp = Blueprint('notion', __name__, url_prefix='/api/notion')


def is_notion_configured() -> bool:
    """Check if Notion credentials are configured."""
    return bool(os.getenv('NOTION_API_KEY') and os.getenv('NOTION_PIPELINE_DB_ID'))


@notion_bp.route('/status')
def get_status():
    """
    Check Notion connection status.

    Returns:
        dict: Connection status and database info
    """
    if not is_notion_configured():
        return jsonify({
            'success': False,
            'configured': False,
            'error': 'Notion credentials not configured. Set NOTION_API_KEY and NOTION_PIPELINE_DB_ID.',
        })

    try:
        from notion.client import NotionClient
        database_id = os.getenv('NOTION_PIPELINE_DB_ID')

        client = NotionClient()
        status = client.test_connection(database_id)

        return jsonify({
            'success': status.get('connected', False),
            'configured': True,
            **status,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'configured': True,
            'connected': False,
            'error': str(e),
        }), 500


@notion_bp.route('/pipeline')
def get_pipeline():
    """
    Get pipeline data from Notion (uses cache if fresh).

    Returns:
        dict: Pipeline data with deals and summary
    """
    if not is_notion_configured():
        return jsonify({
            'success': False,
            'error': 'Notion not configured',
        }), 400

    try:
        from notion.pipeline import get_pipeline as fetch_pipeline_data
        from notion.cache import get_cache_age

        data = fetch_pipeline_data()
        cache_age = get_cache_age('notion_pipeline')

        return jsonify({
            'success': True,
            'data': data,
            'cache_age_minutes': round(cache_age, 1) if cache_age else 0,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@notion_bp.route('/pipeline/sync', methods=['POST'])
def sync_pipeline():
    """
    Force sync pipeline data from Notion (bypasses cache).

    Returns:
        dict: Fresh pipeline data
    """
    if not is_notion_configured():
        return jsonify({
            'success': False,
            'error': 'Notion not configured',
        }), 400

    try:
        from notion.pipeline import sync_pipeline as do_sync

        data = do_sync()

        return jsonify({
            'success': True,
            'message': f'Synced {len(data.get("deals", []))} deals from Notion',
            'data': data,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
