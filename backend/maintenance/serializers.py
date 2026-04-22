"""
مسلسلات التشغيل والصيانة - نظام ERP.
"""

from rest_framework import serializers
from django.utils import timezone


class BackupRecordSerializer(serializers.ModelSerializer):
    """مسلسل سجل النسخ الاحتياطي"""
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True, default=''
    )
    file_size_mb = serializers.FloatField(read_only=True)
    file_exists = serializers.BooleanField(read_only=True)

    class Meta:
        model = 'maintenance.BackupRecord'
        fields = [
            'id', 'filename', 'file_path', 'file_size', 'file_size_mb',
            'backup_type', 'status', 'tables_count', 'records_count',
            'notes', 'created_by', 'created_by_name', 'created_at',
            'file_exists',
        ]
        read_only_fields = [
            'id', 'file_size', 'tables_count', 'records_count',
            'created_by', 'created_by_name', 'created_at',
        ]


class RestoreBackupSerializer(serializers.Serializer):
    """مسلسل عملية الاستعادة"""
    backup_id = serializers.IntegerField(required=True)


class ErrorLogSerializer(serializers.ModelSerializer):
    """مسلسل سجل الأخطاء"""
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True, default=''
    )
    resolved_by_name = serializers.CharField(
        source='resolved_by.get_full_name', read_only=True, default=''
    )

    class Meta:
        model = 'maintenance.ErrorLog'
        fields = [
            'id', 'level', 'source', 'code', 'message', 'stack_trace',
            'url_path', 'request_method', 'ip_address',
            'user', 'user_name', 'user_agent',
            'is_resolved', 'resolved_by', 'resolved_by_name',
            'resolved_at', 'resolution_notes', 'created_at',
        ]
        read_only_fields = [
            'id', 'stack_trace', 'url_path', 'request_method',
            'ip_address', 'user', 'user_agent',
        ]


class ResolveErrorSerializer(serializers.Serializer):
    """مسلسل حل الخطأ"""
    resolution_notes = serializers.CharField(
        required=False, default='', allow_blank=True
    )


class CronJobSerializer(serializers.ModelSerializer):
    """مسلسل المهام المجدولة"""
    success_rate = serializers.FloatField(read_only=True)
    task_display = serializers.CharField(
        source='get_task_display', read_only=True
    )
    frequency_display = serializers.CharField(
        source='get_frequency_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    last_run_status_display = serializers.CharField(
        source='get_last_run_status_display', read_only=True, default=''
    )

    class Meta:
        model = 'maintenance.CronJob'
        fields = [
            'id', 'name', 'task', 'task_display', 'frequency',
            'frequency_display', 'cron_expression', 'status',
            'status_display', 'last_run', 'next_run', 'last_run_status',
            'last_run_status_display', 'last_run_duration',
            'run_count', 'fail_count', 'success_rate',
            'config', 'error_message', 'created_by', 'created_at',
        ]
        read_only_fields = [
            'id', 'last_run', 'next_run', 'last_run_status',
            'last_run_duration', 'run_count', 'fail_count',
            'success_rate', 'error_message', 'created_by',
        ]


class CronJobToggleSerializer(serializers.Serializer):
    """مسلسل تفعيل/إيقاف المهمة"""
    action = serializers.ChoiceField(choices=['activate', 'pause'])


class SystemBackupConfigSerializer(serializers.ModelSerializer):
    """مسلسل إعدادات النسخ الاحتياطي"""

    class Meta:
        from .models import SystemBackup
        model = SystemBackup
        fields = [
            'id', 'auto_backup_enabled', 'backup_frequency',
            'backup_time', 'keep_backups_count', 'backup_directory',
            'include_media',
        ]
