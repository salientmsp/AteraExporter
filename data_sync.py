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
                    existing.machine_name = agent_data.get('MachineName', '')
                    existing.customer_id = str(agent_data.get('CustomerID', ''))
                    existing.customer_name = agent_data.get('CustomerName', '')
                    existing.domain_name = agent_data.get('DomainName', '')
                    existing.operating_system = agent_data.get('OperatingSystem', '')
                    existing.ip_address = agent_data.get('IPAddress', '')
                    existing.last_login_user = agent_data.get('LastLoginUser', '')
                    existing.antivirus_status = agent_data.get('AntivirusStatus', '')
                    existing.agent_version = agent_data.get('AgentVersion', '')
                    existing.online = agent_data.get('Online', False)
                    existing.created_at = parse_atera_datetime(agent_data.get('CreatedOn'))
                    existing.last_seen = parse_atera_datetime(agent_data.get('LastSeen'))
                    existing.synced_at = datetime.now()
                else:
                    agent = Agent(
                        agent_id=agent_id,
                        machine_name=agent_data.get('MachineName', ''),
                        customer_id=str(agent_data.get('CustomerID', '')),
                        customer_name=agent_data.get('CustomerName', ''),
                        domain_name=agent_data.get('DomainName', ''),
                        operating_system=agent_data.get('OperatingSystem', ''),
                        ip_address=agent_data.get('IPAddress', ''),
                        last_login_user=agent_data.get('LastLoginUser', ''),
                        antivirus_status=agent_data.get('AntivirusStatus', ''),
                        agent_version=agent_data.get('AgentVersion', ''),
                        online=agent_data.get('Online', False),
                        created_at=parse_atera_datetime(agent_data.get('CreatedOn')),
                        last_seen=parse_atera_datetime(agent_data.get('LastSeen')),
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
                    existing.additional_info = alert_data.get('AdditionalInfo', '')
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
                        additional_info=alert_data.get('AdditionalInfo', ''),
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

        if contacts_data is None:
            return False, 0, "Failed to fetch contacts from Atera API"

        count = 0
        for contact_data in contacts_data:
            try:
                contact_id = str(contact_data.get('ContactID'))

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
                        created_at=parse_atera_datetime(contact_data.get('CreatedOn')),
                        synced_at=datetime.now()
                    )
                    db.session.add(contact)

                count += 1

            except Exception as e:
                logger.error(f"Error processing contact {contact_id}: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"Successfully synced {count} contacts")
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
