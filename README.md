# Atera Exporter

A comprehensive Flask web application for monitoring Atera tickets, sending SMS notifications to on-call technicians, and exporting all your Atera data to various formats.

## Features

### On-Call Monitoring
- **Ticket Monitoring**: Integration with Atera API to fetch and track support tickets
- **SMS Notifications**: Integration with Twilio for sending text notifications to on-call technicians
- **Multiple On-Call Technicians**: Support for multiple technicians with overlapping schedules
- **Business Hours Configuration**: Configure business hours for each day of the week
- **Holiday Calendar**: Manage holidays with automatic notification handling

### Data Export
- **Comprehensive Data Sync**: Sync all your Atera data including:
  - Customers
  - Agents
  - Alerts
  - Contacts
  - Contracts
  - Invoices
  - Tickets
- **Multiple Export Formats**: Export to CSV, JSON, or Excel (XLSX)
- **Export History**: Track all exports with detailed logs
- **Data Viewing**: Browse all synced data directly in the web interface

### General
- **Web-Based Configuration**: Manage all settings through a user-friendly web interface
- **Comprehensive Logging**: Detailed logging for troubleshooting and monitoring
- **Secure Storage**: All data stored securely in local database

## Setup Instructions

### Prerequisites

- Python 3.8 or higher (or Docker)
- Atera API key
- Twilio account (Account SID, Auth Token, and phone number) - optional for SMS notifications

### Deployment Options

You can deploy this application in two ways:
1. **Docker (Recommended)** - Containerized deployment
2. **Traditional Python** - Direct Python installation

---

## Docker Deployment (Recommended)

### Quick Start with Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/salientmsp/AteraExporter.git
   cd AteraExporter
   ```

2. Create a `.env` file:
   ```bash
   cp example.env .env
   ```

3. Edit `.env` and set your secret key:
   ```
   SECRET_KEY=your-secure-random-key-here
   ```

4. Start the application:
   ```bash
   docker-compose up -d
   ```

5. Access the application at `http://localhost:8000`

### Using Pre-built Image from GitHub Container Registry

Pull and run the latest image:

```bash
# Create data directory with proper permissions
mkdir -p data
chmod 777 data  # Or: sudo chown 1000:1000 data

# Pull and run
docker pull ghcr.io/salientmsp/ateraexporter:latest

docker run -d \
  --name atera-exporter \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret-key \
  ghcr.io/salientmsp/ateraexporter:latest
```

**Important:** The container runs as a non-root user (UID 1000) for security. Ensure the `data` directory is writable by this user.

### Building Your Own Docker Image

```bash
docker build -t atera-exporter .

# Create data directory
mkdir -p data
chmod 777 data

# Run the container
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data atera-exporter
```

### Docker Volumes

The application uses the following volume:
- `/app/data` - Database storage (persist your data)

**Note:** Exports are generated in-memory and downloaded directly to your browser, so no volume mount is needed for exports.

### Docker Environment Variables

- `SECRET_KEY` - Flask secret key (required)
- All Atera/Twilio API keys can be configured via the web UI

### Docker Management Commands

**View logs:**
```bash
docker-compose logs -f
```

**Stop the application:**
```bash
docker-compose down
```

**Restart the application:**
```bash
docker-compose restart
```

**Update to latest version:**
```bash
docker-compose pull
docker-compose up -d
```

**Backup your data:**
```bash
# Backup database
cp data/oncall.db data/oncall.db.backup
```

---

## Traditional Python Installation

### Prerequisites

- Python 3.8 or higher
- Atera API key
- Twilio account (Account SID, Auth Token, and phone number)

### Installation

1. Clone the repository or download the source code

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file from the example:
   ```
   copy example.env .env
   ```

6. Edit the `.env` file to set your Flask secret key:
   ```
   SECRET_KEY=your-secret-key-change-this-in-production
   ```

### Running the Application

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:5000/setup
   ```

3. On first run, you'll be prompted to create an admin account

## Configuration

### API Integration

#### Web-Based API Key Management

All API keys are managed through the Settings page in the web interface:

- **Atera API Key**: Required to fetch tickets from the Atera ticketing system
- **Twilio Account SID**: Required for Twilio SMS integration
- **Twilio Auth Token**: Required for Twilio authentication
- **Twilio Phone Number**: The phone number used to send SMS notifications

This approach offers several advantages:
- No need to restart the application after changing API keys
- Secure storage in the database rather than in files
- Easy management through a user-friendly interface

#### Error Handling and Logging

The application includes comprehensive error handling and logging for API integrations:

- **Atera API**: Detailed logging of API requests, responses, and errors with specific handling for timeouts, connection issues, and authentication problems.
- **Twilio API**: Specific error handling for common Twilio error codes (invalid phone numbers, authentication issues, etc.) with clear error messages.
- **Database Operations**: Transaction logging with proper error handling and rollback mechanisms.

All logs include appropriate severity levels (info, debug, warning, error, critical) to make troubleshooting easier.

Note: For backward compatibility only, API keys can still be provided in the `.env` file, but this is not recommended and is only used as a fallback if keys are not found in the database.

## Production Deployment

### Deploying with Waitress (Windows)

For production deployment on Windows, we recommend using Waitress as the WSGI server. Follow these steps:

1. **Install Waitress**:

   ```bash
   pip install waitress
   ```

2. **Run the application using the provided script**:

   ```bash
   # Option 1: Using the Python script
   python run_production.py
   
   # Option 2: Using the batch file
   start_server.bat
   ```

3. **Access the application**:

   The application will be available at `http://server-ip:8000`

### Production Configuration

1. **Set a strong secret key**:

   Generate a secure random key and set it in your `.env` file:
   ```
   SECRET_KEY=your-secure-random-key
   ```

2. **Configure the database**:

   By default, the application uses SQLite. For production, consider:
   - Using a more robust database like PostgreSQL or MySQL
   - Setting up regular database backups

3. **Set up as a Windows Service (optional)**:

   For automatic startup and recovery, consider using NSSM (Non-Sucking Service Manager) to run the application as a Windows service:

   ```bash
   # Install NSSM
   # Download from http://nssm.cc/
   
   # Install the service
   nssm install OnCallMonitor "C:\Path\To\Python\python.exe" "C:\Path\To\App\run_production.py"
   
   # Configure service details
   nssm set OnCallMonitor Description "On-Call Ticket Monitor Service"
   nssm set OnCallMonitor AppDirectory "C:\Path\To\App"
   
   # Start the service
   nssm start OnCallMonitor
   ```

4. **Network Configuration**:

   - Configure your firewall to allow traffic on port 8000
   - For public access, consider setting up a reverse proxy with Nginx or IIS

### Business Hours and Holidays

#### Business Hours
Configure business hours for each day of the week through the web interface. Tickets that come in outside of these hours will trigger SMS notifications to the on-call technicians.

#### Holiday Calendar
Manage holidays through the dedicated Holiday Calendar page. The system will:
- Treat holidays as outside business hours for notification purposes
- Send notifications to all on-call technicians on holidays regardless of time
- Include holiday information in SMS notifications

### On-Call Schedule

Create schedules for technicians to be on-call. The application supports:

- **Multiple On-Call Technicians**: Configure overlapping schedules with multiple technicians on-call simultaneously
- **Flexible Scheduling**: Set specific date ranges for each technician's on-call period
- **Redundant Notifications**: All on-call technicians receive notifications for after-hours or holiday tickets

The application automatically determines who is currently on-call based on these schedules and displays the current on-call technicians on the dashboard.

## Background Jobs

The application uses APScheduler to run background jobs:

- **Ticket Fetching**: Runs at configurable intervals (default: 5 minutes) to check for new tickets
- **Notification Sending**: Automatically sends SMS to on-call technicians for after-hours or holiday tickets
- **Performance Monitoring**: Tracks job execution time and provides detailed logs

## Using the Export Features

### Accessing the Export Dashboard

1. Navigate to the "Export" menu item in the navigation bar
2. You'll see a dashboard showing all available data types and their record counts

### Syncing Data from Atera

To sync data from your Atera account:

1. Ensure your Atera API key is configured in Settings
2. On the Export dashboard, click "Sync from Atera" for any data type
3. The application will fetch all data from Atera and store it locally
4. You'll see a success message showing how many records were synced

### Viewing Data

To view synced data in the browser:

1. Click "View Data" on any data type card
2. You'll see a table showing up to 100 most recent records
3. This is useful for quick inspection before exporting

### Exporting Data

To export data to a file:

1. Choose the data type you want to export
2. Click on one of the export format buttons (CSV, JSON, or Excel)
3. The file will be generated in-memory and downloaded directly to your browser
4. All exports are logged in the "Recent Exports" section for tracking

### Export Formats

- **CSV**: Comma-separated values, ideal for importing into other applications or Excel
- **JSON**: JavaScript Object Notation, ideal for programmatic use or API integrations
- **Excel (XLSX)**: Microsoft Excel format with formatted headers and auto-sized columns

### Export File Naming

Downloaded files follow this naming convention:

```
{data_type}_{timestamp}.{format}
```

Example: `customers_20260107_143052.csv`

**Note:** Files are generated on-demand and served directly to your browser without being stored on the server, eliminating the need for disk space management and permission issues.

### Best Practices

1. **Regular Syncing**: Sync your data regularly to ensure exports contain the latest information
2. **Check Before Export**: Use the "View Data" feature to verify data before exporting
3. **Monitor Export History**: Check the "Recent Exports" section to track your export activity
4. **Save Important Exports**: Since exports are downloaded directly, remember to save important exports to your preferred location

## Security Considerations

- **Authentication**: This application uses basic authentication. For production use, consider implementing more robust authentication.
- **API Keys**: API keys and credentials are stored securely in the database. For backward compatibility, they can also be provided in the `.env` file.
- **Error Handling**: Comprehensive error handling prevents exposing sensitive information in error messages.
- **Logging**: Detailed logging helps identify security issues, but ensure log files are properly secured and rotated.
- **Production Deployment**: For production, set `debug=False` in the Flask application and use a proper WSGI server like Waitress (Windows) or Gunicorn (Linux).
- **Service Account**: When running as a Windows service, consider using a dedicated service account with limited permissions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
