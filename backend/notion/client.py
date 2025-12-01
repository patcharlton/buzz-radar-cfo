"""Notion API client for database queries."""

import os
import requests
from typing import Optional


class NotionClient:
    """Client for Notion API communication."""

    BASE_URL = 'https://api.notion.com/v1'
    API_VERSION = '2022-06-28'

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Notion client.

        Args:
            api_key: Notion API key. If not provided, reads from NOTION_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('NOTION_API_KEY')
        if not self.api_key:
            raise ValueError("NOTION_API_KEY environment variable not set")

    def _get_headers(self) -> dict:
        """Get headers for Notion API requests."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Notion-Version': self.API_VERSION,
            'Content-Type': 'application/json',
        }

    def query_database(self, database_id: str, filter_obj: Optional[dict] = None,
                       sorts: Optional[list] = None) -> list:
        """
        Query a Notion database with automatic pagination.

        Args:
            database_id: The ID of the database to query
            filter_obj: Optional filter object
            sorts: Optional list of sort objects

        Returns:
            list: All pages from the database
        """
        url = f"{self.BASE_URL}/databases/{database_id}/query"
        headers = self._get_headers()

        all_results = []
        has_more = True
        start_cursor = None

        while has_more:
            body = {}
            if filter_obj:
                body['filter'] = filter_obj
            if sorts:
                body['sorts'] = sorts
            if start_cursor:
                body['start_cursor'] = start_cursor

            response = requests.post(url, headers=headers, json=body)

            if response.status_code != 200:
                raise Exception(f"Notion API error: {response.status_code} - {response.text}")

            data = response.json()
            all_results.extend(data.get('results', []))

            has_more = data.get('has_more', False)
            start_cursor = data.get('next_cursor')

        return all_results

    def get_database(self, database_id: str) -> dict:
        """
        Get database metadata.

        Args:
            database_id: The ID of the database

        Returns:
            dict: Database metadata including title and properties
        """
        url = f"{self.BASE_URL}/databases/{database_id}"
        headers = self._get_headers()

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Notion API error: {response.status_code} - {response.text}")

        return response.json()

    def test_connection(self, database_id: Optional[str] = None) -> dict:
        """
        Test connection to Notion API.

        Args:
            database_id: Optional database ID to test access to

        Returns:
            dict: Connection status with database info if ID provided
        """
        try:
            if database_id:
                db = self.get_database(database_id)
                # Extract title from database
                title_parts = db.get('title', [])
                title = ''.join(t.get('plain_text', '') for t in title_parts)
                return {
                    'connected': True,
                    'database_name': title,
                    'database_id': database_id,
                }
            else:
                # Just verify the API key works by making a simple request
                url = f"{self.BASE_URL}/users/me"
                response = requests.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    return {'connected': True}
                else:
                    return {'connected': False, 'error': response.text}
        except Exception as e:
            return {'connected': False, 'error': str(e)}
