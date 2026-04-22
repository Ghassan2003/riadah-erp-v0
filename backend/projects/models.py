"""
Models for the Projects module: Project, ProjectTask, TaskComment, ProjectExpense.
Handles project management with tasks, comments, and expense tracking.
"""

from django.db import models
from django.utils import timezone


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
        default=timezone.now,
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
