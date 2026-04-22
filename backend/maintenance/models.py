"""
نماذج التشغيل والصيانة - نظام ERP.
تشمل: النسخ الاحتياطي، سجل الأخطاء، المهام المجدولة.
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
import os


class BackupRecord(models.Model):
    """سجل النسخ الاحتياطي - تتبع جميع النسخ الاحتياطية"""

    BACKUP_TYPE_CHOICES = (
        ('manual', 'يدوي'),
        ('auto_daily', 'يومي تلقائي'),
        ('auto_weekly', 'أسبوعي تلقائي'),
        ('auto_monthly', 'شهري تلقائي'),
    )

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('completed', 'مكتمل'),
        ('failed', 'فاشل'),
        ('restoring', 'جاري الاستعادة'),
    )

    filename = models.CharField(
        max_length=255,
        verbose_name='اسم الملف',
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='مسار الملف',
    )
    file_size = models.BigIntegerField(
        default=0,
        verbose_name='حجم الملف (بايت)',
    )
    backup_type = models.CharField(
        max_length=20,
        choices=BACKUP_TYPE_CHOICES,
        default='manual',
        verbose_name='نوع النسخة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name='الحالة',
    )
    tables_count = models.IntegerField(
        default=0,
        verbose_name='عدد الجداول',
    )
    records_count = models.IntegerField(
        default=0,
        verbose_name='عدد السجلات',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backups',
        verbose_name='تم الإنشاء بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'نسخة احتياطية'
        verbose_name_plural = 'النسخ الاحتياطية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.filename} - {self.get_status_display()}'

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def file_exists(self):
        return os.path.exists(self.file_path)


class ErrorLog(models.Model):
    """سجل الأخطاء - تسجيل مركزي لجميع أخطاء النظام"""

    LEVEL_CHOICES = (
        ('debug', 'تصحيح'),
        ('info', 'معلومة'),
        ('warning', 'تحذير'),
        ('error', 'خطأ'),
        ('critical', 'حرج'),
    )

    SOURCE_CHOICES = (
        ('backend', 'الباكلاند'),
        ('frontend', 'الفرانت اند'),
        ('api', 'واجهة API'),
        ('cron', 'مهام مجدولة'),
        ('backup', 'النسخ الاحتياطي'),
        ('database', 'قاعدة البيانات'),
        ('auth', 'المصادقة'),
        ('other', 'أخرى'),
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='error',
        verbose_name='المستوى',
        db_index=True,
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='backend',
        verbose_name='المصدر',
        db_index=True,
    )
    code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='رمز الخطأ',
        db_index=True,
    )
    message = models.TextField(
        verbose_name='رسالة الخطأ',
    )
    stack_trace = models.TextField(
        blank=True,
        verbose_name='تتبع المكدس',
    )
    url_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='المسار',
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='طريقة الطلب',
    )
    request_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات الطلب',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='عنوان IP',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs',
        verbose_name='المستخدم',
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='متصفح المستخدم',
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name='تم الحل',
        db_index=True,
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_errors',
        verbose_name='تم الحل بواسطة',
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الحل',
    )
    resolution_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات الحل',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التسجيل',
        db_index=True,
    )

    class Meta:
        verbose_name = 'خطأ'
        verbose_name_plural = 'سجل الأخطاء'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', 'source', 'created_at']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]

    def __str__(self):
        return f'[{self.get_level_display()}] {self.code} - {self.message[:80]}'

    @staticmethod
    def log_error(level, message, source='backend', code='', stack_trace='',
                  request=None, user=None):
        """Helper to create an error log entry."""
        ip_address = None
        url_path = ''
        request_method = ''
        request_data = {}
        user_agent = ''

        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            url_path = request.path
            request_method = request.method
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            try:
                request_data = dict(request.data) if hasattr(request, 'data') else {}
            except Exception:
                request_data = {}

        return ErrorLog.objects.create(
            level=level,
            source=source,
            code=code,
            message=message,
            stack_trace=stack_trace,
            url_path=url_path,
            request_method=request_method,
            request_data=request_data,
            ip_address=ip_address,
            user=user,
            user_agent=user_agent,
        )


class CronJob(models.Model):
    """المهام المجدولة - إدارة المهام التلقائية"""

    TASK_CHOICES = (
        ('auto_backup_daily', 'نسخ احتياطي يومي'),
        ('auto_backup_weekly', 'نسخ احتياطي أسبوعي'),
        ('auto_backup_monthly', 'نسخ احتياطي شهري'),
        ('inventory_alerts', 'تنبيهات المخزون المنخفض'),
        ('recurring_invoices', 'فواتير متكررة'),
        ('clean_old_logs', 'تنظيف السجلات القديمة'),
        ('clean_old_backups', 'تنظيف النسخ الاحتياطية القديمة'),
        ('employee_attendance_reminder', 'تذكير الحضور'),
        ('expense_alerts', 'تنبيهات المصروفات'),
        ('project_deadline_alerts', 'تنبيهات مواعيد المشاريع'),
    )

    FREQUENCY_CHOICES = (
        ('every_minute', 'كل دقيقة'),
        ('every_5_minutes', 'كل 5 دقائق'),
        ('every_15_minutes', 'كل 15 دقيقة'),
        ('every_30_minutes', 'كل 30 دقيقة'),
        ('hourly', 'كل ساعة'),
        ('every_6_hours', 'كل 6 ساعات'),
        ('daily', 'يومي'),
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
    )

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('paused', 'متوقف'),
        ('running', 'جاري التنفيذ'),
        ('failed', 'فاشل'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم المهمة',
    )
    task = models.CharField(
        max_length=50,
        choices=TASK_CHOICES,
        verbose_name='نوع المهمة',
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='daily',
        verbose_name='التكرار',
    )
    cron_expression = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='تعبير كرون',
        help_text='مثال: 0 2 * * * (يوميا الساعة 2 صباحا)',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة',
        db_index=True,
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر تنفيذ',
    )
    next_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='التنفيذ التالي',
    )
    last_run_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='حالة آخر تنفيذ',
    )
    last_run_duration = models.FloatField(
        null=True,
        blank=True,
        verbose_name='مدة آخر تنفيذ (ثانية)',
    )
    run_count = models.IntegerField(
        default=0,
        verbose_name='عدد مرات التنفيذ',
    )
    fail_count = models.IntegerField(
        default=0,
        verbose_name='عدد مرات الفشل',
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='إعدادات إضافية',
        help_text='إعدادات خاصة بالمهمة مثل عتبة المخزون أو البريد الإلكتروني',
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='رسالة الخطأ',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cron_jobs',
        verbose_name='تم الإنشاء بواسطة',
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
        verbose_name = 'مهمة مجدولة'
        verbose_name_plural = 'المهام المجدولة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_frequency_display()})'

    @property
    def success_rate(self):
        """نسبة النجاح"""
        if self.run_count == 0:
            return 100
        return round(((self.run_count - self.fail_count) / self.run_count) * 100, 1)

    def calculate_next_run(self):
        """حساب موعد التنفيذ التالي بناء على التكرار"""
        now = timezone.now()
        from datetime import timedelta

        frequency_map = {
            'every_minute': timedelta(minutes=1),
            'every_5_minutes': timedelta(minutes=5),
            'every_15_minutes': timedelta(minutes=15),
            'every_30_minutes': timedelta(minutes=30),
            'hourly': timedelta(hours=1),
            'every_6_hours': timedelta(hours=6),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
        }

        delta = frequency_map.get(self.frequency, timedelta(days=1))
        base = self.last_run or now
        self.next_run = base + delta
        self.save(update_fields=['next_run'])
        return self.next_run

    def mark_running(self):
        self.status = 'running'
        self.save(update_fields=['status'])

    def mark_success(self, duration):
        self.status = 'active'
        self.last_run = timezone.now()
        self.last_run_status = 'success'
        self.last_run_duration = duration
        self.run_count += 1
        self.error_message = ''
        self.calculate_next_run()
        self.save(update_fields=[
            'status', 'last_run', 'last_run_status',
            'last_run_duration', 'run_count', 'error_message', 'next_run', 'updated_at'
        ])

    def mark_failed(self, error_msg, duration=0):
        self.status = 'failed'
        self.last_run = timezone.now()
        self.last_run_status = 'failed'
        self.last_run_duration = duration
        self.run_count += 1
        self.fail_count += 1
        self.error_message = error_msg[:1000]
        self.calculate_next_run()
        self.save(update_fields=[
            'status', 'last_run', 'last_run_status',
            'last_run_duration', 'run_count', 'fail_count',
            'error_message', 'next_run', 'updated_at'
        ])


class SystemBackup(models.Model):
    """إعدادات النسخ الاحتياطي التلقائي"""

    auto_backup_enabled = models.BooleanField(
        default=False,
        verbose_name='النسخ التلقائي مفعّل',
    )
    backup_frequency = models.CharField(
        max_length=20,
        choices=(
            ('daily', 'يومي'),
            ('weekly', 'أسبوعي'),
            ('monthly', 'شهري'),
        ),
        default='daily',
        verbose_name='تكرار النسخ',
    )
    backup_time = models.CharField(
        max_length=10,
        default='02:00',
        verbose_name='وقت النسخ',
        help_text='وقت تنفيذ النسخ الاحتياطي (HH:MM)',
    )
    keep_backups_count = models.IntegerField(
        default=30,
        verbose_name='عدد النسخ المحفوظة',
        help_text='الحد الأقصى لعدد النسخ الاحتياطية المحفوظة',
    )
    backup_directory = models.CharField(
        max_length=500,
        default='backups',
        verbose_name='مجلد النسخ الاحتياطية',
    )
    include_media = models.BooleanField(
        default=False,
        verbose_name='تضمين ملفات الوسائط',
    )

    class Meta:
        verbose_name = 'إعداد النسخ الاحتياطي'
        verbose_name_plural = 'إعدادات النسخ الاحتياطي'

    def __str__(self):
        return f'إعدادات النسخ: {self.get_backup_frequency_display()}'
