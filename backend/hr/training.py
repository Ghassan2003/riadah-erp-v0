"""
Training & Development Models for ERP System.
Manages Training Needs, Courses, Sessions, Enrollments, and Budgets.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# =============================================
# Training Needs Assessment
# =============================================

class TrainingNeed(models.Model):
    """Identified training/skill gap for a department or specific employee."""

    PRIORITY_CHOICES = (
        ('high', 'عالية'),
        ('medium', 'متوسطة'),
        ('low', 'منخفضة'),
    )

    STATUS_CHOICES = (
        ('identified', 'مُحدد'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_needs',
        verbose_name='القسم',
        help_text='اتركه فارغاً إذا كان الاحتياج عاماً',
    )
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_needs',
        verbose_name='الموظف',
        help_text='موظف محدد إذا كان الاحتياج فردياً',
    )
    skill_gap = models.CharField(
        max_length=255,
        verbose_name='الفجوة في المهارة',
        help_text='المهارة أو المعرفة المطلوبة',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
        db_index=True,
    )
    suggested_training = models.TextField(
        blank=True,
        default='',
        verbose_name='التدريب المقترح',
    )
    target_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='التاريخ المستهدف',
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='identified',
        verbose_name='الحالة',
        db_index=True,
    )
    identified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_needs_identified',
        verbose_name='مُحدد بواسطة',
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
        verbose_name = 'احتياج تدريبي'
        verbose_name_plural = 'الاحتياجات التدريبية'
        ordering = ['-created_at']

    def __str__(self):
        target = self.employee or self.department or 'عام'
        return f'{self.skill_gap} - {target}'


# =============================================
# Training Course
# =============================================

class Course(models.Model):
    """Training course catalog with details about available courses."""

    TRAINING_TYPE_CHOICES = (
        ('internal', 'داخلي'),
        ('external', 'خارجي'),
        ('online', 'عن بُعد'),
        ('blended', 'مدمج'),
    )

    CATEGORY_CHOICES = (
        ('technical', 'تقني'),
        ('soft_skills', 'مهارات شخصية'),
        ('leadership', 'قيادة'),
        ('compliance', 'امتثال'),
        ('safety', 'السلامة'),
        ('other', 'أخرى'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رمز الدورة',
        db_index=True,
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم الدورة',
        db_index=True,
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم الدورة (إنجليزي)',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    provider = models.CharField(
        max_length=255,
        verbose_name='مزود التدريب',
        help_text='الشركة أو الجهة المقدمة للتدريب',
    )
    training_type = models.CharField(
        max_length=20,
        choices=TRAINING_TYPE_CHOICES,
        default='internal',
        verbose_name='نوع التدريب',
        db_index=True,
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='technical',
        verbose_name='التصنيف',
        db_index=True,
    )
    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name='مدة الدورة (ساعات)',
    )
    max_participants = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='الحد الأقصى للمشاركين',
        help_text='اتركه فارغاً إذا لم يوجد حد',
    )
    cost_per_participant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة لكل مشارك',
    )
    total_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='الميزانية الإجمالية',
    )
    certificate_offered = models.BooleanField(
        default=False,
        verbose_name='شهادة معتمدة',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
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
        verbose_name = 'دورة تدريبية'
        verbose_name_plural = 'الدورات التدريبية'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'


# =============================================
# Training Session
# =============================================

class TrainingSession(models.Model):
    """Scheduled instance of a training course."""

    STATUS_CHOICES = (
        ('planned', 'مخطط'),
        ('ongoing', 'جاري'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='الدورة التدريبية',
    )
    session_number = models.CharField(
        max_length=50,
        verbose_name='رقم الجلسة',
        help_text='مثال: BATCH-001',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
        db_index=True,
    )
    end_date = models.DateField(
        verbose_name='تاريخ النهاية',
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='المكان',
        help_text='رقم القاعة أو رابط التدريب عن بُعد',
    )
    instructor = models.CharField(
        max_length=255,
        verbose_name='المدرب',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name='الحالة',
        db_index=True,
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة الفعلية',
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
        verbose_name = 'جلسة تدريبية'
        verbose_name_plural = 'الجلسات التدريبية'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.course.code} - {self.session_number}'

    @property
    def enrolled_count(self):
        """Number of enrolled participants in this session."""
        return self.enrollments.filter(
            status__in=['enrolled', 'in_progress', 'completed'],
        ).count()


# =============================================
# Training Enrollment
# =============================================

class TrainingEnrollment(models.Model):
    """Employee enrollment record in a specific training session."""

    STATUS_CHOICES = (
        ('enrolled', 'مسجل'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('dropped', 'منسحب'),
        ('failed', 'راسب'),
    )

    session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='الجلسة التدريبية',
    )
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='training_enrollments',
        verbose_name='الموظف',
    )
    enrollment_date = models.DateField(
        auto_now_add=True,
        verbose_name='تاريخ التسجيل',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='enrolled',
        verbose_name='الحالة',
        db_index=True,
    )
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال',
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الدرجة',
        help_text='من 0 إلى 100',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    passed = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='ناجح',
        help_text='يُحدد تلقائياً بناءً على الدرجة',
    )
    certificate_issued = models.BooleanField(
        default=False,
        verbose_name='شهادة صادرة',
    )
    certificate_file = models.FileField(
        upload_to='training_certificates/',
        blank=True,
        verbose_name='ملف الشهادة',
    )
    feedback = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='تقييم الرضا',
        help_text='من 1 إلى 5',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    feedback_notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات التقييم',
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة',
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
        verbose_name = 'تسجيل في تدريب'
        verbose_name_plural = 'تسجيلات التدريب'
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'employee'],
                name='unique_enrollment_session_employee',
            ),
        ]
        ordering = ['-enrollment_date']

    def __str__(self):
        return f'{self.employee.full_name} - {self.session} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        """Auto-set passed flag based on score (passing score >= 60)."""
        if self.score is not None:
            self.passed = self.score >= 60
        super().save(*args, **kwargs)


# =============================================
# Training Budget
# =============================================

class TrainingBudget(models.Model):
    """Annual training budget allocation per year and optionally per department."""

    year = models.IntegerField(
        verbose_name='السنة',
        db_index=True,
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_budgets',
        verbose_name='القسم',
        help_text='اتركه فارغاً للميزانية العامة للشركة',
    )
    total_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='الميزانية الإجمالية',
    )
    utilized_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ المستخدم',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_budgets_approved',
        verbose_name='اعتمد بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاعتماد',
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
        verbose_name = 'ميزانية التدريب'
        verbose_name_plural = 'ميزانيات التدريب'
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'department'],
                name='unique_training_budget_year_department',
            ),
        ]
        ordering = ['-year']

    def __str__(self):
        scope = self.department or 'الشركة'
        return f'ميزانية التدريب - {scope} - {self.year}'

    @property
    def remaining_amount(self):
        """Auto-calculated remaining budget."""
        return self.total_budget - self.utilized_amount

    @property
    def utilization_percentage(self):
        """Budget utilization as a percentage."""
        if self.total_budget > 0:
            return round((self.utilized_amount / self.total_budget) * 100, 1)
        return 0
