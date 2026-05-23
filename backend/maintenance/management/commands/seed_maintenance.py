"""
Seed default system settings and cron jobs.
Usage: python manage.py seed_maintenance
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed default system settings and cron jobs'

    def handle(self, *args, **options):
        from maintenance.models import CronJob
        from users.models import SystemSetting

        # Seed system settings
        defaults = {
            'company_name': 'شركة النظام',
            'company_email': 'info@example.com',
            'company_phone': '+966500000000',
            'default_currency': 'SAR',
            'currency_symbol': 'ر.س',
            'decimal_places': '2',
            'fiscal_year_start': '01',
            'tax_rate': '15',
            'order_prefix': 'SO',
            'purchase_prefix': 'PO',
            'invoice_prefix': 'INV',
            'journal_prefix': 'JE',
            'employee_prefix': 'EMP',
            'product_prefix': 'PRD',
            'next_order_number': '1001',
            'next_purchase_number': '1001',
            'next_invoice_number': '1001',
            'next_journal_number': '1001',
            'system_language': 'ar',
            'timezone': 'Asia/Riyadh',
            'date_format': 'YYYY-MM-DD',
            'items_per_page': '20',
        }

        for key, value in defaults.items():
            SystemSetting.set(key, value)

        # Seed default cron jobs
        default_jobs = [
            {
                'name': 'نسخ احتياطي يومي',
                'task': 'auto_backup_daily',
                'frequency': 'daily',
                'config': {'low_stock_threshold': 10},
            },
            {
                'name': 'تنبيهات المخزون المنخفض',
                'task': 'inventory_alerts',
                'frequency': 'daily',
                'config': {'low_stock_threshold': 10},
            },
            {
                'name': 'تنظيف السجلات القديمة',
                'task': 'clean_old_logs',
                'frequency': 'weekly',
                'config': {'keep_days': 90, 'audit_keep_days': 180},
            },
            {
                'name': 'تنظيف النسخ الاحتياطية القديمة',
                'task': 'clean_old_backups',
                'frequency': 'monthly',
                'config': {'keep_count': 30},
            },
            {
                'name': 'تذكير الحضور اليومي',
                'task': 'employee_attendance_reminder',
                'frequency': 'daily',
                'config': {},
            },
            {
                'name': 'تنبيهات مصروفات مرتفعة',
                'task': 'expense_alerts',
                'frequency': 'weekly',
                'config': {'expense_threshold': 50000},
            },
            {
                'name': 'تنبيهات مواعيد المشاريع',
                'task': 'project_deadline_alerts',
                'frequency': 'daily',
                'config': {'days_before_deadline': 7},
            },
        ]

        created_count = 0
        for job_data in default_jobs:
            _, created = CronJob.objects.get_or_create(
                task=job_data['task'],
                defaults=job_data,
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {created_count} cron jobs and {len(defaults)} settings.'
        ))
