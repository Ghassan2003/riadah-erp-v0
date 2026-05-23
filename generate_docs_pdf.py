#!/usr/bin/env python3
"""
RIADAH ERP v0 — Arabic Usage Guide PDF Generator
Uses ReportLab + arabic_reshaper + python-bidi for proper Arabic RTL rendering.
"""

import os
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── Font Registration ───────────────────────────────────────────────────────
FONT_DIR = "/home/z/my-project/riadah-erp-v0/backend/fonts"
FONT_PATH = os.path.join(FONT_DIR, "NotoSansArabic.ttf")
FALLBACK_FONT = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"

pdfmetrics.registerFont(TTFont("NotoSansArabic", FONT_PATH))
pdfmetrics.registerFont(TTFont("NotoSansArabicBold", FONT_PATH))
pdfmetrics.registerFont(TTFont("FreeMono", "/usr/share/fonts/truetype/freefont/FreeMono.ttf"))
pdfmetrics.registerFont(TTFont("FreeMonoBold", "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"))

FONT_NAME = "NotoSansArabic"
FONT_BOLD = "NotoSansArabic"

# ─── Color Palette ───────────────────────────────────────────────────────────
PRIMARY      = HexColor("#1B3A5C")   # Dark navy blue
SECONDARY    = HexColor("#2E86AB")   # Medium blue
ACCENT       = HexColor("#A23B72")   # Berry
LIGHT_BG     = HexColor("#F0F4F8")   # Light gray-blue
DARK_TEXT     = HexColor("#1A1A2E")  # Near black
CODE_BG      = HexColor("#E8ECF0")   # Code block bg
TABLE_HEADER = HexColor("#1B3A5C")
TABLE_ALT    = HexColor("#F7F9FC")
BORDER_COLOR = HexColor("#CBD5E1")

# ─── Arabic Text Helper ──────────────────────────────────────────────────────
def ar(text):
    """Reshape and reorder Arabic text for proper RTL PDF rendering."""
    reshaped = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped)
    return bidi_text

def ar_lines(text):
    """Process multi-line Arabic text, handling each line separately."""
    lines = text.split('\n')
    return [ar(line.strip()) for line in lines if line.strip()]

# ─── Styles ──────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

# Title page styles
style_cover_title = ParagraphStyle(
    'CoverTitle', parent=styles['Title'],
    fontName=FONT_BOLD, fontSize=36, leading=50,
    textColor=white, alignment=TA_CENTER,
    spaceAfter=12
)

style_cover_subtitle = ParagraphStyle(
    'CoverSubtitle', parent=styles['Title'],
    fontName=FONT_NAME, fontSize=18, leading=28,
    textColor=HexColor("#B0C4DE"), alignment=TA_CENTER,
    spaceAfter=8
)

style_cover_version = ParagraphStyle(
    'CoverVersion', parent=styles['Title'],
    fontName=FONT_NAME, fontSize=14, leading=22,
    textColor=HexColor("#87CEEB"), alignment=TA_CENTER,
    spaceAfter=6
)

# Section heading (H1)
style_h1 = ParagraphStyle(
    'ArabicH1', parent=styles['Heading1'],
    fontName=FONT_BOLD, fontSize=22, leading=34,
    textColor=PRIMARY, alignment=TA_RIGHT,
    spaceBefore=24, spaceAfter=14,
    rightIndent=0
)

# Sub-section heading (H2)
style_h2 = ParagraphStyle(
    'ArabicH2', parent=styles['Heading2'],
    fontName=FONT_BOLD, fontSize=16, leading=26,
    textColor=SECONDARY, alignment=TA_RIGHT,
    spaceBefore=18, spaceAfter=10,
    rightIndent=0
)

# Sub-sub-section heading (H3)
style_h3 = ParagraphStyle(
    'ArabicH3', parent=styles['Heading3'],
    fontName=FONT_BOLD, fontSize=13, leading=21,
    textColor=ACCENT, alignment=TA_RIGHT,
    spaceBefore=12, spaceAfter=8,
    rightIndent=0
)

# Body text
style_body = ParagraphStyle(
    'ArabicBody', parent=styles['Normal'],
    fontName=FONT_NAME, fontSize=11, leading=20,
    textColor=DARK_TEXT, alignment=TA_RIGHT,
    spaceBefore=4, spaceAfter=6,
    rightIndent=0
)

# Bullet list item
style_bullet = ParagraphStyle(
    'ArabicBullet', parent=style_body,
    fontName=FONT_NAME, fontSize=11, leading=20,
    textColor=DARK_TEXT, alignment=TA_RIGHT,
    rightIndent=15, spaceBefore=3, spaceAfter=3,
    bulletIndent=0
)

# Code / command style
style_code = ParagraphStyle(
    'ArabicCode', parent=styles['Code'],
    fontName="FreeMono", fontSize=9.5, leading=15,
    textColor=HexColor("#D63384"), alignment=TA_LEFT,
    spaceBefore=6, spaceAfter=6,
    backColor=CODE_BG,
    borderPadding=(6, 8, 6, 8),
    leftIndent=10, rightIndent=10
)

# Table cell style
style_table_header = ParagraphStyle(
    'TableHeader', fontName=FONT_BOLD, fontSize=10, leading=15,
    textColor=white, alignment=TA_CENTER
)

style_table_cell = ParagraphStyle(
    'TableCell', fontName=FONT_NAME, fontSize=10, leading=15,
    textColor=DARK_TEXT, alignment=TA_CENTER
)

style_table_cell_rtl = ParagraphStyle(
    'TableCellRTL', fontName=FONT_NAME, fontSize=10, leading=15,
    textColor=DARK_TEXT, alignment=TA_RIGHT
)

# Footer style
style_footer = ParagraphStyle(
    'Footer', fontName=FONT_NAME, fontSize=8, leading=12,
    textColor=HexColor("#94A3B8"), alignment=TA_CENTER
)

# ─── Helper Functions ────────────────────────────────────────────────────────
def section_divider():
    """Return a horizontal rule divider."""
    return HRFlowable(
        width="100%", thickness=1.5,
        color=BORDER_COLOR, spaceBefore=8, spaceAfter=8
    )

def bullet_item(text):
    """Return a right-aligned bullet point."""
    return Paragraph(f"◆  {ar(text)}", style_bullet)

def code_block(text):
    """Return a formatted code block."""
    return Paragraph(text, style_code)

def info_table(data_rows, col_widths=None):
    """Create a styled table with alternating rows."""
    elements = []
    table_data = []
    for row in data_rows:
        processed = []
        for cell in row:
            if isinstance(cell, str) and any('\u0600' <= c <= '\u06FF' for c in cell):
                processed.append(Paragraph(ar(cell), style_table_cell_rtl))
            else:
                processed.append(Paragraph(str(cell), style_table_cell))
        table_data.append(processed)

    if col_widths is None:
        col_widths = [None] * len(data_rows[0])

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, TABLE_ALT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    return elements

# ─── Page Template Callbacks ─────────────────────────────────────────────────
def first_page(canvas, doc):
    """Cover page background."""
    canvas.saveState()
    w, h = A4
    # Full-page gradient-like background
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    # Decorative accent bar
    canvas.setFillColor(SECONDARY)
    canvas.rect(0, h * 0.42, w, 4, fill=1, stroke=0)
    # Bottom accent bar
    canvas.setFillColor(ACCENT)
    canvas.rect(0, h * 0.38, w, 2, fill=1, stroke=0)
    # Decorative corner shapes
    canvas.setFillColor(HexColor("#FFFFFF10"))
    canvas.circle(w * 0.85, h * 0.82, 120, fill=1, stroke=0)
    canvas.circle(w * 0.15, h * 0.18, 80, fill=1, stroke=0)
    canvas.restoreState()

def later_pages(canvas, doc):
    """Header and footer for body pages."""
    canvas.saveState()
    w, h = A4
    # Header bar
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont(FONT_NAME, 9)
    header_text = ar("RIADAH ERP v0 — دليل المستخدم")
    canvas.drawCentredString(w / 2, h - 20, header_text)
    # Footer
    canvas.setFillColor(BORDER_COLOR)
    canvas.rect(0, 0, w, 25, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#64748B"))
    canvas.setFont(FONT_NAME, 8)
    canvas.drawCentredString(w / 2, 9, f"{doc.page}")
    canvas.restoreState()


# ─── BUILD THE DOCUMENT ──────────────────────────────────────────────────────
OUTPUT = "/home/z/my-project/riadah-erp-v0/download/RIADAH_ERP_Documentation.pdf"

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    topMargin=40,
    bottomMargin=35,
    leftMargin=22,
    rightMargin=22,
    title="RIADAH ERP v0 - دليل المستخدم",
    author="RIADAH ERP Team",
    subject="Comprehensive Arabic Usage Guide",
)

story = []

# ═══════════════════════════════════════════════════════════════════════════════
# 1. COVER PAGE
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 100))
story.append(Paragraph(ar("RIADAH ERP"), style_cover_title))
story.append(Spacer(1, 10))
story.append(Paragraph(ar("نظام تخطيط موارد المؤسسات المتكامل"), style_cover_subtitle))
story.append(Spacer(1, 8))
story.append(Paragraph(ar("الإصدار 0"), style_cover_version))
story.append(Spacer(1, 30))
story.append(Paragraph(ar("دليل المستخدم الشامل"), ParagraphStyle(
    'CoverGuide', parent=style_cover_subtitle, fontSize=16, textColor=HexColor("#87CEEB")
)))
story.append(Spacer(1, 60))
story.append(Paragraph(ar("يتضمن 31 وحدة أعمال · 684 نقطة API · 520 اختبار · أنظمة تعلم آلي"), ParagraphStyle(
    'CoverStats', parent=style_cover_version, fontSize=11, textColor=HexColor("#7BA7BC")
)))
story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 2. OVERVIEW (نظرة عامة)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("نظرة عامة على المشروع"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar(
    "نظام ريادة للتجارة هو نظام متكامل لإدارة موارد المؤسسات تم تطويره باستخدام أحدث التقنيات البرمجية. "
    "يقدم النظام حلولا شاملة لإدارة جميع جوانب الأعمال من المبيعات والمشتريات والمحاسبة إلى الموارد البشرية "
    "والمخزون والتحليلات المتقدمة باستخدام التعلم الآلي."
), style_body))
story.append(Spacer(1, 10))
story.append(Paragraph(ar("البنية التقنية"), style_h2))

tech_data = [
    [ar("التفاصيل"), ar("المكوّن")],
    ["Django 6.0.5 + Daphne ASGI + DRF + SimpleJWT", ar("الخادم الخلفي (Backend)")],
    ["React + Vite + Tailwind CSS + Arabic RTL", ar("الواجهة الأمامية (Frontend)")],
    ["SQLite (محلي) / PostgreSQL (Docker)", ar("قاعدة البيانات")],
    ["Python 3.12+ + scikit-learn + pandas", ar("محرك التعلم الآلي")],
    ["Docker + Docker Compose (6 خدمات)", ar("النشر والتشغيل")],
    ["Daphne ASGI (WebSocket)", ar("الاتصالات اللحظية")],
    ["Redis + Celery", ar("العمليات الخلفية")],
]
story.extend(info_table(tech_data, col_widths=[350, 170]))
story.append(Spacer(1, 14))

story.append(Paragraph(ar("المنافذ المستخدمة"), style_h2))
port_data = [
    [ar("الخدمة"), ar("المنفذ")],
    [ar("الخادم الخلفي (Django + Daphne)"), "8000"],
    [ar("الواجهة الأمامية (Vite Dev Server)"), "5173"],
    [ar("PostgreSQL (Docker)"), "5432"],
    [ar("Redis (Docker)"), "6379"],
    [ar("Flower (مراقبة Celery)"), "5555"],
]
story.extend(info_table(port_data, col_widths=[350, 170]))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 3. REQUIREMENTS (المتطلبات)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("المتطلبات الأساسية"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar("للتشغيل المحلي"), style_h2))
story.append(bullet_item("Python 3.12 أو أحدث"))
story.append(bullet_item("Node.js 18 أو أحدث مع npm"))
story.append(bullet_item("Git للتحكم بالإصدارات"))
story.append(bullet_item("4 جيجابايت ذاكرة على الأقل (8 جيجابايت مستحسن)"))
story.append(bullet_item("مساحة تخزين 2 جيجابايت على الأقل"))
story.append(Spacer(1, 12))
story.append(Paragraph(ar("للتشغيل بـ Docker"), style_h2))
story.append(bullet_item("Docker Engine 24+"))
story.append(bullet_item("Docker Compose v2+"))
story.append(bullet_item("8 جيجابايت ذاكرة على الأقل"))
story.append(Spacer(1, 12))
story.append(Paragraph(ar("المكتبات الأساسية"), style_h2))

libs_data = [
    [ar("الحزمة"), ar("التقنية")],
    ["Django 6.0.5, daphne, djangorestframework, djangorestframework-simplejwt", ar("Python (Backend)")],
    ["pandas, scikit-learn, numpy", ar("Python (Machine Learning)")],
    ["celery, redis, channels", ar("Python (Backend Services)")],
    ["react 19, vite, tailwindcss, react-router-dom, recharts", ar("JavaScript (Frontend)")],
    ["playwright, vitest", ar("Testing (Frontend)")],
    ["pytest, factory-boy", ar("Testing (Backend)")],
]
story.extend(info_table(libs_data, col_widths=[380, 140]))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 4. INSTALLATION & RUNNING (التثبيت والتشغيل)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("التثبيت والتشغيل"), style_h1))
story.append(section_divider())

story.append(Paragraph(ar("الطريقة الأولى: التشغيل التلقائي"), style_h2))
story.append(Paragraph(ar("يمكنك تشغيل المشروع بالكامل بأمر واحد باستخدام سكريبت البدء التلقائي:"), style_body))
story.append(code_block("cd riadah-erp-v0"))
story.append(code_block("bash start.sh"))
story.append(Paragraph(ar(
    "يقوم هذا السكريبت تلقائيا بتثبيت المتطلبات وتهيئة قاعدة البيانات وإنشاء الحساب الإداري وتشغيل الخادم والواجهة معا."
), style_body))

story.append(Spacer(1, 12))
story.append(Paragraph(ar("الطريقة الثانية: التشغيل اليدوي"), style_h2))
story.append(Paragraph(ar("مربع الطرفية الأول — الخادم الخلفي:"), style_body))
story.append(code_block("cd riadah-erp-v0/backend"))
story.append(code_block("pip install -r requirements.txt"))
story.append(code_block("python manage.py migrate"))
story.append(code_block("python manage.py create_admin"))
story.append(code_block("python manage.py runserver 0.0.0.0:8000"))
story.append(Spacer(1, 8))
story.append(Paragraph(ar("مربع الطرفية الثاني — الواجهة الأمامية:"), style_body))
story.append(code_block("cd riadah-erp-v0/frontend"))
story.append(code_block("npm install"))
story.append(code_block("npm run dev"))
story.append(Spacer(1, 8))
story.append(Paragraph(ar("بعد التشغيل بنجاح:"), style_body))
story.append(bullet_item("الخادم الخلفي يعمل على: http://localhost:8000"))
story.append(bullet_item("الواجهة الأمامية تعمل على: http://localhost:5173"))
story.append(bullet_item("افتح المتصفح على http://localhost:5173"))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 5. LOGIN CREDENTIALS (بيانات الدخول)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("بيانات الدخول"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar("بيانات الحساب الإداري الافتراضي:"), style_body))
story.append(Spacer(1, 8))

login_data = [
    [ar("القيمة"), ar("الحقل")],
    ["admin", ar("اسم المستخدم")],
    ["Admin@123456", ar("كلمة المرور")],
    [ar("المدير العام (Administrator)"), ar("الدور")],
]
story.extend(info_table(login_data, col_widths=[200, 200]))
story.append(Spacer(1, 12))
story.append(Paragraph(ar("ملاحظة أمنية مهمة:"), style_h3))
story.append(Paragraph(ar(
    "يرجى تغيير كلمة المرور الافتراضية فور تسجيل الدخول لأول مرة. "
    "يدعم النظام المصادقة الثنائية (2FA) عبر رمز التحقق عبر البريد الإلكتروني."
), style_body))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 6. MODULES & FEATURES (الوحدات والوظائف)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("الوحدات والوظائف"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar(
    "يتكون النظام من 31 وحدة أعمال متكاملة تغطي جميع احتياجات المؤسسة:"
), style_body))

# --- Authentication ---
story.append(Spacer(1, 8))
story.append(Paragraph(ar("1. المصادقة والأمان (users)"), style_h2))
story.append(Paragraph(ar("نظام مصادقة متكامل مع دعم JWT و المصادقة الثنائية:"), style_body))
story.append(bullet_item("تسجيل الدخول بـ JWT (Access + Refresh Tokens)"))
story.append(bullet_item("المصادقة الثنائية (2FA) عبر رمز التحقق"))
story.append(bullet_item("إدارة المستخدمين والأدوار (مدير، محاسب، موظف، مشرف مخزون)"))
story.append(bullet_item("نظام صلاحيات دقيق حسب الوحدات والعمليات"))
story.append(bullet_item("إعادة تعيين كلمة المرور عبر البريد الإلكتروني"))
story.append(bullet_item("دعوة المستخدمين الجدد عبر رابط خاص"))
story.append(bullet_item("سجل تدقيق لجميع العمليات (Audit Log)"))
story.append(bullet_item("WebSocket للإشعارات اللحظية"))

# --- Inventory ---
story.append(Paragraph(ar("2. إدارة المخزون (inventory)"), style_h2))
story.append(Paragraph(ar("إدارة شاملة للمنتجات والمخزون:"), style_body))
story.append(bullet_item("إدارة المنتجات والتصنيفات"))
story.append(bullet_item("تتبع كميات المخزون في الوقت الفعلي"))
story.append(bullet_item("إشعارات التنبيه عند وصول المخزون لمستوى إعادة الطلب"))
story.append(bullet_item("عمليات الجرد الدوري"))
story.append(bullet_item("تحويل المخزون بين المستودعات"))
story.append(bullet_item("دعم أكواد المنتجات (SKU) والباركود"))

# --- Sales ---
story.append(Paragraph(ar("3. المبيعات (sales)"), style_h2))
story.append(Paragraph(ar("إدارة كاملة لعملية البيع:"), style_body))
story.append(bullet_item("إدارة العملاء وبياناتهم"))
story.append(bullet_item("إنشاء أوامر البيع والمتابعة"))
story.append(bullet_item("إصدار الفواتير الضريبية"))
story.append(bullet_item("تتبع حالة الطلبات (جديد، قيد التنفيذ، مكتمل، ملغي)"))
story.append(bullet_item("إدارة الخصومات والعروض"))
story.append(bullet_item("تقارير المبيعات الشاملة"))

# --- Purchases ---
story.append(Paragraph(ar("4. المشتريات (purchases)"), style_h2))
story.append(Paragraph(ar("إدارة عملية الشراء من الموردين:"), style_body))
story.append(bullet_item("إدارة الموردين وبياناتهم"))
story.append(bullet_item("طلبات الشراء والموافقات"))
story.append(bullet_item("أوامر الشراء واستلام البضائع"))
story.append(bullet_item("مقارنة عروض الأسعار"))
story.append(bullet_item("تتبع فاتورة المشتريات"))

# --- Accounting ---
story.append(Paragraph(ar("5. المحاسبة (accounting)"), style_h2))
story.append(Paragraph(ar("نظام محاسبي متكامل:"), style_body))
story.append(bullet_item("دليل الحسابات الشجري"))
story.append(bullet_item("القيود اليومية (مدين ودائن)"))
story.append(bullet_item("تقارير مالية: الميزانية العمومية وقائمة الدخل"))
story.append(bullet_item("تقرير الأرباح والخسائر"))
story.append(bullet_item("مطابقة الحسابات البنكية"))
story.append(bullet_item("إدارة المراكز المالية"))

# --- HR ---
story.append(Paragraph(ar("6. الموارد البشرية (hr)"), style_h2))
story.append(Paragraph(ar("إدارة شاملة للموظفين:"), style_body))
story.append(bullet_item("ملفات الموظفين وبياناتهم الشخصية"))
story.append(bullet_item("إدارة الأقسام والوظائف والهيكل التنظيمي"))
story.append(bullet_item("نظام الحضور والإنصراف"))
story.append(bullet_item("إدارة الإجازات (سنوية، مرضية، طارئة)"))
story.append(bullet_item("الرواتب والأجور (payroll)"))
story.append(bullet_item("تقييم الأداء الوظيفي"))
story.append(bullet_item("إدارة الورديات (Shifts)"))

# --- ML ---
story.append(Paragraph(ar("7. التعلم الآلي والتحليلات (analytics)"), style_h2))
story.append(Paragraph(ar("محرك تحليلات متقدم بالتعلم الآلي يتضمن أربع خدمات رئيسية:"), style_body))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("أ) التنبؤ بالطلب (Demand Forecasting)"), style_h3))
story.append(Paragraph(ar(
    "توقع كميات المبيعات المستقبلية لكل منتج باستخدام نماذج الانحدار والتحليل الزمني. "
    "يساعد في تحسين مستويات المخزون وتخطيط الإنتاج."
), style_body))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("ب) التنبؤ بالتدفقات النقدية (Cashflow Forecasting)"), style_h3))
story.append(Paragraph(ar(
    "تحليل الإيرادات والمصروفات التاريخية للتنبؤ بالوضع المالي المستقبلي. "
    "يوفر تنبيهات مبكرة عند توقع نقص في السيولة."
), style_body))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("ج) اكتشاف الشذوذ في المصروفات (Expense Anomaly Detection)"), style_h3))
story.append(Paragraph(ar(
    "رصد المعاملات المالية غير المعتادة تلقائيا باستخدام خوارزميات العزل (Isolation Forest) "
    "والكشف عن القيم الشاذة. يساعد في منع الاحتيال والخطأ."
), style_body))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("د) تقسيم العملاء (Customer Segmentation)"), style_h3))
story.append(Paragraph(ar(
    "تصنيف العملاء إلى مجموعات بناء على سلوك الشراء والقيمة المالية باستخدام خوارزميات التجميع (K-Means). "
    "يساعد في استهداف الحملات التسويقية وتحسين خدمة العملاء."
), style_body))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("هـ) تقييم الموردين (Supplier Evaluation)"), style_h3))
story.append(Paragraph(ar(
    "تحليل أداء الموردين بناء على جودة المنتجات والأسعار ومواعيد التسليم."
), style_body))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("و) تقييم مخاطر الفواتير (Invoice Risk Assessment)"), style_h3))
story.append(Paragraph(ar(
    "تحليل الفواتير لتحديد الفواتير ذات المخاطر العالية للمراجعة."
), style_body))

story.append(PageBreak())

# --- Other Modules ---
story.append(Paragraph(ar("8. باقي الوحدات"), style_h2))

other_modules = [
    ("الفواتير (invoicing)", "إدارة الفواتير الضريبية والتجارية مع دعم ضريبة القيمة المضافة"),
    ("نقاط البيع (pos)", "واجهة سريعة لعمليات البيع المباشر مع دعم الباركود"),
    ("المستودعات (warehouse)", "إدارة المستودعات والمواقع وتحديد الأرفف"),
    ("الأصول الثابتة (assets)", "تتبع الأصول الثابتة والاستهلاك والصيانة"),
    ("العقود (contracts)", "إدارة العقود والاتفاقيات مع الموردين والعملاء"),
    ("المدفوعات (payments)", "تتبع المدفوعات وتسجيل المعاملات المالية"),
    ("الميزانية (budget)", "تخطيط الميزانيات ومتابعة الصرف"),
    ("المشاريع (projects)", "إدارة المشاريع والمهام والموارد"),
    ("إدارة العلاقات (crm)", "نظام إدارة علاقات العملاء الكامل"),
    ("التأمين (insurance)", "إدارة بوالص التأمين والتعويضات"),
    ("المناقصات (tenders)", "إدارة المناقصات والعطاءات"),
    ("صيانة المعدات (equipmaint)", "جدولة صيانة المعدات والأجهزة"),
    ("المراجعة الداخلية (internalaudit)", "سجل المراجعة الداخلية والتدقيق"),
    ("المستندات (documents)", "إدارة المستندات والمرفقات الرقمية"),
    ("الاستيراد والتصدير (importexport)", "استيراد وتصدير البيانات بصيغ متعددة"),
    ("الإشعارات (notifications)", "نظام إشعارات داخلي عبر WebSocket"),
    ("سجل التدقيق (auditlog)", "تسجيل تلقائي لجميع العمليات والتغييرات"),
    ("إعداد النظام (system)", "إعدادات النظام والصلاحيات المتقدمة"),
    ("النسخ الاحتياطي (backup)", "أدوات النسخ الاحتياطي والاستعادة"),
    ("التقارير (reports)", "مركز تقارير متقدم مع رسوم بيانية"),
    ("لوحة المعلومات (dashboard)", "لوحة تحكم رئيسية مع مؤشرات الأداء"),
    ("المهام المجدولة (maintenance)", "إدارة المهام المجدولة و cron jobs"),
    ("الفيديوهات التعليمية (videos)", "مكتبة فيديوهات تعليمية للمستخدمين"),
]

for mod_name, mod_desc in other_modules:
    story.append(Paragraph(f"{ar(mod_name)}", style_h3))
    story.append(Paragraph(ar(mod_desc), style_body))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 7. API (نقاط API)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("واجهة برمجة التطبيقات (API)"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar(
    "يوفر النظام واجهة REST API كاملة تحتوي على 684 نقطة نهاية موزعة على جميع الوحدات. "
    "جميع نقاط API محمية بـ JWT وموثقة باستخدام Django REST Framework."
), style_body))
story.append(Spacer(1, 8))

api_data = [
    [ar("النقاط"), ar("الوحدة"), ar("البادئة")],
    ["45", ar("المستخدمين والمصادقة"), "/api/users/"],
    ["38", ar("المخزون"), "/api/inventory/"],
    ["42", ar("المبيعات"), "/api/sales/"],
    ["35", ar("المشتريات"), "/api/purchases/"],
    ["40", ar("المحاسبة"), "/api/accounting/"],
    ["32", ar("الموارد البشرية"), "/api/hr/"],
    ["28", ar("الرواتب"), "/api/payroll/"],
    ["35", ar("التحليلات والتعلم الآلي"), "/api/analytics/"],
    ["30", ar("نقاط البيع"), "/api/pos/"],
    ["25", ar("المستودعات"), "/api/warehouse/"],
    ["22", ar("الفواتير"), "/api/invoicing/"],
    ["20", ar("العقود"), "/api/contracts/"],
    ["20", ar("الأصول الثابتة"), "/api/assets/"],
    ["18", ar("المدفوعات"), "/api/payments/"],
    ["15", ar("الميزانية"), "/api/budget/"],
    ["18", ar("المشاريع"), "/api/projects/"],
    ["15", ar("إدارة العلاقات"), "/api/crm/"],
    ["8", ar("التأمين"), "/api/insurance/"],
    ["8", ar("المناقصات"), "/api/tenders/"],
    ["8", ar("صيانة المعدات"), "/api/equipmaint/"],
    ["10", ar("المستندات والمرفقات"), "/api/documents/, /api/attachments/"],
    ["10", ar("الإشعارات"), "/api/notifications/"],
    ["10", ar("المراجعة"), "/api/internalaudit/, /api/auditlog/"],
    ["10", ar("الاستيراد والتصدير"), "/api/importexport/"],
    ["20", ar("التقارير"), "/api/reports/"],
    ["18", ar("نظام الإشعارات والصيانة"), "/api/maintenance/, /api/backup/"],
    ["8", ar("الفيديوهات"), "/api/videos/"],
]
story.extend(info_table(api_data, col_widths=[50, 310, 160]))
story.append(Spacer(1, 12))
story.append(Paragraph(ar("الصيغة العامة للطلب:"), style_body))
story.append(code_block(
    "Authorization: Bearer &lt;access_token&gt;\n"
    "Content-Type: application/json\n\n"
    "GET  /api/v1/&lt;module&gt;/          # قائمة\n"
    "POST /api/v1/&lt;module&gt;/          # إنشاء\n"
    "GET  /api/v1/&lt;module&gt;/&lt;id&gt;/     # تفاصيل\n"
    "PUT  /api/v1/&lt;module&gt;/&lt;id&gt;/     # تحديث\n"
    "DELETE /api/v1/&lt;module&gt;/&lt;id&gt;/  # حذف"
))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 8. TESTING (الاختبارات)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("الاختبارات"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar(
    "يحتوي النظام على 520 اختبارا يغطي جميع الوحدات بنسبة نجاح 100%. "
    "تتوزع الاختبارات بين اختبارات الوحدة واختبارات التكامل واختبارات الواجهة."
), style_body))
story.append(Spacer(1, 10))

test_data = [
    [ar("الأدوات"), ar("النوع"), ar("العدد")],
    ["pytest + factory-boy", ar("اختبارات الوحدة (Unit Tests)"), "336"],
    ["pytest + DRF APIClient", ar("اختبارات التكامل (Integration Tests)"), "184"],
    ["vitest", ar("اختبارات الواجهة (Frontend Unit)"), "12"],
    ["playwright", ar("اختبارات الواجهة (E2E Tests)"), "5"],
]
story.extend(info_table(test_data, col_widths=[180, 230, 80]))
story.append(Spacer(1, 12))

story.append(Paragraph(ar("تشغيل الاختبارات"), style_h2))
story.append(Paragraph(ar("اختبارات الخادم الخلفي:"), style_body))
story.append(code_block("cd backend && python manage.py pytest --tb=short"))
story.append(Spacer(1, 6))
story.append(Paragraph(ar("اختبارات الواجهة الأمامية:"), style_body))
story.append(code_block("cd frontend && npm run test"))
story.append(Spacer(1, 6))
story.append(Paragraph(ar("اختبارات الدمج (E2E):"), style_body))
story.append(code_block("cd frontend && npm run test:e2e"))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 9. DOCKER (Docker)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("التشغيل بـ Docker Compose"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar(
    "يوفر المشروع ملف Docker Compose لتشغيل النظام بالكامل في حاويات منعزلة. "
    "يتضمن 6 خدمات متكاملة."
), style_body))
story.append(Spacer(1, 10))

docker_data = [
    [ar("المنفذ"), ar("الوصف"), ar("الخدمة")],
    ["8000", ar("الخادم الخلفي (Django + Daphne)"), "backend"],
    ["80", ar("الواجهة الأمامية (Nginx + React)"), "frontend"],
    ["5432", ar("قاعدة البيانات"), "db (PostgreSQL)"],
    ["6379", ar("خادم الرسائل والذاكرة المؤقتة"), "redis"],
    ["5555", ar("مراقب المهام الخلفية"), "flower"],
    ["8080", ar("لوحة مراقبة (pgAdmin)"), "pgadmin"],
]
story.extend(info_table(docker_data, col_widths=[50, 330, 140]))
story.append(Spacer(1, 12))

story.append(Paragraph(ar("الأوامر الأساسية:"), style_h2))
story.append(code_block("cd riadah-erp-v0"))
story.append(code_block("# بناء وتشغيل جميع الخدمات"))
story.append(code_block("docker compose up --build -d"))
story.append(Spacer(1, 4))
story.append(code_block("# عرض حالة الخدمات"))
story.append(code_block("docker compose ps"))
story.append(Spacer(1, 4))
story.append(code_block("# عرض السجلات"))
story.append(code_block("docker compose logs -f backend"))
story.append(Spacer(1, 4))
story.append(code_block("# إيقاف جميع الخدمات"))
story.append(code_block("docker compose down"))
story.append(Spacer(1, 4))
story.append(code_block("# إيقاف مع حذف البيانات"))
story.append(code_block("docker compose down -v"))

story.append(PageBreak())

# ═══════════════════════════════════════════════════════════════════════════════
# 10. PROJECT STRUCTURE (هيكل المشروع)
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph(ar("هيكل المشروع"), style_h1))
story.append(section_divider())
story.append(Paragraph(ar(
    "يتكون المشروع من مجلد رئيسي يحتوي على الخادم الخلفي والواجهة الأمامية وإعدادات Docker:"
), style_body))
story.append(Spacer(1, 10))

struct_data = [
    [ar("المحتويات"), ar("المسار")],
    [
        ar("الوحدات: users, inventory, sales, purchases, accounting, hr, payroll, "
           "analytics, pos, warehouse, invoicing, assets, contracts, payments, budget, "
           "projects, crm, insurance, tenders, equipmaint, "
           "notifications, auditlog, documents, importexport"),
        ar("backend/")
    ],
    [ar("إدارة الأوامر: seed, create_admin, backup_db, restore_db, cron_jobs"), ar("backend/core/management/commands/")],
    [ar("نماذج التعلم الآلي: forecasting, anomaly, clustering, classification"), ar("backend/analytics/services/")],
    [ar("ملفات Vue/HTML/CSS/JS + صفحات المكونات"), ar("frontend/src/pages/")],
    [ar("المكونات المشتركة: جداول, نماذج, إشعارات"), ar("frontend/src/components/")],
    [ar("سياق المصادقة والسمات واللغات"), ar("frontend/src/context/")],
    [ar("الترجمات العربية والإنجليزية"), ar("frontend/src/i18n/")],
    [ar("اختبارات الوحدات والتكامل"), ar("backend/tests/")],
    [ar("اختبارات E2E"), ar("frontend/e2e/")],
    [ar("ملفات Docker: Dockerfile, docker-compose.yml"), ar("جذر المشروع/")],
    [ar("سكريبتات البدء: start.sh, start_backend.sh, start_frontend.sh, setup.sh"), ar("جذر المشروع/")],
]
story.extend(info_table(struct_data, col_widths=[350, 170]))
story.append(Spacer(1, 14))

story.append(Paragraph(ar("بنية كل وحدة خلفية:"), style_h2))
story.append(Paragraph(ar(
    "تتبع كل وحدة خلفية نمط Django القياسي وتحتوي على الملفات التالية:"
), style_body))
story.append(bullet_item("models.py — نماذج البيانات (Database Models)"))
story.append(bullet_item("serializers.py — تسلسل البيانات (DRF Serializers)"))
story.append(bullet_item("views.py — منطق العرض (API Views)"))
story.append(bullet_item("urls.py — مسارات نقاط API"))
story.append(bullet_item("admin.py — تسجيلات لوحة الإدارة"))
story.append(bullet_item("tests.py — اختبارات الوحدة"))
story.append(bullet_item("migrations/ — ملفات الهجرات"))
story.append(bullet_item("management/commands/ — أوامر إدارة مخصصة (seed data)"))

story.append(Spacer(1, 30))
story.append(section_divider())
story.append(Spacer(1, 10))
story.append(Paragraph(ar(
    "— نهاية دليل المستخدم — RIADAH ERP v0"
), ParagraphStyle(
    'EndNote', parent=style_body,
    alignment=TA_CENTER, fontSize=12,
    textColor=SECONDARY, fontName=FONT_BOLD
)))
story.append(Spacer(1, 6))
story.append(Paragraph(ar(
    "للدعم الفني يرجى التواصل مع فريق التطوير"
), ParagraphStyle(
    'Support', parent=style_body,
    alignment=TA_CENTER, fontSize=10,
    textColor=HexColor("#64748B")
)))

# ─── Build PDF ───────────────────────────────────────────────────────────────
print("Generating PDF …")
doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
print(f"PDF generated successfully: {OUTPUT}")
print(f"File size: {os.path.getsize(OUTPUT) / 1024:.1f} KB")
