"""Services for financial projections and analysis."""

from .scenarios import calculate_scenarios
from .costs import get_historical_costs
from .categoriser import categorise_costs
from .gap_analysis import calculate_gap, find_deals_to_close_gap

__all__ = [
    'calculate_scenarios',
    'get_historical_costs',
    'categorise_costs',
    'calculate_gap',
    'find_deals_to_close_gap',
]
