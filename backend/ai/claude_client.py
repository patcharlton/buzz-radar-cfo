"""Claude API client for AI CFO analysis."""

import os
from anthropic import Anthropic

from .prompts import (
    DAILY_INSIGHTS_SYSTEM,
    MONTHLY_ANALYSIS_SYSTEM,
    QA_SYSTEM,
    build_daily_prompt,
    build_monthly_prompt,
    build_qa_prompt,
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
