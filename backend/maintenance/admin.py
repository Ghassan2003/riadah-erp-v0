"""
Admin configuration for the Maintenance module.
"""

from django.contrib import admin
from .models import BackupRecord, ErrorLog, CronJob, SystemBackup


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    """Admin interface for BackupRecord model."""

    list_display = (
        'filename', 'backup_type', 'status', 'file_size_mb',
        'tables_count', 'records_count', 'created_by', 'created_at',
    )
    list_filter = ('backup_type', 'status')
    search_fields = ('filename', 'notes', 'created_by__username')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'file_path', 'file_size', 'tables_count', 'records_count',
        'created_at', 'file_size_mb', 'file_exists',
    )

    fieldsets = (
        ('معلومات النسخة', {
            'fields': ('filename', 'file_path', 'backup_type', 'status')
        }),
        ('تفاصيل', {
            'fields': ('file_size', 'file_size_mb', 'tables_count', 'records_count', 'file_exists')
        }),
        ('معلومات إضافية', {
            'fields': ('notes', 'created_by', 'created_at')
        }),
    )


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """Admin interface for ErrorLog model."""

    list_display = (
        'level', 'source', 'code', 'message_short',
        'is_resolved', 'user', 'created_at',
    )
    list_filter = ('level', 'source', 'is_resolved')
    search_fields = ('code', 'message', 'url_path', 'user__username')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'level', 'source', 'code', 'message', 'stack_trace',
        'url_path', 'request_method', 'request_data', 'ip_address',
        'user_agent', 'user', 'created_at',
    )

    fieldsets = (
        ('معلومات الخطأ', {
            'fields': ('level', 'source', 'code', 'message', 'stack_trace')
        }),
        ('معلومات الطلب', {
            'fields': ('url_path', 'request_method', 'request_data', 'ip_address', 'user_agent')
        }),
        ('المستخدم', {
            'fields': ('user',)
        }),
        ('الحل', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('تاريخ التسجيل', {
            'fields': ('created_at',)
        }),
    )

    def message_short(self, obj):
        return obj.message[:80] + '...' if len(obj.message) > 80 else obj.message
    message_short.short_description = 'الرسالة'

    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
    mark_resolved.short_description = 'تحديد كمحلول'


@admin.register(CronJob)
class CronJobAdmin(admin.ModelAdmin):
    """Admin interface for CronJob model."""

    list_display = (
        'name', 'task', 'frequency', 'status', 'success_rate',
        'last_run', 'next_run', 'run_count',
    )
    list_filter = ('task', 'frequency', 'status')
    search_fields = ('name', 'task', 'error_message')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'last_run', 'last_run_status', 'last_run_duration',
        'run_count', 'fail_count', 'success_rate',
    )

    fieldsets = (
        ('معلومات المهمة', {
            'fields': ('name', 'task', 'frequency', 'cron_expression', 'status')
        }),
        ('إحصائيات التنفيذ', {
            'fields': (
                'last_run', 'next_run', 'last_run_status',
                'last_run_duration', 'run_count', 'fail_count', 'success_rate',
            )
        }),
        ('إعدادات إضافية', {
            'fields': ('config', 'error_message')
        }),
        ('معلومات الإنشاء', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    actions = ['activate_jobs', 'pause_jobs']

    def activate_jobs(self, request, queryset):
        queryset.filter(status='paused').update(status='active')
    activate_jobs.short_description = 'تفعيل المهام المحددة'

    def pause_jobs(self, request, queryset):
        queryset.filter(status='active').update(status='paused')
    pause_jobs.short_description = 'إيقاف المهام المحددة'


@admin.register(SystemBackup)
class SystemBackupAdmin(admin.ModelAdmin):
    """Admin interface for SystemBackup model."""

    list_display = (
        'auto_backup_enabled', 'backup_frequency',
        'backup_time', 'keep_backups_count', 'include_media',
    )
    fieldsets = (
        ('إعدادات النسخ الاحتياطي', {
            'fields': (
                'auto_backup_enabled', 'backup_frequency',
                'backup_time', 'keep_backups_count',
                'backup_directory', 'include_media',
            )
        }),
    )
