import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode
import requests

from config import Config
from database import db, XeroToken


class XeroAuth:
    """Handle Xero OAuth2 authentication flow."""

    def __init__(self):
        self.client_id = Config.XERO_CLIENT_ID
        self.client_secret = Config.XERO_CLIENT_SECRET
        self.redirect_uri = Config.XERO_REDIRECT_URI
        self.auth_url = Config.XERO_AUTH_URL
        self.token_url = Config.XERO_TOKEN_URL
        self.scopes = Config.XERO_SCOPES

    def get_authorization_url(self, state=None):
        """
        Generate the authorization URL for the Xero OAuth2 flow.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            tuple: (authorization_url, state)
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'state': state,
        }

        url = f"{self.auth_url}?{urlencode(params)}"
        return url, state

    def exchange_code_for_tokens(self, authorization_code):
        """
        Exchange the authorization code for access and refresh tokens.

        Args:
            authorization_code: The code received from Xero callback

        Returns:
            dict: Token response from Xero
        """
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
        }

        response = requests.post(
            self.token_url,
            data=data,
            auth=(self.client_id, self.client_secret),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")

        return response.json()

    def refresh_access_token(self, refresh_token):
        """
        Refresh an expired access token.

        Args:
            refresh_token: The current refresh token

        Returns:
            dict: New token response from Xero
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        response = requests.post(
            self.token_url,
            data=data,
            auth=(self.client_id, self.client_secret),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.text}")

        return response.json()

    def get_connections(self, access_token):
        """
        Get the list of connected tenants (organizations).

        Args:
            access_token: Valid access token

        Returns:
            list: Connected Xero tenants
        """
        response = requests.get(
            'https://api.xero.com/connections',
            headers={'Authorization': f'Bearer {access_token}'},
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get connections: {response.text}")

        return response.json()

    def store_tokens(self, token_response, tenant_id=None, tenant_name=None):
        """
        Store tokens securely in the database.

        Args:
            token_response: Response from token exchange
            tenant_id: Xero tenant ID
            tenant_name: Xero tenant name

        Returns:
            XeroToken: The stored token record
        """
        # Calculate expiry time (tokens last 30 minutes)
        expires_in = token_response.get('expires_in', 1800)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Check for existing token and update, or create new
        existing = XeroToken.query.first()

        if existing:
            existing.set_access_token(token_response['access_token'])
            existing.set_refresh_token(token_response['refresh_token'])
            existing.token_type = token_response.get('token_type', 'Bearer')
            existing.expires_at = expires_at
            if tenant_id:
                existing.tenant_id = tenant_id
            if tenant_name:
                existing.tenant_name = tenant_name
            token = existing
        else:
            token = XeroToken(
                token_type=token_response.get('token_type', 'Bearer'),
                expires_at=expires_at,
                tenant_id=tenant_id,
                tenant_name=tenant_name,
            )
            token.set_access_token(token_response['access_token'])
            token.set_refresh_token(token_response['refresh_token'])
            db.session.add(token)

        db.session.commit()
        return token

    def get_valid_token(self):
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            str: Valid access token, or None if not connected
        """
        token = XeroToken.query.first()
        if not token:
            return None

        # Refresh if token is expired or about to expire (within 5 minutes)
        if token.is_expired() or (token.expires_at - datetime.utcnow()).total_seconds() < 300:
            try:
                new_tokens = self.refresh_access_token(token.get_refresh_token())
                token = self.store_tokens(
                    new_tokens,
                    tenant_id=token.tenant_id,
                    tenant_name=token.tenant_name,
                )
            except Exception as e:
                # If refresh fails, token is invalid
                db.session.delete(token)
                db.session.commit()
                raise Exception(f"Token refresh failed: {e}")

        return token.get_access_token()

    def get_tenant_id(self):
        """Get the stored Xero tenant ID."""
        token = XeroToken.query.first()
        return token.tenant_id if token else None

    def is_connected(self):
        """Check if connected to Xero with valid tokens."""
        token = XeroToken.query.first()
        if not token:
            return False

        try:
            self.get_valid_token()
            return True
        except Exception:
            return False

    def disconnect(self):
        """Disconnect from Xero by removing stored tokens."""
        token = XeroToken.query.first()
        if token:
            db.session.delete(token)
            db.session.commit()
            return True
        return False
