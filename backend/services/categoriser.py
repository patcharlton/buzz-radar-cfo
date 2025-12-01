"""Cost categorisation using Claude API."""

import os
import json
from datetime import datetime, timedelta
from typing import Optional
from cachetools import TTLCache

# In-memory cache with 24-hour TTL
_category_cache = TTLCache(maxsize=1000, ttl=86400)  # 24 hours

# Standard cost categories
COST_CATEGORIES = [
    'salaries_contractors',
    'data_apis',
    'software_tools',
    'professional_services',
    'marketing',
    'infrastructure',
    'travel_expenses',
    'office_admin',
]

CATEGORY_LABELS = {
    'salaries_contractors': 'Salaries & Contractors',
    'data_apis': 'Data & APIs',
    'software_tools': 'Software Tools',
    'professional_services': 'Professional Services',
    'marketing': 'Marketing',
    'infrastructure': 'Infrastructure',
    'travel_expenses': 'Travel & Expenses',
    'office_admin': 'Office & Admin',
}

# Default categorisation rules (used when Claude is unavailable)
DEFAULT_RULES = {
    'salaries_contractors': ['salary', 'wages', 'contractor', 'payroll', 'pension', 'ni ', 'national insurance'],
    'data_apis': ['api', 'twitter', 'x api', 'data feed', 'brandwatch', 'meltwater', 'social listening'],
    'software_tools': ['software', 'subscription', 'saas', 'license', 'slack', 'notion', 'github', 'aws', 'azure', 'google cloud', 'anthropic', 'openai'],
    'professional_services': ['legal', 'accounting', 'audit', 'consulting', 'advisory', 'solicitor'],
    'marketing': ['marketing', 'advertising', 'promotion', 'pr ', 'public relations', 'events', 'sponsorship'],
    'infrastructure': ['hosting', 'server', 'cloud', 'bandwidth', 'domain', 'ssl', 'security'],
    'travel_expenses': ['travel', 'flight', 'hotel', 'uber', 'taxi', 'train', 'expenses', 'meals'],
    'office_admin': ['office', 'rent', 'utilities', 'insurance', 'supplies', 'equipment', 'phone'],
}


def categorise_with_rules(item_name: str) -> str:
    """Categorise using simple keyword matching rules."""
    name_lower = item_name.lower()

    for category, keywords in DEFAULT_RULES.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category

    return 'office_admin'  # Default category


def categorise_with_claude(items: list[dict]) -> dict[str, str]:
    """
    Categorise cost items using Claude API.

    Args:
        items: List of dicts with 'name' and 'amount' keys

    Returns:
        dict: Mapping of item name to category
    """
    try:
        from anthropic import Anthropic

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        client = Anthropic(api_key=api_key)

        # Build prompt
        items_text = "\n".join([f"- {item['name']}: {item['amount']}" for item in items])

        prompt = f"""Categorise each of these business expense line items into exactly one of these categories:
- salaries_contractors (salaries, wages, contractor payments, payroll costs)
- data_apis (API costs, data feeds, social listening platforms)
- software_tools (software subscriptions, SaaS tools, cloud services)
- professional_services (legal, accounting, consulting fees)
- marketing (advertising, PR, events, promotions)
- infrastructure (hosting, servers, domains, security)
- travel_expenses (travel, hotels, meals, transport)
- office_admin (rent, utilities, office supplies, general admin)

Expense items:
{items_text}

Return a JSON object mapping each expense name to its category. Example:
{{"Salaries": "salaries_contractors", "AWS Hosting": "infrastructure"}}

Return ONLY the JSON object, no other text."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text
        result = json.loads(response_text)

        # Validate categories
        validated = {}
        for name, category in result.items():
            if category in COST_CATEGORIES:
                validated[name] = category
            else:
                validated[name] = categorise_with_rules(name)

        return validated

    except Exception as e:
        # Fall back to rule-based categorisation
        return {item['name']: categorise_with_rules(item['name']) for item in items}


def categorise_costs(items: list[dict]) -> dict[str, float]:
    """
    Categorise cost items and return totals by category.

    Args:
        items: List of dicts with 'name' and 'amount' keys

    Returns:
        dict: Category totals, e.g., {'salaries_contractors': 50000, ...}
    """
    if not items:
        return {cat: 0.0 for cat in COST_CATEGORIES}

    # Check cache for each item
    uncached_items = []
    cached_categories = {}

    for item in items:
        cache_key = item['name'].lower().strip()
        if cache_key in _category_cache:
            cached_categories[item['name']] = _category_cache[cache_key]
        else:
            uncached_items.append(item)

    # Categorise uncached items
    if uncached_items:
        new_categories = categorise_with_claude(uncached_items)

        # Update cache
        for name, category in new_categories.items():
            cache_key = name.lower().strip()
            _category_cache[cache_key] = category
            cached_categories[name] = category

    # Calculate totals by category
    totals = {cat: 0.0 for cat in COST_CATEGORIES}

    for item in items:
        category = cached_categories.get(item['name'], 'office_admin')
        totals[category] += item.get('amount', 0)

    return totals


def get_category_breakdown(total_expenses: float, use_estimates: bool = True) -> dict:
    """
    Get category breakdown for a total expense amount.

    When detailed line items aren't available, use estimated percentages
    based on typical SaaS company cost structures.

    Args:
        total_expenses: Total monthly expenses
        use_estimates: If True, return estimates based on typical ratios

    Returns:
        dict: Category breakdown with amounts and percentages
    """
    if not use_estimates:
        return {'error': 'Detailed line items not available'}

    # Typical SaaS company cost ratios for Buzz Radar's size
    ratios = {
        'salaries_contractors': 0.55,  # 55% - biggest cost
        'data_apis': 0.12,  # 12% - X/Twitter API, data feeds
        'software_tools': 0.10,  # 10% - SaaS subscriptions
        'professional_services': 0.05,  # 5% - legal, accounting
        'marketing': 0.05,  # 5% - marketing spend
        'infrastructure': 0.08,  # 8% - cloud, hosting
        'travel_expenses': 0.03,  # 3% - travel
        'office_admin': 0.02,  # 2% - office, admin
    }

    breakdown = {}
    for category, ratio in ratios.items():
        amount = total_expenses * ratio
        breakdown[category] = {
            'amount': round(amount, 2),
            'percentage': round(ratio * 100, 1),
            'label': CATEGORY_LABELS[category],
        }

    return {
        'categories': breakdown,
        'total': total_expenses,
        'is_estimate': True,
        'note': 'Based on typical SaaS company cost structure',
    }


def clear_category_cache():
    """Clear the category cache."""
    _category_cache.clear()
