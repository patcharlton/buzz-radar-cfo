"""Claude API client for AI CFO analysis."""

import os
import json
from anthropic import Anthropic

from .prompts import (
    DAILY_INSIGHTS_SYSTEM,
    MONTHLY_ANALYSIS_SYSTEM,
    QA_SYSTEM,
    CASH_FORECAST_SYSTEM,
    ANOMALY_DETECTION_SYSTEM,
    build_daily_prompt,
    build_monthly_prompt,
    build_qa_prompt,
    build_forecast_prompt,
    build_anomaly_prompt,
)


class ClaudeClient:
    """Client for interacting with Claude API."""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 2048

    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self.model = self.DEFAULT_MODEL

    def analyse(self, system_prompt, user_prompt, max_tokens=None):
        """
        Send a prompt to Claude and get a response.

        Args:
            system_prompt: The system prompt setting context
            user_prompt: The user message with specific request
            max_tokens: Maximum tokens in response (default: 2048)

        Returns:
            str: Claude's response text
        """
        if max_tokens is None:
            max_tokens = self.MAX_TOKENS

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text

            return "No response generated."

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

    def analyse_json(self, system_prompt, user_prompt, max_tokens=None):
        """
        Send a prompt to Claude and get a JSON response.

        Args:
            system_prompt: The system prompt setting context
            user_prompt: The user message with specific request
            max_tokens: Maximum tokens in response

        Returns:
            dict: Parsed JSON response
        """
        response_text = self.analyse(system_prompt, user_prompt, max_tokens)

        # Try to extract JSON from the response
        try:
            # First try direct parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Return error structure if JSON parsing fails
            return {
                'error': 'Failed to parse JSON response',
                'raw_response': response_text
            }

    def daily_insights(self, financial_data, context):
        """
        Generate daily financial insights.

        Args:
            financial_data: Dict with cash_position, receivables, payables, profit_loss
            context: Dict with business, clients, goals, rules

        Returns:
            str: Daily insights and recommendations
        """
        user_prompt = build_daily_prompt(financial_data, context)
        return self.analyse(DAILY_INSIGHTS_SYSTEM, user_prompt)

    def monthly_analysis(self, financial_data, context):
        """
        Generate monthly strategic analysis.

        Args:
            financial_data: Dict with financial metrics
            context: Dict with business context

        Returns:
            str: Monthly analysis and strategic recommendations
        """
        user_prompt = build_monthly_prompt(financial_data, context)
        return self.analyse(MONTHLY_ANALYSIS_SYSTEM, user_prompt, max_tokens=3000)

    def answer_question(self, question, financial_data, context):
        """
        Answer a specific financial question.

        Args:
            question: The user's question
            financial_data: Dict with financial data
            context: Dict with business context

        Returns:
            str: Answer to the question
        """
        user_prompt = build_qa_prompt(question, financial_data, context)
        return self.analyse(QA_SYSTEM, user_prompt)

    def cash_forecast(self, financial_data, context):
        """
        Generate 4-week cash flow forecast.

        Args:
            financial_data: Dict with cash_position, receivables, payables
            context: Dict with business context including pipeline

        Returns:
            dict: Structured forecast with weekly projections
        """
        user_prompt = build_forecast_prompt(financial_data, context)
        return self.analyse_json(CASH_FORECAST_SYSTEM, user_prompt, max_tokens=2500)

    def detect_anomalies(self, financial_data, context):
        """
        Detect financial anomalies and risks.

        Args:
            financial_data: Dict with financial data
            context: Dict with business context

        Returns:
            dict: Structured anomaly report
        """
        user_prompt = build_anomaly_prompt(financial_data, context)
        return self.analyse_json(ANOMALY_DETECTION_SYSTEM, user_prompt, max_tokens=2500)
