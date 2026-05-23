"""
Startup Finance Models — نموذج البيانات المالي للشركات الناشئة.
يغطي: Burn Rate, Runway, MRR, CAC, LTV, Subscription Cycles, Funding Rounds.

التصميم مبني على مبادئ Odoo Community (معياري، قابل للتوسع، وراثة لا تعديل).
كل حقل محسوب stored=False إلا إذا كان مطلوباً للتقارير الثقيلة.
الفهارس على جميع الحقول المستخدمة في التصفية/الترتيب.
"""

from django.db import models, transaction
from django.db.models import Sum, Count, Avg, DecimalField, Value, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


def _today():
    return timezone.now().date()


def _now():
    return timezone.now()


# ═══════════════════════════════════════════════════════════════
# 1. ملف تعريف الوحدة — equivalent to Odoo's __manifest__.py
# ═══════════════════════════════════════════════════════════════

MODULE_MANIFEST = {
    'name': 'startup_finance',
    'version': '1.0.0',
    'description': 'نموذج البيانات المالي للشركات الناشئة',
    'depends': ['accounting', 'sales', 'hr'],
    'category': 'Startup/Finance',
    'author': 'Riadah ERP Team',
}


# ═══════════════════════════════════════════════════════════════
# 2. ملف تعريف الشركة الناشئة
# ═══════════════════════════════════════════════════════════════

class StartupProfile(models.Model):
    """
    ملف تعريف الشركة الناشئة — يحتوي على المعلومات الأساسية والمالية.
    يوجد سجل واحد فقط لكل شركة (singleton pattern via settings).
    """

    company_name = models.CharField(
        max_length=255,
        verbose_name='اسم الشركة',
        db_index=True,
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='القطاع',
        db_index=True,
    )
    stage = models.CharField(
        max_length=30,
        choices=(
            ('pre_seed', 'Pre-Seed'),
            ('seed', 'Seed'),
            ('series_a', 'Series A'),
            ('series_b', 'Series B'),
            ('series_c', 'Series C'),
            ('growth', 'Growth'),
            ('profitable', 'مربحة'),
        ),
        default='seed',
        verbose_name='مرحلة التمويل',
        db_index=True,
    )
    founded_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ التأسيس',
    )
    team_size = models.PositiveIntegerField(
        default=1,
        verbose_name='حجم الفريق',
        validators=[MinValueValidator(1)],
    )
    currency = models.CharField(
        max_length=3,
        default='SAR',
        verbose_name='العملة',
    )

    # حقول مالية أولية
    initial_funding = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='التمويل الأولي',
        help_text='إجمالي التمويل المرفوع حتى الآن',
    )
    monthly_recurring_revenue = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='الإيرادات المتكررة الشهرية (MRR)',
        help_text='إجمالي الاشتراكات الشهرية النشطة',
    )
    monthly_operating_expenses = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='المصروفات التشغيلية الشهرية',
        help_text='إجمالي المصروفات الشهرية (رواتب + تشغيل)',
    )
    cash_balance = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='الرصيد النقدي الحالي',
        help_text='السيولة المتاحة حالياً',
    )

    # حقول محسوبة — stored=False (لا تُحفظ في قاعدة البيانات)
    @property
    def burn_rate(self):
        """معدل الحرق الشهري = المصروفات الشهرية - الإيرادات الشهرية."""
        result = self.monthly_operating_expenses - self.monthly_recurring_revenue
        return max(result, 0)

    @property
    def runway_months(self):
        """عدد أشهر المشاركة المتبقية = الرصيد النقدي / معدل الحرق."""
        if self.burn_rate <= 0:
            return 999  # لا حرق = مشاركة لا نهائية
        return self.cash_balance / self.burn_rate

    @property
    def gross_margin_pct(self):
        """هامش الربح الإجمالي %."""
        if self.monthly_recurring_revenue <= 0:
            return 0
        return ((self.monthly_recurring_revenue - self.monthly_operating_expenses)
                / self.monthly_recurring_revenue * 100)

    class Meta:
        verbose_name = 'ملف الشركة الناشئة'
        verbose_name_plural = 'ملفات الشركات الناشئة'
        ordering = ['-id']

    def __str__(self):
        return f'{self.company_name} ({self.get_stage_display()})'


# ═══════════════════════════════════════════════════════════════
# 3. جولات التمويل (Funding Rounds)
# ═══════════════════════════════════════════════════════════════

class FundingRound(models.Model):
    """
    جدول جولات التمويل — Pre-Seed, Seed, Series A/B/C...
    كل جولة ترتبط بملف الشركة وتسجل تفاصيل المستثمرين والمبالغ.
    """

    ROUND_TYPES = (
        ('pre_seed', 'Pre-Seed'),
        ('seed', 'Seed'),
        ('angel', 'Angel'),
        ('series_a', 'Series A'),
        ('series_b', 'Series B'),
        ('series_c', 'Series C'),
        ('bridge', 'Bridge Loan'),
        ('convertible', 'Convertable Note'),
        ('grant', 'منحة'),
        ('revenue', 'تمويل ذاتي من الإيرادات'),
    )

    startup = models.ForeignKey(
        StartupProfile,
        on_delete=models.CASCADE,
        related_name='funding_rounds',
        verbose_name='الشركة الناشئة',
    )
    round_type = models.CharField(
        max_length=20,
        choices=ROUND_TYPES,
        verbose_name='نوع الجولة',
        db_index=True,
    )
    round_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='اسم الجولة',
    )
    amount_raised = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='المبلغ المرفوع',
        validators=[MinValueValidator(0)],
    )
    valuation_pre_money = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='التقييم قبل الجولة',
    )
    valuation_post_money = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='التقييم بعد الجولة',
    )
    investor_names = models.TextField(
        blank=True,
        default='',
        verbose_name='أسماء المستثمرين',
        help_text='قائمة مفصولة بفواصل',
    )
    equity_diluted = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='نسبة التخفيف %',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    round_date = models.DateField(
        default=_today,
        verbose_name='تاريخ الجولة',
        db_index=True,
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أنشئ بواسطة',
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
        verbose_name = 'جولة تمويل'
        verbose_name_plural = 'جولات التمويل'
        ordering = ['-round_date']
        indexes = [
            models.Index(fields=['startup', 'round_type']),
            models.Index(fields=['round_date']),
        ]

    def __str__(self):
        return f'{self.get_round_type_display()} — {self.amount_raised}'


# ═══════════════════════════════════════════════════════════════
# 4. معدل الحرق الشهري (Monthly Burn Rate Tracking)
# ═══════════════════════════════════════════════════════════════

class BurnRateEntry(models.Model):
    """
    سجل شهري لمعدل الحرق — يتتبع المصروفات والإيرادات الفعلية.
    يُستخدم لحساب الاتجاهات والتنبؤات بدقة أكبر من الأرقام الثابتة.
    """

    CATEGORY_CHOICES = (
        ('payroll', 'الرواتب والأجور'),
        ('rent', 'الإيجار'),
        ('marketing', 'التسويق والإعلان'),
        ('software', 'البرمجيات والاشتراكات'),
        ('infrastructure', 'البنية التحتية والاستضافة'),
        ('operations', 'العمليات والتشغيل'),
        ('legal', 'الشؤون القانونية'),
        ('travel', 'السفر والتنقل'),
        ('misc', 'متنوع'),
    )

    startup = models.ForeignKey(
        StartupProfile,
        on_delete=models.CASCADE,
        related_name='burn_rate_entries',
        verbose_name='الشركة الناشئة',
    )
    month = models.DateField(
        verbose_name='الشهر',
        db_index=True,
        help_text='أول يوم في الشهر',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='الفئة',
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='المبلغ',
        validators=[MinValueValidator(0)],
    )
    entry_type = models.CharField(
        max_length=10,
        choices=(
            ('expense', 'مصروف'),
            ('revenue', 'إيراد'),
        ),
        default='expense',
        verbose_name='النوع',
        db_index=True,
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    is_recurring = models.BooleanField(
        default=False,
        verbose_name='مصروف متكرر',
        db_index=True,
        help_text='هل هذا المصروف يتكرر شهرياً؟',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أدخل بواسطة',
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
        verbose_name = 'سجل معدل الحرق'
        verbose_name_plural = 'سجلات معدل الحرق'
        ordering = ['-month', 'category']
        unique_together = ('startup', 'month', 'category', 'entry_type')
        indexes = [
            models.Index(fields=['startup', 'month', 'entry_type']),
            models.Index(fields=['month', 'category']),
        ]

    def __str__(self):
        return f'{self.month.strftime("%Y-%m")} — {self.get_category_display()} — {self.amount}'


# ═══════════════════════════════════════════════════════════════
# 5. دورات الاشتراك (Subscription Cycles / MRR Tracking)
# ═══════════════════════════════════════════════════════════════

class SubscriptionPlan(models.Model):
    """
    خطط الاشتراك — يحدد الأسعار والميزات لكل خطة.
    """

    name = models.CharField(
        max_length=100,
        verbose_name='اسم الخطة',
        db_index=True,
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    price_monthly = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='السعر الشهري',
        validators=[MinValueValidator(0)],
    )
    price_yearly = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='السعر السنوي',
        help_text='يُعرض خصم عند اختيار الفوترة السنوية',
    )
    features = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='الميزات',
        help_text='قائمة الميزات كـ JSON array',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشطة',
        db_index=True,
    )
    trial_days = models.PositiveIntegerField(
        default=0,
        verbose_name='فترة التجربة (أيام)',
    )
    max_users = models.PositiveIntegerField(
        default=1,
        verbose_name='الحد الأقصى للمستخدمين',
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
        verbose_name = 'خطة اشتراك'
        verbose_name_plural = 'خطط الاشتراك'
        ordering = ['price_monthly']

    def __str__(self):
        return f'{self.name} ({self.price_monthly}/شهر)'


class SubscriptionCycle(models.Model):
    """
    دورة الاشتراك لكل عميل — يتتبع حالة الاشتراك والمبالغ.
    يُستخدم لحساب MRR, Churn Rate, ARPU.
    """

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('trialing', 'فترة تجربة'),
        ('past_due', 'متأخر الدفع'),
        ('paused', 'موقوف مؤقتاً'),
        ('cancelled', 'ملغي'),
        ('churned', 'فقد العميل'),
    )
    BILLING_CHOICES = (
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('yearly', 'سنوي'),
    )

    startup = models.ForeignKey(
        StartupProfile,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='الشركة الناشئة',
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name='العميل',
        null=True,
        blank=True,
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم العميل',
        db_index=True,
        help_text='يُملأ تلقائياً من العميل أو يدوياً',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='cycles',
        verbose_name='الخطة',
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة',
        db_index=True,
    )
    billing_cycle = models.CharField(
        max_length=15,
        choices=BILLING_CHOICES,
        default='monthly',
        verbose_name='دورة الفوترة',
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='مبلغ الاشتراك',
        validators=[MinValueValidator(0)],
    )
    start_date = models.DateField(
        verbose_name='تاريخ البدء',
        db_index=True,
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ الانتهاء',
        db_index=True,
    )
    trial_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='نهاية فترة التجربة',
    )
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاريخ الإلغاء',
    )
    cancellation_reason = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='سبب الإلغاء',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أنشئ بواسطة',
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
        verbose_name = 'دورة اشتراك'
        verbose_name_plural = 'دورات الاشتراك'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['startup', 'status']),
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['plan', 'status']),
        ]

    def __str__(self):
        return f'{self.customer_name} — {self.plan.name} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        """تعبئة اسم العميل تلقائياً إذا كان مرتبطاً بعميل."""
        if self.customer and not self.customer_name:
            self.customer_name = self.customer.name
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════
# 6. مقاييس العملاء (Customer Metrics: CAC, LTV)
# ═══════════════════════════════════════════════════════════════

class CustomerMetric(models.Model):
    """
    مقاييس مكتسبة لكل عميل — تكلفة الاكتساب وقيمة العميل مدى الحياة.
    CAC = تكلفة التسويق والبيع / عدد العملاء المكتسبين
    LTV = متوسط الإيراد الشهري × متوسط مدة البقاء × هامش الربح
    """

    startup = models.ForeignKey(
        StartupProfile,
        on_delete=models.CASCADE,
        related_name='customer_metrics',
        verbose_name='الشركة الناشئة',
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.PROTECT,
        related_name='metrics',
        verbose_name='العميل',
        null=True,
        blank=True,
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم العميل',
        db_index=True,
    )
    acquisition_channel = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='قناة الاكتساب',
        db_index=True,
        help_text='مثال: Google Ads, SEO, Referral, Direct',
    )
    acquisition_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الاكتساب (CAC)',
        validators=[MinValueValidator(0)],
        help_text='إجمالي ما أُنفق على تسويق وبيع هذا العميل',
    )
    monthly_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='الإيراد الشهري من العميل',
        validators=[MinValueValidator(0)],
    )
    months_active = models.PositiveIntegerField(
        default=1,
        verbose_name='عدد أشهر النشاط',
        help_text='كم شهراً ظل العميل مشتركاً',
    )
    total_revenue = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الإيراد من العميل',
    )
    projected_ltv = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='قيمة العميل المتوقعة (LTV)',
        help_text='يُحسب تلقائياً: monthly_revenue × avg_lifetime_months × margin',
    )
    cohort = models.DateField(
        blank=True,
        null=True,
        verbose_name='المجموعة (Cohort)',
        db_index=True,
        help_text='شهر اكتساب العميل',
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
        verbose_name = 'مقاييس العميل'
        verbose_name_plural = 'مقاييس العملاء'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['startup', 'acquisition_channel']),
            models.Index(fields=['cohort']),
        ]

    def __str__(self):
        return f'{self.customer_name} — CAC: {self.acquisition_cost}'

    @property
    def ltv_cac_ratio(self):
        """نسبة LTV/CAC — يجب أن تكون > 3."""
        if self.acquisition_cost <= 0:
            return 0
        return (self.projected_ltv or self.total_revenue) / self.acquisition_cost

    @property
    def payback_months(self):
        """أشهر استرداد تكلفة الاكتساب."""
        if self.monthly_revenue <= 0:
            return 0
        return self.acquisition_cost / self.monthly_revenue


# ═══════════════════════════════════════════════════════════════
# 7. مؤشرات الأداء المالي المخزنة (Cached Financial KPIs)
# ═══════════════════════════════════════════════════════════════

class FinancialKPI(models.Model):
    """
    مؤشرات الأداء المالي المحسوبة مسبقاً — تُحدّث دورياً عبر Celery.
    stored=True لأنها تُستخدم في التقارير الثقيلة واللوحات التحكمية.
    """

    startup = models.ForeignKey(
        StartupProfile,
        on_delete=models.CASCADE,
        related_name='kpis',
        verbose_name='الشركة الناشئة',
    )
    month = models.DateField(
        verbose_name='الشهر',
        db_index=True,
    )

    # مؤشرات الإيرادات
    total_revenue = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name='إجمالي الإيرادات',
    )
    mrr = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name='الإيرادات المتكررة الشهرية (MRR)',
    )
    arr = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        verbose_name='الإيرادات السنوية المتكررة (ARR)',
        help_text='MRR × 12',
    )
    arpu = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='متوسط الإيراد لكل مستخدم (ARPU)',
    )

    # مؤشرات التكلفة
    total_expenses = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name='إجمالي المصروفات',
    )
    burn_rate = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name='معدل الحرق (Burn Rate)',
    )
    cac = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='متوسط تكلفة الاكتساب (CAC)',
    )
    ltv = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name='متوسط قيمة العميل (LTV)',
    )

    # مؤشرات الصحة
    runway_months = models.DecimalField(
        max_digits=6, decimal_places=1, default=0,
        verbose_name='أشهر المشاركة المتبقية (Runway)',
    )
    gross_margin_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='هامش الربح الإجمالي %',
    )
    net_margin_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='هامش صافي الربح %',
    )
    ltv_cac_ratio = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='نسبة LTV/CAC',
    )
    quick_ratio = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='Quick Ratio (MRR Expansion)',
        help_text='(New MRR + Expansion) / (Churn + Contraction)',
    )

    # مؤشرات الاشتراك
    total_subscribers = models.PositiveIntegerField(
        default=0, verbose_name='إجمالي المشتركين',
    )
    new_subscribers = models.PositiveIntegerField(
        default=0, verbose_name='المشتركين الجدد',
    )
    churned_subscribers = models.PositiveIntegerField(
        default=0, verbose_name='العملاء المفقودين',
    )
    churn_rate_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='معدل فقد العملاء %',
    )

    # بيانات إضافية
    cash_balance = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name='الرصيد النقدي',
    )
    total_funding_raised = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        verbose_name='إجمالي التمويل المرفوع',
    )

    # مراقبة التحديث
    calculated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ الحساب',
    )

    class Meta:
        verbose_name = 'مؤشر أداء مالي'
        verbose_name_plural = 'مؤشرات الأداء المالي'
        ordering = ['-month']
        unique_together = ('startup', 'month')
        indexes = [
            models.Index(fields=['startup', '-month']),
            models.Index(fields=['month']),
        ]

    def __str__(self):
        return f'KPIs — {self.month.strftime("%Y-%m")} — Burn: {self.burn_rate}, Runway: {self.runway_months}mo'


# ═══════════════════════════════════════════════════════════════
# 8. دفاتر الحسابات المالية (Financial Ledger Entries)
# ═══════════════════════════════════════════════════════════════

class FinancialEntry(models.Model):
    """
    سجل مالي مبسط — يدعم Idempotency Keys للتكاملات الخارجية.
    كل إدخال يُسجّل بـ idempotency_key لضمان عدم التكرار.
    """

    ENTRY_TYPES = (
        ('revenue', 'إيراد'),
        ('expense', 'مصروف'),
        ('investment', 'استثمار'),
        ('refund', 'استرداد'),
        ('adjustment', 'تسوية'),
    )

    startup = models.ForeignKey(
        StartupProfile,
        on_delete=models.CASCADE,
        related_name='financial_entries',
        verbose_name='الشركة الناشئة',
    )
    entry_type = models.CharField(
        max_length=15,
        choices=ENTRY_TYPES,
        verbose_name='نوع القيد',
        db_index=True,
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='الفئة',
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    entry_date = models.DateField(
        default=_today,
        verbose_name='تاريخ القيد',
        db_index=True,
    )
    # Idempotency — يمنع تكرار الإدخال من التكاملات الخارجية
    idempotency_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        unique=True,
        db_index=True,
        verbose_name='مفتاح عدم التكرار',
        help_text='يُمرر من التكاملات الخارجية لمنع التكرار',
    )
    # مرجع خارجي (مثال: Stripe Charge ID, PayPal Transaction ID)
    external_reference = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='المرجع الخارجي',
        db_index=True,
    )
    external_source = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='المصدر الخارجي',
        help_text='مثال: stripe, paypal, manual',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات إضافية',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أدخل بواسطة',
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
        verbose_name = 'قيد مالي'
        verbose_name_plural = 'القيود المالية'
        ordering = ['-entry_date']
        indexes = [
            models.Index(fields=['startup', 'entry_type', 'entry_date']),
            models.Index(fields=['entry_date']),
            models.Index(fields=['external_source', 'external_reference']),
        ]

    def __str__(self):
        return f'{self.get_entry_type_display()} — {self.amount} — {self.entry_date}'
