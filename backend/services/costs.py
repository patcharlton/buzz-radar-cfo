"""Historical cost retrieval from Xero."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional


@dataclass
class CostItem:
    """Represents a cost line item from P&L."""
    account_name: str
    amount: float
    month: str  # YYYY-MM format
    category: Optional[str] = None  # Assigned by categoriser


@dataclass
class MonthlyCosts:
    """Costs for a single month."""
    month: str
    month_label: str
    total: float
    items: list[CostItem]


# Cache for historical costs with timestamp
_costs_cache: dict = {
    'data': None,
    'timestamp': None,
    'ttl_hours': 1,
}


def get_historical_costs(months: int = 3, xero_client=None) -> dict:
    """
    Get historical costs from Xero for the last N months.

    Args:
        months: Number of months to fetch (default: 3)
        xero_client: Optional XeroClient instance (will create if not provided)

    Returns:
        dict: Monthly cost data with line items
    """
    global _costs_cache

    # Check cache
    if _costs_cache['data'] and _costs_cache['timestamp']:
        cache_age = datetime.utcnow() - _costs_cache['timestamp']
        if cache_age < timedelta(hours=_costs_cache['ttl_hours']):
            cached = _costs_cache['data']
            if cached.get('num_months') == months:
                return {**cached, 'cached': True}

    try:
        if xero_client is None:
            from xero import XeroClient
            xero_client = XeroClient()

        today = date.today()
        monthly_data = []

        for i in range(months):
            # Calculate month boundaries (going backwards from current month)
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1

            month_start = date(year, month, 1)

            # Last day of month
            if month == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)

            # For current month, use today as end date
            if i == 0:
                month_end = today

            # Fetch P&L from Xero
            pnl = xero_client.get_profit_and_loss(
                from_date=month_start,
                to_date=month_end
            )

            month_key = month_start.strftime('%Y-%m')
            month_label = month_start.strftime('%B %Y')

            monthly_data.append({
                'month': month_key,
                'month_label': month_label,
                'total_expenses': pnl.get('expenses', 0),
                'revenue': pnl.get('revenue', 0),
                'net_profit': pnl.get('net_profit', 0),
                'is_partial': i == 0,  # Current month is partial
            })

        # Calculate average (excluding partial current month)
        complete_months = [m for m in monthly_data if not m['is_partial']]
        if complete_months:
            avg_expenses = sum(m['total_expenses'] for m in complete_months) / len(complete_months)
        else:
            avg_expenses = monthly_data[0]['total_expenses'] if monthly_data else 0

        result = {
            'months': monthly_data,
            'average_monthly_expenses': round(avg_expenses, 2),
            'num_months': months,
            'last_updated': datetime.utcnow().isoformat(),
            'cached': False,
        }

        # Update cache
        _costs_cache['data'] = result
        _costs_cache['timestamp'] = datetime.utcnow()

        return result

    except Exception as e:
        # If Xero fails, return cached data if available
        if _costs_cache['data']:
            cache_age_hours = 0
            if _costs_cache['timestamp']:
                cache_age = datetime.utcnow() - _costs_cache['timestamp']
                cache_age_hours = cache_age.total_seconds() / 3600

            return {
                **_costs_cache['data'],
                'cached': True,
                'cache_age_hours': round(cache_age_hours, 1),
                'error': str(e),
            }

        # No cached data available
        raise Exception(f"Failed to fetch costs from Xero: {str(e)}")


def get_detailed_pnl(months: int = 3, xero_client=None) -> dict:
    """
    Get detailed P&L with line items for categorisation.

    Note: Xero's standard P&L endpoint returns summary data.
    For detailed line items, we'd need to use the Reports/ProfitAndLoss
    endpoint with specific parameters or the Accounts endpoint.

    Args:
        months: Number of months to fetch
        xero_client: Optional XeroClient instance

    Returns:
        dict: Detailed P&L with expense line items
    """
    # For now, return summary data
    # TODO: Enhance to fetch detailed line items when needed
    return get_historical_costs(months, xero_client)


def clear_costs_cache():
    """Clear the costs cache."""
    global _costs_cache
    _costs_cache = {
        'data': None,
        'timestamp': None,
        'ttl_hours': 1,
    }
