"""
واجهات التشغيل والصيانة - نظام ERP.
تشمل: النسخ الاحتياطي، سجل الأخطاء، إعدادات النظام، المهام المجدولة.
"""

from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import timedelta
import os
import zipfile
import time
import traceback

from users.permissions import IsAdmin
from .models import BackupRecord, ErrorLog, CronJob, SystemBackup
from .serializers import (
    BackupRecordSerializer, RestoreBackupSerializer,
    ErrorLogSerializer, ResolveErrorSerializer,
    CronJobSerializer, CronJobToggleSerializer,
    SystemBackupConfigSerializer,
)

User = get_user_model()


# ==========================================
# النسخ الاحتياطي
# ==========================================

class BackupListView(generics.ListAPIView):
    """قائمة النسخ الاحتياطية"""
    permission_classes = [IsAdmin]
    serializer_class = BackupRecordSerializer
    queryset = BackupRecord.objects.all()
    filterset_fields = ['backup_type', 'status']
    search_fields = ['filename', 'notes']
    ordering_fields = ['-created_at']


class BackupCreateView(views.APIView):
    """إنشاء نسخة احتياطية جديدة"""
    permission_classes = [IsAdmin]

    def post(self, request):
        notes = request.data.get('notes', '')
        backup_type = request.data.get('backup_type', 'manual')

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'erp_backup_{timestamp}.zip'

        # Ensure backup directory exists
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        file_path = os.path.join(backup_dir, filename)

        try:
            from django.core.management import call_command
            from django.apps import apps as django_apps
            from io import BytesIO

            local_apps = [
                'users', 'inventory', 'sales', 'accounting',
                'hr', 'purchases', 'documents', 'projects',
                'notifications', 'auditlog', 'maintenance',
            ]
            models_to_dump = []
            for app_label in local_apps:
                try:
                    app_config = django_apps.get_app_config(app_label)
                    for model in app_config.get_models():
                        models_to_dump.append(f'{app_label}.{model.__name__}')
                except LookupError:
                    pass

            # Create ZIP with JSON dump
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                out = BytesIO()
                call_command('dumpdata', *models_to_dump, '--indent=2', stdout=out)
                out.seek(0)
                json_content = out.read().decode('utf-8')

                # Count records from JSON
                import json
                try:
                    data = json.loads(json_content)
                    records_count = len(data)
                except Exception:
                    records_count = 0

                zf.writestr(f'erp_backup_{timestamp}.json', json_content)

            # Save to file
            buffer.seek(0)
            with open(file_path, 'wb') as f:
                f.write(buffer.read())

            file_size = os.path.getsize(file_path)

            # Create backup record
            record = BackupRecord.objects.create(
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                backup_type=backup_type,
                status='completed',
                tables_count=len(models_to_dump),
                records_count=records_count,
                notes=notes,
                created_by=request.user,
            )

            return Response({
                'message': 'تم إنشاء النسخة الاحتياطية بنجاح',
                'backup': BackupRecordSerializer(record).data,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            ErrorLog.log_error(
                level='error',
                message=f'فشل إنشاء نسخة احتياطية: {str(e)}',
                source='backup',
                code='BACKUP_FAILED',
                stack_trace=traceback.format_exc(),
                request=request,
                user=request.user,
            )
            return Response({
                'error': f'فشل إنشاء النسخة الاحتياطية: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BackupDownloadView(views.APIView):
    """تحميل نسخة احتياطية"""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        try:
            backup = BackupRecord.objects.get(pk=pk)
        except BackupRecord.DoesNotExist:
            return Response({'error': 'النسخة غير موجودة'}, status=404)

        if not backup.file_exists:
            return Response({'error': 'ملف النسخة غير موجود على الخادم'}, status=404)

        try:
            with open(backup.file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{backup.filename}"'
            return response
        except Exception as e:
            return Response({'error': f'فشل تحميل الملف: {str(e)}'}, status=500)


class BackupRestoreView(views.APIView):
    """استعادة نسخة احتياطية"""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = RestoreBackupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            backup = BackupRecord.objects.get(pk=serializer.validated_data['backup_id'])
        except BackupRecord.DoesNotExist:
            return Response({'error': 'النسخة غير موجودة'}, status=404)

        if not backup.file_exists:
            return Response({'error': 'ملف النسخة غير موجود'}, status=400)

        try:
            # Mark as restoring
            backup.status = 'restoring'
            backup.save(update_fields=['status'])

            # Extract and restore
            import tempfile
            from django.core.management import call_command

            with zipfile.ZipFile(backup.file_path, 'r') as zf:
                json_files = [n for n in zf.namelist() if n.endswith('.json')]
                if not json_files:
                    raise Exception('لا يوجد ملف JSON في الأرشيف')

                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                    tmp.write(zf.read(json_files[0]).decode('utf-8'))
                    tmp_path = tmp.name

            call_command('loaddata', tmp_path)

            # Cleanup temp file
            try:
                os.remove(tmp_path)
            except Exception:
                pass

            backup.status = 'completed'
            backup.notes = f'{backup.notes} | تمت الاستعادة بتاريخ {timezone.now().strftime("%Y-%m-%d %H:%M")}'
            backup.save(update_fields=['status', 'notes'])

            return Response({'message': 'تمت استعادة البيانات بنجاح'})

        except Exception as e:
            backup.status = 'completed'
            backup.save(update_fields=['status'])

            ErrorLog.log_error(
                level='error',
                message=f'فشل استعادة النسخة الاحتياطية: {str(e)}',
                source='backup',
                code='RESTORE_FAILED',
                stack_trace=traceback.format_exc(),
                request=request,
                user=request.user,
            )
            return Response({
                'error': f'فشل استعادة البيانات: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BackupDeleteView(views.APIView):
    """حذف نسخة احتياطية"""
    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            backup = BackupRecord.objects.get(pk=pk)
        except BackupRecord.DoesNotExist:
            return Response({'error': 'النسخة غير موجودة'}, status=404)

        # Delete file
        if backup.file_exists:
            try:
                os.remove(backup.file_path)
            except Exception:
                pass

        backup.delete()
        return Response({'message': 'تم حذف النسخة الاحتياطية'})


class BackupStatsView(views.APIView):
    """إحصائيات النسخ الاحتياطية"""
    permission_classes = [IsAdmin]

    def get(self, request):
        total = BackupRecord.objects.count()
        total_size = BackupRecord.objects.aggregate(
            s=Count('file_size')
        )
        completed = BackupRecord.objects.filter(status='completed').count()
        failed = BackupRecord.objects.filter(status='failed').count()
        latest = BackupRecord.objects.filter(status='completed').first()

        total_size_bytes = 0
        for b in BackupRecord.objects.filter(status='completed'):
            total_size_bytes += b.file_size

        return Response({
            'total_backups': total,
            'completed_backups': completed,
            'failed_backups': failed,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
            'latest_backup': BackupRecordSerializer(latest).data if latest else None,
        })


# ==========================================
# سجل الأخطاء
# ==========================================

class ErrorLogListView(generics.ListAPIView):
    """قائمة أخطاء النظام"""
    permission_classes = [IsAdmin]
    serializer_class = ErrorLogSerializer
    queryset = ErrorLog.objects.all()
    filterset_fields = ['level', 'source', 'is_resolved']
    search_fields = ['code', 'message', 'url_path']
    ordering_fields = ['-created_at']


class ErrorLogStatsView(views.APIView):
    """إحصائيات الأخطاء"""
    permission_classes = [IsAdmin]

    def get(self, request):
        total = ErrorLog.objects.count()
        unresolved = ErrorLog.objects.filter(is_resolved=False).count()
        critical = ErrorLog.objects.filter(level='critical', is_resolved=False).count()
        errors = ErrorLog.objects.filter(level='error', is_resolved=False).count()
        warnings = ErrorLog.objects.filter(level='warning', is_resolved=False).count()

        # Errors by source
        by_source = list(ErrorLog.objects.filter(is_resolved=False).values('source').annotate(
            count=Count('id')
        ).order_by('-count'))

        # Recent errors (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent = ErrorLog.objects.filter(created_at__gte=week_ago).count()

        # Level distribution
        by_level = list(ErrorLog.objects.values('level').annotate(
            count=Count('id')
        ).order_by('-count'))

        return Response({
            'total': total,
            'unresolved': unresolved,
            'critical_unresolved': critical,
            'errors_unresolved': errors,
            'warnings_unresolved': warnings,
            'recent_week': recent,
            'by_source': by_source,
            'by_level': by_level,
        })


class ErrorLogResolveView(views.APIView):
    """حل خطأ"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            error = ErrorLog.objects.get(pk=pk)
        except ErrorLog.DoesNotExist:
            return Response({'error': 'الخطأ غير موجود'}, status=404)

        serializer = ResolveErrorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        error.is_resolved = True
        error.resolved_by = request.user
        error.resolved_at = timezone.now()
        error.resolution_notes = serializer.validated_data.get('resolution_notes', '')
        error.save()

        return Response({'message': 'تم تحديد الخطأ كمحلول'})


class ErrorLogBatchResolveView(views.APIView):
    """حل مجموعة أخطاء"""
    permission_classes = [IsAdmin]

    def post(self, request):
        error_ids = request.data.get('error_ids', [])
        resolution_notes = request.data.get('resolution_notes', '')

        if not error_ids:
            return Response({'error': 'لم يتم تحديد أخطاء'}, status=400)

        updated = ErrorLog.objects.filter(
            id__in=error_ids, is_resolved=False
        ).update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now(),
            resolution_notes=resolution_notes,
        )

        return Response({'message': f'تم حل {updated} خطأ'})


class ErrorLogClearView(views.APIView):
    """تنظيف أخطاء قديمة"""
    permission_classes = [IsAdmin]

    def delete(self, request):
        days = int(request.query_params.get('days', 30))
        cutoff = timezone.now() - timedelta(days=days)

        # Only delete resolved errors older than cutoff
        deleted, _ = ErrorLog.objects.filter(
            is_resolved=True,
            created_at__lte=cutoff,
        ).delete()

        return Response({'message': f'تم حذف {deleted} خطأ محلول أقدم من {days} يوم'})


class ErrorLogDetailView(views.APIView):
    """تفاصيل خطأ"""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        try:
            error = ErrorLog.objects.get(pk=pk)
            return Response(ErrorLogSerializer(error).data)
        except ErrorLog.DoesNotExist:
            return Response({'error': 'الخطأ غير موجود'}, status=404)


# ==========================================
# إعدادات النظام
# ==========================================

class SystemSettingsView(views.APIView):
    """إعدادات النظام الشاملة"""
    permission_classes = [IsAdmin]

    def get(self, request):
        from users.models import SystemSetting

        settings_groups = {
            'company': {
                'title': 'معلومات الشركة',
                'keys': [
                    'company_name', 'company_logo', 'company_address',
                    'company_phone', 'company_email', 'company_website',
                    'company_cr_number', 'company_vat_number', 'company_fax',
                ],
            },
            'financial': {
                'title': 'الإعدادات المالية',
                'keys': [
                    'default_currency', 'currency_symbol', 'decimal_places',
                    'fiscal_year_start', 'tax_rate', 'payment_terms',
                ],
            },
            'numbering': {
                'title': 'الأرقام التلقائية',
                'keys': [
                    'order_prefix', 'purchase_prefix', 'invoice_prefix',
                    'journal_prefix', 'employee_prefix', 'product_prefix',
                    'next_order_number', 'next_purchase_number',
                    'next_invoice_number', 'next_journal_number',
                ],
            },
            'backup': {
                'title': 'النسخ الاحتياطي',
                'keys': [
                    'auto_backup_enabled', 'backup_frequency',
                    'backup_time', 'keep_backups_count',
                ],
            },
            'email': {
                'title': 'إعدادات البريد',
                'keys': [
                    'smtp_host', 'smtp_port', 'smtp_user',
                    'smtp_use_tls', 'email_from', 'admin_email',
                ],
            },
            'general': {
                'title': 'عام',
                'keys': [
                    'system_language', 'timezone', 'date_format',
                    'items_per_page', 'session_timeout',
                ],
            },
        }

        result = {}
        for group_key, group in settings_groups.items():
            result[group_key] = {
                'title': group['title'],
                'settings': {},
            }
            for key in group['keys']:
                result[group_key]['settings'][key] = SystemSetting.get(key)

        # Get backup config
        backup_config = SystemBackup.objects.first()
        if not isinstance(backup_config, SystemBackup):
            backup_config = SystemBackup.objects.create()
        result['backup_config'] = SystemBackupConfigSerializer(backup_config).data

        return Response(result)

    def put(self, request):
        """تحديث إعدادات النظام"""
        from users.models import SystemSetting

        settings_data = request.data.get('settings', {})
        updated_count = 0

        for key, value in settings_data.items():
            if value is not None:
                description_map = {
                    'company_name': 'اسم الشركة',
                    'company_address': 'عنوان الشركة',
                    'company_phone': 'هاتف الشركة',
                    'company_email': 'بريد الشركة',
                    'company_website': 'موقع الشركة',
                    'company_cr_number': 'السجل التجاري',
                    'company_vat_number': 'الرقم الضريبي',
                    'company_fax': 'فاكس الشركة',
                    'default_currency': 'العملة الافتراضية',
                    'currency_symbol': 'رمز العملة',
                    'decimal_places': 'المنازل العشرية',
                    'fiscal_year_start': 'بداية السنة المالية',
                    'tax_rate': 'نسبة الضريبة',
                    'payment_terms': 'شروط الدفع',
                    'order_prefix': 'بادئة أوامر البيع',
                    'purchase_prefix': 'بادئة أوامر الشراء',
                    'invoice_prefix': 'بادئة الفواتير',
                    'journal_prefix': 'بادئة القيود',
                    'employee_prefix': 'بادئة الموظفين',
                    'product_prefix': 'بادئة المنتجات',
                    'next_order_number': 'رقم أمر البيع التالي',
                    'next_purchase_number': 'رقم أمر الشراء التالي',
                    'next_invoice_number': 'رقم الفاتورة التالي',
                    'next_journal_number': 'رقم القيد التالي',
                    'auto_backup_enabled': 'تفعيل النسخ التلقائي',
                    'backup_frequency': 'تكرار النسخ',
                    'backup_time': 'وقت النسخ',
                    'keep_backups_count': 'عدد النسخ المحفوظة',
                    'smtp_host': 'خادم SMTP',
                    'smtp_port': 'منفذ SMTP',
                    'smtp_user': 'مستخدم SMTP',
                    'smtp_use_tls': 'استخدام TLS',
                    'email_from': 'البريد المرسل',
                    'admin_email': 'بريد المدير',
                    'system_language': 'لغة النظام',
                    'timezone': 'المنطقة الزمنية',
                    'date_format': 'صيغة التاريخ',
                    'items_per_page': 'عناصر الصفحة',
                    'session_timeout': 'مدة الجلسة',
                }
                SystemSetting.set(
                    key=key,
                    value=str(value),
                    description=description_map.get(key, '')
                )
                updated_count += 1

        return Response({'message': f'تم تحديث {updated_count} إعداد'})


class AutoNumberPreviewView(views.APIView):
    """معاينة الأرقام التلقائية"""
    permission_classes = [IsAdmin]

    def get(self, request):
        from users.models import SystemSetting
        from django.utils import timezone

        now = timezone.now()

        def build_number(prefix, next_num):
            p = prefix or ''
            n = int(next_num or 1)
            date_str = now.strftime('%Y%m')
            return f'{p}-{date_str}-{str(n).zfill(5)}'

        return Response({
            'order': build_number(
                SystemSetting.get('order_prefix', 'SO'),
                SystemSetting.get('next_order_number', '1')
            ),
            'purchase': build_number(
                SystemSetting.get('purchase_prefix', 'PO'),
                SystemSetting.get('next_purchase_number', '1')
            ),
            'invoice': build_number(
                SystemSetting.get('invoice_prefix', 'INV'),
                SystemSetting.get('next_invoice_number', '1')
            ),
            'journal': build_number(
                SystemSetting.get('journal_prefix', 'JE'),
                SystemSetting.get('next_journal_number', '1')
            ),
        })


# ==========================================
# المهام المجدولة (Cron Jobs)
# ==========================================

class CronJobListView(generics.ListAPIView):
    """قائمة المهام المجدولة"""
    permission_classes = [IsAdmin]
    serializer_class = CronJobSerializer
    queryset = CronJob.objects.all()
    filterset_fields = ['task', 'status']
    search_fields = ['name']
    ordering_fields = ['-created_at', '-next_run']


class CronJobCreateView(views.APIView):
    """إنشاء مهمة مجدولة جديدة"""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = CronJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cron_job = serializer.save(created_by=request.user)
        cron_job.calculate_next_run()

        return Response(
            CronJobSerializer(cron_job).data,
            status=status.HTTP_201_CREATED
        )


class CronJobDetailView(views.APIView):
    """تفاصيل مهمة مجدولة"""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        try:
            cron_job = CronJob.objects.get(pk=pk)
            return Response(CronJobSerializer(cron_job).data)
        except CronJob.DoesNotExist:
            return Response({'error': 'المهمة غير موجودة'}, status=404)

    def put(self, request, pk):
        try:
            cron_job = CronJob.objects.get(pk=pk)
        except CronJob.DoesNotExist:
            return Response({'error': 'المهمة غير موجودة'}, status=404)

        serializer = CronJobSerializer(cron_job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        cron_job = serializer.save()
        cron_job.calculate_next_run()

        return Response(CronJobSerializer(cron_job).data)

    def delete(self, request, pk):
        try:
            cron_job = CronJob.objects.get(pk=pk)
        except CronJob.DoesNotExist:
            return Response({'error': 'المهمة غير موجودة'}, status=404)

        cron_job.delete()
        return Response({'message': 'تم حذف المهمة'})


class CronJobToggleView(views.APIView):
    """تفعيل/إيقاف مهمة مجدولة"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            cron_job = CronJob.objects.get(pk=pk)
        except CronJob.DoesNotExist:
            return Response({'error': 'المهمة غير موجودة'}, status=404)

        serializer = CronJobToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        if action == 'activate':
            cron_job.status = 'active'
            cron_job.calculate_next_run()
            message = 'تم تفعيل المهمة'
        else:
            cron_job.status = 'paused'
            cron_job.next_run = None
            cron_job.save(update_fields=['status', 'next_run'])
            message = 'تم إيقاف المهمة'

        return Response({'message': message})


class CronJobRunNowView(views.APIView):
    """تنفيذ مهمة مجدولة فوراً"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            cron_job = CronJob.objects.get(pk=pk)
        except CronJob.DoesNotExist:
            return Response({'error': 'المهمة غير موجودة'}, status=404)

        from .tasks import run_cron_task

        result = run_cron_task(cron_job, force=True)
        return Response(result)


class CronJobStatsView(views.APIView):
    """إحصائيات المهام المجدولة"""
    permission_classes = [IsAdmin]

    def get(self, request):
        total = CronJob.objects.count()
        active = CronJob.objects.filter(status='active').count()
        paused = CronJob.objects.filter(status='paused').count()
        failed = CronJob.objects.filter(status='failed').count()
        total_runs = CronJob.objects.aggregate(
            t=Count('run_count')
        )

        total_run_sum = sum(CronJob.objects.values_list('run_count', flat=True))
        total_fail_sum = sum(CronJob.objects.values_list('fail_count', flat=True))

        return Response({
            'total_jobs': total,
            'active_jobs': active,
            'paused_jobs': paused,
            'failed_jobs': failed,
            'total_executions': total_run_sum,
            'total_failures': total_fail_sum,
        })
