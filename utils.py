import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import sqlite3

def parse_date(date_str):
    """
    Parse date string in format DD.MM.YYYY and return datetime object

    Args:
        date_str (str): Date in format DD.MM.YYYY

    Returns:
        datetime.datetime: Parsed datetime object or None if invalid
    """
    if not date_str or date_str == '-':
        return None

    try:
        return datetime.datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None

def days_until(date_str):
    """
    Calculate days until given date

    Args:
        date_str (str): Date in format DD.MM.YYYY

    Returns:
        int: Days until date or None if date is invalid
    """
    date_obj = parse_date(date_str)
    if not date_obj:
        return None

    days = (date_obj - datetime.datetime.now()).days
    return days

def format_days_remaining(days):
    """
    Format days remaining with colors and warning symbols

    Args:
        days (int): Number of days

    Returns:
        str: Formatted string with emoji and days count
    """
    if days is None:
        return "❓ Не задано"

    if days < 0:
        return f"🚫 Просрочено ({-days} дн.)"
    elif days <= 7:
        return f"⚠️ Критически ({days} дн.)"
    elif days <= 30:
        return f"⚠️ Скоро ({days} дн.)"
    else:
        return f"✅ {days} дн."

def get_to_interval_based_on_mileage(last_to_mileage, current_mileage, interval=10000):
    """
    Calculate remaining kilometers until next TO based on interval

    Args:
        last_to_mileage (int): Mileage at last TO
        current_mileage (int): Current mileage
        interval (int): TO interval in kilometers (default 10000)

    Returns:
        int: Kilometers until next TO
    """
    if not last_to_mileage:
        return None

    next_to_mileage = last_to_mileage + interval
    remaining = next_to_mileage - current_mileage

    return remaining, next_to_mileage

def edit_fuel_info(vehicle_id, fuel_type=None, fuel_tank_capacity=None, avg_fuel_consumption=None):
    """
    Edit fuel information for a vehicle

    Args:
        vehicle_id (int): Vehicle ID
        fuel_type (str, optional): Fuel type
        fuel_tank_capacity (float, optional): Fuel tank capacity in liters
        avg_fuel_consumption (float, optional): Average fuel consumption in l/100km

    Returns:
        bool: True if updated successfully
    """
    conn = sqlite3.connect('vehicles.db')
    cursor = conn.cursor()

    # Create SET clause parts based on provided values
    updates = []
    params = []

    if fuel_type is not None:
        updates.append("fuel_type = ?")
        params.append(fuel_type)

    if fuel_tank_capacity is not None:
        updates.append("fuel_tank_capacity = ?")
        params.append(fuel_tank_capacity)

    if avg_fuel_consumption is not None:
        updates.append("avg_fuel_consumption = ?")
        params.append(avg_fuel_consumption)

    if not updates:  # No fields to update
        conn.close()
        return False

    # Add vehicle_id to params
    params.append(vehicle_id)

    # Execute the update
    try:
        cursor.execute(
            f"UPDATE vehicles SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error updating fuel info: {e}")
        return False

def generate_expiration_report():
    """
    Generate PDF report with all vehicles and their document expiration dates

    Returns:
        str: Path to the generated PDF file
    """
    import logging  # Добавим логирование для диагностики

    # Get today's date
    today = datetime.datetime.now()
    filename = f"report_{today.strftime('%Y%m%d')}.pdf"

    # Connect to the database
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all vehicles with their expiration dates
    cursor.execute("""
        SELECT id, model, reg_number, osago_valid, tech_inspection_valid,
               skzi_valid_date, mileage, tachograph_required, next_to
        FROM vehicles
        ORDER BY model
    """)
    vehicles = cursor.fetchall()

    # Register appropriate fonts with Cyrillic support
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Локальные пути к шрифтам (нужно положить файлы в директорию проекта)
    font_regular = 'DejaVuSans.ttf'
    font_bold = 'DejaVuSans-Bold.ttf'

    # Попробуем зарегистрировать шрифты
    cyrillic_font = 'Helvetica'  # Запасной шрифт по умолчанию
    cyrillic_font_bold = 'Helvetica-Bold'

    try:
        if os.path.exists(font_regular) and os.path.exists(font_bold):
            pdfmetrics.registerFont(TTFont('CustomFont', font_regular))
            pdfmetrics.registerFont(TTFont('CustomFontBold', font_bold))
            cyrillic_font = 'CustomFont'
            cyrillic_font_bold = 'CustomFontBold'
            logging.info("Используются локальные шрифты DejaVuSans")
        else:
            # Попробуем системные пути
            system_font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            system_font_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            if os.path.exists(system_font) and os.path.exists(system_font_bold):
                pdfmetrics.registerFont(TTFont('CustomFont', system_font))
                pdfmetrics.registerFont(TTFont('CustomFontBold', system_font_bold))
                cyrillic_font = 'CustomFont'
                cyrillic_font_bold = 'CustomFontBold'
                logging.info("Используются системные шрифты DejaVuSans")
            else:
                logging.warning("Шрифты DejaVuSans не найдены, используется Helvetica (без полной поддержки кириллицы)")
    except Exception as e:
        logging.error(f"Ошибка при регистрации шрифтов: {e}")
        logging.info("Падение на встроенные шрифты Helvetica")

    # Create the PDF document
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()

    # Create custom styles for Cyrillic text
    cyrillic_normal = ParagraphStyle(
        'CyrillicNormal',
        parent=styles['Normal'],
        fontName=cyrillic_font,
        fontSize=10,
        leading=14,
        encoding='utf-8',
        alignment=1
    )

    cyrillic_title = ParagraphStyle(
        'CyrillicTitle',
        parent=styles['Heading1'],
        fontName=cyrillic_font_bold,
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=20,
        encoding='utf-8'
    )

    # Add title and date
    elements = []
    title_text = "Отчет об истечении сроков документов"
    date_text = f"Дата создания: {today.strftime('%d.%m.%Y')}"

    elements.append(Paragraph(title_text, cyrillic_title))
    elements.append(Paragraph(date_text, cyrillic_normal))
    elements.append(Spacer(1, 20))

    # Create data for the table
    headers = ["Транспортное средство", "ОСАГО", "Техосмотр", "СКЗИ", "ТО"]
    data = [headers]

    for vehicle in vehicles:
        osago_days = days_until(vehicle['osago_valid'])
        tech_days = days_until(vehicle['tech_inspection_valid'])
        skzi_days = days_until(vehicle['skzi_valid_date']) if vehicle['tachograph_required'] else None

        if vehicle['next_to']:
            remaining_to = vehicle['next_to'] - vehicle['mileage']
            if remaining_to <= 0:
                to_status = f"Просрочено ({-remaining_to} км)"
            elif remaining_to <= 500:
                to_status = f"Критически ({remaining_to} км)"
            elif remaining_to <= 1000:
                to_status = f"Скоро ({remaining_to} км)"
            else:
                to_status = f"{remaining_to} км"
        else:
            to_status = "Не задано"

        vehicle_text = f"{vehicle['model']} ({vehicle['reg_number']})"

        if osago_days is not None and osago_days < 0:
            osago_text = f"-{-osago_days} дн."
        else:
            osago_text = format_days_remaining(osago_days).replace("⚠️", "!").replace("✅", "+").replace("🚫", "X").replace("❓", "?").replace("Просрочено", "-").replace("Критически", "!")

        if tech_days is not None and tech_days < 0:
            tech_text = f"-{-tech_days} дн."
        else:
            tech_text = format_days_remaining(tech_days).replace("⚠️", "!").replace("✅", "+").replace("🚫", "X").replace("❓", "?").replace("Просрочено", "-").replace("Критически", "!")

        if vehicle['tachograph_required']:
            if skzi_days is not None and skzi_days < 0:
                skzi_text = f"-{-skzi_days} дн."
            else:
                skzi_text = format_days_remaining(skzi_days).replace("⚠️", "!").replace("✅", "+").replace("🚫", "X").replace("❓", "?").replace("Просрочено", "-").replace("Критически", "!")
        else:
            skzi_text = "Не требуется"

        if vehicle['next_to']:
            remaining_to = vehicle['next_to'] - vehicle['mileage']
            if remaining_to <= 0:
                to_status = f"-{-remaining_to} км"
            elif remaining_to <= 500:
                to_status = f"!{remaining_to} км"
            elif remaining_to <= 1000:
                to_status = f"!{remaining_to} км"
            else:
                to_status = f"{remaining_to} км"
        else:
            to_status = "Не задано"

        row = [vehicle_text, osago_text, tech_text, skzi_text, to_status]
        data.append(row)

    # Create table
    table = Table(data, colWidths=[170, 90, 90, 90, 90])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), cyrillic_font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), cyrillic_font),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ])

    for i in range(1, len(data)):
        for j in range(1, 5):
            cell_data = str(data[i][j]).lower()
            if cell_data.startswith("-") or "критически" in cell_data or "просрочено" in cell_data or "!" in cell_data:
                table_style.add('BACKGROUND', (j, i), (j, i), colors.mistyrose)
                table_style.add('TEXTCOLOR', (j, i), (j, i), colors.darkred)
            elif "скоро" in cell_data:
                table_style.add('BACKGROUND', (j, i), (j, i), colors.lemonchiffon)
                table_style.add('TEXTCOLOR', (j, i), (j, i), colors.saddlebrown)

    table.setStyle(table_style)
    elements.append(table)

    # Build the PDF
    try:
        doc.build(elements)
        logging.info(f"PDF отчет успешно создан: {filename}")
    except Exception as e:
        logging.error(f"Ошибка при сборке PDF: {e}")
        raise

    conn.close()
    return filename
