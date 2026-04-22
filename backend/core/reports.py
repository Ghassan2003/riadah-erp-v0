"""
Advanced PDF Report Engine for ERP System.
Generates professional reports for all modules with filters, headers, footers, and summaries.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

# Register font
FONT_PATH = '/usr/share/fonts/truetype/chinese/SimHei.ttf'
try:
    pdfmetrics.registerFont(TTFont('ArabicFont', FONT_PATH))
    FONT = 'ArabicFont'
except:
    FONT = 'Helvetica'

# Colors
PRIMARY = colors.Color(0.18, 0.47, 0.76)
SECONDARY = colors.Color(0.1, 0.55, 0.35)
ACCENT = colors.Color(0.85, 0.22, 0.22)
LIGHT_BLUE = colors.Color(0.93, 0.96, 1.0)
LIGHT_GREEN = colors.Color(0.9, 0.96, 0.9)
LIGHT_RED = colors.Color(1.0, 0.92, 0.92)
GRAY_BG = colors.Color(0.97, 0.97, 0.97)
DARK = colors.Color(0.15, 0.15, 0.2)

# Styles
STYLES = {
    'title': ParagraphStyle('Title', fontName=FONT, fontSize=20, textColor=DARK, spaceAfter=5, alignment=1),
    'subtitle': ParagraphStyle('Subtitle', fontName=FONT, fontSize=12, textColor=colors.gray, spaceAfter=15),
    'section': ParagraphStyle('Section', fontName=FONT, fontSize=14, textColor=PRIMARY, spaceAfter=8, spaceBefore=12),
    'normal': ParagraphStyle('Normal', fontName=FONT, fontSize=10, textColor=DARK),
    'small': ParagraphStyle('Small', fontName=FONT, fontSize=8, textColor=colors.gray),
    'bold': ParagraphStyle('Bold', fontName=FONT, fontSize=10, textColor=DARK),
    'total': ParagraphStyle('Total', fontName=FONT, fontSize=11, textColor=PRIMARY),
    'footer': ParagraphStyle('Footer', fontName=FONT, fontSize=7, textColor=colors.gray, alignment=1),
}

def format_number(val):
    """Format number with commas for Arabic."""
    if val is None: return '0.00'
    try:
        return f'{float(val):,.2f}'
    except:
        return str(val)

def format_date(val):
    """Format date string."""
    if not val: return ''
    return str(val)

def build_table(data, col_widths, header_color=PRIMARY):
    """Build a styled table."""
    if not data:
        return Paragraph('لا توجد بيانات', STYLES['normal'])
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]
    table.setStyle(TableStyle(style_cmds))
    return table

def add_page_header_footer(canvas, doc, title):
    """Add header and footer to each page."""
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(2*cm, A4[1] - 1.8*cm, A4[0] - 2*cm, A4[1] - 1.8*cm)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(colors.gray)
    canvas.drawString(2*cm, A4[1] - 1.5*cm, 'نظام ERP - نظام تخطيط موارد المؤسسة')
    canvas.drawRightString(A4[0] - 2*cm, A4[1] - 1.5*cm, title)
    
    # Footer
    canvas.setStrokeColor(colors.Color(0.85, 0.85, 0.85))
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)
    canvas.setFont(FONT, 7)
    canvas.drawString(2*cm, 0.8*cm, f'تاريخ الطباعة: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    canvas.drawRightString(A4[0] - 2*cm, 0.8*cm, f'صفحة {doc.page}')
    canvas.restoreState()


# ====== MODULE REPORTS ======

def generate_inventory_report(products, filters=None):
    """Generate inventory products report PDF."""
    buffer = BytesIO()
    title = 'تقرير إدارة المخزون'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    elements.append(Paragraph('تقرير شامل لجميع المنتجات في النظام', STYLES['subtitle']))
    
    filter_text = ''
    if filters:
        parts = []
        if filters.get('search'): parts.append(f'بحث: {filters["search"]}')
        if filters.get('category'): parts.append(f'التصنيف: {filters["category"]}')
        if filters.get('date_from'): parts.append(f'من: {filters["date_from"]}')
        if filters.get('date_to'): parts.append(f'إلى: {filters["date_to"]}')
        if parts:
            filter_text = ' | '.join(parts)
    if filter_text:
        elements.append(Paragraph(f'الفلاتر: {filter_text}', STYLES['small']))
        elements.append(Spacer(1, 10))
    
    # Summary cards as table
    total_products = len(products)
    total_value = sum(float(p.get('total_value', 0) or 0) for p in products)
    low_stock = sum(1 for p in products if int(p.get('stock_quantity', 0) or 0) < 10)
    out_of_stock = sum(1 for p in products if int(p.get('stock_quantity', 0) or 0) == 0)
    
    summary_data = [
        [Paragraph('<b>إجمالي المنتجات</b>', STYLES['small']),
         Paragraph('<b>قيمة المخزون</b>', STYLES['small']),
         Paragraph('<b>مخزون منخفض</b>', STYLES['small']),
         Paragraph('<b>نفذ المخزون</b>', STYLES['small'])],
        [str(total_products), format_number(total_value), str(low_stock), str(out_of_stock)]
    ]
    elements.append(build_table(summary_data, [120, 120, 120, 120]))
    elements.append(Spacer(1, 20))
    
    # Products table
    elements.append(Paragraph('تفاصيل المنتجات', STYLES['section']))
    table_data = [['الكود', 'المنتج', 'التصنيف', 'السعر', 'الكمية', 'القيمة الإجمالية']]
    for p in products:
        price = float(p.get('selling_price', 0) or 0)
        qty = int(p.get('stock_quantity', 0) or 0)
        table_data.append([
            p.get('sku', ''),
            p.get('name', ''),
            p.get('category_name', ''),
            format_number(price),
            str(qty),
            format_number(price * qty),
        ])
    
    if total_products > 0:
        table_data.append(['', 'الإجمالي', '', '', str(total_products), format_number(total_value)])
    
    elements.append(build_table(table_data, [55, 120, 80, 65, 55, 90]))
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer


def generate_sales_report(orders, filters=None):
    """Generate sales orders report PDF."""
    buffer = BytesIO()
    title = 'تقرير المبيعات'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    elements.append(Paragraph('تقرير شامل لأوامر البيع', STYLES['subtitle']))
    
    total_orders = len(orders)
    total_amount = sum(float(o.get('total_amount', 0) or 0) for o in orders)
    confirmed = sum(1 for o in orders if o.get('status') == 'confirmed')
    pending = sum(1 for o in orders if o.get('status') == 'pending')
    cancelled = sum(1 for o in orders if o.get('status') == 'cancelled')
    
    summary = [
        [Paragraph('<b>إجمالي الأوامر</b>', STYLES['small']),
         Paragraph('<b>إجمالي المبالغ</b>', STYLES['small']),
         Paragraph('<b>مؤكدة</b>', STYLES['small']),
         Paragraph('<b>معلقة</b>', STYLES['small']),
         Paragraph('<b>ملغاة</b>', STYLES['small'])],
        [str(total_orders), format_number(total_amount), str(confirmed), str(pending), str(cancelled)]
    ]
    elements.append(build_table(summary, [95, 100, 80, 80, 80]))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph('تفاصيل الأوامر', STYLES['section']))
    table_data = [['رقم الأمر', 'العميل', 'التاريخ', 'الحالة', 'المبلغ']]
    
    STATUS_MAP = {'pending': 'معلق', 'confirmed': 'مؤكد', 'processing': 'قيد التنفيذ', 
                  'shipped': 'مُرسل', 'delivered': 'مُسلّم', 'cancelled': 'ملغى'}
    
    for o in orders:
        table_data.append([
            o.get('order_number', ''),
            o.get('customer_name', ''),
            format_date(o.get('order_date', '')),
            STATUS_MAP.get(o.get('status', ''), o.get('status', '')),
            format_number(o.get('total_amount', 0)),
        ])
    
    if total_orders > 0:
        table_data.append(['', 'الإجمالي', '', '', format_number(total_amount)])
    
    elements.append(build_table(table_data, [90, 120, 80, 70, 95]))
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer


def generate_purchases_report(orders, filters=None):
    """Generate purchase orders report PDF."""
    buffer = BytesIO()
    title = 'تقرير المشتريات'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    elements.append(Paragraph('تقرير شامل لأوامر الشراء', STYLES['subtitle']))
    
    total_orders = len(orders)
    total_amount = sum(float(o.get('total_amount', 0) or 0) for o in orders)
    
    summary = [
        [Paragraph('<b>إجمالي أوامر الشراء</b>', STYLES['small']),
         Paragraph('<b>إجمالي المبالغ</b>', STYLES['small'])],
        [str(total_orders), format_number(total_amount)]
    ]
    elements.append(build_table(summary, [200, 200]))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph('تفاصيل أوامر الشراء', STYLES['section']))
    table_data = [['رقم الأمر', 'المورّد', 'التاريخ', 'الحالة', 'المبلغ']]
    
    STATUS_MAP = {'pending': 'معلق', 'confirmed': 'مؤكد', 'received': 'مستلم', 'cancelled': 'ملغى'}
    
    for o in orders:
        table_data.append([
            o.get('order_number', ''),
            o.get('supplier_name', ''),
            format_date(o.get('order_date', '')),
            STATUS_MAP.get(o.get('status', ''), o.get('status', '')),
            format_number(o.get('total_amount', 0)),
        ])
    
    if total_orders > 0:
        table_data.append(['', 'الإجمالي', '', '', format_number(total_amount)])
    
    elements.append(build_table(table_data, [90, 120, 80, 70, 95]))
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer


def generate_employees_report(employees, filters=None):
    """Generate HR employees report PDF."""
    buffer = BytesIO()
    title = 'تقرير الموارد البشرية'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    elements.append(Paragraph('تقرير شامل للموظفين', STYLES['subtitle']))
    
    total = len(employees)
    active = sum(1 for e in employees if e.get('is_active', True))
    total_salary = sum(float(e.get('salary', 0) or 0) for e in employees)
    
    summary = [
        [Paragraph('<b>إجمالي الموظفين</b>', STYLES['small']),
         Paragraph('<b>الموظفون النشطون</b>', STYLES['small']),
         Paragraph('<b>إجمالي الرواتب</b>', STYLES['small'])],
        [str(total), str(active), format_number(total_salary)]
    ]
    elements.append(build_table(summary, [135, 135, 135]))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph('تفاصيل الموظفين', STYLES['section']))
    table_data = [['الرقم', 'الاسم', 'القسم', 'المسمى الوظيفي', 'الراتب', 'الحالة']]
    
    for e in employees:
        table_data.append([
            e.get('employee_number', ''),
            f"{e.get('first_name', '')} {e.get('last_name', '')}",
            e.get('department_name', ''),
            e.get('position', ''),
            format_number(e.get('salary', 0)),
            'نشط' if e.get('is_active', True) else 'غير نشط',
        ])
    
    elements.append(build_table(table_data, [50, 90, 80, 80, 70, 60]))
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer


def generate_projects_report(projects, filters=None):
    """Generate projects report PDF."""
    buffer = BytesIO()
    title = 'تقرير المشاريع'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    elements.append(Paragraph('تقرير شامل للمشاريع', STYLES['subtitle']))
    
    total = len(projects)
    total_budget = sum(float(p.get('budget', 0) or 0) for p in projects)
    total_spent = sum(float(p.get('spent', 0) or 0) for p in projects)
    active = sum(1 for p in projects if p.get('status') in ('active', 'in_progress'))
    
    summary = [
        [Paragraph('<b>إجمالي المشاريع</b>', STYLES['small']),
         Paragraph('<b>الميزانية</b>', STYLES['small']),
         Paragraph('<b>المصروفات</b>', STYLES['small']),
         Paragraph('<b>نشطة</b>', STYLES['small'])],
        [str(total), format_number(total_budget), format_number(total_spent), str(active)]
    ]
    elements.append(build_table(summary, [100, 100, 100, 100]))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph('تفاصيل المشاريع', STYLES['section']))
    table_data = [['المشروع', 'العميل', 'الحالة', 'الميزانية', 'المصروفات', 'المتبقي']]
    
    STATUS_MAP = {'planning': 'تخطيط', 'active': 'نشط', 'in_progress': 'قيد التنفيذ',
                  'on_hold': 'متوقف', 'completed': 'مكتمل', 'cancelled': 'ملغى'}
    
    for p in projects:
        budget = float(p.get('budget', 0) or 0)
        spent = float(p.get('spent', 0) or 0)
        table_data.append([
            p.get('name', ''),
            p.get('customer_name', ''),
            STATUS_MAP.get(p.get('status', ''), p.get('status', '')),
            format_number(budget),
            format_number(spent),
            format_number(budget - spent),
        ])
    
    elements.append(build_table(table_data, [100, 80, 60, 70, 70, 70]))
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer


def generate_cash_flow_statement(date_from=None, date_to=None):
    """Generate cash flow statement PDF."""
    buffer = BytesIO()
    title = 'قائمة التدفقات النقدية'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    from accounting.models import Account, JournalEntry, Transaction, AccountType
    from django.db.models import Sum, F, DecimalField, Value
    from django.db.models.functions import Coalesce
    from django.utils import timezone
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    
    period_text = 'لفترة التشغيل'
    if date_from and date_to:
        period_text = f'من {date_from} إلى {date_to}'
    elif date_from:
        period_text = f'من {date_from}'
    elif date_to:
        period_text = f'إلى {date_to}'
    elements.append(Paragraph(period_text, STYLES['subtitle']))
    
    # Get posted entries in date range
    entries = JournalEntry.objects.filter(is_posted=True)
    if date_from:
        entries = entries.filter(entry_date__gte=date_from)
    if date_to:
        entries = entries.filter(entry_date__lte=date_to)
    
    # Operating Activities
    operating_in = 0
    operating_out = 0
    for account in Account.objects.filter(account_type=AccountType.INCOME, is_active=True):
        total = account.transactions.filter(journal_entry__in=entries, transaction_type='credit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        total -= account.transactions.filter(journal_entry__in=entries, transaction_type='debit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        if total > 0:
            operating_in += total
    
    for account in Account.objects.filter(account_type=AccountType.EXPENSE, is_active=True):
        total = account.transactions.filter(journal_entry__in=entries, transaction_type='debit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        total -= account.transactions.filter(journal_entry__in=entries, transaction_type='credit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        if total > 0:
            operating_out += total
    
    net_operating = operating_in - operating_out
    
    # Investing Activities (asset changes)
    investing = 0
    for account in Account.objects.filter(account_type=AccountType.ASSET, is_active=True):
        total = account.transactions.filter(journal_entry__in=entries, transaction_type='debit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        total -= account.transactions.filter(journal_entry__in=entries, transaction_type='credit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        investing += total
    
    # Financing Activities (liability + equity changes)
    financing = 0
    for account in Account.objects.filter(account_type__in=[AccountType.LIABILITY, AccountType.EQUITY], is_active=True):
        total = account.transactions.filter(journal_entry__in=entries, transaction_type='credit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        total -= account.transactions.filter(journal_entry__in=entries, transaction_type='debit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        financing += total
    
    net_cash = net_operating + investing + financing
    
    # Operating Activities Section
    elements.append(Paragraph('أولاً: التدفقات النقدية من الأنشطة التشغيلية', STYLES['section']))
    op_data = [
        ['البند', 'المبلغ'],
        ['التدفقات النقدية الداخلة', format_number(operating_in)],
        ['التدفقات النقدية الخارجة', f'({format_number(operating_out)})'],
        [Paragraph('<b>صافي التدفقات التشغيلية</b>', STYLES['total']), 
         Paragraph(f'<b>{format_number(net_operating)}</b>', STYLES['total'])]
    ]
    elements.append(build_table(op_data, [300, 150], PRIMARY))
    elements.append(Spacer(1, 15))
    
    # Investing Activities Section
    elements.append(Paragraph('ثانياً: التدفقات النقدية من الأنشطة الاستثمارية', STYLES['section']))
    inv_data = [
        ['البند', 'المبلغ'],
        ['صافي التدفقات الاستثمارية', format_number(investing)],
    ]
    color = SECONDARY if investing >= 0 else ACCENT
    elements.append(build_table(inv_data, [300, 150], color))
    elements.append(Spacer(1, 15))
    
    # Financing Activities Section
    elements.append(Paragraph('ثالثاً: التدفقات النقدية من الأنشطة التمويلية', STYLES['section']))
    fin_data = [
        ['البند', 'المبلغ'],
        ['صافي التدفقات التمويلية', format_number(financing)],
    ]
    color = SECONDARY if financing >= 0 else ACCENT
    elements.append(build_table(fin_data, [300, 150], color))
    elements.append(Spacer(1, 20))
    
    # Net Cash Flow
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    elements.append(Spacer(1, 10))
    net_data = [
        [Paragraph('<b>صافي التغير في النقدية</b>', STYLES['total']), 
         Paragraph(f'<b>{format_number(net_cash)}</b>', STYLES['total'])]
    ]
    net_table = Table(net_data, colWidths=[300, 150])
    net_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('GRID', (0, 0), (-1, -1), 1.5, PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(net_table)
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer


def generate_enhanced_income_statement(date_from=None, date_to=None):
    """Generate enhanced income statement PDF with comparison."""
    buffer = BytesIO()
    title = 'قائمة الدخل التفصيلية'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    from accounting.models import Account, AccountType, JournalEntry, Transaction
    from django.db.models import Sum, DecimalField, Value
    from django.db.models.functions import Coalesce
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    period_text = ''
    if date_from and date_to:
        period_text = f'الفترة: من {date_from} إلى {date_to}'
    elements.append(Paragraph(period_text, STYLES['subtitle']))
    elements.append(Spacer(1, 15))
    
    entries = JournalEntry.objects.filter(is_posted=True)
    if date_from: entries = entries.filter(entry_date__gte=date_from)
    if date_to: entries = entries.filter(entry_date__lte=date_to)
    
    # Revenue
    elements.append(Paragraph('الإيرادات', STYLES['section']))
    rev_data = [['رمز الحساب', 'اسم الحساب', 'المبلغ']]
    total_rev = 0
    for acc in Account.objects.filter(account_type=AccountType.INCOME, is_active=True):
        cr = acc.transactions.filter(journal_entry__in=entries, transaction_type='credit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        dr = acc.transactions.filter(journal_entry__in=entries, transaction_type='debit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        bal = cr - dr
        if bal != 0:
            rev_data.append([acc.code, acc.name, format_number(bal)])
            total_rev += bal
    rev_data.append([Paragraph('<b>إجمالي الإيرادات</b>', STYLES['total']), '', 
                     Paragraph(f'<b>{format_number(total_rev)}</b>', STYLES['total'])])
    elements.append(build_table(rev_data, [80, 220, 120], SECONDARY))
    elements.append(Spacer(1, 15))
    
    # Expenses
    elements.append(Paragraph('المصروفات', STYLES['section']))
    exp_data = [['رمز الحساب', 'اسم الحساب', 'المبلغ']]
    total_exp = 0
    for acc in Account.objects.filter(account_type=AccountType.EXPENSE, is_active=True):
        dr = acc.transactions.filter(journal_entry__in=entries, transaction_type='debit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        cr = acc.transactions.filter(journal_entry__in=entries, transaction_type='credit').aggregate(
            t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        bal = dr - cr
        if bal != 0:
            exp_data.append([acc.code, acc.name, format_number(bal)])
            total_exp += bal
    exp_data.append([Paragraph('<b>إجمالي المصروفات</b>', STYLES['total']), '', 
                     Paragraph(f'<b>{format_number(total_exp)}</b>', STYLES['total'])])
    elements.append(build_table(exp_data, [80, 220, 120], ACCENT))
    elements.append(Spacer(1, 20))
    
    # Net Profit
    net = total_rev - total_exp
    net_color = SECONDARY if net >= 0 else ACCENT
    net_data = [[Paragraph('<b>صافي الربح / الخسارة</b>', STYLES['total']), 
                 Paragraph(f'<b>{format_number(net)}</b>', STYLES['total'])]]
    net_table = Table(net_data, colWidths=[300, 150])
    net_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE if net >= 0 else LIGHT_RED),
        ('GRID', (0, 0), (-1, -1), 1.5, net_color),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(net_table)
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer


def generate_enhanced_balance_sheet(date_to=None):
    """Generate enhanced balance sheet PDF."""
    buffer = BytesIO()
    title = 'الميزانية العمومية التفصيلية'
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    
    from accounting.models import Account, AccountType
    
    elements = []
    elements.append(Paragraph(title, STYLES['title']))
    if date_to:
        elements.append(Paragraph(f'كما في: {date_to}', STYLES['subtitle']))
    else:
        elements.append(Paragraph(f'كما في: {datetime.now().strftime("%Y-%m-%d")}', STYLES['subtitle']))
    elements.append(Spacer(1, 15))
    
    # Assets
    elements.append(Paragraph('الأصول', STYLES['section']))
    asset_data = [['رمز الحساب', 'اسم الحساب', 'المبلغ']]
    total_assets = 0
    for acc in Account.objects.filter(account_type=AccountType.ASSET, is_active=True):
        if acc.current_balance != 0:
            asset_data.append([acc.code, acc.name, format_number(acc.current_balance)])
            total_assets += acc.current_balance
    asset_data.append([Paragraph('<b>إجمالي الأصول</b>', STYLES['total']), '', 
                      Paragraph(f'<b>{format_number(total_assets)}</b>', STYLES['total'])])
    elements.append(build_table(asset_data, [80, 220, 120], PRIMARY))
    elements.append(Spacer(1, 15))
    
    # Liabilities
    elements.append(Paragraph('الخصوم', STYLES['section']))
    liab_data = [['رمز الحساب', 'اسم الحساب', 'المبلغ']]
    total_liab = 0
    for acc in Account.objects.filter(account_type=AccountType.LIABILITY, is_active=True):
        if acc.current_balance != 0:
            liab_data.append([acc.code, acc.name, format_number(acc.current_balance)])
            total_liab += acc.current_balance
    liab_data.append([Paragraph('<b>إجمالي الخصوم</b>', STYLES['total']), '', 
                     Paragraph(f'<b>{format_number(total_liab)}</b>', STYLES['total'])])
    elements.append(build_table(liab_data, [80, 220, 120], colors.Color(0.6, 0.3, 0.3)))
    elements.append(Spacer(1, 15))
    
    # Equity
    elements.append(Paragraph('حقوق الملكية', STYLES['section']))
    eq_data = [['رمز الحساب', 'اسم الحساب', 'المبلغ']]
    total_eq = 0
    for acc in Account.objects.filter(account_type=AccountType.EQUITY, is_active=True):
        if acc.current_balance != 0:
            eq_data.append([acc.code, acc.name, format_number(acc.current_balance)])
            total_eq += acc.current_balance
    eq_data.append([Paragraph('<b>إجمالي حقوق الملكية</b>', STYLES['total']), '', 
                   Paragraph(f'<b>{format_number(total_eq)}</b>', STYLES['total'])])
    elements.append(build_table(eq_data, [80, 220, 120], colors.Color(0.3, 0.5, 0.3)))
    elements.append(Spacer(1, 20))
    
    # Total check
    total_le = total_liab + total_eq
    check_data = [
        [Paragraph('<b>إجمالي الخصوم + حقوق الملكية</b>', STYLES['total']),
         Paragraph(f'<b>{format_number(total_le)}</b>', STYLES['total'])],
        [Paragraph('<b>إجمالي الأصول</b>', STYLES['total']),
         Paragraph(f'<b>{format_number(total_assets)}</b>', STYLES['total'])],
        [Paragraph('<b>الفرق</b>', STYLES['total']),
         Paragraph(f'<b>{format_number(total_assets - total_le)}</b>', STYLES['total'])],
    ]
    check_table = Table(check_data, colWidths=[300, 150])
    check_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('GRID', (0, 0), (-1, -1), 1, PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(check_table)
    
    doc.build(elements, lambda c, d: add_page_header_footer(c, d, title))
    buffer.seek(0)
    return buffer
