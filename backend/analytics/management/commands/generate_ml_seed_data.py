"""
Generate realistic seed data for ML analytics system.
Creates 12 months of business data (June 2025 - May 2026) with:
- Monthly growth ~12% compound
- Seasonality (Ramadan, summer, Eid)
- Customer segmentation (VIP, regular, occasional, new, at-risk)
- Product demand tiers (fast/medium/slow moving)
- Deliberate anomalies for anomaly detection testing
"""

import random
import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from sales.models import Customer, SalesOrder, SalesOrderItem
# TODO: inventory module removed - seed data needs redesign
# from inventory.models import Product
from invoicing.models import Invoice, InvoiceItem, Payment
from accounting.models import Account, JournalEntry, Transaction
from purchases.models import Supplier, PurchaseOrder, PurchaseOrderItem
from hr.models import Department, Employee, Attendance
from payroll.models import PayrollPeriod, PayrollRecord
from crm.models import Contact, Lead, Campaign

# ─── Decimal helper ────────────────────────────────────────────────────
def D(value):
    """Convert to Decimal safely."""
    return Decimal(str(value))

def Q(value, places=2):
    """Quantize a Decimal to given places."""
    return D(value).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)

# ─── Constants ─────────────────────────────────────────────────────────
START_DATE = datetime.date(2025, 6, 1)
END_DATE = datetime.date(2026, 5, 31)

MONTH_MULTIPLIERS = {
    6: 1.00,   # June 2025 – baseline
    7: 0.95,   # July – slight summer drop
    8: 0.90,   # August – summer low
    9: 0.95,   # September
    10: 1.05,  # October
    11: 1.10,  # November
    12: 1.20,  # December – year-end rush
    1: 0.95,   # January 2026
    2: 1.30,   # February – Ramadan
    3: 1.25,   # March – continued Ramadan effect
    4: 1.15,   # April
    5: 1.10,   # May
}

BASE_MONTHLY_ORDERS = 20
MONTHLY_GROWTH = D('1.12')

# ─── Arabic Customer Names ────────────────────────────────────────────
CUSTOMER_NAMES = [
    'شركة النور للتجارة', 'مؤسسة الأمل', 'شركة الفجر', 'مصنع الريادة',
    'شركة البناء الحديث', 'مؤسسة الإبداع', 'شركة السلام للتجارة',
    'مؤسسة التقدم', 'شركة الصفا', 'مصنع المستقبل',
    'شركة البركة', 'مؤسسة النجاح', 'شركة الخليج للتجارة',
    'مؤسسة البناء المتطور', 'شركة الوفاء', 'مصنع الذهب',
    'شركة الأندلس', 'مؤسسة اليقين', 'شركة المدينة',
    'مصنع الحديد', 'شركة النخبة', 'مؤسسة الصناعة',
    'شركة الرياض', 'مؤسسة الإنتاج', 'شركة الدار',
    'مصنع الإبداع', 'شركة الشرق', 'مؤسسة البحر',
    'شركة الجبل', 'مؤسسة السهم', 'شركة الواحة',
    'مصنع النجمة', 'شركة الفيحاء', 'مؤسسة الحرف',
    'شركة البطحاء', 'مؤسسة المنار', 'شركة العين',
    'مصنع القمر', 'شركة الزهراء', 'مؤسسة الربيع',
    'شركة الخريف', 'مؤسسة الشتاء', 'شركة الصيف',
    'مصنع الكون', 'شركة الغد', 'مؤسسة البداية',
    'شركة النهاية', 'مؤسسة الوسط', 'شركة الطريق',
    'شركة الجسر', 'مؤسسة النفق',
]

# ─── Supplier Names ────────────────────────────────────────────────────
SUPPLIER_NAMES = [
    ('شركة التوريدات الأولى', 'First Supplies Co.', 'info@firstsupply.sa'),
    ('مصنع الحديد السعودي', 'Saudi Iron Factory', 'sales@saudiron.sa'),
    ('شركة الخشب العربي', 'Arab Wood Company', 'contact@arabwood.sa'),
    ('مؤسسة الورق الوطنية', 'National Paper Est.', 'info@natpaper.sa'),
    ('شركة الإلكترونيات المتقدمة', 'Advanced Electronics', 'sales@advelec.sa'),
    ('مؤسسة النقل السريع', 'Express Transport', 'info@exptrans.sa'),
    ('شركة البلاستيك الحديثة', 'Modern Plastics Co.', 'contact@modplastic.sa'),
    ('مصنع الأثاث المكتبي', 'Office Furniture Factory', 'sales@offfurn.sa'),
    ('شركة الكيماويات', 'Chemicals Company', 'info@chemco.sa'),
    ('مؤسسة الأدوات الكهربائية', 'Electric Tools Est.', 'contact@electools.sa'),
    ('شركة الحبر والطلاء', 'Ink & Paint Co.', 'info@inkpaint.sa'),
    ('مصنع الزجاج', 'Glass Factory', 'sales@glassfac.sa'),
    ('شركة التكييف المركزي', 'Central AC Company', 'info@centralac.sa'),
    ('مؤسسة المواد الغذائية', 'Food Materials Est.', 'contact@foodmat.sa'),
    ('شركة النظافة المتخصصة', 'Specialized Cleaning', 'info@specclean.sa'),
    ('مصنع الأبواب والنوافذ', 'Doors & Windows Factory', 'sales@doorwin.sa'),
    ('شركة الأسلاك والكابلات', 'Wires & Cables Co.', 'info@wirecable.sa'),
    ('مؤسسة الدهانات', 'Paints Est.', 'contact@paints.sa'),
    ('شركة الأرضيات', 'Flooring Company', 'info@flooring.sa'),
    ('مصنع الأنابيب', 'Pipes Factory', 'sales@pipesfac.sa'),
]

# ─── Products by Category ─────────────────────────────────────────────
PRODUCTS = [
    # Electronics (20) – fast-moving tier
    ('شاشة سامسونج 55 بوصة', 'ELEC-001', D('3500'), 500, 20),
    ('شاشة LG 43 بوصة', 'ELEC-002', D('2800'), 400, 20),
    ('لابتوب HP ProBook', 'ELEC-003', D('4500'), 300, 15),
    ('لابتوب Dell Latitude', 'ELEC-004', D('5200'), 250, 15),
    ('طابعة كانون MF4450', 'ELEC-005', D('1800'), 350, 15),
    ('طابعة HP LaserJet', 'ELEC-006', D('2200'), 300, 15),
    ('شاشة كمبيوتر 27 بوصة', 'ELEC-007', D('1200'), 600, 10),
    ('ماوس لاسلكي لوجيتك', 'ELEC-008', D('150'), 2000, 50),
    ('لوحة مفاتيح ميكانيكية', 'ELEC-009', D('450'), 800, 30),
    ('سماعة بلوتوث', 'ELEC-010', D('350'), 1000, 40),
    ('كاميرا مراقبة IP', 'ELEC-011', D('800'), 500, 25),
    ('راوتر شبكة', 'ELEC-012', D('650'), 600, 30),
    ('مزود طاقة UPS', 'ELEC-013', D('900'), 400, 20),
    ('هارد خارجي 2TB', 'ELEC-014', D('280'), 1500, 40),
    ('فلاش ميموري 64GB', 'ELEC-015', D('45'), 3000, 100),
    ('جهاز عرض بروكتور', 'ELEC-016', D('3800'), 100, 10),
    ('سماعة رأس احترافية', 'ELEC-017', D('250'), 800, 30),
    ('شارج لابتوس عالمي', 'ELEC-018', D('120'), 2000, 50),
    ('كابل HDMI 3m', 'ELEC-019', D('35'), 5000, 100),
    ('حبر طابعة أصلي', 'ELEC-020', D('180'), 1200, 50),
    # Furniture (20) – medium-moving tier
    ('مكتب خشبي كبير', 'FURN-001', D('2500'), 200, 10),
    ('مكتب خشبي صغير', 'FURN-002', D('1500'), 300, 10),
    ('كرسي مكتبي مريح', 'FURN-003', D('1200'), 400, 15),
    ('كرسي مكتبي عادي', 'FURN-004', D('600'), 600, 20),
    ('خزانة ملفات كبيرة', 'FURN-005', D('1800'), 150, 10),
    ('خزانة ملفات صغيرة', 'FURN-006', D('900'), 250, 10),
    ('طاولة اجتماعات 12 شخص', 'FURN-007', D('5500'), 50, 5),
    ('طاولة اجتماعات 6 شخص', 'FURN-008', D('3200'), 80, 5),
    ('رف كتب', 'FURN-009', D('700'), 200, 10),
    ('خزنة حديدية', 'FURN-010', D('2800'), 100, 8),
    ('مقعد انتظار', 'FURN-011', D('450'), 300, 15),
    ('طاولة استقبال', 'FURN-012', D('3500'), 60, 5),
    ('باب مكتب خشبي', 'FURN-013', D('2200'), 80, 8),
    ('ستارة مكتب', 'FURN-014', D('350'), 500, 20),
    ('إضاءة سقف LED', 'FURN-015', D('280'), 800, 30),
    ('براندة حائط', 'FURN-016', D('150'), 600, 20),
    ('سجادة مكتب', 'FURN-017', D('400'), 300, 15),
    ('صندوق بريد', 'FURN-018', D('120'), 400, 20),
    ('لوح إعلانات', 'FURN-019', D('200'), 250, 15),
    ('منظم مكتب', 'FURN-020', D('80'), 1000, 40),
    # Office Supplies (20) – medium-moving tier
    ('ورق A4 ريم 500', 'OFFC-001', D('18'), 10000, 500),
    ('ورق A3 ريم 500', 'OFFC-002', D('28'), 5000, 200),
    ('أقلام حبر جاف علبة 12', 'OFFC-003', D('15'), 8000, 300),
    ('أقلام رصاص علبة 12', 'OFFC-004', D('8'), 6000, 200),
    ('ملف بلاستيك A4 علبة 20', 'OFFC-005', D('25'), 5000, 200),
    ('ملف كرتون A4 علبة 20', 'OFFC-006', D('35'), 4000, 150),
    ('دباسة معدنية', 'OFFC-007', D('12'), 5000, 200),
    ('مسطرة 30سم', 'OFFC-008', D('5'), 8000, 300),
    ('ممحاة', 'OFFC-009', D('3'), 10000, 500),
    ('لاصق شفاف', 'OFFC-010', D('8'), 6000, 200),
    ('غراء أبيض', 'OFFC-011', D('6'), 7000, 250),
    ('مقص مكتب', 'OFFC-012', D('15'), 4000, 150),
    ('دبابيس علبة 500', 'OFFC-013', D('5'), 8000, 300),
    ('كليبر ملفات علبة 12', 'OFFC-014', D('10'), 6000, 200),
    ('علامة فلومستر علبة 8', 'OFFC-015', D('20'), 5000, 200),
    ('مذكرة A5 100 ورقة', 'OFFC-016', D('8'), 8000, 300),
    ('مذكرة A4 100 ورقة', 'OFFC-017', D('12'), 6000, 250),
    ('مظروف بني A4 علبة 50', 'OFFC-018', D('15'), 5000, 200),
    ('ورق لاصق ملون', 'OFFC-019', D('6'), 7000, 250),
    ('حامل أقلام', 'OFFC-020', D('25'), 3000, 100),
    # Raw Materials (20) – slow-moving tier
    ('حديد تسليح 12مم طن', 'RAW-001', D('3500'), 200, 20),
    ('حديد تسليح 16مم طن', 'RAW-002', D('3800'), 150, 20),
    ('أسمنت袋 50كجم', 'RAW-003', D('25'), 5000, 200),
    ('رمل washed طن', 'RAW-004', D('150'), 300, 20),
    ('حصى طن', 'RAW-005', D('120'), 300, 20),
    ('طوب أحمر 1000', 'RAW-006', D('1800'), 100, 10),
    ('أسلاك كهربائية 2.5مم متر', 'RAW-007', D('8'), 10000, 500),
    ('أنابيب PVC 4 بوصة متر', 'RAW-008', D('15'), 5000, 200),
    ('أنابيب حديدية 2 بوصة متر', 'RAW-009', D('45'), 3000, 200),
    ('دهان أبيض 20 لتر', 'RAW-010', D('350'), 500, 30),
    ('دهان زيتي 20 لتر', 'RAW-011', D('450'), 400, 25),
    ('مسامير خشب علبة 200', 'RAW-012', D('20'), 3000, 150),
    ('براغي 8مم علبة 100', 'RAW-013', D('30'), 2500, 100),
    ('زجاج عادي 6مم متر مربع', 'RAW-014', D('120'), 500, 30),
    ('عوازل حرارية رول', 'RAW-015', D('200'), 300, 20),
    ('بلاط سيراميك متر مربع', 'RAW-016', D('45'), 2000, 100),
    ('بلاط رخام متر مربع', 'RAW-017', D('250'), 300, 20),
    ('بويات ماء 20 لتر', 'RAW-018', D('180'), 400, 25),
    ('أسمنت أبيض 50 كجم', 'RAW-019', D('35'), 2000, 100),
    ('شريط لاصق صناعي رول', 'RAW-020', D('15'), 5000, 200),
    # Services (20) – slow-moving tier
    ('خدمة صيانة عامة', 'SERV-001', D('500'), 0, 0),
    ('خدمة نقل داخل المدينة', 'SERV-002', D('800'), 0, 0),
    ('خدمة نقل بين المدن', 'SERV-003', D('2500'), 0, 0),
    ('خدمة تنظيف مكتبي', 'SERV-004', D('300'), 0, 0),
    ('خدمة تنظيف دوري', 'SERV-005', D('1500'), 0, 0),
    ('خدمة صيانة تكييف', 'SERV-006', D('350'), 0, 0),
    ('خدمة صيانة طابعة', 'SERV-007', D('200'), 0, 0),
    ('خدمة صيانة شبكة', 'SERV-008', D('600'), 0, 0),
    ('خدمة تصميم جرافيك', 'SERV-009', D('2000'), 0, 0),
    ('خدمة طباعة بروشورات', 'SERV-010', D('500'), 0, 0),
    ('خدمة استشارة قانونية', 'SERV-011', D('1500'), 0, 0),
    ('خدمة استشارة مالية', 'SERV-012', D('2000'), 0, 0),
    ('خدمة تأمين مبنى', 'SERV-013', D('5000'), 0, 0),
    ('خدمة تأمين سيارات', 'SERV-014', D('3000'), 0, 0),
    ('خدمة تدريب موظفين', 'SERV-015', D('1200'), 0, 0),
    ('خدمة تأجير سيارات', 'SERV-016', D('3000'), 0, 0),
    ('خدمة حراسة أمنية', 'SERV-017', D('4000'), 0, 0),
    ('خدمة كافتيريا شهرياً', 'SERV-018', D('8000'), 0, 0),
    ('خدمة صيانة مصاعد', 'SERV-019', D('1500'), 0, 0),
    ('خدمة مكافحة حشرات', 'SERV-020', D('400'), 0, 0),
]

# Product movement tiers
FAST_MOVING_SKUS = [p[1] for p in PRODUCTS[:10]]   # ELEC-001..020 (first 10)
MEDIUM_MOVING_SKUS = [p[1] for p in PRODUCTS[10:40]]  # Next 30
SLOW_MOVING_SKUS = [p[1] for p in PRODUCTS[40:]]     # Last 60

# ─── Employee Data ─────────────────────────────────────────────────────
ARABIC_FIRST_NAMES = [
    'محمد', 'أحمد', 'عبدالله', 'سعيد', 'خالد', 'فهد', 'ناصر', 'عمر',
    'يوسف', 'إبراهيم', 'سلطان', 'ماجد', 'بندر', 'تركي', 'فيصل',
    'سعد', 'عبدالرحمن', 'وليد', 'هشام', 'طلال', 'منصور', 'عبدالعزيز',
    'مشعل', 'زيد', 'حمد', 'نواف', 'بدر', 'سلمان', 'عايض', 'صالح',
]
ARABIC_LAST_NAMES = [
    'العتيبي', 'الشمري', 'القحطاني', 'المطيري', 'الحربي', 'الدوسري',
    'الزهراني', 'الغامدي', 'السبيعي', 'الرشيدي', 'البلوي', 'العنزي',
    'الجهني', 'العمري', 'الشهري', 'المالكي', 'الأحمدي', 'الثبيتي',
    'الكناني', 'السلمي',
]

DEPARTMENTS = [
    {'name': 'الإدارة العليا', 'name_en': 'Executive Management'},
    {'name': 'المبيعات', 'name_en': 'Sales'},
    {'name': 'المحاسبة', 'name_en': 'Accounting'},
    {'name': 'الموارد البشرية', 'name_en': 'Human Resources'},
    {'name': 'المخازن والعمليات', 'name_en': 'Warehouse & Operations'},
]

POSITIONS_BY_DEPT = {
    0: ['المدير التنفيذي', 'مدير العمليات', 'مساعد المدير', 'مدير المشاريع', 'مستشار تنفيذي', 'سكرتير تنفيذي'],
    1: ['مدير المبيعات', 'مندوب مبيعات أول', 'مندوب مبيعات', 'مندوب مبيعات', 'منسق المبيعات', 'مندوب مبيعات'],
    2: ['المحاسب الرئيسي', 'محاسب أول', 'محاسب', 'محاسب', 'مراجع حسابات', 'محاسب ضرائب'],
    3: ['مدير الموارد البشرية', 'أخصائي توظيف', 'أخصائي موارد بشرية', 'أخصائي موارد بشرية', 'مندوب رواتب', 'أخصائي تدريب'],
    4: ['مدير المخازن', 'مسؤول مخزن', 'أمين مخزن', 'أمين مخزن', 'مشرف تشغيل', 'سائق توصيل'],
}

SALARIES_BY_LEVEL = {
    'executive': (D('18000'), D('35000'), D('3000'), D('1500')),
    'manager':   (D('12000'), D('18000'), D('2500'), D('1000')),
    'senior':    (D('8000'), D('12000'), D('2000'), D('800')),
    'mid':       (D('5000'), D('8000'), D('1500'), D('600')),
    'junior':    (D('3500'), D('5500'), D('1000'), D('500')),
}

SALARY_LEVELS_BY_DEPT = {
    0: ['executive', 'manager', 'manager', 'senior', 'senior', 'mid'],
    1: ['manager', 'senior', 'mid', 'mid', 'mid', 'junior'],
    2: ['manager', 'senior', 'mid', 'mid', 'mid', 'junior'],
    3: ['manager', 'senior', 'mid', 'mid', 'mid', 'junior'],
    4: ['manager', 'senior', 'mid', 'mid', 'mid', 'junior'],
}

# ─── Chart of Accounts ─────────────────────────────────────────────────
CHART_OF_ACCOUNTS = [
    ('1000', 'الأصول', 'Assets', 'asset', None),
    ('1100', 'النقدية والبنوك', 'Cash & Banks', 'asset', '1000'),
    ('1200', 'المدينون (العملاء)', 'Accounts Receivable', 'asset', '1000'),
    ('1300', 'المخزون', 'Inventory', 'asset', '1000'),
    ('1400', 'المصروفات المدفوعة مقدماً', 'Prepaid Expenses', 'asset', '1000'),
    ('1500', 'الأصول الثابتة', 'Fixed Assets', 'asset', '1000'),
    ('2000', 'الخصوم', 'Liabilities', 'liability', None),
    ('2100', 'الدائنون (الموردين)', 'Accounts Payable', 'liability', '2000'),
    ('2200', 'مصروفات مستحقة', 'Accrued Expenses', 'liability', '2000'),
    ('2300', 'ضريبة القيمة المضافة', 'VAT Payable', 'liability', '2000'),
    ('2400', 'قروض قصيرة الأجل', 'Short-term Loans', 'liability', '2000'),
    ('3000', 'حقوق الملكية', 'Equity', 'equity', None),
    ('3100', 'رأس المال', 'Capital', 'equity', '3000'),
    ('3200', 'الأرباح المحتجزة', 'Retained Earnings', 'equity', '3000'),
    ('4000', 'الإيرادات', 'Income', 'income', None),
    ('4100', 'إيرادات المبيعات', 'Sales Revenue', 'income', '4000'),
    ('4200', 'إيرادات الخدمات', 'Service Revenue', 'income', '4000'),
    ('4300', 'إيرادات أخرى', 'Other Income', 'income', '4000'),
    ('5000', 'المصروفات', 'Expenses', 'expense', None),
    ('5100', 'تكلفة البضاعة المباعة', 'Cost of Goods Sold', 'expense', '5000'),
    ('5200', 'الرواتب والأجور', 'Salaries & Wages', 'expense', '5000'),
    ('5300', 'إيجار المكاتب', 'Rent Expense', 'expense', '5000'),
    ('5400', 'المرافق (كهرباء/ماء)', 'Utilities Expense', 'expense', '5000'),
    ('5500', 'قرطاسية ومستلزمات مكتبية', 'Office Supplies', 'expense', '5000'),
    ('5600', 'صيانة وإصلاحات', 'Maintenance Expense', 'expense', '5000'),
    ('5700', 'نقل وتنقلات', 'Transportation Expense', 'expense', '5000'),
    ('5800', 'التأمينات الاجتماعية', 'GOSI Expense', 'expense', '5000'),
    ('5900', 'إستهلاك الأصول', 'Depreciation Expense', 'expense', '5000'),
    ('5950', 'مصروفات تسويقية', 'Marketing Expense', 'expense', '5000'),
    ('5960', 'مصروفات بنكية', 'Bank Charges', 'expense', '5000'),
]

# ─── CRM Data ──────────────────────────────────────────────────────────
CAMPAIGN_NAMES = [
    ('عرض رمضان 2026', 'email', 'draft', D('15000'), D('0'), D('0'), D('0'), D('0')),
    ('تخفيضات الصيف', 'social_media', 'active', D('25000'), D('18500'), D('450'), D('38'), D('12000')),
    ('عودة المدارس', 'ads', 'completed', D('20000'), D('19800'), D('320'), D('25'), D('35000')),
    ('تطوير الأعمال B2B', 'email', 'active', D('8000'), D('5500'), D('180'), D('12'), D('45000')),
    ('البيئة الخضراء', 'social_media', 'paused', D('5000'), D('3200'), D('250'), D('8'), D('8000')),
    ('معرض الرياض الدولي', 'event', 'completed', D('40000'), D('38500'), D('600'), D('45'), D('85000')),
]


class Command(BaseCommand):
    help = 'Generate realistic seed data for ML analytics (12 months of business data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing data before generating',
        )

    # ── Main handler ──────────────────────────────────────────────────
    def handle(self, *args, **options):
        random.seed(42)
        now = timezone.now()

        with transaction.atomic():
            if options['clear']:
                self._clear_existing_data()

            self.stdout.write('\n  📊 Generating ML seed data...\n')
            self.stdout.write('  ' + '─' * 56)

            # 1 – Departments
            departments = self._gen_departments()
            self._log('Departments', len(departments))

            # 2 – Employees
            employees = self._gen_employees(departments)
            self._log('Employees', len(employees))

            # 3 – Products
            products = self._gen_products()
            self._log('Products', len(products))

            # 4 – Customers
            customers, customer_segments = self._gen_customers()
            self._log('Customers', len(customers))

            # 5 – Suppliers
            suppliers = self._gen_suppliers()
            self._log('Suppliers', len(suppliers))

            # 6 – Chart of accounts
            accounts = self._gen_accounts()
            self._log('Chart of Accounts', len(accounts))

            # 7 – Sales orders + items
            orders, order_items = self._gen_sales_orders(customers, customer_segments, products)
            self._log('Sales Orders', len(orders))
            self._log('Sales Order Items', len(order_items))

            # 8 – Invoices, items, payments
            invoices, inv_items, payments = self._gen_invoices_payments(orders, customers)
            self._log('Invoices', len(invoices))
            self._log('Invoice Items', len(inv_items))
            self._log('Payments', len(payments))

            # 9 – Journal entries + transactions
            je_count, txn_count = self._gen_journal_entries(accounts, orders, payments, employees)
            self._log('Journal Entries', je_count)
            self._log('Transactions', txn_count)

            # 10 – Purchase orders
            po_count, poi_count = self._gen_purchase_orders(suppliers, products)
            self._log('Purchase Orders', po_count)
            self._log('Purchase Order Items', poi_count)

            # 11 – Attendance
            att_count = self._gen_attendance(employees)
            self._log('Attendance Records', att_count)

            # 12 – Payroll
            pp_count, pr_count = self._gen_payroll(employees)
            self._log('Payroll Periods', pp_count)
            self._log('Payroll Records', pr_count)

            # 13 – CRM data
            self._gen_crm_data(customers)
            self._log('CRM Data', 'created')

            # 14 – Deliberate anomalies
            anomaly_count = self._gen_anomalies(accounts)
            self._log('Anomalies (transactions)', anomaly_count)

            self.stdout.write('  ' + '─' * 56)
            self.stdout.write(self.style.SUCCESS('  ✅ Seed data generation complete!\n'))

    # ── Utilities ─────────────────────────────────────────────────────
    def _log(self, label, count):
        self.stdout.write(f'  ✔ {label:<28} {count}')

    def _clear_existing_data(self):
        """Clear all data in reverse dependency order."""
        delete_order = [
            Transaction, JournalEntry,
            Payment, InvoiceItem, Invoice,
            PurchaseOrderItem, PurchaseOrder,
            SalesOrderItem, SalesOrder,
            PayrollRecord, PayrollPeriod,
            Attendance,
            Employee, Department,
            Product,
            Customer,
            Supplier,
            Account,
            Contact, Lead, Campaign,
        ]
        for model in delete_order:
            try:
                qs = model.all_objects.all() if hasattr(model, 'all_objects') else model.objects.all()
                count, _ = qs.delete()
                if count:
                    self.stdout.write(f'    Cleared {count} {model.__name__}')
            except Exception:
                pass  # Table may not exist yet

    def _working_days_in_month(self, year, month):
        """Return list of working-day dates (Sun–Thu) for a month."""
        import calendar
        days = []
        for d in range(1, calendar.monthrange(year, month)[1] + 1):
            dt = datetime.date(year, month, d)
            if dt.weekday() < 5:  # Mon=0 … Sat=5, but Saudi weekend = Fri(4)+Sat(5)
                # Actually: weekday() returns 0=Mon, 4=Fri, 5=Sat
                # Working days: Sun(6) → treated as 6, Mon(0)–Thu(3)
                pass
            # Saudi weekend: Friday=4, Saturday=5 → NOT working
            if dt.weekday() not in (4, 5):
                days.append(dt)
        return days

    def _month_range(self, month_idx):
        """Return (year, month) for month_idx (0=June2025 … 11=May2026)."""
        m = (START_DATE.month - 1 + month_idx) % 12 + 1
        y = START_DATE.year + (START_DATE.month - 1 + month_idx) // 12
        return y, m

    # ── 1. Departments ────────────────────────────────────────────────
    def _gen_departments(self):
        objs = []
        for d in DEPARTMENTS:
            objs.append(Department(
                name=d['name'], name_en=d['name_en'],
                is_active=True,
            ))
        return Department.objects.bulk_create(objs)

    # ── 2. Employees ──────────────────────────────────────────────────
    def _gen_employees(self, departments):
        objs = []
        emp_idx = 0
        for dept_idx, dept in enumerate(departments):
            positions = POSITIONS_BY_DEPT[dept_idx]
            levels = SALARY_LEVELS_BY_DEPT[dept_idx]
            for i, pos in enumerate(positions):
                level = levels[i] if i < len(levels) else 'mid'
                sal_range = SALARIES_BY_LEVEL[level]
                salary = Q(random.randint(int(sal_range[0]), int(sal_range[1])))
                housing = Q(random.randint(int(float(sal_range[2]) * 0.8), int(float(sal_range[2]) * 1.2)))
                transport = Q(random.randint(int(float(sal_range[3]) * 0.8), int(float(sal_range[3]) * 1.2)))
                hire_month = random.randint(1, 24)  # months ago
                hire_date = START_DATE - datetime.timedelta(days=hire_month * 30)

                objs.append(Employee(
                    employee_number=f'EMP-{emp_idx + 1:04d}',
                    first_name=ARABIC_FIRST_NAMES[emp_idx % len(ARABIC_FIRST_NAMES)],
                    last_name=ARABIC_LAST_NAMES[emp_idx % len(ARABIC_LAST_NAMES)],
                    email=f'employee{emp_idx + 1}@riadah.sa',
                    phone=f'05{random.randint(10000000, 99999999)}',
                    gender='male' if random.random() > 0.2 else 'female',
                    department=dept,
                    position=pos,
                    hire_date=hire_date,
                    salary=salary,
                    housing_allowance=housing,
                    transport_allowance=transport,
                    status='active',
                    is_active=True,
                    bank_name=random.choice(['البنك الأهلي', 'بنك الراجحي', 'بنك ساب', 'البنك السعودي الفرنسي']),
                    bank_account=f'SA{random.randint(10, 99)}{random.randint(1000000000, 9999999999)}',
                    national_id=f'{random.randint(1000000000, 2999999999)}',
                ))
                emp_idx += 1
        return Employee.objects.bulk_create(objs)

    # ── 3. Products ───────────────────────────────────────────────────
    def _gen_products(self):
        objs = []
        for name, sku, price, qty, reorder in PRODUCTS:
            objs.append(Product(
                name=name, sku=sku,
                description=f'منتج: {name}',
                unit_price=price,
                quantity=qty,
                reorder_level=reorder,
                is_active=True,
            ))
        return Product.objects.bulk_create(objs)

    # ── 4. Customers ──────────────────────────────────────────────────
    def _gen_customers(self):
        """Create 50 customers with segment assignments.
        Returns (customers_list, segment_dict).
        segment_dict: {segment_name: [customer_obj, ...]}
        """
        objs = []
        for i, name in enumerate(CUSTOMER_NAMES):
            email_domain = random.choice(['company.sa', 'trade.sa', 'biz.sa', 'est.sa'])
            objs.append(Customer(
                name=name,
                email=f'contact{i + 1}@{email_domain}',
                phone=f'01{random.randint(1000000, 9999999)}',
                address=f'الرياض، حي العليا، شارع {random.choice(["الأمير محمد", "فيصل", "تحت الربوة", "العليا", "الملك فهد"])}',
                is_active=True,
            ))
        customers = Customer.objects.bulk_create(objs)

        # Segment assignment:
        # 0-4: VIP (5), 5-19: regular (15), 20-29: occasional (10),
        # 30-39: new (10), 40-49: at-risk (10)
        segments = {
            'vip': customers[0:5],
            'regular': customers[5:20],
            'occasional': customers[20:30],
            'new': customers[30:40],
            'at_risk': customers[40:50],
        }
        # Mark at-risk customers as inactive
        Customer.objects.filter(id__in=[c.id for c in segments['at_risk']]).update(is_active=False)
        return customers, segments

    # ── 5. Suppliers ──────────────────────────────────────────────────
    def _gen_suppliers(self):
        objs = []
        for name, name_en, email in SUPPLIER_NAMES:
            objs.append(Supplier(
                name=name, name_en=name_en,
                contact_person=f'{random.choice(ARABIC_FIRST_NAMES)} {random.choice(ARABIC_LAST_NAMES)}',
                email=email,
                phone=f'01{random.randint(1000000, 9999999)}',
                address='الرياض، المنطقة الصناعية الثانية',
                tax_number=f'30{random.randint(10 ** 13, 30 ** 13 - 1)}',
                is_active=True,
                balance=Q(random.randint(5000, 50000)),
            ))
        return Supplier.objects.bulk_create(objs)

    # ── 6. Chart of Accounts ──────────────────────────────────────────
    def _gen_accounts(self):
        if Account.objects.exists():
            return list(Account.objects.all())

        # Build hierarchy: top-level first, then children
        parent_map = {}
        all_accounts = []

        # Parse chart into levels
        top_level = [(c, n, ne, a, p) for c, n, ne, a, p in CHART_OF_ACCOUNTS if p is None]
        child_level = [(c, n, ne, a, p) for c, n, ne, a, p in CHART_OF_ACCOUNTS if p is not None]

        # Save top-level accounts first
        for code, name, name_en, atype, parent_code in top_level:
            obj = Account(code=code, name=name, name_en=name_en, account_type=atype, is_active=True)
            obj.save()
            parent_map[code] = obj
            all_accounts.append(obj)

        # Save child accounts with parent reference
        for code, name, name_en, atype, parent_code in child_level:
            parent = parent_map.get(parent_code)
            obj = Account(code=code, name=name, name_en=name_en, account_type=atype, parent=parent, is_active=True)
            obj.save()
            parent_map[code] = obj
            all_accounts.append(obj)

        return all_accounts

    # ── 7. Sales Orders + Items ──────────────────────────────────────
    def _gen_sales_orders(self, customers, segments, products):
        """Generate 500+ sales orders with seasonal patterns."""
        product_by_sku = {p.sku: p for p in products}
        all_orders = []
        all_items = []
        so_seq = 1

        for month_idx in range(12):
            y, m = self._month_range(month_idx)
            working_days = self._working_days_in_month(y, m)

            # Calculate order count for this month
            growth = float(MONTHLY_GROWTH ** month_idx)
            season = MONTH_MULTIPLIERS[m]
            noise = 1 + random.uniform(-0.10, 0.10)
            order_count = max(5, int(BASE_MONTHLY_ORDERS * growth * season * noise))

            # Build customer pool for this month
            pool = []
            weights = []
            # VIP always available
            pool.extend(segments['vip'])
            weights.extend([5] * len(segments['vip']))
            # Regular always available
            pool.extend(segments['regular'])
            weights.extend([3] * len(segments['regular']))
            # Occasional
            pool.extend(segments['occasional'])
            weights.extend([1] * len(segments['occasional']))
            # New customers: active in last 3 months (months 9-11)
            if month_idx >= 9:
                pool.extend(segments['new'])
                weights.extend([2] * len(segments['new']))
            # At-risk: active in first 6 months only
            if month_idx <= 6:
                pool.extend(segments['at_risk'])
                weights.extend([2] * len(segments['at_risk']))

            if not pool:
                continue

            for _ in range(order_count):
                # Pick a working day, weighted towards month start
                day = random.choice(working_days)
                cust = random.choices(pool, weights=weights, k=1)[0]

                # Determine order value tier by customer segment
                if cust in segments['vip']:
                    avg_value = random.uniform(8000, 25000)
                    num_items = random.randint(3, 6)
                elif cust in segments['regular']:
                    avg_value = random.uniform(2000, 10000)
                    num_items = random.randint(2, 5)
                elif cust in segments['new']:
                    avg_value = random.uniform(1000, 8000)
                    num_items = random.randint(1, 4)
                else:
                    avg_value = random.uniform(500, 5000)
                    num_items = random.randint(1, 3)

                order_num = f'SO-{day.strftime("%Y%m%d")}-{so_seq:04d}'
                so_seq += 1

                order = SalesOrder(
                    order_number=order_num,
                    customer=cust,
                    status=random.choices(
                        ['delivered', 'shipped', 'confirmed', 'cancelled'],
                        weights=[70, 15, 10, 5], k=1
                    )[0],
                    order_date=day,
                    total_amount=D('0'),
                )
                all_orders.append(order)

                # Select products for items (respect unique_together)
                chosen_products = random.choices(
                    FAST_MOVING_SKUS + MEDIUM_MOVING_SKUS + SLOW_MOVING_SKUS,
                    weights=([6] * len(FAST_MOVING_SKUS) +
                             [3] * len(MEDIUM_MOVING_SKUS) +
                             [1] * len(SLOW_MOVING_SKUS)),
                    k=num_items
                )
                # Remove duplicates
                seen = set()
                unique_skus = []
                for s in chosen_products:
                    if s not in seen:
                        seen.add(s)
                        unique_skus.append(s)

                total = D('0')
                for sku in unique_skus:
                    prod = product_by_sku[sku]
                    # Service products (SERV-*) have qty=1 always
                    if sku.startswith('SERV'):
                        qty = 1
                    else:
                        qty = random.randint(1, 20)
                    unit_price = prod.unit_price * Q(random.uniform(0.95, 1.05))
                    subtotal = Q(qty * unit_price)
                    total += subtotal

                    all_items.append(SalesOrderItem(
                        order=order, product=prod,
                        quantity=qty,
                        unit_price=unit_price,
                        subtotal=subtotal,
                    ))

                order.total_amount = Q(total)

        # Bulk create
        SalesOrder.objects.bulk_create(all_orders, batch_size=500)
        SalesOrderItem.objects.bulk_create(all_items, batch_size=500)
        return all_orders, all_items

    # ── 8. Invoices, Items, Payments ─────────────────────────────────
    def _gen_invoices_payments(self, orders, customers):
        """Generate 300+ invoices and 200+ payments."""
        # Create invoices for delivered & shipped orders (~60%)
        invoiceable = [o for o in orders if o.status in ('delivered', 'shipped')]
        random.shuffle(invoiceable)
        selected = invoiceable[:max(300, int(len(invoiceable) * 0.6))]

        invoices = []
        inv_items = []
        inv_seq = 1

        for order in selected:
            issue_date = order.order_date + datetime.timedelta(days=random.randint(0, 3))
            due_date = issue_date + datetime.timedelta(days=30)

            # Calculate subtotal from order items
            order_subtotal = sum(item.subtotal for item in order.items.all()) if hasattr(order, 'items') else D('0')

            # For simplicity, recalc from items that exist
            subtotal = D('0')
            for item in all_items if False else []:
                pass
            subtotal = order.total_amount  # Use order total as base

            inv_number = f'INV-{issue_date.strftime("%Y%m%d")}-{inv_seq:04d}'
            inv_seq += 1

            inv = Invoice(
                invoice_number=inv_number,
                invoice_type='sales',
                sales_order=order,
                customer=order.customer,
                issue_date=issue_date,
                due_date=due_date,
                subtotal=Q(subtotal),
                discount_type='percentage',
                discount_value=D('0'),
                discount_amount=D('0'),
                vat_rate=D('15.00'),
                vat_amount=Q(subtotal * D('0.15')),
                total_after_discount=Q(subtotal),
                total_amount=Q(subtotal * D('1.15')),
                currency='SAR',
                payment_status='unpaid',
                paid_amount=D('0'),
                status='sent',
                company_tax_number='300000000000003',
            )
            invoices.append(inv)

            # Create invoice items from order items
            for oitem in SalesOrderItem.objects.filter(order=order):
                inv_items.append(InvoiceItem(
                    invoice=inv,
                    product=oitem.product,
                    description=oitem.product_name or '',
                    quantity=D(oitem.quantity),
                    unit_price=oitem.unit_price,
                    unit='piece',
                    discount_type='percentage',
                    discount_value=D('0'),
                    vat_rate=D('0'),  # No item-level VAT (invoice-level only)
                    subtotal=Q(oitem.quantity * oitem.unit_price),
                    vat_amount=D('0'),
                    total=Q(oitem.quantity * oitem.unit_price),
                ))

        Invoice.objects.bulk_create(invoices, batch_size=200)
        InvoiceItem.objects.bulk_create(inv_items, batch_size=500)

        # Generate payments based on patterns:
        # 60% paid on time, 20% late, 10% partial, 5% overdue, 5% long overdue
        payments = []
        pay_seq = 1

        for i, inv in enumerate(invoices):
            roll = random.random()
            if roll < 0.60:
                # Paid on time
                pay_date = inv.issue_date + datetime.timedelta(days=random.randint(0, 30))
                pay_amount = inv.total_amount
                inv.payment_status = 'paid'
                inv.paid_amount = inv.total_amount
                inv.status = 'paid'
            elif roll < 0.80:
                # Paid late (1-15 days after due)
                pay_date = inv.due_date + datetime.timedelta(days=random.randint(1, 15))
                pay_amount = inv.total_amount
                inv.payment_status = 'paid'
                inv.paid_amount = inv.total_amount
                inv.status = 'paid'
            elif roll < 0.90:
                # Partially paid (30-70% of total)
                pay_date = inv.issue_date + datetime.timedelta(days=random.randint(5, 25))
                pay_amount = Q(inv.total_amount * D(random.uniform(0.30, 0.70)))
                inv.payment_status = 'partially_paid'
                inv.paid_amount = pay_amount
                inv.status = 'partially_paid'
            elif roll < 0.95:
                # Overdue (>30 days)
                # No payment yet
                inv.payment_status = 'overdue'
                continue  # No payment for this invoice
            else:
                # Long overdue (>60 days) – no payment
                inv.payment_status = 'overdue'
                continue

            pay_number = f'PAY-{pay_date.strftime("%Y%m%d")}-{pay_seq:04d}'
            pay_seq += 1
            payments.append(Payment(
                payment_number=pay_number,
                invoice=inv,
                amount=pay_amount,
                payment_method=random.choice(['bank_transfer', 'cash', 'card', 'online']),
                payment_date=pay_date,
                reference_number=f'REF-{random.randint(100000, 999999)}',
                bank_name=random.choice(['البنك الأهلي', 'بنك الراجحي', 'بنك ساب']),
                notes='',
            ))

        Payment.objects.bulk_create(payments, batch_size=200)
        # Update invoices with payment info
        for inv in invoices:
            inv.save(update_fields=['payment_status', 'paid_amount', 'status'])

        return invoices, inv_items, payments

    # ── 9. Journal Entries + Transactions ─────────────────────────────
    def _gen_journal_entries(self, accounts, orders, payments, employees):
        """Generate 1000+ transactions via journal entries."""
        acct_map = {a.code: a for a in accounts}
        now_ts = timezone.now()

        all_entries = []
        all_transactions = []
        je_seq = 1

        # A) Journal entries for each sales order (debit AR, credit Revenue)
        delivered_orders = [o for o in orders if o.status in ('delivered', 'shipped')]
        for order in delivered_orders:
            entry_num = f'JE-{order.order_date.strftime("%Y%m%d")}-{je_seq:04d}'
            je_seq += 1
            amt = order.total_amount
            all_entries.append(JournalEntry(
                entry_number=entry_num,
                entry_type='sale',
                description=f'مبيعات - {order.order_number}',
                reference=order.order_number,
                entry_date=order.order_date,
                is_posted=True,
                sales_order=order,
                created_at=now_ts, updated_at=now_ts,
            ))
            entry = all_entries[-1]
            # Debit: Accounts Receivable
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['1200'],
                transaction_type='debit',
                amount=amt,
                description=f'مدين: {order.customer.name}',
            ))
            # Credit: Sales Revenue
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['4100'],
                transaction_type='credit',
                amount=amt,
                description=f'إيراد مبيعات: {order.order_number}',
            ))

        # B) Monthly expense entries (various expense types)
        expense_accounts = [
            ('5300', 'إيجار شهري', 7500),
            ('5400', 'فاتورة كهرباء', 3500),
            ('5400', 'فاتورة مياه', 1200),
            ('5500', 'قرطمية مكتبية', 800),
            ('5600', 'صيانة مكاتب', 2000),
            ('5700', 'نقل وتنقلات', 1500),
            ('5800', 'تأمينات اجتماعية', 0),  # will calculate
            ('5900', 'إستهلاك أصول', 4000),
            ('5950', 'مصروفات تسويقية', 3000),
            ('5960', 'مصروفات بنكية', 500),
        ]

        for month_idx in range(12):
            y, m = self._month_range(month_idx)
            last_day = datetime.date(y, m, 28)  # Safe end of month

            # Calculate GOSI based on employee count
            month_start = datetime.date(y, m, 1)
            active_emps = [e for e in employees if e.hire_date <= month_start]
            gosi_total = sum(Q(e.salary * D('0.0975')) for e in active_emps)

            for code, desc, base_amount in expense_accounts:
                if code == '5800':
                    amt = gosi_total
                else:
                    growth = 1 + (month_idx * 0.01)  # slight increase
                    amt = Q(base_amount * D(growth) * D(random.uniform(0.85, 1.15)))

                entry_num = f'JE-{last_day.strftime("%Y%m%d")}-{je_seq:04d}'
                je_seq += 1
                all_entries.append(JournalEntry(
                    entry_number=entry_num,
                    entry_type='manual',
                    description=desc,
                    entry_date=last_day,
                    is_posted=True,
                    created_at=now_ts, updated_at=now_ts,
                ))
                entry = all_entries[-1]
                # Debit expense account
                all_transactions.append(Transaction(
                    journal_entry=entry,
                    account=acct_map[code],
                    transaction_type='debit',
                    amount=amt,
                    description=desc,
                ))
                # Credit Cash
                all_transactions.append(Transaction(
                    journal_entry=entry,
                    account=acct_map['1100'],
                    transaction_type='credit',
                    amount=amt,
                    description=f'دفعة: {desc}',
                ))

        # C) Payroll journal entries (one per payroll month: Dec-May)
        payroll_months = [(2025, 12), (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5)]
        for py, pm in payroll_months:
            month_start = datetime.date(py, pm, 1)
            active_emps = [e for e in employees if e.hire_date <= month_start]
            total_net = sum(e.total_salary for e in active_emps)
            gosi_employer = sum(Q(e.salary * D('0.115')) for e in active_emps)
            total_payroll = total_net + gosi_employer

            last_day = datetime.date(py, pm, 27)
            entry_num = f'JE-{last_day.strftime("%Y%m%d")}-{je_seq:04d}'
            je_seq += 1
            all_entries.append(JournalEntry(
                entry_number=entry_num,
                entry_type='manual',
                description=f'رواتب ومستحقات {pm}/{py}',
                entry_date=last_day,
                is_posted=True,
                created_at=now_ts, updated_at=now_ts,
            ))
            entry = all_entries[-1]
            # Debit salaries
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['5200'],
                transaction_type='debit',
                amount=Q(total_payroll),
                description=f'رواتب شهر {pm}/{py} - {len(active_emps)} موظف',
            ))
            # Credit Cash
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['1100'],
                transaction_type='credit',
                amount=Q(total_net),
                description=f'صافي رواتب شهر {pm}/{py}',
            ))
            # Credit GOSI payable (employer portion)
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['2400'],
                transaction_type='credit',
                amount=gosi_employer,
                description=f'حصة صاحب العمل GOSI {pm}/{py}',
            ))

        # D) Purchase order journal entries
        # (We'll create generic monthly purchase entries)
        for month_idx in range(12):
            y, m = self._month_range(month_idx)
            mid_day = datetime.date(y, m, 15)
            season = MONTH_MULTIPLIERS[m]
            growth = float(MONTHLY_GROWTH ** month_idx)
            purchase_amount = Q(20000 * growth * season * random.uniform(0.8, 1.2))

            entry_num = f'JE-{mid_day.strftime("%Y%m%d")}-{je_seq:04d}'
            je_seq += 1
            all_entries.append(JournalEntry(
                entry_number=entry_num,
                entry_type='manual',
                description=f'مشتريات شهر {m}/{y}',
                entry_date=mid_day,
                is_posted=True,
                created_at=now_ts, updated_at=now_ts,
            ))
            entry = all_entries[-1]
            # Debit Inventory / COGS
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['1300'],
                transaction_type='debit',
                amount=purchase_amount,
                description=f'مشتريات بضاعة شهر {m}/{y}',
            ))
            # Credit AP
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['2100'],
                transaction_type='credit',
                amount=purchase_amount,
                description=f'موردون - مشتريات شهر {m}/{y}',
            ))

        # Bulk create
        JournalEntry.objects.bulk_create(all_entries, batch_size=500)
        Transaction.objects.bulk_create(all_transactions, batch_size=500)
        return len(all_entries), len(all_transactions)

    # ── 10. Purchase Orders ───────────────────────────────────────────
    def _gen_purchase_orders(self, suppliers, products):
        """Generate 30 purchase orders."""
        product_by_sku = {p.sku: p for p in products}
        all_pos = []
        all_pois = []
        po_seq = 1

        for month_idx in range(12):
            y, m = self._month_range(month_idx)
            # 2-3 POs per month
            num_pos = 2 if month_idx < 10 else 3

            for _ in range(num_pos):
                supplier = random.choice(suppliers)
                day = random.randint(1, 25)
                order_date = datetime.date(y, m, day)
                expected_date = order_date + datetime.timedelta(days=random.randint(7, 30))

                order_num = f'PO-{order_date.strftime("%Y%m%d")}-{po_seq:04d}'
                po_seq += 1

                status = random.choices(
                    ['received', 'confirmed', 'partial', 'draft'],
                    weights=[50, 25, 15, 10], k=1
                )[0]

                po = PurchaseOrder(
                    order_number=order_num,
                    supplier=supplier,
                    status=status,
                    order_date=order_date,
                    expected_date=expected_date,
                    total_amount=D('0'),
                )
                all_pos.append(po)

                # 2-5 items per PO
                num_items = random.randint(2, 5)
                chosen = random.sample(list(product_by_sku.values()), min(num_items, len(products)))
                total = D('0')
                for prod in chosen:
                    qty = random.randint(10, 200)
                    unit_price = Q(prod.unit_price * D(random.uniform(0.6, 0.85)))  # Purchase price
                    subtotal = Q(qty * unit_price)
                    total += subtotal
                    received = qty if status == 'received' else (int(qty * 0.6) if status == 'partial' else 0)

                    all_pois.append(PurchaseOrderItem(
                        order=po, product=prod,
                        quantity=qty,
                        unit_price=unit_price,
                        subtotal=subtotal,
                        received_quantity=received,
                    ))
                po.total_amount = Q(total)

        PurchaseOrder.objects.bulk_create(all_pos, batch_size=100)
        PurchaseOrderItem.objects.bulk_create(all_pois, batch_size=200)
        return len(all_pos), len(all_pois)

    # ── 11. Attendance ────────────────────────────────────────────────
    def _gen_attendance(self, employees):
        """Generate 6 months of attendance records (Dec 2025 – May 2026)."""
        import calendar
        all_att = []
        start_y, start_m = 2025, 12
        end_y, end_m = 2026, 5

        current_y, current_m = start_y, start_m
        while (current_y, current_m) <= (end_y, end_m):
            days_in_month = calendar.monthrange(current_y, current_m)[1]
            for day in range(1, days_in_month + 1):
                dt = datetime.date(current_y, current_m, day)
                # Skip weekends (Friday=4, Saturday=5 in weekday())
                if dt.weekday() in (4, 5):
                    continue

                for emp in employees:
                    if emp.hire_date > dt:
                        continue

                    roll = random.random()
                    if roll < 0.80:
                        status = 'present'
                        check_in = datetime.time(random.randint(7, 8), random.randint(0, 59))
                        check_out = datetime.time(random.randint(16, 17), random.randint(0, 59))
                    elif roll < 0.88:
                        status = 'late'
                        check_in = datetime.time(random.randint(8, 10), random.randint(0, 59))
                        check_out = datetime.time(random.randint(16, 18), random.randint(0, 59))
                    elif roll < 0.92:
                        status = 'half_day'
                        check_in = datetime.time(random.randint(7, 8), random.randint(0, 59))
                        check_out = datetime.time(random.randint(12, 13), random.randint(0, 59))
                    elif roll < 0.94:
                        status = 'absent'
                        check_in, check_out = None, None
                    else:
                        status = 'holiday'
                        check_in, check_out = None, None

                    all_att.append(Attendance(
                        employee=emp,
                        date=dt,
                        check_in=check_in,
                        check_out=check_out,
                        status=status,
                    ))

            # Advance month
            if current_m == 12:
                current_m = 1
                current_y += 1
            else:
                current_m += 1

        Attendance.objects.bulk_create(all_att, batch_size=1000)
        return len(all_att)

    # ── 12. Payroll ───────────────────────────────────────────────────
    def _gen_payroll(self, employees):
        """Generate 6 payroll periods with records."""
        periods_data = [
            (2025, 12, 'ديسمبر 2025'),
            (2026, 1, 'يناير 2026'),
            (2026, 2, 'فبراير 2026'),
            (2026, 3, 'مارس 2026'),
            (2026, 4, 'أبريل 2026'),
            (2026, 5, 'مايو 2026'),
        ]

        import calendar
        all_periods = []
        all_records = []

        for y, m, name in periods_data:
            month_start = datetime.date(y, m, 1)
            days_in_month = calendar.monthrange(y, m)[1]
            month_end = datetime.date(y, m, days_in_month)
            pay_day = min(28, days_in_month)

            period = PayrollPeriod(
                name=name, month=m, year=y,
                start_date=month_start,
                end_date=month_end,
                status=random.choices(
                    ['paid', 'closed', 'processing', 'draft'],
                    weights=[50, 30, 15, 5], k=1
                )[0],
                total_employees=0,
                total_salaries=D('0'),
                total_deductions=D('0'),
                total_net=D('0'),
                created_at=timezone.now(), updated_at=timezone.now(),
            )
            all_periods.append(period)

            for emp in employees:
                if emp.hire_date > month_end:
                    continue

                basic = emp.salary
                housing = emp.housing_allowance
                transport = emp.transport_allowance
                food = Q(random.randint(300, 800))
                overtime_hrs = Q(random.uniform(0, 15))
                overtime_amt = Q(overtime_hrs * basic / 174 * D('1.5'))  # 1.5x rate
                bonus = D('0')
                commission = D('0')
                if random.random() < 0.10:
                    bonus = Q(basic * D(random.uniform(0.1, 0.5)))

                total_earnings = basic + housing + transport + food + overtime_amt + bonus + commission

                gosi = Q(basic * D('0.0975'))
                tax = D('0')
                absence = D('0')
                loan = D('0')
                other = D('0')

                # Check for absences
                absences = Attendance.objects.filter(
                    employee=emp, date__year=y, date__month=m, status='absent'
                ).count()
                if absences > 0:
                    daily_rate = basic / D('30')
                    absence = Q(daily_rate * absences)

                if random.random() < 0.15:
                    loan = Q(basic * D(random.uniform(0.05, 0.15)))

                total_deductions = gosi + tax + absence + loan + other
                net = total_earnings - total_deductions

                payment_method = random.choices(
                    ['bank_transfer', 'cash', 'cheque'],
                    weights=[85, 10, 5], k=1
                )[0]

                all_records.append(PayrollRecord(
                    period=period,
                    employee=emp,
                    basic_salary=basic,
                    housing_allowance=housing,
                    transport_allowance=transport,
                    food_allowance=food,
                    overtime_hours=overtime_hrs,
                    overtime_amount=overtime_amt,
                    bonus=bonus,
                    commission=commission,
                    deductions_gosi=gosi,
                    deductions_tax=tax,
                    deductions_absence=absence,
                    deductions_loan=loan,
                    deductions_other=other,
                    total_earnings=total_earnings,
                    total_deductions_amount=total_deductions,
                    net_salary=net,
                    payment_method=payment_method,
                    payment_status=random.choices(
                        ['paid', 'pending', 'partially_paid'],
                        weights=[70, 25, 5], k=1
                    )[0],
                    payment_date=month_end if payment_method == 'bank_transfer' else None,
                    bank_reference=f'BREF{random.randint(100000, 999999)}' if payment_method == 'bank_transfer' else '',
                    created_at=timezone.now(), updated_at=timezone.now(),
                ))

        PayrollPeriod.objects.bulk_create(all_periods)
        PayrollRecord.objects.bulk_create(all_records, batch_size=200)

        # Update period totals
        for period in all_periods:
            records = [r for r in all_records if r.period_id == period.id]
            period.total_employees = len(records)
            period.total_salaries = sum(r.total_earnings for r in records)
            period.total_deductions = sum(r.total_deductions_amount for r in records)
            period.total_net = sum(r.net_salary for r in records)
        PayrollPeriod.objects.bulk_update(
            all_periods,
            ['total_employees', 'total_salaries', 'total_deductions', 'total_net'],
            batch_size=100,
        )
        return len(all_periods), len(all_records)

    # ── 13. CRM Data ──────────────────────────────────────────────────
    def _gen_crm_data(self, customers):
        """Generate contacts, leads, and campaigns."""
        # Contacts
        contacts = []
        for i, cust in enumerate(customers[:20]):
            contacts.append(Contact(
                first_name=f'{ARABIC_FIRST_NAMES[i % len(ARABIC_FIRST_NAMES)]}',
                last_name=f'{ARABIC_LAST_NAMES[i % len(ARABIC_LAST_NAMES)]}',
                email=cust.email or f'contact{i}@crm.sa',
                phone=cust.phone,
                mobile=f'05{random.randint(10000000, 99999999)}',
                company=cust.name,
                position=random.choice(['مدير المشتريات', 'المدير المالي', 'مدير عام', 'مسؤول عقود']),
                source=random.choice(['website', 'referral', 'social_media', 'event']),
                status=random.choices(['active', 'inactive', 'lost'], weights=[70, 20, 10], k=1)[0],
            ))
        Contact.objects.bulk_create(contacts, batch_size=100)

        # Leads
        leads = []
        for i, contact in enumerate(contacts[:15]):
            month_idx = random.randint(0, 11)
            y, m = self._month_range(month_idx)
            leads.append(Lead(
                title=f'فرصة بيع - {contact.company}',
                contact=contact,
                value=Q(random.uniform(10000, 150000)),
                probability=random.randint(10, 90),
                expected_close_date=datetime.date(y, m, random.randint(15, 28)),
                status=random.choices(
                    ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost'],
                    weights=[10, 15, 15, 15, 10, 25, 10], k=1
                )[0],
                pipeline_stage=random.choices(
                    ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost'],
                    weights=[15, 20, 20, 15, 20, 10], k=1
                )[0],
                source=contact.source,
            ))
        Lead.objects.bulk_create(leads, batch_size=100)

        # Campaigns
        campaigns = []
        for i, (name, ctype, status, budget, cost, leads_cnt, conv, rev) in enumerate(CAMPAIGN_NAMES):
            y, m = self._month_range(random.randint(0, 11))
            start_date = datetime.date(y, m, 1)
            end_date = start_date + datetime.timedelta(days=random.randint(14, 60))
            campaigns.append(Campaign(
                name=name,
                description=f'حملة تسويقية - {name}',
                campaign_type=ctype,
                status=status,
                start_date=start_date,
                end_date=end_date if status in ('completed',) else None,
                budget=budget,
                actual_cost=cost,
                target_audience=random.choice(['جميع العملاء', 'عملاء VIP', 'قطاع الأعمال', 'قطاع الأفراد']),
            ))
        Campaign.objects.bulk_create(campaigns, batch_size=50)

    # ── 14. Deliberate Anomalies ──────────────────────────────────────
    def _gen_anomalies(self, accounts):
        """Insert 5-8 deliberate anomalies for ML anomaly detection."""
        acct_map = {a.code: a for a in accounts}
        now_ts = timezone.now()
        all_entries = []
        all_transactions = []
        je_seq = JournalEntry.objects.count() + 1

        anomaly_descriptions = []

        # 1-3: Expense transactions with 5-10x normal amounts
        expense_anomalies = [
            ('5300', 'إيجار مكتب إضافي - شهادة', D('75000'), '2025-11-15'),     # Normal: 7,500
            ('5400', 'فاتورة كهرباء استثنائية', D('45000'), '2026-01-20'),       # Normal: 3,500
            ('5600', 'صيانة طارئة لمبنى', D('38000'), '2026-03-10'),             # Normal: 2,000
        ]
        for code, desc, amt, date_str in expense_anomalies:
            dt = datetime.date.fromisoformat(date_str)
            entry_num = f'JE-{dt.strftime("%Y%m%d")}-ANOM-{len(all_entries) + 1:04d}'
            entry = JournalEntry(
                entry_number=entry_num,
                entry_type='manual',
                description=desc,
                entry_date=dt,
                is_posted=True,
                created_at=now_ts, updated_at=now_ts,
            )
            all_entries.append(entry)
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map[code],
                transaction_type='debit',
                amount=amt,
                description=f'⚠️ ANOMALY: {desc} (المبلغ غير طبيعي)',
            ))
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['1100'],
                transaction_type='credit',
                amount=amt,
                description=f'⚠️ ANOMALY: دفعة مقابلة - {desc}',
            ))
            anomaly_descriptions.append(f'  ⚠ Expense anomaly: {desc} = {amt} SAR (code={code})')

        # 4-5: Sales revenue entries with 3x normal daily average
        sales_anomalies = [
            (D('180000'), '2026-02-18', 'مبيعات نقدية كبيرة - معرض'),   # ~3x normal daily
            (D('150000'), '2026-03-25', 'صفقة خاصة - عميل جديد VIP'),     # ~3x normal daily
        ]
        for amt, date_str, desc in sales_anomalies:
            dt = datetime.date.fromisoformat(date_str)
            entry_num = f'JE-{dt.strftime("%Y%m%d")}-ANOM-{len(all_entries) + 1:04d}'
            entry = JournalEntry(
                entry_number=entry_num,
                entry_type='sale',
                description=desc,
                entry_date=dt,
                is_posted=True,
                created_at=now_ts, updated_at=now_ts,
            )
            all_entries.append(entry)
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['1200'],
                transaction_type='debit',
                amount=amt,
                description=f'⚠️ ANOMALY: {desc}',
            ))
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['4100'],
                transaction_type='credit',
                amount=amt,
                description=f'⚠️ ANOMALY: إيراد - {desc}',
            ))
            anomaly_descriptions.append(f'  ⚠ Sales anomaly: {desc} = {amt} SAR')

        # 6-7: Payment anomalies (suspicious round amounts)
        payment_anomalies = [
            (D('250000'), '2026-04-01', 'دفعة نقدية مشتبهة - مبلغ مقطوع'),
            (D('100000'), '2026-04-15', 'تحويل بنكي غير معتاد - مبلغ دقيق'),
        ]
        for amt, date_str, desc in payment_anomalies:
            dt = datetime.date.fromisoformat(date_str)
            entry_num = f'JE-{dt.strftime("%Y%m%d")}-ANOM-{len(all_entries) + 1:04d}'
            entry = JournalEntry(
                entry_number=entry_num,
                entry_type='payment',
                description=desc,
                entry_date=dt,
                is_posted=True,
                created_at=now_ts, updated_at=now_ts,
            )
            all_entries.append(entry)
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['1100'],
                transaction_type='debit',
                amount=amt,
                description=f'⚠️ ANOMALY: {desc}',
            ))
            all_transactions.append(Transaction(
                journal_entry=entry,
                account=acct_map['1200'],
                transaction_type='credit',
                amount=amt,
                description=f'⚠️ ANOMALY: تحصيل مشبوه - {desc}',
            ))
            anomaly_descriptions.append(f'  ⚠ Payment anomaly: {desc} = {amt} SAR')

        JournalEntry.objects.bulk_create(all_entries)
        Transaction.objects.bulk_create(all_transactions)

        self.stdout.write('\n  🔴 Deliberate anomalies injected:')
        for d in anomaly_descriptions:
            self.stdout.write(self.style.WARNING(d))

        return len(all_transactions)
