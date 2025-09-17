import os
from flask import Blueprint, redirect, url_for, session, request, flash, render_template
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery

auth_bp = Blueprint('auth', __name__)

CLIENT_SECRETS_FILE = 'credentials.json'
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

@auth_bp.route('/login-page')
def login_page():
    return render_template('login.html')

@auth_bp.route('/login')
def login():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        flash("Error: credentials.json not found. The app cannot authenticate.", "danger")
        return redirect(url_for('auth.login_page'))
    
    redirect_uri = url_for('auth.oauth2callback', _external=True)
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['state'] = state
    return redirect(authorization_url)


@auth_bp.route('/callback')
def oauth2callback():
    state = session.pop('state', '')
    redirect_uri = url_for('auth.oauth2callback', _external=True)
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri
    )
    
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        flash(f"Authentication failed: {e}", "danger")
        # CORRECTED: Redirect to the correct campaigns.index
        return redirect(url_for('campaigns.index'))

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    try:
        service = googleapiclient.discovery.build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        session['user_email'] = user_info['email']
    except Exception as e:
        flash(f"Error getting user info: {e}", "danger")
        # CORRECTED: Redirect to the correct campaigns.index
        return redirect(url_for('campaigns.index'))

    # --- THIS IS THE FINAL FIX ---
    # Redirect to the correct campaigns.index endpoint after successful login
    return redirect(url_for('campaigns.index'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login_page'))
