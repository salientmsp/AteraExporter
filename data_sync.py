"""
Data Synchronization Module
Syncs data from Atera API to local database
"""

from datetime import datetime
import logging
from atera_api import AteraAPIClient, parse_atera_datetime, parse_atera_date

logger = logging.getLogger(__name__)


def sync_customers(db, Customer, api_key):
    """
    Sync customers from Atera API to database

    Args:
        db: SQLAlchemy database instance
        Customer: Customer model class
        api_key: Atera API key

    Returns:
        Tuple of (success, count, error_message)
    """
    try:
        client = AteraAPIClient(api_key)
        customers_data = client.fetch_customers()

        if customers_data is None:
            return False, 0, "Failed to fetch customers from Atera API"

        count = 0
        for customer_data in customers_data:
            try:
                customer_id = str(customer_data.get('CustomerID'))

                # Check if customer exists
                existing = Customer.query.filter_by(customer_id=customer_id).first()

                if existing:
                    # Update existing customer
                    existing.customer_name = customer_data.get('CustomerName', '')
                    existing.domain = customer_data.get('Domain', '')
                    existing.business_number = customer_data.get('BusinessNumber', '')
                    existing.address = customer_data.get('Address', '')
                    existing.city = customer_data.get('City', '')
                    existing.state = customer_data.get('State', '')
                    existing.country = customer_data.get('Country', '')
                    existing.zip_code = customer_data.get('ZipCodeStr', '')
                    existing.phone = customer_data.get('Phone', '')
                    existing.fax = customer_data.get('Fax', '')
                    existing.notes = customer_data.get('Notes', '')
                    existing.created_at = parse_atera_datetime(customer_data.get('CreatedOn'))
                    existing.last_modified = parse_atera_datetime(customer_data.get('LastModified'))
                    existing.synced_at = datetime.now()
                else:
                    # Create new customer
                    customer = Customer(
                        customer_id=customer_id,
                        customer_name=customer_data.get('CustomerName', ''),
                        domain=customer_data.get('Domain', ''),
                        business_number=customer_data.get('BusinessNumber', ''),
                        address=customer_data.get('Address', ''),
                        city=customer_data.get('City', ''),
                        state=customer_data.get('State', ''),
                        country=customer_data.get('Country', ''),
                        zip_code=customer_data.get('ZipCodeStr', ''),
                        phone=customer_data.get('Phone', ''),
                        fax=customer_data.get('Fax', ''),
                        notes=customer_data.get('Notes', ''),
                        created_at=parse_atera_datetime(customer_data.get('CreatedOn')),
                        last_modified=parse_atera_datetime(customer_data.get('LastModified')),
                        synced_at=datetime.now()
                    )
                    db.session.add(customer)

                count += 1

            except Exception as e:
                logger.error(f"Error processing customer {customer_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} customers")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing customers: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_agents(db, Agent, api_key):
    """Sync agents from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        agents_data = client.fetch_agents()

        if agents_data is None:
            return False, 0, "Failed to fetch agents from Atera API"

        count = 0
        for agent_data in agents_data:
            try:
                agent_id = str(agent_data.get('AgentID'))

                existing = Agent.query.filter_by(agent_id=agent_id).first()

                if existing:
                    existing.device_guid = agent_data.get('DeviceGuid', '')
                    existing.machine_name = agent_data.get('MachineName', '')
                    existing.system_name = agent_data.get('SystemName', '')
                    existing.customer_id = str(agent_data.get('CustomerID', ''))
                    existing.customer_name = agent_data.get('CustomerName', '')
                    existing.folder_id = str(agent_data.get('FolderID', ''))
                    existing.folder_name = agent_data.get('FolderName', '')
                    existing.domain_name = agent_data.get('DomainName', '')
                    existing.operating_system = agent_data.get('OperatingSystem', '')
                    existing.os_version = agent_data.get('OSVersion', '')
                    existing.os_build = agent_data.get('OSBuild', '')
                    existing.ip_address = agent_data.get('IPAddress', '')
                    # Convert MacAddresses array to JSON string
                    mac_addrs = agent_data.get('MacAddresses', [])
                    existing.mac_addresses = json.dumps(mac_addrs) if mac_addrs else None
                    existing.last_login_user = agent_data.get('LastLoginUser', '')
                    existing.antivirus_status = agent_data.get('AntivirusStatus', '')
                    existing.agent_version = agent_data.get('AgentVersion', '')
                    existing.online = agent_data.get('Online', False)
                    existing.monitored = agent_data.get('Monitored', False)
                    existing.favorite = agent_data.get('Favorite', False)
                    # Hardware details
                    existing.processor = agent_data.get('Processor', '')
                    existing.processor_cores_count = agent_data.get('ProcessorCoresCount', 0)
                    existing.memory = agent_data.get('Memory', 0)
                    existing.motherboard = agent_data.get('Motherboard', '')
                    existing.display = agent_data.get('Display', '')
                    existing.sound = agent_data.get('Sound', '')
                    # Vendor information
                    existing.vendor = agent_data.get('Vendor', '')
                    existing.vendor_serial_number = agent_data.get('VendorSerialNumber', '')
                    existing.vendor_brand_model = agent_data.get('VendorBrandModel', '')
                    existing.product_name = agent_data.get('ProductName', '')
                    # BIOS information
                    existing.bios_manufacturer = agent_data.get('BiosManufacturer', '')
                    existing.bios_version = agent_data.get('BiosVersion', '')
                    existing.bios_release_date = parse_atera_datetime(agent_data.get('BiosReleaseDate'))
                    # Software
                    existing.office = agent_data.get('Office', '')
                    existing.office_full_version = agent_data.get('OfficeFullVersion', '')
                    # Monitoring
                    existing.threshold_id = str(agent_data.get('ThresholdID', ''))
                    existing.reported_from_ip = agent_data.get('ReportedFromIP', '')
                    existing.device_type = agent_data.get('DeviceType', '')
                    # Timestamps
                    existing.created_at = parse_atera_datetime(agent_data.get('CreatedOn'))
                    existing.modified = parse_atera_datetime(agent_data.get('Modified'))
                    existing.last_seen = parse_atera_datetime(agent_data.get('LastSeen'))
                    existing.last_reboot_time = parse_atera_datetime(agent_data.get('LastRebootTime'))
                    existing.synced_at = datetime.now()
                else:
                    # Convert MacAddresses array to JSON string
                    mac_addrs = agent_data.get('MacAddresses', [])
                    agent = Agent(
                        agent_id=agent_id,
                        device_guid=agent_data.get('DeviceGuid', ''),
                        machine_name=agent_data.get('MachineName', ''),
                        system_name=agent_data.get('SystemName', ''),
                        customer_id=str(agent_data.get('CustomerID', '')),
                        customer_name=agent_data.get('CustomerName', ''),
                        folder_id=str(agent_data.get('FolderID', '')),
                        folder_name=agent_data.get('FolderName', ''),
                        domain_name=agent_data.get('DomainName', ''),
                        operating_system=agent_data.get('OperatingSystem', ''),
                        os_version=agent_data.get('OSVersion', ''),
                        os_build=agent_data.get('OSBuild', ''),
                        ip_address=agent_data.get('IPAddress', ''),
                        mac_addresses=json.dumps(mac_addrs) if mac_addrs else None,
                        last_login_user=agent_data.get('LastLoginUser', ''),
                        antivirus_status=agent_data.get('AntivirusStatus', ''),
                        agent_version=agent_data.get('AgentVersion', ''),
                        online=agent_data.get('Online', False),
                        monitored=agent_data.get('Monitored', False),
                        favorite=agent_data.get('Favorite', False),
                        # Hardware details
                        processor=agent_data.get('Processor', ''),
                        processor_cores_count=agent_data.get('ProcessorCoresCount', 0),
                        memory=agent_data.get('Memory', 0),
                        motherboard=agent_data.get('Motherboard', ''),
                        display=agent_data.get('Display', ''),
                        sound=agent_data.get('Sound', ''),
                        # Vendor information
                        vendor=agent_data.get('Vendor', ''),
                        vendor_serial_number=agent_data.get('VendorSerialNumber', ''),
                        vendor_brand_model=agent_data.get('VendorBrandModel', ''),
                        product_name=agent_data.get('ProductName', ''),
                        # BIOS information
                        bios_manufacturer=agent_data.get('BiosManufacturer', ''),
                        bios_version=agent_data.get('BiosVersion', ''),
                        bios_release_date=parse_atera_datetime(agent_data.get('BiosReleaseDate')),
                        # Software
                        office=agent_data.get('Office', ''),
                        office_full_version=agent_data.get('OfficeFullVersion', ''),
                        # Monitoring
                        threshold_id=str(agent_data.get('ThresholdID', '')),
                        reported_from_ip=agent_data.get('ReportedFromIP', ''),
                        device_type=agent_data.get('DeviceType', ''),
                        # Timestamps
                        created_at=parse_atera_datetime(agent_data.get('CreatedOn')),
                        modified=parse_atera_datetime(agent_data.get('Modified')),
                        last_seen=parse_atera_datetime(agent_data.get('LastSeen')),
                        last_reboot_time=parse_atera_datetime(agent_data.get('LastRebootTime')),
                        synced_at=datetime.now()
                    )
                    db.session.add(agent)

                count += 1

            except Exception as e:
                logger.error(f"Error processing agent {agent_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} agents")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing agents: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_alerts(db, Alert, api_key):
    """Sync alerts from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        alerts_data = client.fetch_alerts()

        if alerts_data is None:
            return False, 0, "Failed to fetch alerts from Atera API"

        count = 0
        for alert_data in alerts_data:
            try:
                alert_id = str(alert_data.get('AlertID'))

                existing = Alert.query.filter_by(alert_id=alert_id).first()

                if existing:
                    existing.alert_message = alert_data.get('AlertMessage', '')
                    existing.alert_category = alert_data.get('AlertCategoryName', '')
                    existing.severity = alert_data.get('Severity', '')
                    existing.customer_id = str(alert_data.get('CustomerID', ''))
                    existing.customer_name = alert_data.get('CustomerName', '')
                    existing.device_name = alert_data.get('DeviceName', '')
                    existing.alert_source = alert_data.get('AlertSource', '')
                    existing.archived = alert_data.get('Archived', False)
                    existing.created_at = parse_atera_datetime(alert_data.get('Created'))
                    existing.threshold_value = alert_data.get('ThresholdValue', '')
                    existing.threshold_value2 = alert_data.get('ThresholdValue2', '')
                    existing.threshold_value3 = alert_data.get('ThresholdValue3', '')
                    existing.threshold_value4 = alert_data.get('ThresholdValue4', '')
                    existing.threshold_value5 = alert_data.get('ThresholdValue5', '')
                    existing.additional_info = alert_data.get('AdditionalInfo', '')
                    existing.code = alert_data.get('Code', '')
                    existing.snoozed_end_date = parse_atera_datetime(alert_data.get('SnoozedEndDate'))
                    existing.archived_date = parse_atera_datetime(alert_data.get('ArchivedDate'))
                    existing.folder_id = str(alert_data.get('FolderID', ''))
                    existing.polling_cycles_count = alert_data.get('PollingCyclesCount', 0)
                    existing.synced_at = datetime.now()
                else:
                    alert = Alert(
                        alert_id=alert_id,
                        alert_message=alert_data.get('AlertMessage', ''),
                        alert_category=alert_data.get('AlertCategoryName', ''),
                        severity=alert_data.get('Severity', ''),
                        customer_id=str(alert_data.get('CustomerID', '')),
                        customer_name=alert_data.get('CustomerName', ''),
                        device_name=alert_data.get('DeviceName', ''),
                        alert_source=alert_data.get('AlertSource', ''),
                        archived=alert_data.get('Archived', False),
                        created_at=parse_atera_datetime(alert_data.get('Created')),
                        threshold_value=alert_data.get('ThresholdValue', ''),
                        threshold_value2=alert_data.get('ThresholdValue2', ''),
                        threshold_value3=alert_data.get('ThresholdValue3', ''),
                        threshold_value4=alert_data.get('ThresholdValue4', ''),
                        threshold_value5=alert_data.get('ThresholdValue5', ''),
                        additional_info=alert_data.get('AdditionalInfo', ''),
                        code=alert_data.get('Code', ''),
                        snoozed_end_date=parse_atera_datetime(alert_data.get('SnoozedEndDate')),
                        archived_date=parse_atera_datetime(alert_data.get('ArchivedDate')),
                        folder_id=str(alert_data.get('FolderID', '')),
                        polling_cycles_count=alert_data.get('PollingCyclesCount', 0),
                        synced_at=datetime.now()
                    )
                    db.session.add(alert)

                count += 1

            except Exception as e:
                logger.error(f"Error processing alert {alert_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} alerts")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing alerts: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_contacts(db, Contact, api_key):
    """Sync contacts from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        contacts_data = client.fetch_contacts()

        logger.info(f"Raw contacts_data type: {type(contacts_data)}, is None: {contacts_data is None}")
        if contacts_data is not None:
            logger.info(f"Raw contacts_data length: {len(contacts_data)}")

        if contacts_data is None:
            logger.error("fetch_contacts returned None - check API logs for errors")
            return False, 0, "Failed to fetch contacts from Atera API"

        if len(contacts_data) == 0:
            logger.warning("fetch_contacts returned empty list - no contacts available or API permission issue")
            return True, 0, None

        logger.info(f"Fetched {len(contacts_data)} contacts from Atera API")

        # Log first contact structure for debugging
        if contacts_data and len(contacts_data) > 0:
            logger.info(f"First contact structure: {contacts_data[0]}")

        count = 0
        skipped = 0
        for contact_data in contacts_data:
            try:
                # Skip contacts without a valid EndUserID
                raw_contact_id = contact_data.get('EndUserID')
                if not raw_contact_id:
                    logger.warning(f"Skipping contact without EndUserID: {contact_data.get('Email', 'unknown')}")
                    skipped += 1
                    continue

                contact_id = str(raw_contact_id)

                existing = Contact.query.filter_by(contact_id=contact_id).first()

                if existing:
                    existing.customer_id = str(contact_data.get('CustomerID', ''))
                    existing.customer_name = contact_data.get('CustomerName', '')
                    existing.email = contact_data.get('Email', '')
                    existing.firstname = contact_data.get('Firstname', '')
                    existing.lastname = contact_data.get('Lastname', '')
                    existing.phone = contact_data.get('Phone', '')
                    existing.mobile_phone = contact_data.get('MobilePhone', '')
                    existing.job_title = contact_data.get('JobTitle', '')
                    existing.is_contact_person = contact_data.get('IsContactPerson', False)
                    existing.in_ignore_mode = contact_data.get('InIgnoreMode', False)
                    existing.department_id = str(contact_data.get('DepartmentID', ''))
                    existing.department_name = contact_data.get('DepartmentName', '')
                    existing.created_at = parse_atera_datetime(contact_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    contact = Contact(
                        contact_id=contact_id,
                        customer_id=str(contact_data.get('CustomerID', '')),
                        customer_name=contact_data.get('CustomerName', ''),
                        email=contact_data.get('Email', ''),
                        firstname=contact_data.get('Firstname', ''),
                        lastname=contact_data.get('Lastname', ''),
                        phone=contact_data.get('Phone', ''),
                        mobile_phone=contact_data.get('MobilePhone', ''),
                        job_title=contact_data.get('JobTitle', ''),
                        is_contact_person=contact_data.get('IsContactPerson', False),
                        in_ignore_mode=contact_data.get('InIgnoreMode', False),
                        department_id=str(contact_data.get('DepartmentID', '')),
                        department_name=contact_data.get('DepartmentName', ''),
                        created_at=parse_atera_datetime(contact_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(contact)

                count += 1

            except Exception as e:
                contact_identifier = contact_data.get('EndUserID', contact_data.get('Email', 'unknown'))
                logger.error(f"Error processing contact {contact_identifier}: {str(e)}", exc_info=True)
                # Log the problematic contact data for debugging
                logger.error(f"Problematic contact data: {contact_data}")
                skipped += 1
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} contacts (skipped {skipped} contacts without IDs or errors)")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing contacts: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_contracts(db, Contract, api_key):
    """Sync contracts from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        contracts_data = client.fetch_contracts()

        if contracts_data is None:
            return False, 0, "Failed to fetch contracts from Atera API"

        count = 0
        for contract_data in contracts_data:
            try:
                contract_id = str(contract_data.get('ContractID'))

                existing = Contract.query.filter_by(contract_id=contract_id).first()

                if existing:
                    existing.customer_id = str(contract_data.get('CustomerID', ''))
                    existing.customer_name = contract_data.get('CustomerName', '')
                    existing.contract_name = contract_data.get('ContractName', '')
                    existing.description = contract_data.get('Description', '')
                    existing.start_date = parse_atera_date(contract_data.get('StartDate'))
                    existing.end_date = parse_atera_date(contract_data.get('EndDate'))
                    existing.contract_type = contract_data.get('ContractType', '')
                    existing.amount = contract_data.get('Amount', 0.0)
                    existing.billing_period = contract_data.get('BillingPeriod', '')
                    existing.created_at = parse_atera_datetime(contract_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    contract = Contract(
                        contract_id=contract_id,
                        customer_id=str(contract_data.get('CustomerID', '')),
                        customer_name=contract_data.get('CustomerName', ''),
                        contract_name=contract_data.get('ContractName', ''),
                        description=contract_data.get('Description', ''),
                        start_date=parse_atera_date(contract_data.get('StartDate')),
                        end_date=parse_atera_date(contract_data.get('EndDate')),
                        contract_type=contract_data.get('ContractType', ''),
                        amount=contract_data.get('Amount', 0.0),
                        billing_period=contract_data.get('BillingPeriod', ''),
                        created_at=parse_atera_datetime(contract_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(contract)

                count += 1

            except Exception as e:
                logger.error(f"Error processing contract {contract_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} contracts")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing contracts: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_invoices(db, Invoice, api_key):
    """Sync invoices from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        invoices_data = client.fetch_invoices()

        if invoices_data is None:
            return False, 0, "Failed to fetch invoices from Atera API"

        count = 0
        for invoice_data in invoices_data:
            try:
                invoice_id = str(invoice_data.get('InvoiceID'))

                existing = Invoice.query.filter_by(invoice_id=invoice_id).first()

                if existing:
                    existing.customer_id = str(invoice_data.get('CustomerID', ''))
                    existing.customer_name = invoice_data.get('CustomerName', '')
                    existing.invoice_number = invoice_data.get('InvoiceNumber', '')
                    existing.invoice_date = parse_atera_date(invoice_data.get('InvoiceDate'))
                    existing.due_date = parse_atera_date(invoice_data.get('DueDate'))
                    existing.total_amount = invoice_data.get('TotalAmount', 0.0)
                    existing.paid = invoice_data.get('Paid', False)
                    existing.status = invoice_data.get('Status', '')
                    existing.description = invoice_data.get('Description', '')
                    existing.created_at = parse_atera_datetime(invoice_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    invoice = Invoice(
                        invoice_id=invoice_id,
                        customer_id=str(invoice_data.get('CustomerID', '')),
                        customer_name=invoice_data.get('CustomerName', ''),
                        invoice_number=invoice_data.get('InvoiceNumber', ''),
                        invoice_date=parse_atera_date(invoice_data.get('InvoiceDate')),
                        due_date=parse_atera_date(invoice_data.get('DueDate')),
                        total_amount=invoice_data.get('TotalAmount', 0.0),
                        paid=invoice_data.get('Paid', False),
                        status=invoice_data.get('Status', ''),
                        description=invoice_data.get('Description', ''),
                        created_at=parse_atera_datetime(invoice_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(invoice)

                count += 1

            except Exception as e:
                logger.error(f"Error processing invoice {invoice_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} invoices")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing invoices: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_tickets(db, Ticket, api_key):
    """Sync tickets from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        tickets_data = client.fetch_all_tickets()

        if tickets_data is None:
            return False, 0, "Failed to fetch tickets from Atera API"

        count = 0
        for ticket_data in tickets_data:
            try:
                ticket_id = str(ticket_data.get('TicketID'))

                existing = Ticket.query.filter_by(ticket_id=ticket_id).first()

                if existing:
                    existing.ticket_number = str(ticket_data.get('TicketNumber', ''))
                    existing.title = ticket_data.get('TicketTitle', '')
                    existing.description = ticket_data.get('TicketDetails', '')
                    existing.comment = ticket_data.get('Comment', '')
                    existing.resolution = ticket_data.get('TicketResolvedComments', '')
                    existing.created_at = parse_atera_datetime(ticket_data.get('TicketCreatedDate'))
                    existing.closed_date = parse_atera_datetime(ticket_data.get('TicketClosedDate'))
                    existing.resolved_date = parse_atera_datetime(ticket_data.get('TicketResolvedDate'))
                    existing.priority = ticket_data.get('TicketPriority', '')
                    existing.status = ticket_data.get('TicketStatus', '')
                    existing.ticket_type = ticket_data.get('TicketType', '')
                    existing.ticket_impact = ticket_data.get('TicketImpact', '')
                    existing.client = ticket_data.get('CustomerName', '')
                    existing.user = ticket_data.get('TechnicianFullName', '')
                    existing.end_user_firstname = ticket_data.get('FirstName', '')
                    existing.end_user_lastname = ticket_data.get('LastName', '')
                    existing.end_user_email = ticket_data.get('EndUserEmail', '')
                    existing.end_user_phone = ticket_data.get('EndUserPhone', '')
                    # Additional timing fields
                    existing.technician_first_comment_date = parse_atera_datetime(ticket_data.get('TechnicianFirstCommentDate'))
                    existing.first_response_due_date = parse_atera_datetime(ticket_data.get('FirstResponseDueDate'))
                    existing.closed_ticket_due_date = parse_atera_datetime(ticket_data.get('ClosedTicketDueDate'))
                    # Comment tracking
                    existing.first_comment = ticket_data.get('FirstComment', '')
                    existing.last_end_user_comment_timestamp = parse_atera_datetime(ticket_data.get('LastEndUserCommentTimestamp'))
                    existing.last_technician_comment_timestamp = parse_atera_datetime(ticket_data.get('LastTechnicianCommentTimestamp'))
                    # Related information
                    existing.customer_business_number = ticket_data.get('CustomerBusinessNumber', '')
                    existing.technician_full_name = ticket_data.get('TechnicianFullName', '')
                    existing.technician_email = ticket_data.get('TechnicianEmail', '')
                    existing.contract_id = str(ticket_data.get('ContractID', ''))
                    existing.synced_at = datetime.now()
                else:
                    ticket = Ticket(
                        ticket_id=ticket_id,
                        ticket_number=str(ticket_data.get('TicketNumber', '')),
                        title=ticket_data.get('TicketTitle', ''),
                        description=ticket_data.get('TicketDetails', ''),
                        comment=ticket_data.get('Comment', ''),
                        resolution=ticket_data.get('TicketResolvedComments', ''),
                        created_at=parse_atera_datetime(ticket_data.get('TicketCreatedDate')),
                        closed_date=parse_atera_datetime(ticket_data.get('TicketClosedDate')),
                        resolved_date=parse_atera_datetime(ticket_data.get('TicketResolvedDate')),
                        priority=ticket_data.get('TicketPriority', ''),
                        status=ticket_data.get('TicketStatus', ''),
                        ticket_type=ticket_data.get('TicketType', ''),
                        ticket_impact=ticket_data.get('TicketImpact', ''),
                        client=ticket_data.get('CustomerName', ''),
                        user=ticket_data.get('TechnicianFullName', ''),
                        end_user_firstname=ticket_data.get('FirstName', ''),
                        end_user_lastname=ticket_data.get('LastName', ''),
                        end_user_email=ticket_data.get('EndUserEmail', ''),
                        end_user_phone=ticket_data.get('EndUserPhone', ''),
                        notified=False,
                        # Additional timing fields
                        technician_first_comment_date=parse_atera_datetime(ticket_data.get('TechnicianFirstCommentDate')),
                        first_response_due_date=parse_atera_datetime(ticket_data.get('FirstResponseDueDate')),
                        closed_ticket_due_date=parse_atera_datetime(ticket_data.get('ClosedTicketDueDate')),
                        # Comment tracking
                        first_comment=ticket_data.get('FirstComment', ''),
                        last_end_user_comment_timestamp=parse_atera_datetime(ticket_data.get('LastEndUserCommentTimestamp')),
                        last_technician_comment_timestamp=parse_atera_datetime(ticket_data.get('LastTechnicianCommentTimestamp')),
                        # Related information
                        customer_business_number=ticket_data.get('CustomerBusinessNumber', ''),
                        technician_full_name=ticket_data.get('TechnicianFullName', ''),
                        technician_email=ticket_data.get('TechnicianEmail', ''),
                        contract_id=str(ticket_data.get('ContractID', '')),
                        synced_at=datetime.now()
                    )
                    db.session.add(ticket)

                count += 1

            except Exception as e:
                logger.error(f"Error processing ticket {ticket_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} tickets")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing tickets: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_snmp_devices(db, SNMPDevice, api_key):
    """Sync SNMP devices from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        devices_data = client.fetch_snmp_devices()

        if devices_data is None:
            return False, 0, "Failed to fetch SNMP devices from Atera API"

        count = 0
        for device_data in devices_data:
            try:
                device_id = str(device_data.get('SNMPDeviceID') or device_data.get('DeviceID'))
                existing = SNMPDevice.query.filter_by(device_id=device_id).first()

                if existing:
                    existing.device_name = device_data.get('DeviceName', '')
                    existing.customer_id = str(device_data.get('CustomerID', ''))
                    existing.customer_name = device_data.get('CustomerName', '')
                    existing.ip_address = device_data.get('IPAddress', '')
                    existing.snmp_version = device_data.get('SNMPVersion', '')
                    existing.device_type = device_data.get('DeviceType', '')
                    existing.system_name = device_data.get('SystemName', '')
                    existing.system_location = device_data.get('SystemLocation', '')
                    existing.system_contact = device_data.get('SystemContact', '')
                    existing.system_description = device_data.get('SystemDescription', '')
                    existing.last_online = parse_atera_datetime(device_data.get('LastOnline'))
                    existing.created_at = parse_atera_datetime(device_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    device = SNMPDevice(
                        device_id=device_id,
                        device_name=device_data.get('DeviceName', ''),
                        customer_id=str(device_data.get('CustomerID', '')),
                        customer_name=device_data.get('CustomerName', ''),
                        ip_address=device_data.get('IPAddress', ''),
                        snmp_version=device_data.get('SNMPVersion', ''),
                        device_type=device_data.get('DeviceType', ''),
                        system_name=device_data.get('SystemName', ''),
                        system_location=device_data.get('SystemLocation', ''),
                        system_contact=device_data.get('SystemContact', ''),
                        system_description=device_data.get('SystemDescription', ''),
                        last_online=parse_atera_datetime(device_data.get('LastOnline')),
                        created_at=parse_atera_datetime(device_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(device)
                count += 1
            except Exception as e:
                logger.error(f"Error processing SNMP device {device_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} SNMP devices")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing SNMP devices: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_tcp_devices(db, TCPDevice, api_key):
    """Sync TCP devices from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        devices_data = client.fetch_tcp_devices()

        if devices_data is None:
            return False, 0, "Failed to fetch TCP devices from Atera API"

        count = 0
        for device_data in devices_data:
            try:
                device_id = str(device_data.get('TCPDeviceID') or device_data.get('DeviceID'))
                existing = TCPDevice.query.filter_by(device_id=device_id).first()

                if existing:
                    existing.device_name = device_data.get('DeviceName', '')
                    existing.customer_id = str(device_data.get('CustomerID', ''))
                    existing.customer_name = device_data.get('CustomerName', '')
                    existing.ip_address = device_data.get('IPAddress', '')
                    existing.port = device_data.get('Port', 0)
                    existing.device_type = device_data.get('DeviceType', '')
                    existing.monitoring_enabled = device_data.get('MonitoringEnabled', True)
                    existing.last_online = parse_atera_datetime(device_data.get('LastOnline'))
                    existing.created_at = parse_atera_datetime(device_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    device = TCPDevice(
                        device_id=device_id,
                        device_name=device_data.get('DeviceName', ''),
                        customer_id=str(device_data.get('CustomerID', '')),
                        customer_name=device_data.get('CustomerName', ''),
                        ip_address=device_data.get('IPAddress', ''),
                        port=device_data.get('Port', 0),
                        device_type=device_data.get('DeviceType', ''),
                        monitoring_enabled=device_data.get('MonitoringEnabled', True),
                        last_online=parse_atera_datetime(device_data.get('LastOnline')),
                        created_at=parse_atera_datetime(device_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(device)
                count += 1
            except Exception as e:
                logger.error(f"Error processing TCP device {device_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} TCP devices")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing TCP devices: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_knowledge_base(db, KnowledgeBase, api_key):
    """Sync knowledge base articles from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        articles_data = client.fetch_knowledge_base()

        if articles_data is None:
            return False, 0, "Failed to fetch knowledge base from Atera API"

        count = 0
        for article_data in articles_data:
            try:
                article_id = str(article_data.get('ArticleID') or article_data.get('KnowledgeBaseID'))
                existing = KnowledgeBase.query.filter_by(article_id=article_id).first()

                if existing:
                    existing.title = article_data.get('Title', '')
                    existing.content = article_data.get('Content', '')
                    existing.category = article_data.get('Category', '')
                    existing.keywords = article_data.get('Keywords', '')
                    existing.created_by = article_data.get('CreatedBy', '')
                    existing.last_modified_by = article_data.get('LastModifiedBy', '')
                    existing.created_at = parse_atera_datetime(article_data.get('CreatedOn'))
                    existing.last_modified = parse_atera_datetime(article_data.get('LastModified'))
                    existing.synced_at = datetime.now()
                else:
                    article = KnowledgeBase(
                        article_id=article_id,
                        title=article_data.get('Title', ''),
                        content=article_data.get('Content', ''),
                        category=article_data.get('Category', ''),
                        keywords=article_data.get('Keywords', ''),
                        created_by=article_data.get('CreatedBy', ''),
                        last_modified_by=article_data.get('LastModifiedBy', ''),
                        created_at=parse_atera_datetime(article_data.get('CreatedOn')),
                        last_modified=parse_atera_datetime(article_data.get('LastModified')),
                        synced_at=datetime.now()
                    )
                    db.session.add(article)
                count += 1
            except Exception as e:
                logger.error(f"Error processing knowledge base article {article_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} knowledge base articles")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing knowledge base: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_products(db, Product, api_key):
    """Sync products from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        products_data = client.fetch_products()

        if products_data is None:
            return False, 0, "Failed to fetch products from Atera API"

        count = 0
        for product_data in products_data:
            try:
                product_id = str(product_data.get('ProductID'))
                existing = Product.query.filter_by(product_id=product_id).first()

                if existing:
                    existing.product_name = product_data.get('ProductName', '')
                    existing.description = product_data.get('Description', '')
                    existing.category = product_data.get('Category', '')
                    existing.rate = product_data.get('Rate', 0.0)
                    existing.rate_type = product_data.get('RateType', '')
                    existing.active = product_data.get('Active', True)
                    existing.created_at = parse_atera_datetime(product_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    product = Product(
                        product_id=product_id,
                        product_name=product_data.get('ProductName', ''),
                        description=product_data.get('Description', ''),
                        category=product_data.get('Category', ''),
                        rate=product_data.get('Rate', 0.0),
                        rate_type=product_data.get('RateType', ''),
                        active=product_data.get('Active', True),
                        created_at=parse_atera_datetime(product_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(product)
                count += 1
            except Exception as e:
                logger.error(f"Error processing product {product_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} products")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing products: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_expenses(db, Expense, api_key):
    """Sync expenses from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        expenses_data = client.fetch_expenses()

        if expenses_data is None:
            return False, 0, "Failed to fetch expenses from Atera API"

        count = 0
        for expense_data in expenses_data:
            try:
                expense_id = str(expense_data.get('ExpenseID'))
                existing = Expense.query.filter_by(expense_id=expense_id).first()

                if existing:
                    existing.expense_name = expense_data.get('ExpenseName', '')
                    existing.description = expense_data.get('Description', '')
                    existing.amount = expense_data.get('Amount', 0.0)
                    existing.customer_id = str(expense_data.get('CustomerID', ''))
                    existing.customer_name = expense_data.get('CustomerName', '')
                    existing.ticket_id = str(expense_data.get('TicketID', ''))
                    existing.expense_date = parse_atera_date(expense_data.get('ExpenseDate'))
                    existing.created_at = parse_atera_datetime(expense_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    expense = Expense(
                        expense_id=expense_id,
                        expense_name=expense_data.get('ExpenseName', ''),
                        description=expense_data.get('Description', ''),
                        amount=expense_data.get('Amount', 0.0),
                        customer_id=str(expense_data.get('CustomerID', '')),
                        customer_name=expense_data.get('CustomerName', ''),
                        ticket_id=str(expense_data.get('TicketID', '')),
                        expense_date=parse_atera_date(expense_data.get('ExpenseDate')),
                        created_at=parse_atera_datetime(expense_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(expense)
                count += 1
            except Exception as e:
                logger.error(f"Error processing expense {expense_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} expenses")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing expenses: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_http_devices(db, HTTPDevice, api_key):
    """Sync HTTP devices from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        devices_data = client.fetch_http_devices()

        if devices_data is None:
            return False, 0, "Failed to fetch HTTP devices from Atera API"

        count = 0
        for device_data in devices_data:
            try:
                device_id = str(device_data.get('HTTPDeviceID') or device_data.get('DeviceID'))
                existing = HTTPDevice.query.filter_by(device_id=device_id).first()

                if existing:
                    existing.device_name = device_data.get('DeviceName', '')
                    existing.customer_id = str(device_data.get('CustomerID', ''))
                    existing.customer_name = device_data.get('CustomerName', '')
                    existing.url = device_data.get('URL', '')
                    existing.expected_response = device_data.get('ExpectedResponse', '')
                    existing.monitoring_enabled = device_data.get('MonitoringEnabled', True)
                    existing.last_online = parse_atera_datetime(device_data.get('LastOnline'))
                    existing.created_at = parse_atera_datetime(device_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    device = HTTPDevice(
                        device_id=device_id,
                        device_name=device_data.get('DeviceName', ''),
                        customer_id=str(device_data.get('CustomerID', '')),
                        customer_name=device_data.get('CustomerName', ''),
                        url=device_data.get('URL', ''),
                        expected_response=device_data.get('ExpectedResponse', ''),
                        monitoring_enabled=device_data.get('MonitoringEnabled', True),
                        last_online=parse_atera_datetime(device_data.get('LastOnline')),
                        created_at=parse_atera_datetime(device_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(device)
                count += 1
            except Exception as e:
                logger.error(f"Error processing HTTP device {device_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} HTTP devices")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing HTTP devices: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_generic_devices(db, GenericDevice, api_key):
    """Sync Generic devices from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        devices_data = client.fetch_generic_devices()

        if devices_data is None:
            return False, 0, "Failed to fetch Generic devices from Atera API"

        count = 0
        for device_data in devices_data:
            try:
                device_id = str(device_data.get('GenericDeviceID') or device_data.get('DeviceID'))
                existing = GenericDevice.query.filter_by(device_id=device_id).first()

                if existing:
                    existing.device_name = device_data.get('DeviceName', '')
                    existing.customer_id = str(device_data.get('CustomerID', ''))
                    existing.customer_name = device_data.get('CustomerName', '')
                    existing.monitoring_enabled = device_data.get('MonitoringEnabled', True)
                    existing.last_online = parse_atera_datetime(device_data.get('LastOnline'))
                    existing.created_at = parse_atera_datetime(device_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    device = GenericDevice(
                        device_id=device_id,
                        device_name=device_data.get('DeviceName', ''),
                        customer_id=str(device_data.get('CustomerID', '')),
                        customer_name=device_data.get('CustomerName', ''),
                        monitoring_enabled=device_data.get('MonitoringEnabled', True),
                        last_online=parse_atera_datetime(device_data.get('LastOnline')),
                        created_at=parse_atera_datetime(device_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(device)
                count += 1
            except Exception as e:
                logger.error(f"Error processing Generic device {device_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} Generic devices")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing Generic devices: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_departments(db, Department, api_key):
    """Sync departments from Atera API to database"""
    try:
        client = AteraAPIClient(api_key)
        departments_data = client.fetch_departments()

        if departments_data is None:
            return False, 0, "Failed to fetch departments from Atera API"

        count = 0
        for department_data in departments_data:
            try:
                department_id = str(department_data.get('DepartmentID'))
                existing = Department.query.filter_by(department_id=department_id).first()

                if existing:
                    existing.department_name = department_data.get('DepartmentName', '')
                    existing.description = department_data.get('Description', '')
                    existing.created_at = parse_atera_datetime(department_data.get('CreatedOn'))
                    existing.synced_at = datetime.now()
                else:
                    department = Department(
                        department_id=department_id,
                        department_name=department_data.get('DepartmentName', ''),
                        description=department_data.get('Description', ''),
                        created_at=parse_atera_datetime(department_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(department)
                count += 1
            except Exception as e:
                logger.error(f"Error processing department {department_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} departments")
        return True, count, None
    except Exception as e:
        logger.error(f"Error syncing departments: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_account(db, Account, api_key):
    """Sync account information from Atera API"""
    try:
        client = AteraAPIClient(api_key)
        account_data = client.fetch_account()

        if account_data is None:
            return False, 0, "Failed to fetch account from Atera API"

        # Update or create single account record
        account = Account.query.first()
        if account:
            account.account_id = account_data.get('AccountID', '')
            account.country = account_data.get('Country', '')
            account.company_name = account_data.get('CompanyName', '')
            account.created_on = parse_atera_datetime(account_data.get('CreatedOn'))
            account.state = account_data.get('State', '')
            account.timezone_name = account_data.get('TimeZoneName', '')
            account.city = account_data.get('City', '')
            account.address = account_data.get('Address', '')
            account.postal_code = account_data.get('PostalCode', '')
            account.phone = account_data.get('Phone', '')
            account.is_it_department = account_data.get('IsITDepartment', False)
            account.plan = account_data.get('Plan', '')
            account.synced_at = datetime.now()
        else:
            account = Account(
                account_id=account_data.get('AccountID', ''),
                country=account_data.get('Country', ''),
                company_name=account_data.get('CompanyName', ''),
                created_on=parse_atera_datetime(account_data.get('CreatedOn')),
                state=account_data.get('State', ''),
                timezone_name=account_data.get('TimeZoneName', ''),
                city=account_data.get('City', ''),
                address=account_data.get('Address', ''),
                postal_code=account_data.get('PostalCode', ''),
                phone=account_data.get('Phone', ''),
                is_it_department=account_data.get('IsITDepartment', False),
                plan=account_data.get('Plan', ''),
                synced_at=datetime.now()
            )
            db.session.add(account)

        db.session.commit()
        logger.info("Successfully synced account information")
        return True, 1, None
    except Exception as e:
        logger.error(f"Error syncing account: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_ticket_comments(db, TicketComment, Ticket, api_key):
    """Sync all ticket comments from Atera API"""
    try:
        client = AteraAPIClient(api_key)

        # Delete existing comments to avoid duplicates
        TicketComment.query.delete()

        # Get all tickets
        tickets = Ticket.query.all()
        total_comments = 0

        for ticket in tickets:
            try:
                comments_data = client.fetch_ticket_comments(ticket.ticket_id)

                if comments_data:
                    for comment_data in comments_data:
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
                logger.error(f"Error syncing comments for ticket {ticket.ticket_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {total_comments} ticket comments across {len(tickets)} tickets")
        return True, total_comments, None

    except Exception as e:
        logger.error(f"Error syncing ticket comments: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_ticket_workhours(db, TicketWorkHour, Ticket, api_key):
    """Sync all ticket work hours from Atera API"""
    try:
        client = AteraAPIClient(api_key)

        # Delete existing work hours to avoid duplicates
        TicketWorkHour.query.delete()

        # Get all tickets
        tickets = Ticket.query.all()
        total_hours = 0

        for ticket in tickets:
            try:
                workhours_data = client.fetch_ticket_workhours(ticket.ticket_id)

                if workhours_data:
                    for workhour_data in workhours_data:
                        workhour = TicketWorkHour(
                            ticket_id=ticket.ticket_id,
                            work_hours_id=str(workhour_data.get('WorkHoursID', '')),
                            start_work_hour=parse_atera_datetime(workhour_data.get('StartWorkHour')),
                            end_work_hour=parse_atera_datetime(workhour_data.get('EndWorkHour')),
                            technician_contact_id=str(workhour_data.get('TechnicianContactID', '')),
                            billable=workhour_data.get('Billiable', False),  # Note: API has typo 'Billiable'
                            on_customer_site=workhour_data.get('OnCustomerSite', False),
                            description=workhour_data.get('Description', ''),
                            technician_full_name=workhour_data.get('TechnicianFullName', ''),
                            technician_email=workhour_data.get('TechnicianEmail', ''),
                            rate_id=workhour_data.get('RateID'),
                            rate_amount=workhour_data.get('RateAmount'),
                            synced_at=datetime.now()
                        )
                        db.session.add(workhour)
                        total_hours += 1
            except Exception as e:
                logger.error(f"Error syncing work hours for ticket {ticket.ticket_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {total_hours} work hour records across {len(tickets)} tickets")
        return True, total_hours, None

    except Exception as e:
        logger.error(f"Error syncing ticket work hours: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_agent_patches(db, AgentInstalledPatch, AgentAvailablePatch, Agent, api_key):
    """Sync agent patch information from Atera API"""
    try:
        client = AteraAPIClient(api_key)

        # Delete existing patches to avoid duplicates
        AgentInstalledPatch.query.delete()
        AgentAvailablePatch.query.delete()

        # Get all agents
        agents = Agent.query.all()
        total_installed = 0
        total_available = 0

        for agent in agents:
            try:
                # Fetch installed patches
                installed_patches = client.fetch_agent_installed_patches(agent.device_guid)
                if installed_patches:
                    for patch_data in installed_patches:
                        patch = AgentInstalledPatch(
                            device_guid=agent.device_guid,
                            agent_id=str(agent.agent_id),
                            name=patch_data.get('Name', ''),
                            patch_class=patch_data.get('Class', ''),
                            kb_id=patch_data.get('KBId', ''),
                            install_date=parse_atera_datetime(patch_data.get('InstallDate')),
                            synced_at=datetime.now()
                        )
                        db.session.add(patch)
                        total_installed += 1

                # Fetch available patches
                available_patches = client.fetch_agent_available_patches(agent.device_guid)
                if available_patches:
                    for patch_data in available_patches:
                        patch = AgentAvailablePatch(
                            device_guid=agent.device_guid,
                            agent_id=str(agent.agent_id),
                            name=patch_data.get('Name', ''),
                            patch_class=patch_data.get('Class', ''),
                            kb_id=patch_data.get('KBId', ''),
                            status=patch_data.get('Status', ''),
                            synced_at=datetime.now()
                        )
                        db.session.add(patch)
                        total_available += 1

            except Exception as e:
                logger.error(f"Error syncing patches for agent {agent.device_guid}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {total_installed} installed patches and {total_available} available patches across {len(agents)} agents")
        return True, total_installed + total_available, None

    except Exception as e:
        logger.error(f"Error syncing agent patches: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def sync_custom_field_definitions(db, CustomFieldDefinition, api_key):
    """Sync custom field definitions from Atera API"""
    try:
        client = AteraAPIClient(api_key)
        fields_data = client.fetch_custom_field_definitions()

        if fields_data is None:
            return False, 0, "Failed to fetch custom field definitions from Atera API"

        # Delete existing definitions
        CustomFieldDefinition.query.delete()

        count = 0
        for field_data in fields_data:
            try:
                import json
                field = CustomFieldDefinition(
                    field_name=field_data.get('Name', ''),
                    data_type=field_data.get('DataType', ''),
                    target=field_data.get('Target', ''),
                    possible_values=json.dumps(field_data.get('PossibleValues', [])),
                    synced_at=datetime.now()
                )
                db.session.add(field)
                count += 1
            except Exception as e:
                logger.error(f"Error processing custom field definition: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} custom field definitions")
        return True, count, None

    except Exception as e:
        logger.error(f"Error syncing custom field definitions: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)
