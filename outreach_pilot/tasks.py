import os
import gspread
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import base64
import re
from celery import Celery, group
import random
from .models import EmailTemplate

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
celery = Celery('tasks', broker=redis_url, backend=redis_url)

def calculate_seconds(value, unit):
    if unit == 'seconds': return value
    if unit == 'minutes': return value * 60
    if unit == 'hours': return value * 3600
    if unit == 'days': return value * 86400
    if unit == 'weeks': return value * 7 * 86400
    if unit == 'months': return value * 30 * 86400
    return value * 86400

def send_gmail_message(service, to, subject, body):
    try:
        profile = service.users().getProfile(userId='me').execute()
        sender_email = profile['emailAddress']
        message = MIMEMultipart(); message['to'] = to; message['subject'] = subject
        message['from'] = f"iTranscript360 <{sender_email}>"
        message.attach(MIMEText(body, 'html'))
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent_message = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        return sent_message.get('threadId')
    except Exception as e:
        print(f"ERROR sending email to {to}: {e}"); return None

def clean_reply_content(full_body):
    cleaned_body = re.split(r'\nOn .*wrote:', full_body, flags=re.IGNORECASE)[0]
    cleaned_body = re.split(r'From:.*', cleaned_body)[0]
    cleaned_body = re.split(r'Sent:.*', cleaned_body)[0]
    lines = cleaned_body.splitlines()
    non_quoted_lines = [line for line in lines if not line.strip().startswith('>')]
    return "\n".join(non_quoted_lines).strip()

def get_reply_body(message_part):
    if message_part.get('mimeType') == 'text/plain':
        data = message_part['body'].get('data')
        if data: return base64.urlsafe_b64decode(data).decode('utf-8')
    if 'parts' in message_part:
        for part in message_part['parts']:
            body = get_reply_body(part)
            if body: return body
    return ""

@celery.task
def start_outreach_campaign(credentials_dict, g_sheet_id, column_mappings, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, campaign_templates, use_random_followups):
    creds = Credentials(**credentials_dict); gc = gspread.authorize(creds)
    workbook = gc.open_by_key(g_sheet_id); job_signatures = []
    for sheet_name, mappings in column_mappings.items():
        name_column = mappings['name']; email_column = mappings['email']
        try:
            worksheet = workbook.worksheet(sheet_name)
            contacts = worksheet.get_all_records(head=1)
            for contact in contacts:
                contact_stripped = {k.strip(): v for k,v in contact.items()}
                if not contact_stripped.get("Send Status") or contact_stripped.get("Send Status") == "":
                    contact_email = contact_stripped.get(email_column)
                    contact_name = contact_stripped.get(name_column)
                    if not contact_email or not contact_name:
                        print(f"Skipping row in '{sheet_name}'. Mapped Name='{name_column}', Mapped Email='{email_column}'. Data: {contact_stripped}"); continue
                    task_sig = process_single_contact.s(credentials_dict, g_sheet_id, sheet_name, contact_email, contact_name, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, campaign_templates, use_random_followups)
                    job_signatures.append(task_sig)
        except gspread.exceptions.WorksheetNotFound:
            print(f"ERROR: Worksheet '{sheet_name}' not found. Skipping."); continue
    if job_signatures:
        job_group = group(job_signatures); job_group.apply_async()
        print(f"Dispatched a group of {len(job_signatures)} tasks to the workers.")

@celery.task
def process_single_contact(credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, contact_name, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, campaign_templates, use_random_followups):
    creds = Credentials(**credentials_dict); gmail_service = build('gmail', 'v1', credentials=creds)
    initial_template = campaign_templates[0]
    email_body = initial_template['body'].replace("{dr_name}", contact_name).replace("{name}", contact_name)
    thread_id = send_gmail_message(gmail_service, contact_email, initial_template['subject'], email_body)
    if thread_id:
        start_time_iso = datetime.utcnow().isoformat()
        update_sheet_task.delay(credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, {"Send Status": "INITIAL_SENT", "Thread ID": thread_id, "Follow-up Count": 0, "Wait Period Start Time": start_time_iso})
        check_frequency_seconds = calculate_seconds(check_frequency_value, check_frequency_unit)
        check_for_reply.apply_async(args=[credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, contact_name, thread_id, 0, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, start_time_iso, campaign_templates, use_random_followups], countdown=check_frequency_seconds)

@celery.task
def check_for_reply(credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, contact_name, thread_id, followups_sent, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, start_time_iso, campaign_templates, use_random_followups):
    creds = Credentials(**credentials_dict); gmail_service = build('gmail', 'v1', credentials=creds)
    try:
        thread = gmail_service.users().threads().get(userId='me', id=str(thread_id), format='full').execute()
        if len(thread['messages']) > (followups_sent + 1):
            last_message = thread['messages'][-1]
            reply_content = clean_reply_content(get_reply_body(last_message['payload']))
            analyzer = SentimentIntensityAnalyzer(); score = analyzer.polarity_scores(reply_content)['compound']
            sentiment = "Positive" if score >= 0.05 else "Negative" if score <= -0.05 else "Neutral"
            update_sheet_task.delay(credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, { "Send Status": "REPLIED", "Reply Content": reply_content, "Reply Sentiment": sentiment })
        else:
            start_time = datetime.fromisoformat(start_time_iso)
            total_wait_seconds = calculate_seconds(total_wait_time_value, total_wait_time_unit)
            if datetime.utcnow() < start_time + timedelta(seconds=total_wait_seconds):
                check_frequency_seconds = calculate_seconds(check_frequency_value, check_frequency_unit)
                check_for_reply.apply_async(args=[credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, contact_name, thread_id, followups_sent, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, start_time_iso, campaign_templates, use_random_followups], countdown=check_frequency_seconds)
            elif followups_sent < num_followups:
                print(f"BACKGROUND TASK: Sending follow-up {followups_sent + 1} to {contact_email}")
                email_template = None
                if use_random_followups:
                    all_templates = EmailTemplate.query.all()
                    if all_templates: email_template = {'subject': random.choice(all_templates).subject, 'body': random.choice(all_templates).body}
                else:
                    template_index = followups_sent + 1
                    if len(campaign_templates) > template_index: email_template = campaign_templates[template_index]
                    else: email_template = campaign_templates[-1]
                if not email_template:
                    print(f"ERROR: Could not determine a template for follow-up for {contact_email}."); return
                email_body = email_template['body'].replace("{dr_name}", contact_name).replace("{name}", contact_name)
                send_gmail_message(gmail_service, contact_email, email_template['subject'], email_body)
                new_followup_count = followups_sent + 1; new_start_time_iso = datetime.utcnow().isoformat()
                update_sheet_task.delay(credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, {"Send Status": f"FOLLOWUP_{new_followup_count}_SENT", "Follow-up Count": new_followup_count, "Wait Period Start Time": new_start_time_iso})
                check_frequency_seconds = calculate_seconds(check_frequency_value, check_frequency_unit)
                check_for_reply.apply_async(args=[credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, contact_name, thread_id, new_followup_count, num_followups, total_wait_time_value, total_wait_time_unit, check_frequency_value, check_frequency_unit, new_start_time_iso, campaign_templates, use_random_followups], countdown=check_frequency_seconds)
            else:
                update_sheet_task.delay(credentials_dict, g_sheet_id, contacts_sheet_name, contact_email, {"Send Status": "COMPLETED_NO_REPLY"})
    except Exception as e: print(f"ERROR checking reply for {contact_email}: {e}")

@celery.task
def update_sheet_task(credentials_dict, g_sheet_id, contacts_sheet_name, email, data_to_update):
    creds = Credentials(**credentials_dict); gc = gspread.authorize(creds)
    try:
        sheet = gc.open_by_key(g_sheet_id).worksheet(contacts_sheet_name)
        cell = sheet.find(email)
        if not cell: return
        headers = sheet.row_values(1); header_map = {header: i for i, header in enumerate(headers)}
        new_headers = [h for h in data_to_update.keys() if h not in header_map]
        if new_headers:
            new_header_cells = [gspread.Cell(1, len(headers) + i + 1, header) for i, header in enumerate(new_headers)]
            sheet.update_cells(new_header_cells)
            for header in new_headers: header_map[header] = len(headers); headers.append(header)
        cells_to_update = []
        for header, value in data_to_update.items():
            cells_to_update.append(gspread.Cell(cell.row, header_map[header] + 1, str(value)))
        if "Timestamp" not in header_map:
             sheet.update_cell(1, len(headers) + 1, "Timestamp"); header_map["Timestamp"] = len(headers)
        cells_to_update.append(gspread.Cell(cell.row, header_map["Timestamp"] + 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        sheet.update_cells(cells_to_update)
    except Exception as e: print(f"ERROR updating sheet for {email}: {e}")
