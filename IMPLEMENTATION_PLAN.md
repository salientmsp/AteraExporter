# Implementation Plan - Complete Atera API Coverage

## Executive Summary

**Current State**: 15 data types, ~68% API coverage
**Target State**: 22 data types, 100% API coverage
**Critical Gaps**: Ticket comments, work hours, agent patches, missing fields

---

## Phase 1: Critical Missing Data (HIGH PRIORITY) 🔴

### 1.1 Account Information
**Files to modify**: `atera_api.py`, `app.py`, `data_sync.py`, `templates/export.html`

**API Method** (atera_api.py):
```python
def fetch_account(self):
    """Fetch account information"""
    logger.info("Fetching account from Atera")
    return self._make_request('/account')
```

**Database Model** (app.py):
```python
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(100), unique=True)
    country = db.Column(db.String(100))
    company_name = db.Column(db.String(200))
    created_on = db.Column(db.DateTime)
    state = db.Column(db.String(100))
    timezone_name = db.Column(db.String(100))
    city = db.Column(db.String(100))
    address = db.Column(db.String(200))
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(50))
    is_it_department = db.Column(db.Boolean)
    plan = db.Column(db.String(100))
    synced_at = db.Column(db.DateTime, default=datetime.now)
```

**Sync Function** (data_sync.py):
```python
def sync_account(db, Account, api_key):
    """Sync account information from Atera API"""
    try:
        client = AteraAPIClient(api_key)
        account_data = client.fetch_account()

        if account_data is None:
            return False, 0, "Failed to fetch account"

        # Update or create single account record
        account = Account.query.first()
        if account:
            # Update existing
            account.account_id = account_data.get('AccountID', '')
            account.country = account_data.get('Country', '')
            # ... update all fields
        else:
            # Create new
            account = Account(
                account_id=account_data.get('AccountID', ''),
                country=account_data.get('Country', ''),
                # ... all fields
            )
            db.session.add(account)

        db.session.commit()
        return True, 1, None
    except Exception as e:
        db.session.rollback()
        return False, 0, str(e)
```

---

### 1.2 Ticket Comments (CRITICAL)
**Files to modify**: `atera_api.py`, `app.py`, `data_sync.py`, `export_utils.py`

**API Method** (atera_api.py):
```python
def fetch_ticket_comments(self, ticket_id):
    """Fetch comments for a specific ticket"""
    logger.info(f"Fetching comments for ticket {ticket_id}")
    return self._fetch_paginated(f'/tickets/{ticket_id}/comments')
```

**Database Model** (app.py):
```python
class TicketComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(50), db.ForeignKey('ticket.ticket_id'), nullable=False)
    comment_date = db.Column(db.DateTime)
    comment_text = db.Column(db.Text)
    end_user_id = db.Column(db.String(50))
    technician_contact_id = db.Column(db.String(50))
    email = db.Column(db.String(200))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    is_internal = db.Column(db.Boolean)
    synced_at = db.Column(db.DateTime, default=datetime.now)

    # Relationship
    ticket = db.relationship('Ticket', backref='comments')
```

**Sync Function** (data_sync.py):
```python
def sync_ticket_comments(db, TicketComment, Ticket, api_key):
    """Sync all ticket comments"""
    try:
        client = AteraAPIClient(api_key)

        # Get all tickets
        tickets = Ticket.query.all()
        total_comments = 0

        for ticket in tickets:
            try:
                comments_data = client.fetch_ticket_comments(ticket.ticket_id)

                if comments_data:
                    for comment_data in comments_data:
                        # Create or update comment
                        comment = TicketComment(
                            ticket_id=ticket.ticket_id,
                            comment_date=parse_atera_datetime(comment_data.get('Date')),
                            comment_text=comment_data.get('Comment', ''),
                            end_user_id=str(comment_data.get('EndUserID', '')),
                            technician_contact_id=str(comment_data.get('TechnicianContactID', '')),
                            email=comment_data.get('Email', ''),
                            first_name=comment_data.get('FirstName', ''),
                            last_name=comment_data.get('LastName', ''),
                            is_internal=comment_data.get('IsInternal', False),
                            synced_at=datetime.now()
                        )
                        db.session.add(comment)
                        total_comments += 1
            except Exception as e:
                logger.error(f"Error syncing comments for ticket {ticket.ticket_id}: {e}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {total_comments} ticket comments")
        return True, total_comments, None

    except Exception as e:
        db.session.rollback()
        return False, 0, str(e)
```

---

### 1.3 Ticket Work Hours (CRITICAL)
**Files to modify**: `atera_api.py`, `app.py`, `data_sync.py`

**API Method** (atera_api.py):
```python
def fetch_ticket_workhours(self, ticket_id):
    """Fetch work hours for a specific ticket"""
    logger.info(f"Fetching work hours for ticket {ticket_id}")
    return self._fetch_paginated(f'/tickets/{ticket_id}/workhoursrecords')
```

**Database Model** (app.py):
```python
class TicketWorkHour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(50), db.ForeignKey('ticket.ticket_id'), nullable=False)
    work_hours_id = db.Column(db.String(50))
    start_work_hour = db.Column(db.DateTime)
    end_work_hour = db.Column(db.DateTime)
    technician_contact_id = db.Column(db.String(50))
    billable = db.Column(db.Boolean)
    on_customer_site = db.Column(db.Boolean)
    description = db.Column(db.Text)
    technician_full_name = db.Column(db.String(200))
    technician_email = db.Column(db.String(200))
    rate_id = db.Column(db.Integer)
    rate_amount = db.Column(db.Float)
    synced_at = db.Column(db.DateTime, default=datetime.now)

    # Relationship
    ticket = db.relationship('Ticket', backref='work_hours')
```

---

### 1.4 Agent Patches (Security/Compliance)
**Files to modify**: `atera_api.py`, `app.py`, `data_sync.py`

**API Methods** (atera_api.py):
```python
def fetch_agent_installed_patches(self, device_guid):
    """Fetch installed patches for an agent"""
    logger.info(f"Fetching installed patches for agent {device_guid}")
    return self._make_request(f'/agents/{device_guid}/installed-patches')

def fetch_agent_available_patches(self, device_guid):
    """Fetch available patches for an agent"""
    logger.info(f"Fetching available patches for agent {device_guid}")
    return self._make_request(f'/agents/{device_guid}/available-patches')
```

**Database Models** (app.py):
```python
class AgentInstalledPatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_guid = db.Column(db.String(100), db.ForeignKey('agent.device_guid'), nullable=False)
    name = db.Column(db.String(200))
    patch_class = db.Column(db.String(100))
    kb_id = db.Column(db.String(50))
    install_date = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.now)

    agent = db.relationship('Agent', backref='installed_patches')

class AgentAvailablePatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_guid = db.Column(db.String(100), db.ForeignKey('agent.device_guid'), nullable=False)
    name = db.Column(db.String(200))
    patch_class = db.Column(db.String(100))
    kb_id = db.Column(db.String(50))
    status = db.Column(db.String(50))
    synced_at = db.Column(db.DateTime, default=datetime.now)

    agent = db.relationship('Agent', backref='available_patches')
```

---

## Phase 2: Field Coverage Completion

### 2.1 Update Contact Model
**Missing Fields**:
```python
# Add to Contact model in app.py
mobile_phone = db.Column(db.String(50))
department_id = db.Column(db.String(50))
department_name = db.Column(db.String(200))
```

**Update sync_contacts** to include:
```python
mobile_phone=contact_data.get('MobilePhone', ''),
department_id=str(contact_data.get('DepartmentID', '')),
department_name=contact_data.get('DepartmentName', ''),
```

### 2.2 Update Agent Model
**Missing Fields** (~20 fields):
```python
# Add to Agent model
agent_version = db.Column(db.String(50))
favorite = db.Column(db.Boolean)
threshold_id = db.Column(db.String(50))
reported_from_ip = db.Column(db.String(50))
display = db.Column(db.String(200))
sound = db.Column(db.String(200))
processor_cores_count = db.Column(db.Integer)
vendor = db.Column(db.String(100))
vendor_serial_number = db.Column(db.String(100))
vendor_brand_model = db.Column(db.String(200))
product_name = db.Column(db.String(200))
windows_serial_number = db.Column(db.String(100))
office_sp = db.Column(db.String(50))
office_oem = db.Column(db.Boolean)
office_serial_number = db.Column(db.String(100))
os_num = db.Column(db.Float)
device_type = db.Column(db.String(50))
# Note: HardwareDisks, BatteryInfo may need separate tables
```

### 2.3 Update Ticket Model
**Missing Fields**:
```python
# Add to Ticket model
ticket_resolved_date = db.Column(db.DateTime)
technician_first_comment_date = db.Column(db.DateTime)
first_response_due_date = db.Column(db.DateTime)
closed_ticket_due_date = db.Column(db.DateTime)
first_comment = db.Column(db.Text)
last_end_user_comment_timestamp = db.Column(db.DateTime)
last_technician_comment_timestamp = db.Column(db.DateTime)
customer_business_number = db.Column(db.String(100))
technician_full_name = db.Column(db.String(200))
technician_email = db.Column(db.String(200))
contract_id = db.Column(db.String(50))
```

---

## Phase 3: Custom Fields & Advanced Features

### 3.1 Custom Field Definitions
```python
class CustomFieldDefinition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(200), unique=True)
    data_type = db.Column(db.String(50))  # Text, Boolean, Numeric, Date, Options
    target = db.Column(db.String(50))  # Customer, Ticket, Contact, etc.
    possible_values = db.Column(db.Text)  # JSON array
    synced_at = db.Column(db.DateTime, default=datetime.now)
```

### 3.2 Custom Field Values
```python
class CustomFieldValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(200))
    entity_type = db.Column(db.String(50))  # Customer, Ticket, etc.
    entity_id = db.Column(db.String(50))  # Foreign key to entity
    value_as_string = db.Column(db.Text)
    value_as_decimal = db.Column(db.Float)
    value_as_datetime = db.Column(db.DateTime)
    value_as_bool = db.Column(db.Boolean)
    synced_at = db.Column(db.DateTime, default=datetime.now)
```

---

## Implementation Estimates

### Phase 1 (Critical Missing Data)
- **Time**: 4-6 hours
- **Files Modified**: 4 (atera_api.py, app.py, data_sync.py, templates/export.html)
- **New Models**: 5 (Account, TicketComment, TicketWorkHour, AgentInstalledPatch, AgentAvailablePatch)
- **New API Methods**: 5
- **New Sync Functions**: 5
- **UI Updates**: Add 5 new cards to export dashboard

### Phase 2 (Field Coverage)
- **Time**: 2-3 hours
- **Files Modified**: 2 (app.py, data_sync.py)
- **Models Updated**: 4 (Contact, Agent, Ticket, Alert)
- **Fields Added**: ~40

### Phase 3 (Custom Fields)
- **Time**: 3-4 hours
- **Files Modified**: 3 (atera_api.py, app.py, data_sync.py)
- **New Models**: 2 (CustomFieldDefinition, CustomFieldValue)
- **Complex sync logic**: Polymorphic relations

**Total Estimated Time**: 9-13 hours for 100% coverage

---

## Recommendations

1. **Start with Phase 1.2 and 1.3** (Ticket Comments & Work Hours)
   - Most valuable for analysis
   - Highest customer demand
   - Moderate complexity

2. **Then Phase 2** (Field Updates)
   - Quick wins
   - Completes existing data types
   - No new complexity

3. **Finally Phase 1.4** (Agent Patches)
   - Security/compliance value
   - Requires nested API calls (slower)

4. **Phase 3 as needed** (Custom Fields)
   - Organization-specific
   - Only if using custom fields
   - Most complex implementation

---

## Testing Strategy

For each phase:
1. Test API methods individually
2. Test sync functions with small datasets
3. Test export functionality
4. Verify database relationships
5. Check UI display
6. Performance test with large datasets

## Performance Considerations

**Nested API Calls**:
- Ticket comments: 1 API call per ticket
- Work hours: 1 API call per ticket
- Agent patches: 2 API calls per agent

**Optimization**:
- Batch operations where possible
- Rate limiting consideration
- Caching strategy
- Incremental sync support (use lastmodified endpoints)
