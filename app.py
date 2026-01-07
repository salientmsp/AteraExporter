from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, time, timedelta
import os
from dotenv import load_dotenv
import requests
import json
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Database configuration - use file-based SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'data', 'atera.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
print(f"Using SQLite database at: {db_path}")

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Add context processor for templates
@app.context_processor
def inject_now():
    return {
        'now': datetime.now(),
        'format_datetime': format_datetime,
        'format_date': lambda date: date.strftime('%Y-%m-%d') if date else ''
    }

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)

class OnCallSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    technician = db.relationship('Technician', backref='schedules')

class BusinessHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(50), nullable=False, unique=True)
    ticket_number = db.Column(db.String(50))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    comment = db.Column(db.Text)  # Latest comment/worklog
    resolution = db.Column(db.Text)  # Resolved comments
    created_at = db.Column(db.DateTime, nullable=False)
    closed_date = db.Column(db.DateTime)
    resolved_date = db.Column(db.DateTime)
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20))
    ticket_type = db.Column(db.String(50))
    ticket_impact = db.Column(db.String(50))
    client = db.Column(db.String(100))
    user = db.Column(db.String(100))  # Technician
    end_user_firstname = db.Column(db.String(100))
    end_user_lastname = db.Column(db.String(100))
    end_user_email = db.Column(db.String(200))
    end_user_phone = db.Column(db.String(50))
    notified = db.Column(db.Boolean, default=False)

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), nullable=False, unique=True)
    value = db.Column(db.String(255))

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    notified = db.Column(db.Boolean, default=False)

# Atera Data Models for Export
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), nullable=False, unique=True)
    customer_name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(200))
    business_number = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    phone = db.Column(db.String(50))
    fax = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    last_modified = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(50), nullable=False, unique=True)
    machine_name = db.Column(db.String(200))
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    domain_name = db.Column(db.String(200))
    operating_system = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    last_login_user = db.Column(db.String(100))
    antivirus_status = db.Column(db.String(50))
    agent_version = db.Column(db.String(50))
    online = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(50), nullable=False, unique=True)
    alert_message = db.Column(db.Text)
    alert_category = db.Column(db.String(100))
    severity = db.Column(db.String(50))
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    device_name = db.Column(db.String(200))
    alert_source = db.Column(db.String(100))
    archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    threshold_value = db.Column(db.String(100))
    additional_info = db.Column(db.Text)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.String(50), nullable=False, unique=True)
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    mobile_phone = db.Column(db.String(50))
    job_title = db.Column(db.String(100))
    is_contact_person = db.Column(db.Boolean, default=False)
    in_ignore_mode = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.String(50), nullable=False, unique=True)
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    contract_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    contract_type = db.Column(db.String(100))
    amount = db.Column(db.Float)
    billing_period = db.Column(db.String(50))
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.String(50), nullable=False, unique=True)
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    total_amount = db.Column(db.Float)
    paid = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class SNMPDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False, unique=True)
    device_name = db.Column(db.String(200))
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    snmp_version = db.Column(db.String(20))
    device_type = db.Column(db.String(100))
    system_name = db.Column(db.String(200))
    system_location = db.Column(db.String(200))
    system_contact = db.Column(db.String(200))
    system_description = db.Column(db.Text)
    last_online = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class TCPDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False, unique=True)
    device_name = db.Column(db.String(200))
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    port = db.Column(db.Integer)
    device_type = db.Column(db.String(100))  # TCP, HTTP, Generic
    monitoring_enabled = db.Column(db.Boolean, default=True)
    last_online = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class KnowledgeBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.String(50), nullable=False, unique=True)
    title = db.Column(db.String(500))
    content = db.Column(db.Text)
    category = db.Column(db.String(100))
    keywords = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    last_modified_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime)
    last_modified = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), nullable=False, unique=True)
    product_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    rate = db.Column(db.Float)
    rate_type = db.Column(db.String(50))  # hourly, monthly, one-time, etc.
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.String(50), nullable=False, unique=True)
    expense_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    ticket_id = db.Column(db.String(50))
    expense_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class HTTPDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False, unique=True)
    device_name = db.Column(db.String(200))
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    url = db.Column(db.String(500))
    expected_response = db.Column(db.String(500))
    monitoring_enabled = db.Column(db.Boolean, default=True)
    last_online = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class GenericDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False, unique=True)
    device_name = db.Column(db.String(200))
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    monitoring_enabled = db.Column(db.Boolean, default=True)
    last_online = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.String(50), nullable=False, unique=True)
    department_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

class ExportLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    export_type = db.Column(db.String(50), nullable=False)  # tickets, customers, agents, etc.
    export_format = db.Column(db.String(20), nullable=False)  # csv, json, excel
    file_path = db.Column(db.String(500))
    record_count = db.Column(db.Integer)
    status = db.Column(db.String(20))  # success, failed, in_progress
    error_message = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

# Helper functions
def get_setting(key, default=''):
    """Get a setting value from the database or return the default"""
    try:
        with app.app_context():
            setting = SystemSetting.query.filter_by(key=key).first()
            if setting:
                return setting.value
            return default
    except Exception as e:
        app.logger.warning(f"Error getting setting {key}: {str(e)}")
        return default

def save_setting(key, value):
    """Save a setting value to the database"""
    try:
        with app.app_context():
            setting = SystemSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SystemSetting(key=key, value=value)
                db.session.add(setting)
            db.session.commit()
            return True
    except Exception as e:
        app.logger.error(f"Error saving setting {key}: {str(e)}")
        db.session.rollback()
        return False

def get_timezone():
    """Get the configured timezone or default to UTC"""
    with app.app_context():
        setting = SystemSetting.query.filter_by(key='timezone').first()
        if setting and setting.value in pytz.all_timezones:
            return pytz.timezone(setting.value)
        return pytz.timezone('UTC')  # Default to UTC

def convert_to_local_time(dt):
    """Convert a datetime to the configured local timezone"""
    if dt is None:
        return None
        
    # If the datetime is naive (no timezone info), assume it's UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
        
    # Convert to the configured timezone
    local_tz = get_timezone()
    return dt.astimezone(local_tz)

def format_datetime(dt, format_str='%Y-%m-%d %H:%M'):
    """Format a datetime in the configured timezone"""
    if dt is None:
        return ''
        
    local_dt = convert_to_local_time(dt)
    return local_dt.strftime(format_str)

def is_business_hours(dt=None):
    """Check if the current time is within business hours and not a holiday"""
    if dt is None:
        dt = datetime.now()
    
    # Ensure the datetime is in the local timezone
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        # Convert to local timezone if it has timezone info
        local_dt = convert_to_local_time(dt)
    else:
        # If it's a naive datetime, assume it's already local
        local_dt = dt
    
    app.logger.debug(f"Checking business hours for datetime: {local_dt} (original: {dt})")
    
    # Check if today is a holiday
    today_date = local_dt.date()
    holiday = Holiday.query.filter_by(date=today_date).first()
    if holiday:
        app.logger.info(f"Today is a holiday: {holiday.name}")
        return False  # If it's a holiday, it's not business hours
    
    # Get day of week (0 = Monday, 6 = Sunday)
    day_of_week = local_dt.weekday()
    app.logger.debug(f"Day of week: {day_of_week} (0=Monday, 6=Sunday)")
    
    # Get current time
    current_time = local_dt.time()
    app.logger.debug(f"Current time: {current_time}")
    
    # Check if business hours exist for this day
    business_hours = BusinessHours.query.filter_by(day_of_week=day_of_week).first()
    if not business_hours:
        app.logger.info(f"No business hours defined for day {day_of_week}")
        return False
    
    app.logger.debug(f"Business hours for day {day_of_week}: {business_hours.start_time} - {business_hours.end_time}")
    
    is_within_hours = business_hours.start_time <= current_time <= business_hours.end_time
    app.logger.info(f"Is within business hours: {is_within_hours}")
    
    return is_within_hours

def get_current_on_call():
    """Get all current on-call technicians (handles overlapping schedules)"""
    now = datetime.now()
    schedules = OnCallSchedule.query.filter(
        OnCallSchedule.start_date <= now,
        OnCallSchedule.end_date >= now
    ).all()
    
    technicians = []
    for schedule in schedules:
        if schedule.technician not in technicians:
            technicians.append(schedule.technician)
    
    return technicians

def send_sms_notification(technician, ticket, holiday_message=""):
    """Send SMS notification to on-call technician"""
    # Check if the ticket has already been notified
    if ticket.notified:
        app.logger.info(f"Skipping notification for ticket #{ticket.ticket_id} as it was already sent")
        return True
        
    # Get Twilio credentials from settings (fall back to environment variables if not in database)
    account_sid = get_setting('twilio_account_sid', os.getenv('TWILIO_ACCOUNT_SID', ''))
    auth_token = get_setting('twilio_auth_token', os.getenv('TWILIO_AUTH_TOKEN', ''))
    from_number = get_setting('twilio_phone_number', os.getenv('TWILIO_PHONE_NUMBER', ''))
    
    if not all([account_sid, auth_token, from_number]):
        app.logger.error("Twilio credentials not configured")
        return False
    
    # Check if technician has a valid phone number
    if not technician.phone or not technician.phone.strip():
        app.logger.error(f"Cannot send notification: Technician {technician.name} has no phone number")
        return False
        
    client = Client(account_sid, auth_token)
    
    # Format the message according to the requested template
    message = f"New On Call Ticket{holiday_message}\n"
    message += f"Client: {ticket.client if hasattr(ticket, 'client') and ticket.client else 'Unknown'}\n"
    message += f"User: {ticket.user if hasattr(ticket, 'user') and ticket.user else 'Unknown'}\n"
    message += f"Subject: {ticket.title}\n"
    message += f"Link: https://app.atera.com/new/ticket/{ticket.ticket_id}"
    
    try:
        # Log the notification attempt
        app.logger.info(f"Initiating Twilio SMS to {technician.name} at {technician.phone} for ticket #{ticket.ticket_id}")
        
        # Send the message
        try:
            message_response = client.messages.create(
                body=message,
                from_=from_number,
                to=technician.phone
            )
            
            # Log the successful message with Twilio SID for tracking
            app.logger.info(f"SMS notification sent to {technician.name} for ticket #{ticket.ticket_id} - Twilio SID: {message_response.sid}")
            return True
            
        except TwilioRestException as e:
            # Handle specific Twilio errors with detailed logging
            error_code = e.code if hasattr(e, 'code') else 'unknown'
            error_msg = e.msg if hasattr(e, 'msg') else str(e)
            
            app.logger.error(f"Twilio API error when sending SMS to {technician.name}: Code {error_code} - {error_msg}")
            
            # Log specific error types for easier troubleshooting
            if error_code == 21211:
                app.logger.error(f"Invalid phone number format for {technician.name}: {technician.phone}")
            elif error_code == 21612:
                app.logger.error("Twilio account lacks permission to send SMS to this number")
            elif error_code == 21608:
                app.logger.error("Twilio message body exceeds maximum allowed length")
            elif error_code == 20003:
                app.logger.error("Twilio authentication error - check account SID and auth token")
            
            return False
            
        except Exception as e:
            app.logger.error(f"Unexpected error when sending SMS via Twilio: {str(e)}")
            return False
            
    except Exception as e:
        app.logger.error(f"Failed to send SMS (general error): {str(e)}")
        return False

def fetch_tickets_from_atera():
    """Fetch tickets from Atera API"""
    # Update the last check time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    last_check = SystemSetting.query.filter_by(key='last_ticket_check').first()
    
    if last_check:
        last_check.value = current_time
    else:
        last_check = SystemSetting(key='last_ticket_check', value=current_time)
        db.session.add(last_check)
    
    db.session.commit()
    
    # Get Atera API key from settings (fall back to environment variable if not in database)
    api_key = get_setting('atera_api_key', os.getenv('ATERA_API_KEY', ''))
    if not api_key:
        app.logger.error("Atera API key not configured")
        return []
    
    headers = {
        'X-API-KEY': api_key,
        'Accept': 'application/json'
    }
    
    try:
        app.logger.info("Initiating connection to Atera API to fetch tickets")
        
        # Fetch tickets from Atera API with query parameters for open tickets
        try:
            response = requests.get(
                'https://app.atera.com/api/v3/tickets',
                headers=headers,
                params={
                    'page': 1,
                    'itemsInPage': 50,
                    'ticketStatus': 'Open'
                },
                timeout=30  # Add timeout to prevent hanging indefinitely
            )
            
            app.logger.info(f"Atera API response received with status code: {response.status_code}")
            
            if response.status_code != 200:
                error_message = f"Failed to fetch tickets from Atera API: HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    error_message += f" - {error_detail}"
                except:
                    pass
                
                app.logger.error(error_message)
                return []
                
        except requests.exceptions.Timeout:
            app.logger.error("Timeout error connecting to Atera API - connection timed out after 30 seconds")
            return []
        except requests.exceptions.ConnectionError as e:
            app.logger.error(f"Connection error connecting to Atera API: {str(e)}")
            return []
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error connecting to Atera API: {str(e)}")
            return []
        
        # Get the items from the response
        response_data = response.json()
        tickets = response_data.get('items', [])
        
        app.logger.info(f"Found {len(tickets)} tickets from Atera API")
        
        # Process new tickets
        for ticket_data in tickets:
            try:
                # Extract ticket ID
                ticket_id = str(ticket_data.get('TicketID'))
                app.logger.debug(f"Processing ticket ID: {ticket_id}")
                
                # Check if ticket already exists in our database
                existing_ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
                if existing_ticket:
                    app.logger.debug(f"Skipping existing ticket: {ticket_id}")
                    continue
                
                app.logger.info(f"Found new ticket: {ticket_id}")
                    
                # Get ticket details
                title = ticket_data.get('TicketTitle', 'No Title')
                description = ticket_data.get('FirstComment', '')
                status = ticket_data.get('TicketStatus', 'Unknown')
                priority = ticket_data.get('TicketPriority', 'Unknown')
                
                # Extract client and user information
                client = ticket_data.get('CustomerName', 'Unknown')
                
                # Combine first and last name for the user if available
                first_name = ticket_data.get('EndUserFirstName', '')
                last_name = ticket_data.get('EndUserLastName', '')
                if first_name or last_name:
                    user = f"{first_name} {last_name}".strip()
                else:
                    user = 'Unknown'
                
                # Parse creation date - use current time if not available
                try:
                    # The API returns date in format: 2025-04-16T16:34:41Z
                    created_at_str = ticket_data.get('TicketCreatedDate')
                    if created_at_str:
                        # Remove the Z and handle timezone
                        created_at_str = created_at_str.replace('Z', '+00:00')
                        created_at = datetime.fromisoformat(created_at_str)
                        app.logger.debug(f"Ticket {ticket_id} created at UTC: {created_at}")
                        
                        # Convert to local timezone for proper business hours checking
                        local_created_at = convert_to_local_time(created_at)
                        app.logger.debug(f"Ticket {ticket_id} created at local time: {local_created_at}")
                    else:
                        app.logger.warning(f"No creation date found for ticket {ticket_id}, using current time")
                        created_at = datetime.now()
                        local_created_at = created_at  # Already local time
                except (ValueError, TypeError) as e:
                    app.logger.error(f"Error parsing date for ticket {ticket_id}: {str(e)} - Date string: {created_at_str if 'created_at_str' in locals() else 'N/A'}")
                    created_at = datetime.now()
                    local_created_at = created_at  # Already local time
                    app.logger.warning(f"Using current time for ticket {ticket_id} creation date")
                
                # Create new ticket record
                try:
                    new_ticket = Ticket(
                        ticket_id=ticket_id,
                        title=title,
                        description=description,
                        status=status,
                        priority=priority,
                        client=client,
                        user=user,
                        created_at=created_at,
                        notified=False
                    )
                    
                    # Add to database session
                    db.session.add(new_ticket)
                    db.session.flush()  # Flush to get the ID without committing
                    app.logger.debug(f"Successfully added ticket {ticket_id} to database session")
                except Exception as e:
                    app.logger.error(f"Error creating ticket record in database: {str(e)}")
                    continue  # Skip to next ticket if we can't create this one
                
                # Check if today is a holiday
                today_date = datetime.now().date()
                holiday = Holiday.query.filter_by(date=today_date).first()
                
                app.logger.info(f"Checking notification criteria for ticket {ticket_id}")
                app.logger.info(f"Ticket creation time (UTC): {created_at}")
                app.logger.info(f"Ticket creation time (local): {local_created_at}")
                
                # Check business hours status using the local creation time
                is_within_hours = is_business_hours(local_created_at)
                app.logger.info(f"Is ticket within business hours: {is_within_hours}")
                
                # Check if notification is needed (outside business hours or holiday)
                should_notify = holiday or not is_within_hours
                app.logger.info(f"Should send notification: {should_notify} (Holiday: {bool(holiday)}, Outside business hours: {not is_within_hours})")
                
                if should_notify:
                    # Get all current on-call technicians
                    technicians = get_current_on_call()
                    app.logger.info(f"Found {len(technicians)} on-call technicians")
                    
                    if technicians:
                        notification_sent = False
                        
                        # Prepare notification message with holiday info if applicable
                        holiday_message = f" (Holiday: {holiday.name})" if holiday else ""
                        
                        # Send notification to each on-call technician
                        for technician in technicians:
                            app.logger.info(f"Sending notification for ticket {ticket_id} to {technician.name}{holiday_message}")
                            
                            # Send notification
                            if send_sms_notification(technician, new_ticket, holiday_message):
                                notification_sent = True
                                app.logger.info(f"Notification sent successfully to {technician.name} for ticket {ticket_id}")
                            else:
                                app.logger.error(f"Failed to send notification to {technician.name} for ticket {ticket_id}")
                        
                        # Mark as notified if at least one notification was sent successfully
                        if notification_sent:
                            new_ticket.notified = True
                            
                            # Mark holiday as notified if applicable
                            if holiday and not holiday.notified:
                                holiday.notified = True
                                app.logger.info(f"Holiday {holiday.name} marked as notified")
                            
                app.logger.info(f"Added new ticket: {ticket_id} - {title}")
                            
            except Exception as e:
                app.logger.error(f"Error processing ticket: {str(e)}")
                continue
        
        try:
            db.session.commit()
            app.logger.info(f"Successfully committed {len(tickets)} new tickets to database")
            return tickets
        except Exception as e:
            app.logger.error(f"Database commit error: {str(e)}")
            db.session.rollback()
            app.logger.warning("Database changes rolled back due to error")
            return []
    except Exception as e:
        app.logger.error(f"Error fetching tickets: {str(e)}")
        try:
            db.session.rollback()
            app.logger.warning("Database changes rolled back due to error")
        except Exception as rollback_error:
            app.logger.critical(f"Failed to rollback database transaction: {str(rollback_error)}")
        return []

# Get refresh interval from settings or use default (5 minutes)
def get_refresh_interval():
    try:
        with app.app_context():
            setting = SystemSetting.query.filter_by(key='refresh_interval').first()
            if setting and setting.value.isdigit():
                return int(setting.value)
            return 5  # Default: 5 minutes
    except Exception as e:
        app.logger.warning(f"Error getting refresh interval: {str(e)}. Using default value.")
        return 5  # Default: 5 minutes

# Schedule the ticket fetching job with the configurable interval
@scheduler.scheduled_job('interval', minutes=get_refresh_interval())
def scheduled_ticket_check():
    job_start_time = datetime.now()
    app.logger.info(f"Starting scheduled ticket check at {job_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        with app.app_context():
            app.logger.info(f"Running scheduled ticket check (every {get_refresh_interval()} minutes)")
            
            # Update last check time
            try:
                now = datetime.now()
                last_check = SystemSetting.query.filter_by(key='last_ticket_check').first()
                if last_check:
                    last_check.value = format_datetime(now)
                    app.logger.debug(f"Updated last_ticket_check to {format_datetime(now)}")
                else:
                    last_check = SystemSetting(key='last_ticket_check', value=format_datetime(now))
                    db.session.add(last_check)
                    app.logger.debug(f"Created new last_ticket_check with value {format_datetime(now)}")
                db.session.commit()
            except Exception as e:
                app.logger.error(f"Database error updating last check time: {str(e)}")
                try:
                    db.session.rollback()
                    app.logger.warning("Database changes rolled back due to error")
                except Exception as rollback_error:
                    app.logger.critical(f"Failed to rollback database transaction: {str(rollback_error)}")
            
            # Fetch tickets
            try:
                tickets = fetch_tickets_from_atera()
                app.logger.info(f"Ticket check completed, processed {len(tickets) if tickets else 0} tickets")
            except Exception as e:
                app.logger.error(f"Error fetching tickets from Atera: {str(e)}")
                
    except Exception as e:
        app.logger.error(f"Unhandled error in scheduled ticket check: {str(e)}")
    finally:
        job_end_time = datetime.now()
        duration = (job_end_time - job_start_time).total_seconds()
        app.logger.info(f"Scheduled ticket check completed in {duration:.2f} seconds")

# Routes
@app.route('/restart-service')
@login_required
def restart_service():
    """Restart the application service"""
    try:
        app.logger.info(f"Service restart initiated by {current_user.username}")
        
        # Return success response before actually restarting
        response = jsonify({
            'success': True,
            'message': 'Service restart initiated. Please wait a moment for the service to restart.'
        })
        
        # Schedule the restart to happen after the response is sent
        def restart_after_response():
            # Give a brief delay to ensure the response is sent
            import time
            time.sleep(1)
            
            # Attempt to restart using different methods depending on the environment
            import os
            import sys
            import subprocess
            
            app.logger.info("Executing service restart")
            
            try:
                # Check if we're running as a Windows service
                service_name = os.getenv('SERVICE_NAME', 'OnCallTicketMonitor')
                subprocess.run(['sc', 'stop', service_name], check=False)
                subprocess.run(['sc', 'start', service_name], check=False)
                app.logger.info(f"Attempted to restart Windows service: {service_name}")
            except Exception as e:
                app.logger.error(f"Failed to restart as Windows service: {str(e)}")
                
                # Fallback to restarting the Python process
                try:
                    os.execv(sys.executable, ['python'] + sys.argv)
                    app.logger.info("Attempted to restart Python process")
                except Exception as e:
                    app.logger.critical(f"Failed to restart Python process: {str(e)}")
        
        # Start the restart process in a separate thread
        import threading
        restart_thread = threading.Thread(target=restart_after_response)
        restart_thread.daemon = True
        restart_thread.start()
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error initiating service restart: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error restarting service: {str(e)}'
        }), 500

@app.route('/refresh-tickets')
@login_required
def refresh_tickets_route():
    """Manually refresh tickets from Atera API"""
    job_start_time = datetime.now()
    app.logger.info(f"Manual ticket refresh initiated by {current_user.username} at {job_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Update last check time
        now = datetime.now()
        try:
            last_check = SystemSetting.query.filter_by(key='last_ticket_check').first()
            if last_check:
                last_check.value = format_datetime(now)
                app.logger.debug(f"Updated last_ticket_check to {format_datetime(now)}")
            else:
                last_check = SystemSetting(key='last_ticket_check', value=format_datetime(now))
                db.session.add(last_check)
                app.logger.debug(f"Created new last_ticket_check with value {format_datetime(now)}")
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Database error updating last check time: {str(e)}")
            try:
                db.session.rollback()
                app.logger.warning("Database changes rolled back due to error")
            except Exception as rollback_error:
                app.logger.critical(f"Failed to rollback database transaction: {str(rollback_error)}")
            return jsonify({
                'success': False,
                'message': f'Database error: {str(e)}'
            }), 500
        
        # Fetch tickets
        try:
            tickets = fetch_tickets_from_atera()
            
            job_end_time = datetime.now()
            duration = (job_end_time - job_start_time).total_seconds()
            app.logger.info(f"Manual ticket refresh completed in {duration:.2f} seconds, processed {len(tickets) if tickets else 0} tickets")
            
            # Return JSON response for AJAX requests
            return jsonify({
                'success': True,
                'message': f'Successfully fetched {len(tickets)} tickets in {duration:.2f} seconds',
                'last_check': format_datetime(now),
                'ticket_count': len(tickets)
            })
        except Exception as e:
            app.logger.error(f"Error fetching tickets from Atera API: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'API Error: {str(e)}'
            }), 503  # Service Unavailable
            
    except Exception as e:
        app.logger.error(f"Unhandled error refreshing tickets: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error refreshing tickets: {str(e)}'
        }), 500

@app.route('/')
@login_required
def index():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(20).all()
    current_on_call_technicians = get_current_on_call()
    
    # Get the last ticket check time
    last_check = SystemSetting.query.filter_by(key='last_ticket_check').first()
    last_check_time = last_check.value if last_check else None
    
    return render_template('index.html', 
                           tickets=tickets, 
                           current_on_call_technicians=current_on_call_technicians,
                           last_check_time=last_check_time)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # In production, use proper password hashing
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/technicians')
@login_required
def technicians():
    techs = Technician.query.all()
    return render_template('technicians.html', technicians=techs)

@app.route('/technicians/add', methods=['GET', 'POST'])
@login_required
def add_technician():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        new_tech = Technician(name=name, phone=phone, email=email)
        db.session.add(new_tech)
        db.session.commit()
        
        flash('Technician added successfully')
        return redirect(url_for('technicians'))
    
    return render_template('add_technician.html')

@app.route('/technicians/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_technician(id):
    tech = Technician.query.get_or_404(id)
    
    if request.method == 'POST':
        tech.name = request.form.get('name')
        tech.phone = request.form.get('phone')
        tech.email = request.form.get('email')
        
        db.session.commit()
        
        flash('Technician updated successfully')
        return redirect(url_for('technicians'))
    
    return render_template('edit_technician.html', technician=tech)

@app.route('/technicians/delete/<int:id>')
@login_required
def delete_technician(id):
    tech = Technician.query.get_or_404(id)
    db.session.delete(tech)
    db.session.commit()
    
    flash('Technician deleted successfully')
    return redirect(url_for('technicians'))

@app.route('/oncall')
@login_required
def oncall():
    schedules = OnCallSchedule.query.order_by(OnCallSchedule.start_date).all()
    technicians = Technician.query.all()
    return render_template('oncall.html', schedules=schedules, technicians=technicians)

@app.route('/oncall/add', methods=['GET', 'POST'])
@login_required
def add_oncall():
    if request.method == 'POST':
        technician_id = request.form.get('technician_id')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        
        new_schedule = OnCallSchedule(
            technician_id=technician_id,
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        flash('On-call schedule added successfully')
        return redirect(url_for('oncall'))
    
    technicians = Technician.query.all()
    return render_template('add_oncall.html', technicians=technicians)

@app.route('/oncall/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_oncall(id):
    schedule = OnCallSchedule.query.get_or_404(id)
    
    if request.method == 'POST':
        schedule.technician_id = request.form.get('technician_id')
        schedule.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        schedule.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        
        db.session.commit()
        
        flash('On-call schedule updated successfully')
        return redirect(url_for('oncall'))
    
    technicians = Technician.query.all()
    return render_template('edit_oncall.html', schedule=schedule, technicians=technicians)

@app.route('/oncall/delete/<int:id>')
@login_required
def delete_oncall(id):
    schedule = OnCallSchedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()
    
    flash('On-call schedule deleted successfully')
    return redirect(url_for('oncall'))

@app.route('/business-hours')
@login_required
def business_hours():
    hours = BusinessHours.query.order_by(BusinessHours.day_of_week).all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return render_template('business_hours.html', hours=hours, days=days)

@app.route('/holidays')
@login_required
def holidays():
    # Get all holidays sorted by date
    all_holidays = Holiday.query.order_by(Holiday.date).all()
    return render_template('holidays.html', holidays=all_holidays)

@app.route('/holidays/add', methods=['POST'])
@login_required
def add_holiday():
    if request.method == 'POST':
        name = request.form.get('name')
        date_str = request.form.get('date')
        description = request.form.get('description', '')
        
        try:
            # Parse the date string into a date object
            holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create new holiday
            holiday = Holiday(
                name=name,
                date=holiday_date,
                description=description,
                notified=False
            )
            
            db.session.add(holiday)
            db.session.commit()
            
            flash(f'Holiday "{name}" added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding holiday: {str(e)}")
            flash(f'Error adding holiday: {str(e)}', 'danger')
        
    return redirect(url_for('holidays'))

@app.route('/holidays/edit/<int:holiday_id>', methods=['GET', 'POST'])
@login_required
def edit_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        date_str = request.form.get('date')
        description = request.form.get('description', '')
        
        try:
            # Parse the date string into a date object
            holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Update holiday
            holiday.name = name
            holiday.date = holiday_date
            holiday.description = description
            holiday.notified = False  # Reset notification status when edited
            
            db.session.commit()
            
            flash(f'Holiday "{name}" updated successfully', 'success')
            return redirect(url_for('holidays'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating holiday: {str(e)}")
            flash(f'Error updating holiday: {str(e)}', 'danger')
    
    return render_template('edit_holiday.html', holiday=holiday)

@app.route('/holidays/delete/<int:holiday_id>')
@login_required
def delete_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    
    try:
        name = holiday.name
        db.session.delete(holiday)
        db.session.commit()
        flash(f'Holiday "{name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting holiday: {str(e)}")
        flash(f'Error deleting holiday: {str(e)}', 'danger')
    
    return redirect(url_for('holidays'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page for configuring application settings"""
    # Get current refresh interval
    refresh_setting = SystemSetting.query.filter_by(key='refresh_interval').first()
    current_refresh = int(refresh_setting.value) if refresh_setting and refresh_setting.value.isdigit() else 5
    
    # Get current timezone
    timezone_setting = SystemSetting.query.filter_by(key='timezone').first()
    current_timezone = timezone_setting.value if timezone_setting else 'UTC'
    
    # Get current API keys
    atera_api_key = get_setting('atera_api_key', os.getenv('ATERA_API_KEY', ''))
    twilio_account_sid = get_setting('twilio_account_sid', os.getenv('TWILIO_ACCOUNT_SID', ''))
    twilio_auth_token = get_setting('twilio_auth_token', os.getenv('TWILIO_AUTH_TOKEN', ''))
    twilio_phone_number = get_setting('twilio_phone_number', os.getenv('TWILIO_PHONE_NUMBER', ''))
    
    if request.method == 'POST':
        # Get form values
        new_refresh = request.form.get('refresh_interval', '5')
        new_timezone = request.form.get('timezone', 'UTC')
        new_atera_api_key = request.form.get('atera_api_key', '')
        new_twilio_account_sid = request.form.get('twilio_account_sid', '')
        new_twilio_auth_token = request.form.get('twilio_auth_token', '')
        new_twilio_phone_number = request.form.get('twilio_phone_number', '')
        
        # Validate refresh interval
        try:
            refresh_value = int(new_refresh)
            if refresh_value < 1 or refresh_value > 60:
                flash('Refresh interval must be between 1 and 60 minutes', 'danger')
                return render_template('settings.html', 
                                      refresh_interval=current_refresh,
                                      current_timezone=current_timezone,
                                      atera_api_key=atera_api_key,
                                      twilio_account_sid=twilio_account_sid,
                                      twilio_auth_token=twilio_auth_token,
                                      twilio_phone_number=twilio_phone_number,
                                      timezones=pytz.common_timezones)
        except ValueError:
            flash('Refresh interval must be a number', 'danger')
            return render_template('settings.html', 
                                  refresh_interval=current_refresh,
                                  current_timezone=current_timezone,
                                  atera_api_key=atera_api_key,
                                  twilio_account_sid=twilio_account_sid,
                                  twilio_auth_token=twilio_auth_token,
                                  twilio_phone_number=twilio_phone_number,
                                  timezones=pytz.common_timezones)
        
        # Validate timezone
        if new_timezone not in pytz.all_timezones:
            flash('Invalid timezone selected', 'danger')
            return render_template('settings.html', 
                                  refresh_interval=current_refresh,
                                  current_timezone=current_timezone,
                                  atera_api_key=atera_api_key,
                                  twilio_account_sid=twilio_account_sid,
                                  twilio_auth_token=twilio_auth_token,
                                  twilio_phone_number=twilio_phone_number,
                                  timezones=pytz.common_timezones)
        
        # Save refresh interval setting
        save_setting('refresh_interval', new_refresh)
        
        # Save timezone setting
        save_setting('timezone', new_timezone)
        
        # Save API keys
        save_setting('atera_api_key', new_atera_api_key)
        save_setting('twilio_account_sid', new_twilio_account_sid)
        save_setting('twilio_auth_token', new_twilio_auth_token)
        save_setting('twilio_phone_number', new_twilio_phone_number)
        
        # Determine what changed for appropriate message
        api_keys_changed = (atera_api_key != new_atera_api_key or 
                           twilio_account_sid != new_twilio_account_sid or 
                           twilio_auth_token != new_twilio_auth_token or 
                           twilio_phone_number != new_twilio_phone_number)
        timezone_changed = current_timezone != new_timezone
        refresh_changed = current_refresh != int(new_refresh)
        
        # Different message based on what was changed
        if api_keys_changed and timezone_changed and refresh_changed:
            flash('All settings updated successfully. API keys and timezone changes are effective immediately. Refresh interval changes will take effect after restarting the application.', 'success')
        elif api_keys_changed and timezone_changed:
            flash('API keys and timezone updated successfully.', 'success')
        elif api_keys_changed and refresh_changed:
            flash('API keys updated successfully. Refresh interval changes will take effect after restarting the application.', 'success')
        elif timezone_changed and refresh_changed:
            flash('Timezone updated successfully. Refresh interval changes will take effect after restarting the application.', 'success')
        elif api_keys_changed:
            flash('API keys updated successfully.', 'success')
        elif timezone_changed:
            flash('Timezone updated successfully.', 'success')
        elif refresh_changed:
            flash('Refresh interval updated successfully. Restart the application for changes to take effect.', 'success')
        else:
            flash('No changes detected.', 'info')
            
        return redirect(url_for('settings'))
    
    return render_template('settings.html', 
                          refresh_interval=current_refresh,
                          current_timezone=current_timezone,
                          atera_api_key=atera_api_key,
                          twilio_account_sid=twilio_account_sid,
                          twilio_auth_token=twilio_auth_token,
                          twilio_phone_number=twilio_phone_number,
                          timezones=pytz.common_timezones)

@app.route('/business-hours/add', methods=['GET', 'POST'])
@login_required
def add_business_hours():
    if request.method == 'POST':
        day_of_week = int(request.form.get('day_of_week'))
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        
        # Check if entry for this day already exists
        existing = BusinessHours.query.filter_by(day_of_week=day_of_week).first()
        if existing:
            existing.start_time = start_time
            existing.end_time = end_time
        else:
            new_hours = BusinessHours(
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(new_hours)
        
        db.session.commit()
        
        flash('Business hours updated successfully')
        return redirect(url_for('business_hours'))
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return render_template('add_business_hours.html', days=days)

@app.route('/tickets')
@login_required
def tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(20).all()
    return render_template('tickets.html', tickets=tickets)

@app.route('/tickets/refresh')
@login_required
def refresh_tickets():
    fetch_tickets_from_atera()
    return redirect(url_for('tickets'))

@app.route('/dashboard/refresh-tickets')
@login_required
def dashboard_refresh_tickets():
    """Refresh tickets and return to the dashboard"""
    fetch_tickets_from_atera()
    return redirect(url_for('index'))

@app.route('/business-hours/status')
@login_required
def business_hours_status():
    """Return the current business hours status"""
    is_within_hours = is_business_hours()
    return jsonify({
        'within_business_hours': is_within_hours,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/test-atera')
@login_required
def test_atera():
    """Test route to manually fetch and display tickets from Atera API"""
    api_key = os.getenv('ATERA_API_KEY')
    if not api_key:
        return jsonify({'error': 'Atera API key not configured'}), 500
    
    headers = {
        'X-API-KEY': api_key,
        'Accept': 'application/json'
    }
    
    try:
        # Fetch tickets from Atera API with query parameters for open tickets
        response = requests.get(
            'https://app.atera.com/api/v3/tickets',
            headers=headers,
            params={
                'page': 1,
                'itemsInPage': 50,
                'ticketStatus': 'Open'
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': f'Failed to fetch tickets: {response.status_code}',
                'response': response.text
            }), 500
        
        # Return the raw API response
        return jsonify(response.json())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    # Check if any users exist
    if User.query.count() > 0:
        flash('Setup already completed')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Create admin user
        admin = User(username=username, password=password, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        
        flash('Setup completed successfully. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('setup.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Data Export Routes
@app.route('/export')
@login_required
def export_home():
    """Main export dashboard showing all data types"""
    # Get counts for each data type
    counts = {
        'tickets': Ticket.query.count(),
        'customers': Customer.query.count(),
        'agents': Agent.query.count(),
        'alerts': Alert.query.count(),
        'contacts': Contact.query.count(),
        'contracts': Contract.query.count(),
        'invoices': Invoice.query.count(),
        'snmp_devices': SNMPDevice.query.count(),
        'tcp_devices': TCPDevice.query.count(),
        'knowledge_base': KnowledgeBase.query.count(),
        'products': Product.query.count(),
        'expenses': Expense.query.count(),
        'http_devices': HTTPDevice.query.count(),
        'generic_devices': GenericDevice.query.count(),
        'departments': Department.query.count()
    }

    # Get recent export logs
    recent_exports = ExportLog.query.order_by(ExportLog.created_at.desc()).limit(10).all()

    return render_template('export.html', counts=counts, recent_exports=recent_exports)

@app.route('/sync/<data_type>')
@login_required
def sync_data(data_type):
    """Sync data from Atera API to database"""
    from data_sync import (sync_customers, sync_agents, sync_alerts,
                           sync_contacts, sync_contracts, sync_invoices, sync_tickets,
                           sync_snmp_devices, sync_tcp_devices, sync_knowledge_base,
                           sync_products, sync_expenses, sync_http_devices,
                           sync_generic_devices, sync_departments)

    # Get API key from settings
    api_key = get_setting('atera_api_key', os.getenv('ATERA_API_KEY', ''))
    if not api_key:
        flash('Atera API key not configured', 'danger')
        return redirect(url_for('export_home'))

    try:
        if data_type == 'customers':
            success, count, error = sync_customers(db, Customer, api_key)
        elif data_type == 'agents':
            success, count, error = sync_agents(db, Agent, api_key)
        elif data_type == 'alerts':
            success, count, error = sync_alerts(db, Alert, api_key)
        elif data_type == 'contacts':
            success, count, error = sync_contacts(db, Contact, api_key)
        elif data_type == 'contracts':
            success, count, error = sync_contracts(db, Contract, api_key)
        elif data_type == 'invoices':
            success, count, error = sync_invoices(db, Invoice, api_key)
        elif data_type == 'tickets':
            success, count, error = sync_tickets(db, Ticket, api_key)
        elif data_type == 'snmp_devices':
            success, count, error = sync_snmp_devices(db, SNMPDevice, api_key)
        elif data_type == 'tcp_devices':
            success, count, error = sync_tcp_devices(db, TCPDevice, api_key)
        elif data_type == 'knowledge_base':
            success, count, error = sync_knowledge_base(db, KnowledgeBase, api_key)
        elif data_type == 'products':
            success, count, error = sync_products(db, Product, api_key)
        elif data_type == 'expenses':
            success, count, error = sync_expenses(db, Expense, api_key)
        elif data_type == 'http_devices':
            success, count, error = sync_http_devices(db, HTTPDevice, api_key)
        elif data_type == 'generic_devices':
            success, count, error = sync_generic_devices(db, GenericDevice, api_key)
        elif data_type == 'departments':
            success, count, error = sync_departments(db, Department, api_key)
        else:
            flash(f'Unknown data type: {data_type}', 'danger')
            return redirect(url_for('export_home'))

        if success:
            flash(f'Successfully synced {count} {data_type}', 'success')
        else:
            flash(f'Error syncing {data_type}: {error}', 'danger')

    except Exception as e:
        app.logger.error(f"Error syncing {data_type}: {str(e)}")
        flash(f'Error syncing {data_type}: {str(e)}', 'danger')

    return redirect(url_for('export_home'))

@app.route('/sync/all')
@login_required
def sync_all_data():
    """Sync all data types from Atera"""
    from data_sync import (sync_customers, sync_agents, sync_alerts,
                           sync_contacts, sync_contracts, sync_invoices, sync_tickets,
                           sync_snmp_devices, sync_tcp_devices, sync_knowledge_base,
                           sync_products, sync_expenses, sync_http_devices,
                           sync_generic_devices, sync_departments)

    # Get API key from settings
    api_key = get_setting('atera_api_key', os.getenv('ATERA_API_KEY', ''))
    if not api_key:
        flash('Atera API key not configured', 'danger')
        return redirect(url_for('export_home'))

    total_synced = 0
    errors = []

    # Define all sync operations
    sync_operations = [
        ('customers', lambda: sync_customers(db, Customer, api_key)),
        ('agents', lambda: sync_agents(db, Agent, api_key)),
        ('alerts', lambda: sync_alerts(db, Alert, api_key)),
        ('contacts', lambda: sync_contacts(db, Contact, api_key)),
        ('contracts', lambda: sync_contracts(db, Contract, api_key)),
        ('invoices', lambda: sync_invoices(db, Invoice, api_key)),
        ('tickets', lambda: sync_tickets(db, Ticket, api_key)),
        ('snmp_devices', lambda: sync_snmp_devices(db, SNMPDevice, api_key)),
        ('tcp_devices', lambda: sync_tcp_devices(db, TCPDevice, api_key)),
        ('http_devices', lambda: sync_http_devices(db, HTTPDevice, api_key)),
        ('generic_devices', lambda: sync_generic_devices(db, GenericDevice, api_key)),
        ('knowledge_base', lambda: sync_knowledge_base(db, KnowledgeBase, api_key)),
        ('products', lambda: sync_products(db, Product, api_key)),
        ('expenses', lambda: sync_expenses(db, Expense, api_key)),
        ('departments', lambda: sync_departments(db, Department, api_key))
    ]

    # Execute all syncs
    for data_type, sync_func in sync_operations:
        try:
            success, count, error = sync_func()
            if success:
                total_synced += count
                app.logger.info(f"Synced {count} {data_type}")
            else:
                errors.append(f"{data_type}: {error}")
                app.logger.error(f"Failed to sync {data_type}: {error}")
        except Exception as e:
            errors.append(f"{data_type}: {str(e)}")
            app.logger.error(f"Error syncing {data_type}: {str(e)}")

    # Display results
    if errors:
        flash(f'Synced {total_synced} total records with {len(errors)} errors', 'warning')
        for error in errors[:5]:  # Show first 5 errors
            flash(f'Error: {error}', 'danger')
    else:
        flash(f'Successfully synced {total_synced} total records across all data types!', 'success')

    return redirect(url_for('export_home'))

@app.route('/export/all/<export_format>')
@login_required
def export_all_data(export_format):
    """Export all data types in a ZIP file"""
    from export_utils import export_models
    import zipfile
    from io import BytesIO

    try:
        # Create ZIP file in memory
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Define all data types
            exports = [
                ('customers', Customer.query.all()),
                ('agents', Agent.query.all()),
                ('alerts', Alert.query.all()),
                ('contacts', Contact.query.all()),
                ('contracts', Contract.query.all()),
                ('invoices', Invoice.query.all()),
                ('tickets', Ticket.query.all()),
                ('snmp_devices', SNMPDevice.query.all()),
                ('tcp_devices', TCPDevice.query.all()),
                ('http_devices', HTTPDevice.query.all()),
                ('generic_devices', GenericDevice.query.all()),
                ('knowledge_base', KnowledgeBase.query.all()),
                ('products', Product.query.all()),
                ('expenses', Expense.query.all()),
                ('departments', Department.query.all())
            ]

            total_exported = 0
            for data_type, data in exports:
                if data:
                    bytes_buffer, filename, count, error = export_models(data, data_type, export_format, exclude_fields=['id'])
                    if bytes_buffer:
                        zip_file.writestr(filename, bytes_buffer.read())
                        total_exported += count
                        app.logger.info(f"Added {data_type} to ZIP: {count} records")

        # Prepare ZIP for download
        zip_buffer.seek(0)

        # Log the bulk export
        export_log = ExportLog(
            export_type='all',
            export_format=export_format,
            file_path=f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            record_count=total_exported,
            status='success',
            error_message=None,
            created_by=current_user.username,
            created_at=datetime.now()
        )
        db.session.add(export_log)
        db.session.commit()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'atera_all_data_{timestamp}.zip'
        )

    except Exception as e:
        app.logger.error(f"Error exporting all data: {str(e)}")
        flash(f'Error exporting all data: {str(e)}', 'danger')
        return redirect(url_for('export_home'))

@app.route('/export/<data_type>/<export_format>')
@login_required
def export_data(data_type, export_format):
    """Export data to specified format and serve as download"""
    from export_utils import export_models

    try:
        # Get the appropriate model and data
        if data_type == 'tickets':
            data = Ticket.query.all()
            exclude_fields = ['id']
        elif data_type == 'customers':
            data = Customer.query.all()
            exclude_fields = ['id']
        elif data_type == 'agents':
            data = Agent.query.all()
            exclude_fields = ['id']
        elif data_type == 'alerts':
            data = Alert.query.all()
            exclude_fields = ['id']
        elif data_type == 'contacts':
            data = Contact.query.all()
            exclude_fields = ['id']
        elif data_type == 'contracts':
            data = Contract.query.all()
            exclude_fields = ['id']
        elif data_type == 'invoices':
            data = Invoice.query.all()
            exclude_fields = ['id']
        elif data_type == 'snmp_devices':
            data = SNMPDevice.query.all()
            exclude_fields = ['id']
        elif data_type == 'tcp_devices':
            data = TCPDevice.query.all()
            exclude_fields = ['id']
        elif data_type == 'knowledge_base':
            data = KnowledgeBase.query.all()
            exclude_fields = ['id']
        elif data_type == 'products':
            data = Product.query.all()
            exclude_fields = ['id']
        elif data_type == 'expenses':
            data = Expense.query.all()
            exclude_fields = ['id']
        elif data_type == 'http_devices':
            data = HTTPDevice.query.all()
            exclude_fields = ['id']
        elif data_type == 'generic_devices':
            data = GenericDevice.query.all()
            exclude_fields = ['id']
        elif data_type == 'departments':
            data = Department.query.all()
            exclude_fields = ['id']
        else:
            flash(f'Unknown data type: {data_type}', 'danger')
            return redirect(url_for('export_home'))

        # Perform export (now returns BytesIO buffer)
        bytes_buffer, filename, count, error = export_models(data, data_type, export_format, exclude_fields)

        # Log the export
        export_log = ExportLog(
            export_type=data_type,
            export_format=export_format,
            file_path=filename if bytes_buffer else None,  # Just store filename for history
            record_count=count,
            status='success' if bytes_buffer else 'failed',
            error_message=error,
            created_by=current_user.username,
            created_at=datetime.now()
        )
        db.session.add(export_log)
        db.session.commit()

        if bytes_buffer:
            # Determine mimetype based on format
            mimetypes = {
                'csv': 'text/csv',
                'json': 'application/json',
                'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            mimetype = mimetypes.get(export_format, 'application/octet-stream')

            # Serve file directly from memory
            return send_file(
                bytes_buffer,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
        else:
            flash(f'Error exporting {data_type}: {error}', 'danger')
            return redirect(url_for('export_home'))

    except Exception as e:
        app.logger.error(f"Error exporting {data_type}: {str(e)}")
        flash(f'Error exporting {data_type}: {str(e)}', 'danger')
        return redirect(url_for('export_home'))

@app.route('/view/<data_type>')
@login_required
def view_data(data_type):
    """View data in the browser"""
    try:
        if data_type == 'customers':
            data = Customer.query.order_by(Customer.synced_at.desc()).limit(100).all()
        elif data_type == 'agents':
            data = Agent.query.order_by(Agent.synced_at.desc()).limit(100).all()
        elif data_type == 'alerts':
            data = Alert.query.order_by(Alert.created_at.desc()).limit(100).all()
        elif data_type == 'contacts':
            data = Contact.query.order_by(Contact.synced_at.desc()).limit(100).all()
        elif data_type == 'contracts':
            data = Contract.query.order_by(Contract.synced_at.desc()).limit(100).all()
        elif data_type == 'invoices':
            data = Invoice.query.order_by(Invoice.synced_at.desc()).limit(100).all()
        elif data_type == 'tickets':
            data = Ticket.query.order_by(Ticket.created_at.desc()).limit(100).all()
        elif data_type == 'snmp_devices':
            data = SNMPDevice.query.order_by(SNMPDevice.synced_at.desc()).limit(100).all()
        elif data_type == 'tcp_devices':
            data = TCPDevice.query.order_by(TCPDevice.synced_at.desc()).limit(100).all()
        elif data_type == 'knowledge_base':
            data = KnowledgeBase.query.order_by(KnowledgeBase.synced_at.desc()).limit(100).all()
        elif data_type == 'products':
            data = Product.query.order_by(Product.synced_at.desc()).limit(100).all()
        elif data_type == 'expenses':
            data = Expense.query.order_by(Expense.synced_at.desc()).limit(100).all()
        elif data_type == 'http_devices':
            data = HTTPDevice.query.order_by(HTTPDevice.synced_at.desc()).limit(100).all()
        elif data_type == 'generic_devices':
            data = GenericDevice.query.order_by(GenericDevice.synced_at.desc()).limit(100).all()
        elif data_type == 'departments':
            data = Department.query.order_by(Department.synced_at.desc()).limit(100).all()
        else:
            flash(f'Unknown data type: {data_type}', 'danger')
            return redirect(url_for('export_home'))

        return render_template('view_data.html', data_type=data_type, data=data)

    except Exception as e:
        app.logger.error(f"Error viewing {data_type}: {str(e)}")
        flash(f'Error viewing {data_type}: {str(e)}', 'danger')
        return redirect(url_for('export_home'))

# Create database tables and default admin user
with app.app_context():
    db.create_all()

    # Create default admin user if no users exist
    if User.query.count() == 0:
        default_admin = User(
            username='admin',
            password='admin',
            is_admin=True
        )
        db.session.add(default_admin)
        db.session.commit()
        app.logger.info("Created default admin user (username: admin, password: admin)")
        print("=" * 60)
        print("DEFAULT ADMIN USER CREATED")
        print("Username: admin")
        print("Password: admin")
        print("PLEASE CHANGE THE PASSWORD AFTER FIRST LOGIN!")
        print("=" * 60)

if __name__ == '__main__':
    app.run(debug=True)
