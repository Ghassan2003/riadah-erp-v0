"""
نماذج إدارة علاقات العملاء (CRM) لنظام ERP.
يتضمن الشركات، جهات الاتصال، فرص البيع، أنشطة الفرص، شرائح العملاء، الحملات التسويقية، وأنشطة الحملات.

=== ملاحظة التهجير (Migration Note) ===
تم إضافة نموذج Company (الشركة/الحساب) في هذا التحديث.
- تم إضافة نموذج Company جديد بعلاقات كاملة.
- تم إضافة حقل company_account (ForeignKey) إلى نموذج Contact (nullable=True) للحفاظ على التوافق العكسي.
- حقل company الأصلي (CharField) على Contact بقي كما هو دون تغيير لضمان التوافقية.
- يجب تشغيل: python manage.py makemigrations crm && python manage.py migrate
=============================================
"""

from django.db import models
from django.utils import timezone


# =============================================
# نموذج الشركة / الحساب
# =============================================

class Company(models.Model):
    """شركة / حساب - Company / Account"""

    COMPANY_TYPE_CHOICES = (
        ('customer', 'عميل'),
        ('partner', 'شريك'),
        ('vendor', 'مورد'),
        ('competitor', 'منافس'),
        ('other', 'أخرى'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم الشركة',
        db_index=True,
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='الاسم بالإنجليزية',
    )
    industry = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='القطاع الصناعي',
    )
    website = models.URLField(
        blank=True,
        default='',
        verbose_name='الموقع الإلكتروني',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='الهاتف',
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name='البريد الإلكتروني',
    )
    address = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='العنوان',
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='المدينة',
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='البلد',
    )
    company_type = models.CharField(
        max_length=20,
        choices=COMPANY_TYPE_CHOICES,
        default='customer',
        verbose_name='نوع الشركة',
        db_index=True,
    )
    annual_revenue = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='الإيرادات السنوية',
    )
    employee_count = models.IntegerField(
        default=0,
        verbose_name='عدد الموظفين',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='مسند إلى',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'شركة'
        verbose_name_plural = 'الشركات'

    def __str__(self):
        return self.name


# =============================================
# نماذج إدارة علاقات العملاء
# =============================================


class Contact(models.Model):
    """جهة اتصال - Contact"""

    SOURCE_CHOICES = (
        ('website', 'الموقع الإلكتروني'),
        ('referral', 'إحالة'),
        ('social_media', 'وسائل التواصل الاجتماعي'),
        ('phone', 'الهاتف'),
        ('email', 'البريد الإلكتروني'),
        ('event', 'فعالية'),
        ('other', 'أخرى'),
    )

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('lost', 'مفقود'),
    )

    first_name = models.CharField(
        max_length=100,
        verbose_name='الاسم الأول',
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='الاسم الأخير',
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name='البريد الإلكتروني',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='الهاتف',
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='الهاتف المحمول',
    )
    company = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='الشركة',
        help_text='اسم الشركة النصي (للتوافق العكسي)',
    )
    company_account = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        verbose_name='الشركة (الحساب)',
        help_text='الربط بنموذج الشركة الرسمي',
    )
    position = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='المنصب',
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        blank=True,
        default='',
        verbose_name='المصدر',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة',
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='مسند إلى',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'جهة اتصال'
        verbose_name_plural = 'جهات الاتصال'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Lead(models.Model):
    """فرصة بيع - Lead"""

    STATUS_CHOICES = (
        ('new', 'جديد'),
        ('contacted', 'تم التواصل'),
        ('qualified', 'مؤهل'),
        ('proposal', 'عرض سعر'),
        ('negotiation', 'تفاوض'),
        ('won', 'مكتسب'),
        ('lost', 'مفقود'),
    )

    PIPELINE_STAGE_CHOICES = (
        ('lead', 'فرصة'),
        ('qualified', 'مؤهل'),
        ('proposal', 'عرض سعر'),
        ('negotiation', 'تفاوض'),
        ('closed_won', 'مكتمل - مكتسب'),
        ('closed_lost', 'مكتمل - مفقود'),
    )

    SOURCE_CHOICES = (
        ('website', 'الموقع الإلكتروني'),
        ('referral', 'إحالة'),
        ('social_media', 'وسائل التواصل الاجتماعي'),
        ('phone', 'الهاتف'),
        ('email', 'البريد الإلكتروني'),
        ('event', 'فعالية'),
        ('other', 'أخرى'),
    )

    title = models.CharField(
        max_length=255,
        verbose_name='العنوان',
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='leads',
        verbose_name='جهة الاتصال',
    )
    value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='القيمة',
    )
    probability = models.IntegerField(
        default=0,
        verbose_name='نسبة الاحتمالية',
        help_text='نسبة احتمالية إغلاق الفرصة (0-100)',
    )
    expected_close_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإغلاق المتوقع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='الحالة',
        db_index=True,
    )
    pipeline_stage = models.CharField(
        max_length=20,
        choices=PIPELINE_STAGE_CHOICES,
        default='lead',
        verbose_name='مرحلة خط المبيعات',
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='مسند إلى',
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        blank=True,
        default='',
        verbose_name='المصدر',
    )
    lost_reason = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='سبب الفقدان',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'فرصة بيع'
        verbose_name_plural = 'فرص البيع'

    def __str__(self):
        return self.title


class LeadActivity(models.Model):
    """نشاط الفرصة - Lead Activity"""

    ACTIVITY_TYPE_CHOICES = (
        ('call', 'مكالمة'),
        ('email', 'بريد إلكتروني'),
        ('meeting', 'اجتماع'),
        ('task', 'مهمة'),
        ('note', 'ملاحظة'),
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='فرصة البيع',
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPE_CHOICES,
        verbose_name='نوع النشاط',
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='الموضوع',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='التاريخ المجدول',
    )
    completed = models.BooleanField(
        default=False,
        verbose_name='مكتمل',
    )
    completed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أكتمل بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نشاط فرصة'
        verbose_name_plural = 'أنشطة الفرص'

    def __str__(self):
        return f'{self.lead.title} - {self.get_activity_type_display()}'


class CustomerSegment(models.Model):
    """شريحة عملاء - Customer Segment"""

    name = models.CharField(
        max_length=200,
        verbose_name='الاسم',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    criteria = models.JSONField(
        null=True,
        blank=True,
        verbose_name='معايير التجزئة',
    )
    customer_count = models.IntegerField(
        default=0,
        verbose_name='عدد العملاء',
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نسبة الخصم',
        help_text='الحد الأقصى 100%',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'شريحة عملاء'
        verbose_name_plural = 'شرائح العملاء'

    def __str__(self):
        return self.name


class Campaign(models.Model):
    """حملة تسويقية - Campaign"""

    CAMPAIGN_TYPE_CHOICES = (
        ('email', 'بريد إلكتروني'),
        ('sms', 'رسائل نصية'),
        ('social_media', 'وسائل التواصل الاجتماعي'),
        ('ads', 'إعلانات'),
        ('event', 'فعالية'),
    )

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('active', 'نشطة'),
        ('paused', 'متوقفة'),
        ('completed', 'مكتملة'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='الاسم',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    campaign_type = models.CharField(
        max_length=20,
        choices=CAMPAIGN_TYPE_CHOICES,
        verbose_name='نوع الحملة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية',
    )
    budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الميزانية',
    )
    actual_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة الفعلية',
    )
    target_audience = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='الجمهور المستهدف',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='مسند إلى',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'حملة تسويقية'
        verbose_name_plural = 'الحملات التسويقية'

    def __str__(self):
        return self.name


class CampaignActivity(models.Model):
    """نشاط حملة - Campaign Activity"""

    ACTIVITY_TYPE_CHOICES = (
        ('email_sent', 'بريد مرسل'),
        ('call_made', 'مكالمة تمت'),
        ('meeting_scheduled', 'اجتماع مجدول'),
        ('form_submitted', 'نموذج مُرسل'),
        ('purchase_made', 'عملية شراء'),
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='الحملة التسويقية',
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPE_CHOICES,
        verbose_name='نوع النشاط',
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='جهة الاتصال',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    activity_date = models.DateTimeField(
        verbose_name='تاريخ النشاط',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-activity_date']
        verbose_name = 'نشاط حملة'
        verbose_name_plural = 'أنشطة الحملات'

    def __str__(self):
        return f'{self.campaign.name} - {self.get_activity_type_display()}'


# =============================================
# نماذج الدعم الفني (تذاكر الدعم)
# =============================================


class SLAPolicy(models.Model):
    """سياسة اتفاقية مستوى الخدمة - SLA Policy"""

    PRIORITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم السياسة',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        verbose_name='الأولوية',
        db_index=True,
    )
    first_response_time = models.PositiveIntegerField(
        verbose_name='وقت الاستجابة الأولية',
        help_text='بالدقائق',
    )
    resolution_time = models.PositiveIntegerField(
        verbose_name='وقت الحل',
        help_text='بالدقائق',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشطة',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'سياسة SLA'
        verbose_name_plural = 'سياسات SLA'

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """تذكرة دعم - Support Ticket"""

    STATUS_CHOICES = (
        ('new', 'جديد'),
        ('in_progress', 'قيد التنفيذ'),
        ('pending_customer', 'بانتظار العميل'),
        ('resolved', 'تم الحل'),
        ('closed', 'مغلق'),
        ('reopened', 'مُعاد فتحه'),
    )

    PRIORITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    CATEGORY_CHOICES = (
        ('technical', 'تقني'),
        ('billing', 'فواتير'),
        ('general', 'عام'),
        ('complaint', 'شكوى'),
        ('feature_request', 'طلب ميزة'),
        ('other', 'أخرى'),
    )

    ticket_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم التذكرة',
        help_text='توليد تلقائي: TK-YYYYMMDD-XXXX',
    )
    subject = models.CharField(
        max_length=500,
        verbose_name='الموضوع',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='الحالة',
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
        db_index=True,
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name='التصنيف',
        db_index=True,
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='جهة الاتصال',
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='الشركة',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_tickets',
        verbose_name='مسند إلى',
    )
    sla_policy = models.ForeignKey(
        SLAPolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='سياسة SLA',
    )
    resolution = models.TextField(
        blank=True,
        default='',
        verbose_name='الحل',
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الحل',
    )
    first_response_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاستجابة الأولى',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tickets',
        verbose_name='أُنشئ بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تذكرة دعم'
        verbose_name_plural = 'تذاكر الدعم'

    def __str__(self):
        return f'{self.ticket_number} - {self.subject}'


class TicketComment(models.Model):
    """تعليق على تذكرة - Ticket Comment"""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='التذكرة',
    )
    content = models.TextField(
        verbose_name='المحتوى',
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name='داخلي - لا يراه العميل',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أُنشئ بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'تعليق تذكرة'
        verbose_name_plural = 'تعليقات التذاكر'

    def __str__(self):
        return f'{self.ticket.ticket_number} - تعليق'


# =============================================
# نماذج عروض الأسعار
# =============================================


class Quotation(models.Model):
    """عرض سعر - Quotation"""

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('sent', 'مرسل'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
        ('expired', 'منتهي الصلاحية'),
        ('cancelled', 'ملغي'),
    )

    quote_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم العرض',
        help_text='توليد تلقائي: QT-YYYYMMDD-XXXX',
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        verbose_name='الشركة',
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='جهة الاتصال',
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        verbose_name='فرصة البيع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    valid_until = models.DateField(
        verbose_name='صالح حتى',
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المجموع الفرعي',
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نسبة الخصم',
    )
    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مبلغ الخصم',
    )
    vat_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,
        verbose_name='نسبة ضريبة القيمة المضافة',
    )
    vat_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مبلغ ضريبة القيمة المضافة',
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الإجمالي',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    terms_conditions = models.TextField(
        blank=True,
        default='',
        verbose_name='الشروط والأحكام',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أُنشئ بواسطة',
    )
    converted_to_order = models.BooleanField(
        default=False,
        verbose_name='تم التحويل لأمر بيع',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'عرض سعر'
        verbose_name_plural = 'عروض الأسعار'

    def __str__(self):
        return self.quote_number


class QuotationItem(models.Model):
    """بند عرض سعر - Quotation Item"""

    ITEM_TYPE_CHOICES = (
        ('product', 'منتج'),
        ('service', 'خدمة'),
        ('custom', 'مخصص'),
    )

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='عرض السعر',
    )
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        verbose_name='نوع البند',
    )
    item_name = models.CharField(
        max_length=500,
        verbose_name='اسم البند',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name='الكمية',
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='سعر الوحدة',
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نسبة الخصم',
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المجموع الفرعي',
        help_text='الكمية × سعر الوحدة × (1 - نسبة الخصم / 100)',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='الترتيب',
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'بند عرض سعر'
        verbose_name_plural = 'بنود عروض الأسعار'

    def __str__(self):
        return f'{self.quotation.quote_number} - {self.item_name}'


# =============================================
# نماذج العمولات
# =============================================


class Commission(models.Model):
    """عمولة - Commission"""

    SALE_TYPE_CHOICES = (
        ('order', 'أمر بيع'),
        ('project', 'مشروع'),
        ('contract', 'عقد'),
    )

    STATUS_CHOICES = (
        ('pending', 'معلق'),
        ('approved', 'معتمد'),
        ('paid', 'مدفوع'),
        ('cancelled', 'ملغي'),
    )

    salesperson = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name='مندوب المبيعات',
    )
    sale_type = models.CharField(
        max_length=20,
        choices=SALE_TYPE_CHOICES,
        verbose_name='نوع البيع',
        db_index=True,
    )
    reference_id = models.PositiveIntegerField(
        verbose_name='معرف المرجع',
        help_text='رقم التعريف - order/project/contract id',
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='رقم المرجع',
        help_text='رقم المرجع - SO-xxx, إلخ',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='قيمة المبيعات',
    )
    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='نسبة العمولة',
    )
    commission_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='مبلغ العمولة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الدفع',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    period_month = models.PositiveIntegerField(
        verbose_name='الشهر',
        help_text='1-12',
    )
    period_year = models.PositiveIntegerField(
        verbose_name='السنة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'عمولة'
        verbose_name_plural = 'العمولات'

    def __str__(self):
        return f'{self.salesperson} - {self.get_sale_type_display()} - {self.commission_amount}'
