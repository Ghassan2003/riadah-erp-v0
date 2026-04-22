"""
نماذج إدارة علاقات العملاء (CRM) لنظام ERP.
يتضمن جهات الاتصال، فرص البيع، أنشطة الفرص، شرائح العملاء، الحملات التسويقية، وأنشطة الحملات.
"""

from django.db import models
from django.utils import timezone


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
