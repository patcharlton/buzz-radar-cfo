"""Tests for revenue scenario calculations."""

import pytest
from datetime import date, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scenarios import (
    calculate_scenarios,
    parse_deals,
    allocate_deal_to_month,
    get_month_key,
    Deal,
)


# Sample test data matching pipeline.yaml format
SAMPLE_PIPELINE = [
    {
        "name": "ViiV DLP",
        "client": "ViiV Healthcare",
        "deal_value": 650000,
        "best_case": 650000,
        "likelihood": 9,
        "stage": "Won",
        "expected_close": "2025-01-15",
    },
    {
        "name": "Bayer DOL",
        "client": "Bayer",
        "deal_value": 100000,
        "best_case": 150000,
        "likelihood": 5,
        "stage": "Proposal Being Reviewed",
        "expected_close": "2026-02-01",
    },
    {
        "name": "Ferring BRIANN Pilot",
        "client": "Ferring Pharmaceuticals",
        "deal_value": 30000,
        "best_case": 196000,
        "likelihood": 8,
        "stage": "Verbal Agreement",
        "expected_close": "2025-11-30",
    },
    {
        "name": "GSK Oncology",
        "client": "GSK",
        "deal_value": 250000,
        "best_case": 350000,
        "likelihood": 7,
        "stage": "Warm Lead",
        "expected_close": "2026-01-31",
    },
    {
        "name": "Cold Lead Deal",
        "client": "Test Corp",
        "deal_value": 50000,
        "best_case": 75000,
        "likelihood": 3,
        "stage": "Cold Lead",
        "expected_close": "2026-03-15",
    },
]


class TestParseDeals:
    """Test deal parsing from dict to Deal objects."""

    def test_parse_deals_basic(self):
        """Test basic deal parsing."""
        deals = parse_deals(SAMPLE_PIPELINE)

        assert len(deals) == 5
        assert deals[0].name == "ViiV DLP"
        assert deals[0].deal_value == 650000
        assert deals[0].likelihood == 9
        assert deals[0].stage == "Won"

    def test_parse_deals_best_case(self):
        """Test best_case parsing."""
        deals = parse_deals(SAMPLE_PIPELINE)

        # Best case set explicitly
        assert deals[1].best_case == 150000

        # Best case equals deal_value when same
        assert deals[0].best_case == 650000

    def test_parse_deals_empty(self):
        """Test parsing empty pipeline."""
        deals = parse_deals([])
        assert deals == []

    def test_parse_deals_missing_fields(self):
        """Test parsing with missing optional fields."""
        minimal = [{"name": "Test", "client": "Client", "stage": "Won", "deal_value": 100}]
        deals = parse_deals(minimal)

        assert len(deals) == 1
        assert deals[0].likelihood == 0
        assert deals[0].expected_close is None


class TestAllocateDealToMonth:
    """Test deal allocation to projection months."""

    def test_allocate_won_deal_no_date(self):
        """Won deals without date go to first month."""
        deal = Deal(
            name="Test",
            client="Client",
            stage="Won",
            deal_value=100000,
            likelihood=10,
        )
        target_months = ["2025-12", "2026-01", "2026-02"]

        result = allocate_deal_to_month(deal, target_months)
        assert result == "2025-12"

    def test_allocate_non_won_no_date_excluded(self):
        """Non-won deals without date are excluded."""
        deal = Deal(
            name="Test",
            client="Client",
            stage="Proposal Being Reviewed",
            deal_value=100000,
            likelihood=5,
        )
        target_months = ["2025-12", "2026-01", "2026-02"]

        result = allocate_deal_to_month(deal, target_months)
        assert result is None

    def test_allocate_past_date_to_first_month(self):
        """Deals with past close dates go to first month."""
        deal = Deal(
            name="Test",
            client="Client",
            stage="Procurement",
            deal_value=100000,
            likelihood=8,
            expected_close="2025-10-01",  # Past date
        )
        target_months = ["2025-12", "2026-01", "2026-02"]

        result = allocate_deal_to_month(deal, target_months)
        assert result == "2025-12"

    def test_allocate_within_period(self):
        """Deals closing within period go to correct month."""
        deal = Deal(
            name="Test",
            client="Client",
            stage="Verbal Agreement",
            deal_value=100000,
            likelihood=8,
            expected_close="2026-01-15",
        )
        target_months = ["2025-12", "2026-01", "2026-02"]

        result = allocate_deal_to_month(deal, target_months)
        assert result == "2026-01"

    def test_allocate_after_period_excluded(self):
        """Deals closing after projection period are excluded."""
        deal = Deal(
            name="Test",
            client="Client",
            stage="Warm Lead",
            deal_value=100000,
            likelihood=5,
            expected_close="2026-06-01",  # After 3-month projection
        )
        target_months = ["2025-12", "2026-01", "2026-02"]

        result = allocate_deal_to_month(deal, target_months)
        assert result is None


class TestCalculateScenarios:
    """Test scenario calculation logic."""

    def test_calculate_scenarios_structure(self):
        """Test result structure."""
        result = calculate_scenarios(SAMPLE_PIPELINE, months=3)

        assert "months" in result
        assert "totals" in result
        assert "deals_by_month" in result
        assert "projection_period" in result

        assert len(result["months"]) == 3
        assert "conservative" in result["totals"]
        assert "base" in result["totals"]
        assert "optimistic" in result["totals"]

    def test_conservative_calculation(self):
        """Test conservative scenario: Won + (Verbal Agreement * 0.8)."""
        # Create simple test data
        pipeline = [
            {
                "name": "Won Deal",
                "client": "Client A",
                "deal_value": 100000,
                "likelihood": 10,
                "stage": "Won",
                "expected_close": date.today().isoformat(),
            },
            {
                "name": "Verbal Deal",
                "client": "Client B",
                "deal_value": 50000,
                "likelihood": 8,
                "stage": "Verbal Agreement",
                "expected_close": date.today().isoformat(),
            },
        ]

        result = calculate_scenarios(pipeline, months=1)

        # Conservative = 100000 (Won) + 50000 * 0.8 (Verbal) = 140000
        assert result["totals"]["conservative"] == 140000

    def test_base_calculation(self):
        """Test base scenario: deal_value * (likelihood / 10)."""
        pipeline = [
            {
                "name": "Deal 1",
                "client": "Client A",
                "deal_value": 100000,
                "likelihood": 10,
                "stage": "Won",
                "expected_close": date.today().isoformat(),
            },
            {
                "name": "Deal 2",
                "client": "Client B",
                "deal_value": 100000,
                "likelihood": 5,
                "stage": "Proposal Being Reviewed",
                "expected_close": date.today().isoformat(),
            },
        ]

        result = calculate_scenarios(pipeline, months=1)

        # Base = 100000 * 1.0 + 100000 * 0.5 = 150000
        assert result["totals"]["base"] == 150000

    def test_optimistic_calculation(self):
        """Test optimistic scenario: best_case for likelihood >= 5."""
        pipeline = [
            {
                "name": "High Likelihood",
                "client": "Client A",
                "deal_value": 100000,
                "best_case": 150000,
                "likelihood": 7,
                "stage": "Warm Lead",
                "expected_close": date.today().isoformat(),
            },
            {
                "name": "Low Likelihood",
                "client": "Client B",
                "deal_value": 50000,
                "best_case": 100000,
                "likelihood": 3,  # Below threshold
                "stage": "Cold Lead",
                "expected_close": date.today().isoformat(),
            },
            {
                "name": "Won Deal",
                "client": "Client C",
                "deal_value": 80000,
                "likelihood": 10,
                "stage": "Won",
                "expected_close": date.today().isoformat(),
            },
        ]

        result = calculate_scenarios(pipeline, months=1)

        # Optimistic = 150000 (best_case, L>=5) + 80000 (Won always counts)
        # Low likelihood deal excluded
        assert result["totals"]["optimistic"] == 230000

    def test_monthly_allocation(self):
        """Test deals are allocated to correct months."""
        today = date.today()
        next_month = today.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=15)

        pipeline = [
            {
                "name": "This Month",
                "client": "Client A",
                "deal_value": 100000,
                "likelihood": 10,
                "stage": "Won",
                "expected_close": today.isoformat(),
            },
            {
                "name": "Next Month",
                "client": "Client B",
                "deal_value": 50000,
                "likelihood": 8,
                "stage": "Verbal Agreement",
                "expected_close": next_month.isoformat(),
            },
        ]

        result = calculate_scenarios(pipeline, months=2)
        deals_by_month = result["deals_by_month"]

        current_month = get_month_key(today)
        next_month_key = get_month_key(next_month)

        # Check deals are in correct months
        current_deals = [d["name"] for d in deals_by_month.get(current_month, [])]
        next_deals = [d["name"] for d in deals_by_month.get(next_month_key, [])]

        assert "This Month" in current_deals
        assert "Next Month" in next_deals

    def test_empty_pipeline(self):
        """Test handling of empty pipeline."""
        result = calculate_scenarios([], months=3)

        assert result["totals"]["conservative"] == 0
        assert result["totals"]["base"] == 0
        assert result["totals"]["optimistic"] == 0
        assert len(result["months"]) == 3

    def test_projection_period(self):
        """Test projection period metadata."""
        result = calculate_scenarios(SAMPLE_PIPELINE, months=3)

        period = result["projection_period"]
        assert period["num_months"] == 3
        assert "start" in period
        assert "end" in period


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_date_format(self):
        """Test handling of invalid date format."""
        pipeline = [
            {
                "name": "Bad Date",
                "client": "Client",
                "deal_value": 100000,
                "likelihood": 5,
                "stage": "Proposal Being Reviewed",
                "expected_close": "not-a-date",
            },
        ]

        # Should not raise, deal should be excluded
        result = calculate_scenarios(pipeline, months=3)
        assert result["totals"]["base"] == 0

    def test_zero_likelihood(self):
        """Test deal with zero likelihood."""
        pipeline = [
            {
                "name": "Zero Likelihood",
                "client": "Client",
                "deal_value": 100000,
                "likelihood": 0,
                "stage": "Cold Lead",
                "expected_close": date.today().isoformat(),
            },
        ]

        result = calculate_scenarios(pipeline, months=1)

        assert result["totals"]["conservative"] == 0
        assert result["totals"]["base"] == 0
        assert result["totals"]["optimistic"] == 0

    def test_very_large_values(self):
        """Test handling of large deal values."""
        pipeline = [
            {
                "name": "Big Deal",
                "client": "Enterprise",
                "deal_value": 10000000,
                "best_case": 15000000,
                "likelihood": 8,
                "stage": "Verbal Agreement",
                "expected_close": date.today().isoformat(),
            },
        ]

        result = calculate_scenarios(pipeline, months=1)

        assert result["totals"]["conservative"] == 8000000  # 10M * 0.8
        assert result["totals"]["base"] == 8000000  # 10M * 0.8
        assert result["totals"]["optimistic"] == 15000000

    def test_months_boundary(self):
        """Test months parameter boundaries."""
        # Minimum 1 month
        result = calculate_scenarios(SAMPLE_PIPELINE, months=1)
        assert len(result["months"]) == 1

        # Maximum 6 months (based on route limits)
        result = calculate_scenarios(SAMPLE_PIPELINE, months=6)
        assert len(result["months"]) == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
