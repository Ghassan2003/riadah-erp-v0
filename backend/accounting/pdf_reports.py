"""
توليد تقارير PDF للمحاسبة - نظام ERP.
يستخدم مكتبة ReportLab لتوليد تقارير قائمة الدخل والميزانية العمومية بصيغة PDF.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from io import BytesIO

# Try to register Arabic font
FONT_PATH = '/usr/share/fonts/truetype/chinese/SimHei.ttf'
try:
    pdfmetrics.registerFont(TTFont('ArabicFont', '/usr/share/fonts/truetype/chinese/SimHei.ttf'))
    ARABIC_FONT = 'ArabicFont'
except:
    ARABIC_FONT = 'Helvetica'


def generate_income_statement_pdf(income_data, period_from=None, period_to=None):
    """توليد تقرير قائمة الدخل بصيغة PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'ArabicTitle', parent=styles['Title'],
        fontName=ARABIC_FONT, fontSize=18, spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        'ArabicHeading', parent=styles['Heading2'],
        fontName=ARABIC_FONT, fontSize=14, spaceAfter=10,
    )
    normal_style = ParagraphStyle(
        'ArabicNormal', parent=styles['Normal'],
        fontName=ARABIC_FONT, fontSize=10,
    )

    elements = []
    elements.append(Paragraph('قائمة الدخل', title_style))
    elements.append(Spacer(1, 10))

    if period_from and period_to:
        elements.append(Paragraph(f'الفترة: {period_from} إلى {period_to}', normal_style))
    elements.append(Spacer(1, 20))

    # Revenue section
    elements.append(Paragraph('الإيرادات', heading_style))
    revenue_data = [['البند', 'المبلغ']]
    for item in income_data.get('revenue_items', []):
        revenue_data.append([item['name'], str(item['amount'])])
    revenue_data.append(['إجمالي الإيرادات', str(income_data.get('total_revenue', 0))])

    revenue_table = Table(revenue_data, colWidths=[300, 150])
    revenue_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.6, 0.86)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), ARABIC_FONT),
        ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.9, 0.95, 1.0)),
    ]))
    elements.append(revenue_table)
    elements.append(Spacer(1, 20))

    # Expense section
    elements.append(Paragraph('المصروفات', heading_style))
    expense_data = [['البند', 'المبلغ']]
    for item in income_data.get('expense_items', []):
        expense_data.append([item['name'], str(item['amount'])])
    expense_data.append(['إجمالي المصروفات', str(income_data.get('total_expenses', 0))])

    expense_table = Table(expense_data, colWidths=[300, 150])
    expense_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.85, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.Color(1.0, 0.9, 0.9)),
    ]))
    elements.append(expense_table)
    elements.append(Spacer(1, 20))

    # Net income
    net = income_data.get('net_income', 0)
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue))
    elements.append(Spacer(1, 10))
    net_data = [['صافي الربح/الخسارة', str(net)]]
    net_table = Table(net_data, colWidths=[300, 150])
    net_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.9, 0.95, 0.9)),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.darkblue),
    ]))
    elements.append(net_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_balance_sheet_pdf(balance_data):
    """توليد تقرير الميزانية العمومية بصيغة PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ArabicTitle', parent=styles['Title'],
        fontName=ARABIC_FONT, fontSize=18, spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        'ArabicHeading', parent=styles['Heading2'],
        fontName=ARABIC_FONT, fontSize=14, spaceAfter=10,
    )
    normal_style = ParagraphStyle(
        'ArabicNormal', parent=styles['Normal'],
        fontName=ARABIC_FONT, fontSize=10,
    )

    elements = []
    elements.append(Paragraph('الميزانية العمومية', title_style))
    elements.append(Spacer(1, 20))

    # Assets
    elements.append(Paragraph('الأصول', heading_style))
    assets_data = [['البند', 'المبلغ']]
    for item in balance_data.get('assets', []):
        assets_data.append([item['name'], str(item['amount'])])
    assets_data.append(['إجمالي الأصول', str(balance_data.get('total_assets', 0))])

    assets_table = Table(assets_data, colWidths=[300, 150])
    assets_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.6, 0.86)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.9, 0.95, 1.0)),
    ]))
    elements.append(assets_table)
    elements.append(Spacer(1, 20))

    # Liabilities & Equity
    elements.append(Paragraph('الخصوم وحقوق الملكية', heading_style))
    le_data = [['البند', 'المبلغ']]
    for item in balance_data.get('liabilities', []):
        le_data.append([item['name'], str(item['amount'])])
    for item in balance_data.get('equity', []):
        le_data.append([item['name'], str(item['amount'])])
    le_data.append(['إجمالي الخصوم وحقوق الملكية', str(balance_data.get('total_liabilities_equity', 0))])

    le_table = Table(le_data, colWidths=[300, 150])
    le_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.6, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.9, 0.95, 0.9)),
    ]))
    elements.append(le_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
