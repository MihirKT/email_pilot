from flask import (Blueprint, session, render_template, flash, redirect, url_for, request, jsonify)
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
import gspread
from outreach_pilot.tasks import start_outreach_campaign
from outreach_pilot.models import EmailTemplate
from outreach_pilot.auth.utils import login_required
import json

campaigns_bp = Blueprint('campaigns', __name__)

def get_user_credentials():
    if 'credentials' not in session: return None
    try:
        creds_data = session['credentials']
        creds = Credentials(**creds_data)
        if creds.expired and creds.refresh_token:
            import google.auth.transport.requests
            creds.refresh(google.auth.transport.requests.Request())
            session['credentials'] = {'token': creds.token, 'refresh_token': creds.refresh_token, 'token_uri': creds.token_uri, 'client_id': creds.client_id, 'client_secret': creds.client_secret, 'scopes': creds.scopes}
        return creds
    except Exception as e:
        print(f"get_user_credentials error: {e}"); session.clear(); return None

def find_best_match(headers, keywords):
    lower_headers = {h.lower().strip(): h for h in headers}
    for keyword in keywords:
        if keyword in lower_headers: return lower_headers[keyword]
    for keyword in keywords:
        for lower_h, original_h in lower_headers.items():
            if keyword in lower_h: return original_h
    return None

@campaigns_bp.route('/')
@login_required
def index():
    creds = get_user_credentials()
    if not creds: return redirect(url_for('auth.login'))
    try:
        drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
        results = drive_service.files().list(q="mimeType='application/vnd.google-apps.spreadsheet'", pageSize=100, fields="files(id, name)").execute()
        return render_template('start_campaign.html', user_email=session.get('user_email'), sheets=results.get('files', []))
    except Exception as e:
        flash(f"Error fetching Google Sheets: {e}", "danger")
        return render_template('start_campaign.html', user_email=session.get('user_email'), sheets=[])

@campaigns_bp.route('/configure', methods=['POST'])
@login_required
def configure_campaign():
    sheet_id = request.form.get('sheet_id')
    if not sheet_id:
        flash("Error: You must select a Google Sheet.", "danger")
        return redirect(url_for('campaigns.index'))
    creds = get_user_credentials()
    if not creds: return redirect(url_for('auth.login'))
    gc = gspread.authorize(creds)
    try:
        workbook = gc.open_by_key(sheet_id)
        session['g_sheet_id'] = sheet_id; session['g_sheet_name'] = workbook.title
        serializable_templates = [{'id': t.id, 'subject': t.subject, 'body': t.body} for t in EmailTemplate.query.all()]
        return render_template('configure_campaign.html', sheets=[s.title for s in workbook.worksheets()], g_sheet_name=workbook.title, templates=serializable_templates)
    except Exception as e:
        flash(f"Error opening sheet: {e}", "danger")
        return redirect(url_for('campaigns.index'))

@campaigns_bp.route('/get-sheet-headers', methods=['POST'])
@login_required
def get_sheet_headers():
    sheet_id = session.get('g_sheet_id')
    worksheet_name = request.json.get('worksheet_name')
    if not sheet_id or not worksheet_name: return jsonify({"error": "Missing sheet ID or worksheet name"}), 400
    creds = get_user_credentials()
    if not creds: return jsonify({"error": "Not authenticated"}), 401
    try:
        gc = gspread.authorize(creds)
        headers = gc.open_by_key(sheet_id).worksheet(worksheet_name).row_values(1)
        return jsonify({"headers": headers, "suggested_name": find_best_match(headers, ['name', 'full name', 'contact']), "suggested_email": find_best_match(headers, ['email', 'e-mail', 'email address', 'mail'])})
    except Exception as e: return jsonify({"error": str(e)}), 500

@campaigns_bp.route('/start', methods=['POST'])
@login_required
def start_campaign():
    if 'credentials' not in session: return redirect(url_for('auth.login'))
    g_sheet_id = session.get('g_sheet_id'); g_sheet_name = session.get('g_sheet_name')
    contacts_sheet_names = request.form.getlist('contacts_sheet')
    column_mappings = {}
    for sheet_name in contacts_sheet_names:
        name_col = request.form.get(f'name_column_{sheet_name}'); email_col = request.form.get(f'email_column_{sheet_name}')
        if not name_col or not email_col:
            flash(f"Error: Missing column mapping for sheet '{sheet_name}'.", "danger"); return redirect(request.referrer or url_for('campaigns.index'))
        column_mappings[sheet_name] = {'name': name_col, 'email': email_col}
    try:
        num_followups = int(request.form.get('num_followups', 1)); total_wait_time_value = int(request.form.get('total_wait_time_value', 3)); check_frequency_value = int(request.form.get('check_frequency_value', 4))
        total_wait_time_unit = request.form.get('total_wait_time_unit', 'days'); check_frequency_unit = request.form.get('check_frequency_unit', 'hours')
    except (ValueError, TypeError):
        flash("Error: Invalid numeric values provided.", "danger"); return redirect(request.referrer or url_for('campaigns.index'))
    campaign_templates = []
    initial_subject = request.form.get('initial_subject'); initial_body = request.form.get('initial_body')
    if not initial_subject or not initial_body:
        flash("Error: Initial email subject and body are required.", "danger"); return redirect(request.referrer or url_for('campaigns.index'))
    campaign_templates.append({'subject': initial_subject, 'body': initial_body})
    if 'use_different_followups' in request.form:
        for i in range(1, num_followups + 1):
            subject = request.form.get(f'followup_{i}_subject'); body = request.form.get(f'followup_{i}_body')
            if not subject or not body:
                flash(f"Error: Missing subject/body for follow-up #{i}.", "danger"); return redirect(request.referrer or url_for('campaigns.index'))
            campaign_templates.append({'subject': subject, 'body': body})
    use_random_followups = 'use_random_followups' in request.form
    start_outreach_campaign.delay(session['credentials'], g_sheet_id, column_mappings, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, campaign_templates, use_random_followups)
    return render_template('campaign_started.html', sheet_name=g_sheet_name)
