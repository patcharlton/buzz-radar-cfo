from flask import Blueprint, redirect, request, session, jsonify, url_for

from xero import XeroAuth

auth_bp = Blueprint('auth', __name__)
xero_auth = XeroAuth()


@auth_bp.route('/auth/login')
def login():
    """Initiate Xero OAuth2 flow."""
    auth_url, state = xero_auth.get_authorization_url()

    # Store state in session for CSRF protection
    session['oauth_state'] = state

    return redirect(auth_url)


@auth_bp.route('/callback')
def callback():
    """Handle OAuth2 callback from Xero."""
    # Verify state to prevent CSRF
    state = request.args.get('state')
    stored_state = session.get('oauth_state')

    if state != stored_state:
        return jsonify({'error': 'Invalid state parameter'}), 400

    # Check for errors
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', 'Unknown error')
        return jsonify({'error': error, 'description': error_description}), 400

    # Get authorization code
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400

    try:
        # Exchange code for tokens
        token_response = xero_auth.exchange_code_for_tokens(code)

        # Get connected tenants
        access_token = token_response['access_token']
        connections = xero_auth.get_connections(access_token)

        if not connections:
            return jsonify({'error': 'No Xero organizations found'}), 400

        # Use the first tenant (for single-tenant apps)
        tenant = connections[0]
        tenant_id = tenant['tenantId']
        tenant_name = tenant.get('tenantName', 'Unknown Organization')

        # Store tokens with tenant info
        xero_auth.store_tokens(token_response, tenant_id, tenant_name)

        # Clear OAuth state from session
        session.pop('oauth_state', None)

        # Redirect to frontend dashboard
        return redirect('http://localhost:5173/')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/auth/status')
def status():
    """Check Xero connection status."""
    try:
        is_connected = xero_auth.is_connected()

        if is_connected:
            from database import XeroToken
            token = XeroToken.query.first()
            return jsonify({
                'connected': True,
                'tenant_name': token.tenant_name if token else None,
                'tenant_id': token.tenant_id if token else None,
            })
        else:
            return jsonify({'connected': False})

    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})


@auth_bp.route('/auth/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from Xero."""
    try:
        xero_auth.disconnect()
        return jsonify({'success': True, 'message': 'Disconnected from Xero'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
