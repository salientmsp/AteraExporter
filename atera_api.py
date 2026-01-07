"""
Atera API Integration Module
Handles all API calls to Atera platform for data fetching
"""

import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AteraAPIClient:
    """Client for interacting with Atera API v3"""

    BASE_URL = 'https://app.atera.com/api/v3'

    def __init__(self, api_key):
        """Initialize the Atera API client with API key"""
        self.api_key = api_key
        self.headers = {
            'X-API-KEY': api_key,
            'Accept': 'application/json'
        }

    def _make_request(self, endpoint, params=None, method='GET'):
        """
        Make a request to the Atera API

        Args:
            endpoint: API endpoint path (e.g., '/customers')
            params: Query parameters
            method: HTTP method (GET, POST, etc.)

        Returns:
            Response data or None on error
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            logger.info(f"Making {method} request to Atera API: {endpoint}")

            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                timeout=30
            )

            logger.info(f"Atera API response: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Atera API error for {endpoint}: HTTP {response.status_code} - {response.text}")
                if response.status_code == 400 and "incorrect account type" in response.text.lower():
                    logger.error(f"Account type does not have access to {endpoint} - check Atera subscription/permissions")
                return None

            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error connecting to Atera API: {endpoint}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error connecting to Atera API: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Atera API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            return None

    def _fetch_paginated(self, endpoint, params=None, items_per_page=50):
        """
        Fetch paginated data from Atera API

        Args:
            endpoint: API endpoint path
            params: Additional query parameters
            items_per_page: Number of items per page

        Returns:
            List of all items across all pages
        """
        all_items = []
        page = 1

        if params is None:
            params = {}

        while True:
            params['page'] = page
            params['itemsInPage'] = items_per_page

            logger.debug(f"Fetching page {page} from {endpoint}")

            response_data = self._make_request(endpoint, params=params)

            if response_data is None:
                break

            items = response_data.get('items', [])

            if not items:
                break

            all_items.extend(items)
            logger.info(f"Fetched {len(items)} items from page {page} (total: {len(all_items)})")

            # Check if there are more pages
            if len(items) < items_per_page:
                break

            page += 1

        logger.info(f"Completed fetching {len(all_items)} items from {endpoint}")
        return all_items

    def fetch_customers(self):
        """Fetch all customers from Atera"""
        logger.info("Fetching customers from Atera")
        return self._fetch_paginated('/customers')

    def fetch_agents(self):
        """Fetch all agents from Atera"""
        logger.info("Fetching agents from Atera")
        return self._fetch_paginated('/agents')

    def fetch_alerts(self, archived=False):
        """
        Fetch alerts from Atera

        Args:
            archived: Include archived alerts (default: False)
        """
        logger.info(f"Fetching alerts from Atera (archived={archived})")
        params = {}
        if not archived:
            params['archived'] = 'false'
        return self._fetch_paginated('/alerts', params=params)

    def fetch_contacts(self):
        """Fetch all contacts from Atera"""
        logger.info("Fetching contacts from Atera")
        return self._fetch_paginated('/contacts')

    def fetch_contracts(self):
        """Fetch all contracts from Atera"""
        logger.info("Fetching contracts from Atera")
        return self._fetch_paginated('/contracts')

    def fetch_tickets(self, status='Open'):
        """
        Fetch tickets from Atera

        Args:
            status: Ticket status filter (Open, Closed, etc.)
        """
        logger.info(f"Fetching tickets from Atera (status={status})")
        params = {}
        if status:
            params['ticketStatus'] = status
        return self._fetch_paginated('/tickets', params=params)

    def fetch_invoices(self):
        """Fetch all invoices from Atera"""
        logger.info("Fetching invoices from Atera")
        return self._fetch_paginated('/billing/invoices')

    def fetch_all_tickets(self):
        """Fetch all tickets regardless of status"""
        logger.info("Fetching all tickets from Atera")
        return self._fetch_paginated('/tickets')

    def fetch_snmp_devices(self):
        """Fetch all SNMP devices from Atera"""
        logger.info("Fetching SNMP devices from Atera")
        return self._fetch_paginated('/devices/snmpdevices')

    def fetch_tcp_devices(self):
        """Fetch all TCP devices from Atera"""
        logger.info("Fetching TCP devices from Atera")
        return self._fetch_paginated('/devices/tcpdevices')

    def fetch_knowledge_base(self):
        """Fetch all knowledge base articles from Atera"""
        logger.info("Fetching knowledge base articles from Atera")
        return self._fetch_paginated('/knowledgebases')

    def fetch_products(self):
        """Fetch all products/rates from Atera"""
        logger.info("Fetching products from Atera")
        return self._fetch_paginated('/rates/products')

    def fetch_expenses(self):
        """Fetch all expenses from Atera"""
        logger.info("Fetching expenses from Atera")
        return self._fetch_paginated('/rates/expenses')

    def fetch_http_devices(self):
        """Fetch all HTTP devices from Atera"""
        logger.info("Fetching HTTP devices from Atera")
        return self._fetch_paginated('/devices/httpdevices')

    def fetch_generic_devices(self):
        """Fetch all Generic devices from Atera"""
        logger.info("Fetching Generic devices from Atera")
        return self._fetch_paginated('/devices/genericdevices')

    def fetch_departments(self):
        """Fetch all departments from Atera"""
        logger.info("Fetching departments from Atera")
        return self._fetch_paginated('/departments')

    def fetch_account(self):
        """Fetch account information from Atera"""
        logger.info("Fetching account information from Atera")
        return self._make_request('/account')

    def fetch_ticket_comments(self, ticket_id):
        """Fetch comments for a specific ticket"""
        logger.info(f"Fetching comments for ticket {ticket_id}")
        return self._fetch_paginated(f'/tickets/{ticket_id}/comments')

    def fetch_ticket_workhours(self, ticket_id):
        """Fetch work hours for a specific ticket"""
        logger.info(f"Fetching work hours for ticket {ticket_id}")
        return self._fetch_paginated(f'/tickets/{ticket_id}/workhoursrecords')

    def fetch_agent_installed_patches(self, device_guid):
        """Fetch installed patches for an agent"""
        logger.info(f"Fetching installed patches for agent {device_guid}")
        result = self._make_request(f'/agents/{device_guid}/installed-patches')
        if result and 'InstalledUpdates' in result:
            return result['InstalledUpdates']
        return []

    def fetch_agent_available_patches(self, device_guid):
        """Fetch available patches for an agent"""
        logger.info(f"Fetching available patches for agent {device_guid}")
        result = self._make_request(f'/agents/{device_guid}/available-patches')
        if result and 'AvailableUpdates' in result:
            return result['AvailableUpdates']
        return []

    def fetch_custom_field_definitions(self):
        """Fetch custom field definitions"""
        logger.info("Fetching custom field definitions from Atera")
        return self._make_request('/customvalues/customfields')


def parse_atera_datetime(date_string):
    """
    Parse datetime string from Atera API

    Args:
        date_string: Date string from Atera API (e.g., '2025-04-16T16:34:41Z')

    Returns:
        datetime object or None
    """
    if not date_string:
        return None

    try:
        # Remove Z and handle timezone
        date_string = date_string.replace('Z', '+00:00')
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing date: {date_string} - {str(e)}")
        return None


def parse_atera_date(date_string):
    """
    Parse date string from Atera API

    Args:
        date_string: Date string from Atera API

    Returns:
        date object or None
    """
    if not date_string:
        return None

    try:
        dt = parse_atera_datetime(date_string)
        return dt.date() if dt else None
    except Exception as e:
        logger.error(f"Error parsing date: {date_string} - {str(e)}")
        return None
