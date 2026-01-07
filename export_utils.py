"""
Export Utilities Module
Handles exporting data to various formats (CSV, JSON, Excel)
All exports are generated in-memory and returned as BytesIO objects
"""

import csv
import json
from io import BytesIO, StringIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def generate_filename(data_type, export_format):
    """
    Generate a filename for the export (for download headers)

    Args:
        data_type: Type of data being exported (e.g., 'customers', 'tickets')
        export_format: Format of export ('csv', 'json', 'excel')

    Returns:
        Filename string (no path)
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{data_type}_{timestamp}.{export_format}"

    if export_format == 'excel':
        filename = f"{data_type}_{timestamp}.xlsx"

    return filename


def export_to_csv(data, fieldnames=None):
    """
    Export data to CSV format in-memory

    Args:
        data: List of dictionaries to export
        fieldnames: Optional list of field names (columns)

    Returns:
        BytesIO object containing CSV data, or None on failure
    """
    try:
        if not data:
            logger.warning("No data to export to CSV")
            return None

        # If fieldnames not provided, use keys from first item
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        # Create StringIO for CSV writing
        string_buffer = StringIO()
        writer = csv.DictWriter(string_buffer, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

        # Convert to BytesIO for Flask send_file
        bytes_buffer = BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode('utf-8'))
        bytes_buffer.seek(0)

        logger.info(f"Successfully generated CSV with {len(data)} records")
        return bytes_buffer

    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return None


def export_to_json(data, indent=2):
    """
    Export data to JSON format in-memory

    Args:
        data: Data to export (list or dict)
        indent: JSON indentation level

    Returns:
        BytesIO object containing JSON data, or None on failure
    """
    try:
        if not data:
            logger.warning("No data to export to JSON")
            return None

        # Generate JSON string
        json_string = json.dumps(data, indent=indent, default=str)

        # Convert to BytesIO for Flask send_file
        bytes_buffer = BytesIO()
        bytes_buffer.write(json_string.encode('utf-8'))
        bytes_buffer.seek(0)

        logger.info(f"Successfully generated JSON export")
        return bytes_buffer

    except Exception as e:
        logger.error(f"Error exporting to JSON: {str(e)}")
        return None


def export_to_excel(data, sheet_name='Data'):
    """
    Export data to Excel format in-memory

    Args:
        data: List of dictionaries to export
        sheet_name: Name of the Excel sheet

    Returns:
        BytesIO object containing Excel data, or None on failure
    """
    try:
        # Import openpyxl for Excel support
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            logger.error("openpyxl not installed. Install with: pip install openpyxl")
            return None

        if not data:
            logger.warning("No data to export to Excel")
            return None

        # Create workbook and sheet
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name

        # Get fieldnames from first item
        fieldnames = list(data[0].keys())

        # Write header row with formatting
        for col_num, fieldname in enumerate(fieldnames, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = fieldname
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')

        # Write data rows
        for row_num, item in enumerate(data, 2):
            for col_num, fieldname in enumerate(fieldnames, 1):
                value = item.get(fieldname)
                # Convert datetime objects to strings
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                ws.cell(row=row_num, column=col_num, value=value)

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save workbook to BytesIO
        bytes_buffer = BytesIO()
        wb.save(bytes_buffer)
        bytes_buffer.seek(0)

        logger.info(f"Successfully generated Excel with {len(data)} records")
        return bytes_buffer

    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return None


def model_to_dict(model_instance, exclude_fields=None):
    """
    Convert SQLAlchemy model instance to dictionary

    Args:
        model_instance: SQLAlchemy model instance
        exclude_fields: List of field names to exclude

    Returns:
        Dictionary representation of model
    """
    if exclude_fields is None:
        exclude_fields = []

    data = {}
    for column in model_instance.__table__.columns:
        if column.name not in exclude_fields:
            value = getattr(model_instance, column.name)
            # Convert datetime to string
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            data[column.name] = value

    return data


def models_to_list(model_instances, exclude_fields=None):
    """
    Convert list of SQLAlchemy model instances to list of dictionaries

    Args:
        model_instances: List of SQLAlchemy model instances
        exclude_fields: List of field names to exclude

    Returns:
        List of dictionaries
    """
    return [model_to_dict(instance, exclude_fields) for instance in model_instances]


def export_models(model_instances, data_type, export_format, exclude_fields=None):
    """
    Export SQLAlchemy models to specified format in-memory

    Args:
        model_instances: List of SQLAlchemy model instances
        data_type: Type of data (for filename)
        export_format: Format to export to ('csv', 'json', 'excel')
        exclude_fields: Fields to exclude from export

    Returns:
        Tuple of (bytes_buffer, filename, record_count, error_message)
        bytes_buffer will be None if export fails
    """
    try:
        if not model_instances:
            return None, None, 0, "No data to export"

        # Convert models to dictionaries
        data = models_to_list(model_instances, exclude_fields)

        # Generate filename
        filename = generate_filename(data_type, export_format)

        # Export based on format
        if export_format == 'csv':
            bytes_buffer = export_to_csv(data)
        elif export_format == 'json':
            bytes_buffer = export_to_json(data)
        elif export_format == 'excel':
            bytes_buffer = export_to_excel(data)
        else:
            return None, None, 0, f"Unsupported export format: {export_format}"

        if bytes_buffer:
            return bytes_buffer, filename, len(data), None
        else:
            return None, None, 0, "Export failed"

    except Exception as e:
        logger.error(f"Error in export_models: {str(e)}")
        return None, None, 0, str(e)
