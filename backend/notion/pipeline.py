"""Pipeline data transformation from Notion to internal format."""

import os
import re
from datetime import datetime
from typing import Optional, Any

from .client import NotionClient
from .cache import get_cached, set_cached, clear_cache


CACHE_KEY = 'notion_pipeline'


def parse_currency(value: Any) -> float:
    """
    Parse currency value from Notion.

    Handles formats like:
    - "£250,000.00"
    - "250000"
    - 250000.0

    Args:
        value: Currency value in various formats

    Returns:
        float: Parsed numeric value
    """
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[£$€,\s]', '', value)
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    return 0.0


def extract_property_value(prop: dict) -> Any:
    """
    Extract value from a Notion property object.

    Args:
        prop: Notion property object

    Returns:
        Extracted value in appropriate Python type
    """
    if not prop:
        return None

    prop_type = prop.get('type')

    if prop_type == 'title':
        title_parts = prop.get('title', [])
        return ''.join(t.get('plain_text', '') for t in title_parts) or None

    elif prop_type == 'rich_text':
        text_parts = prop.get('rich_text', [])
        return ''.join(t.get('plain_text', '') for t in text_parts) or None

    elif prop_type == 'number':
        return prop.get('number')

    elif prop_type == 'select':
        select = prop.get('select')
        return select.get('name') if select else None

    elif prop_type == 'multi_select':
        items = prop.get('multi_select', [])
        return [item.get('name') for item in items]

    elif prop_type == 'date':
        date_obj = prop.get('date')
        if date_obj:
            return date_obj.get('start')  # Returns ISO date string
        return None

    elif prop_type == 'people':
        people = prop.get('people', [])
        names = []
        for person in people:
            name = person.get('name')
            if name:
                names.append(name)
        return names[0] if len(names) == 1 else names if names else None

    elif prop_type == 'email':
        return prop.get('email')

    elif prop_type == 'phone_number':
        return prop.get('phone_number')

    elif prop_type == 'url':
        return prop.get('url')

    elif prop_type == 'checkbox':
        return prop.get('checkbox', False)

    elif prop_type == 'formula':
        formula = prop.get('formula', {})
        formula_type = formula.get('type')
        if formula_type == 'string':
            return formula.get('string')
        elif formula_type == 'number':
            return formula.get('number')
        elif formula_type == 'boolean':
            return formula.get('boolean')
        elif formula_type == 'date':
            date_obj = formula.get('date')
            return date_obj.get('start') if date_obj else None
        return None

    elif prop_type == 'rollup':
        rollup = prop.get('rollup', {})
        rollup_type = rollup.get('type')
        if rollup_type == 'number':
            return rollup.get('number')
        elif rollup_type == 'array':
            # Return first value from array if present
            array = rollup.get('array', [])
            if array:
                return extract_property_value(array[0])
        return None

    return None


def transform_deal(page: dict) -> Optional[dict]:
    """
    Transform a Notion page into a deal dict matching pipeline.yaml format.

    Args:
        page: Notion page object

    Returns:
        dict or None: Transformed deal or None if invalid
    """
    props = page.get('properties', {})

    # Extract name - skip if empty
    name = extract_property_value(props.get('Name'))
    if not name:
        return None

    # Extract client/account owner
    client = extract_property_value(props.get('Client')) or extract_property_value(props.get('Account'))
    account_owner = extract_property_value(props.get('Account owner'))

    # Extract stage and likelihood
    stage = extract_property_value(props.get('Deal stage')) or extract_property_value(props.get('Stage'))
    likelihood = extract_property_value(props.get('Likelihood'))
    if likelihood is not None:
        likelihood = int(likelihood) if isinstance(likelihood, (int, float)) else 0

    # Extract deal value - try multiple possible field names
    deal_value = None
    for field_name in ['Deal value', 'Deal Value', 'Value', 'Amount']:
        val = extract_property_value(props.get(field_name))
        if val is not None:
            deal_value = parse_currency(val)
            break

    if deal_value is None:
        deal_value = 0

    # Extract dates
    expected_close = extract_property_value(props.get('Expected close date')) or \
                     extract_property_value(props.get('Expected Close')) or \
                     extract_property_value(props.get('Close Date'))
    last_contact = extract_property_value(props.get('Last contact date')) or \
                   extract_property_value(props.get('Last Contact'))

    # Extract revenue ranges
    revenue_min = parse_currency(extract_property_value(props.get('Target Revenue Min')))
    revenue_max = parse_currency(extract_property_value(props.get('Target Revenue Max')))

    # Extract scenarios
    worst_case = parse_currency(extract_property_value(props.get('Worst Case Scenario')))
    best_case = parse_currency(extract_property_value(props.get('Best Case Scenario')))

    # Extract decision maker
    decision_maker = extract_property_value(props.get('Decision maker')) or \
                     extract_property_value(props.get('Decision Maker')) or \
                     extract_property_value(props.get('Contact'))

    # Extract notes
    notes = extract_property_value(props.get('Notes')) or extract_property_value(props.get('Description'))

    # Build deal dict
    deal = {
        'name': name,
        'client': client,
        'stage': stage,
        'deal_value': deal_value,
        'likelihood': likelihood or 0,
    }

    # Add optional fields only if they have values
    if account_owner:
        deal['account_owner'] = account_owner
    if expected_close:
        deal['expected_close'] = expected_close
    if last_contact:
        deal['last_contact'] = last_contact
    if decision_maker:
        deal['decision_maker'] = decision_maker
    if revenue_min:
        deal['revenue_min'] = revenue_min
    if revenue_max:
        deal['revenue_max'] = revenue_max
    if worst_case:
        deal['worst_case'] = worst_case
    if best_case:
        deal['best_case'] = best_case
    if notes:
        deal['notes'] = notes

    # Add Notion page ID for reference
    deal['notion_id'] = page.get('id')

    return deal


def calculate_pipeline_summary(deals: list) -> dict:
    """
    Calculate summary statistics for pipeline.

    Args:
        deals: List of deal dicts

    Returns:
        dict: Pipeline summary stats
    """
    total_value = sum(d.get('deal_value', 0) for d in deals)

    # Weighted value based on likelihood
    weighted_value = sum(
        d.get('deal_value', 0) * (d.get('likelihood', 0) / 10.0)
        for d in deals
    )

    # Count by stage
    by_stage = {}
    for deal in deals:
        stage = deal.get('stage') or 'Unknown'
        if stage not in by_stage:
            by_stage[stage] = {'count': 0, 'value': 0}
        by_stage[stage]['count'] += 1
        by_stage[stage]['value'] += deal.get('deal_value', 0)

    # High confidence deals (likelihood >= 8)
    high_confidence = [d for d in deals if d.get('likelihood', 0) >= 8]
    high_confidence_value = sum(d.get('deal_value', 0) for d in high_confidence)

    return {
        'total_pipeline_value': total_value,
        'weighted_pipeline': int(weighted_value),
        'deals_count': len(deals),
        'high_confidence_value': high_confidence_value,
        'high_confidence_count': len(high_confidence),
        'by_stage': by_stage,
    }


def fetch_pipeline() -> dict:
    """
    Fetch pipeline data from Notion and transform it.

    Returns:
        dict: Pipeline data with deals, summary, and metadata
    """
    database_id = os.getenv('NOTION_PIPELINE_DB_ID')
    if not database_id:
        raise ValueError("NOTION_PIPELINE_DB_ID environment variable not set")

    client = NotionClient()

    # Query all pages from the database
    pages = client.query_database(
        database_id,
        sorts=[{'property': 'Deal value', 'direction': 'descending'}]
    )

    # Transform pages to deals
    deals = []
    for page in pages:
        deal = transform_deal(page)
        if deal:
            deals.append(deal)

    # Calculate summary
    summary = calculate_pipeline_summary(deals)

    result = {
        'deals': deals,
        'pipeline_summary': summary,
        'synced_at': datetime.utcnow().isoformat(),
        'source': 'notion',
    }

    # Cache the result
    set_cached(CACHE_KEY, result)

    return result


def get_pipeline() -> dict:
    """
    Get pipeline data, using cache if fresh.

    Returns:
        dict: Pipeline data with deals and summary
    """
    # Check cache first
    cached = get_cached(CACHE_KEY)
    if cached:
        cached['cached'] = True
        return cached

    # Fetch fresh data
    return fetch_pipeline()


def sync_pipeline() -> dict:
    """
    Force a fresh sync from Notion, bypassing cache.

    Returns:
        dict: Fresh pipeline data
    """
    clear_cache(CACHE_KEY)
    return fetch_pipeline()
