"""
Models for the Projects module: Project, ProjectTask, TaskComment, ProjectExpense.
Handles project management with tasks, comments, and expense tracking.
"""

from datetime import date

from django.db import models
from django.utils import timezone

from core.validators import validate_file_type


class Project(models.Model):
    """Project model for managing project information and progress."""

    STATUS_CHOICES = (
        ('planning', 'تخطيط'),
        ('active', 'نشط'),
        ('on_hold', 'متوقف مؤقتاً'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )
    PRIORITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم المشروع',
        db_index=True,
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم المشروع (إنجليزي)',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning',
        verbose_name='الحالة',
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية المتوقع',
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء الفعلي',
    )
    budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='الميزانية',
    )
    spent = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المصروف',
    )
    progress = models.PositiveIntegerField(
        default=0,
        verbose_name='نسبة الإنجاز %',
        help_text='من 0 إلى 100',
    )
    manager = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects',
        verbose_name='مدير المشروع',
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='العميل',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
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
        verbose_name = 'مشروع'
        verbose_name_plural = 'المشاريع'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def remaining_budget(self):
        return self.budget - self.spent

    @property
    def budget_usage_percent(self):
        if self.budget > 0:
            return round((self.spent / self.budget) * 100, 1)
        return 0

    def soft_delete(self):
        """Soft delete by marking as inactive."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def recalculate_spent(self):
        """Recalculate total spent from expenses."""
        from django.db.models import Sum
        total = self.expenses.aggregate(total=Sum('amount'))['total'] or 0
        self.spent = total
        self.save(update_fields=['spent', 'updated_at'])


class ProjectTask(models.Model):
    """Task model linked to a project with status and assignment tracking."""

    STATUS_CHOICES = (
        ('todo', 'قيد الانتظار'),
        ('in_progress', 'قيد التنفيذ'),
        ('review', 'قيد المراجعة'),
        ('done', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='المشروع',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان المهمة',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
        verbose_name='الحالة',
    )
    priority = models.CharField(
        max_length=20,
        choices=Project.PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='مسند إلى',
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ البداية',
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاستحقاق',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال',
    )
    depends_on = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='blocks',
        verbose_name='يعتمد على',
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الساعات المقدرة',
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الساعات الفعلية',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
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
        verbose_name = 'مهمة مشروع'
        verbose_name_plural = 'مهام المشاريع'
        ordering = ['priority', 'due_date']

    def __str__(self):
        return f'{self.project.name} - {self.title}'


class TaskComment(models.Model):
    """Comment model for task discussions."""

    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='المهمة',
    )
    content = models.TextField(
        verbose_name='المحتوى',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='أضاف بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'تعليق مهمة'
        verbose_name_plural = 'تعليقات المهام'
        ordering = ['-created_at']

    def __str__(self):
        return f'تعليق على {self.task.title}'


class ProjectExpense(models.Model):
    """Expense model for tracking project costs."""

    EXPENSE_TYPE_CHOICES = (
        ('material', 'مواد'),
        ('labor', 'أيدي عاملة'),
        ('equipment', 'معدات'),
        ('travel', 'سفر'),
        ('other', 'أخرى'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='المشروع',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان المصروف',
    )
    expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_TYPE_CHOICES,
        verbose_name='نوع المصروف',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    date = models.DateField(
        default=date.today,
        verbose_name='التاريخ',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='أضاف بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'مصروف مشروع'
        verbose_name_plural = 'مصروفات المشاريع'
        ordering = ['-date']

    def __str__(self):
        return f'{self.project.name} - {self.title} ({self.amount})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update project spent amount
        self.project.recalculate_spent()


class ProjectPhase(models.Model):
    """Project phase/stage model supporting Waterfall & Agile methodologies."""

    PHASE_TYPE_CHOICES = (
        ('planning', 'تخطيط'),
        ('design', 'تصميم'),
        ('development', 'تطوير'),
        ('testing', 'اختبار'),
        ('deployment', 'نشر'),
        ('closure', 'إغلاق'),
        ('sprint', 'سبرنت'),
    )
    STATUS_CHOICES = (
        ('not_started', 'لم يبدأ'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('delayed', 'متأخر'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='phases',
        verbose_name='المشروع',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم المرحلة',
    )
    phase_type = models.CharField(
        max_length=20,
        choices=PHASE_TYPE_CHOICES,
        verbose_name='نوع المرحلة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
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
    progress = models.PositiveIntegerField(
        default=0,
        verbose_name='نسبة الإنجاز %',
        help_text='من 0 إلى 100',
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name='ترتيب',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
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
        verbose_name = 'مرحلة مشروع'
        verbose_name_plural = 'مراحل المشاريع'
        ordering = ['order', 'start_date']

    def __str__(self):
        return f'{self.project.name} - {self.name}'


class ProjectMilestone(models.Model):
    """Key milestone model for tracking project deliverables."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('achieved', 'تم التحقيق'),
        ('overdue', 'متأخر'),
        ('cancelled', 'ملغي'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name='المشروع',
    )
    phase = models.ForeignKey(
        ProjectPhase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='milestones',
        verbose_name='المرحلة',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم المعلم',
    )
    due_date = models.DateField(
        verbose_name='تاريخ الاستحقاق',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'معلم مشروع'
        verbose_name_plural = 'معالم المشاريع'
        ordering = ['due_date']

    def __str__(self):
        return f'{self.project.name} - {self.name}'


class BudgetItem(models.Model):
    """Budget line item model for planned vs actual cost tracking."""

    CATEGORY_CHOICES = (
        ('material', 'مواد'),
        ('labor', 'أيدي عاملة'),
        ('equipment', 'معدات'),
        ('subcontractor', 'مقاول من الباطن'),
        ('travel', 'سفر'),
        ('overhead', 'نفقات عامة'),
        ('contingency', 'طوارئ'),
        ('other', 'أخرى'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='budget_items',
        verbose_name='المشروع',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='الفئة',
        db_index=True,
    )
    name = models.CharField(
        max_length=255,
        verbose_name='بند الميزانية',
    )
    planned_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='المبلغ المخطط',
    )
    actual_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='المبلغ الفعلي',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
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
        verbose_name = 'بند ميزانية'
        verbose_name_plural = 'بنود الميزانية'
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_category_display()})'

    @property
    def variance(self):
        """Difference between planned and actual amount."""
        return self.planned_amount - self.actual_amount

    @property
    def variance_percent(self):
        """Percentage variance from planned budget."""
        if self.planned_amount > 0:
            return round((self.variance / self.planned_amount) * 100, 1)
        return 0


class ProjectRisk(models.Model):
    """Risk register model for identifying and tracking project risks."""

    CATEGORY_CHOICES = (
        ('financial', 'مالي'),
        ('operational', 'تشغيلي'),
        ('technical', 'تقني'),
        ('regulatory', 'تنظيمي'),
        ('environmental', 'بيئي'),
        ('schedule', 'جدول زمني'),
        ('resource', 'موارد'),
    )
    STATUS_CHOICES = (
        ('identified', 'محدد'),
        ('analyzing', 'قيد التحليل'),
        ('mitigating', 'قيد التخفيف'),
        ('occurred', 'وقع'),
        ('closed', 'مغلق'),
        ('accepted', 'مقبول'),
    )
    RESPONSE_STRATEGY_CHOICES = (
        ('avoid', 'تجنب'),
        ('mitigate', 'تخفيف'),
        ('transfer', 'نقل'),
        ('accept', 'قبول'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='risks',
        verbose_name='المشروع',
    )
    risk_name = models.CharField(
        max_length=255,
        verbose_name='اسم الخطر',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='الفئة',
        db_index=True,
    )
    probability = models.PositiveIntegerField(
        verbose_name='احتمالية الحدوث',
        help_text='من 1 (منخفض) إلى 5 (مرتفع)',
    )
    impact = models.PositiveIntegerField(
        verbose_name='درجة التأثير',
        help_text='من 1 (منخفض) إلى 5 (مرتفع)',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='identified',
        verbose_name='الحالة',
        db_index=True,
    )
    response_strategy = models.CharField(
        max_length=20,
        choices=RESPONSE_STRATEGY_CHOICES,
        blank=True,
        default='',
        verbose_name='استراتيجية الاستجابة',
    )
    response_plan = models.TextField(
        blank=True,
        default='',
        verbose_name='خطة الاستجابة',
    )
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_risks',
        verbose_name='المسؤول',
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاستحقاق',
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الحل',
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
        verbose_name = 'خطر مشروع'
        verbose_name_plural = 'مخاطر المشاريع'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.risk_name} (درجة الخطر: {self.risk_score})'

    @property
    def risk_score(self):
        """Calculated risk score: probability × impact."""
        return self.probability * self.impact


class TimeEntry(models.Model):
    """Time entry model for tracking hours worked per task."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='المشروع',
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        verbose_name='المهمة',
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='project_time_entries',
        verbose_name='المستخدم',
    )
    date = models.DateField(
        verbose_name='التاريخ',
    )
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='عدد الساعات',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    billable = models.BooleanField(
        default=True,
        verbose_name='قابل للفوترة',
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='معدل الساعة',
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
        verbose_name = 'سجل وقت'
        verbose_name_plural = 'سجلات الوقت'
        ordering = ['-date']
        unique_together = [['user', 'project', 'date']]

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} - {self.hours}س - {self.date}'

    @property
    def total_amount(self):
        """Calculate total billable amount based on hours and rate."""
        if self.hourly_rate:
            return self.hours * self.hourly_rate
        return 0


class ProjectContract(models.Model):
    """Contract management model for external projects."""

    CONTRACT_TYPE_CHOICES = (
        ('fixed_price', 'سعر ثابت'),
        ('time_materials', 'وقت ومواد'),
        ('milestone', 'مراحل'),
        ('retainer', 'اشتراك شهري'),
    )
    BILLING_SCHEDULE_CHOICES = (
        ('monthly', 'شهري'),
        ('milestone', 'بمراحل'),
        ('completion', 'عند الإكمال'),
        ('custom', 'مخصص'),
    )
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('active', 'نشط'),
        ('suspended', 'معلق'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_contracts',
        verbose_name='المشروع',
    )
    contract_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='رقم العقد',
        db_index=True,
    )
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_contracts',
        verbose_name='العميل',
    )
    contract_type = models.CharField(
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        verbose_name='نوع العقد',
    )
    total_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='القيمة الإجمالية',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية',
    )
    payment_terms = models.TextField(
        blank=True,
        default='',
        verbose_name='شروط الدفع',
    )
    billing_schedule = models.CharField(
        max_length=20,
        choices=BILLING_SCHEDULE_CHOICES,
        default='monthly',
        verbose_name='جدول الفوترة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
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
        verbose_name = 'عقد مشروع'
        verbose_name_plural = 'عقود المشاريع'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.contract_number} - {self.project.name}'


class ProjectDocument(models.Model):
    """Document management model for project files and attachments."""

    DOC_TYPE_CHOICES = (
        ('contract', 'عقد'),
        ('specification', 'مواصفات'),
        ('drawing', 'رسم'),
        ('correspondence', 'مراسلات'),
        ('report', 'تقرير'),
        ('invoice', 'فاتورة'),
        ('other', 'أخرى'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='المشروع',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان المستند',
    )
    doc_type = models.CharField(
        max_length=20,
        choices=DOC_TYPE_CHOICES,
        verbose_name='نوع المستند',
        db_index=True,
    )
    file = models.FileField(
        upload_to='project_documents/',
        verbose_name='الملف',
        validators=[validate_file_type],
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_project_documents',
        verbose_name='رفع بواسطة',
    )
    version = models.PositiveIntegerField(
        default=1,
        verbose_name='الإصدار',
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
        verbose_name = 'مستند مشروع'
        verbose_name_plural = 'مستندات المشاريع'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} (v{self.version})'
