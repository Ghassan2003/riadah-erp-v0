"""
Management command to create sample audit log entries for testing.
Usage: python manage.py seed_auditlog
"""

from django.core.management.base import BaseCommand
from auditlog.models import AuditLog
from users.models import User
from django.utils import timezone
from datetime import timedelta
import json


class Command(BaseCommand):
    help = 'Creates sample audit log entries for testing the audit log module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing audit logs before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            AuditLog.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all audit logs.'))

        admin_user = User.objects.filter(role='admin').first()
        users = list(User.objects.filter(is_active=True))

        if not users:
            self.stdout.write(self.style.ERROR('No users found. Create users first.'))
            return

        # Seed sample audit log entries
        logs_data = [
            {
                'user': admin_user,
                'action': 'login',
                'model_name': 'User',
                'object_id': admin_user.id if admin_user else 1,
                'object_repr': str(admin_user) if admin_user else 'admin',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'url_path': '/api/auth/login/',
                'created_at': timezone.now() - timedelta(hours=2),
            },
            {
                'user': admin_user,
                'action': 'create',
                'model_name': 'Product',
                'object_id': 1,
                'object_repr': 'لابتوب Dell Latitude 5540',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'url_path': '/api/inventory/products/',
                'new_values': {'name': 'لابتوب Dell Latitude 5540', 'sku': 'LAP-DELL-5540', 'quantity': 25},
                'created_at': timezone.now() - timedelta(hours=1),
            },
            {
                'user': users[0] if len(users) > 0 else admin_user,
                'action': 'update',
                'model_name': 'SalesOrder',
                'object_id': 1,
                'object_repr': 'SO-20240301-0001',
                'ip_address': '192.168.1.101',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'url_path': '/api/sales/orders/1/',
                'old_values': {'status': 'draft'},
                'new_values': {'status': 'confirmed'},
                'created_at': timezone.now() - timedelta(minutes=45),
            },
            {
                'user': admin_user,
                'action': 'export',
                'model_name': 'Product',
                'object_id': None,
                'object_repr': 'تصدير المنتجات',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'url_path': '/api/export/products/',
                'created_at': timezone.now() - timedelta(minutes=30),
            },
            {
                'user': users[1] if len(users) > 1 else admin_user,
                'action': 'create',
                'model_name': 'PurchaseOrder',
                'object_id': 1,
                'object_repr': 'PO-20240301-0001',
                'ip_address': '192.168.1.102',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'url_path': '/api/purchases/orders/',
                'new_values': {'supplier': 'شركة التقنية المتقدمة', 'total_amount': '42000.00'},
                'created_at': timezone.now() - timedelta(minutes=15),
            },
            {
                'user': admin_user,
                'action': 'status_change',
                'model_name': 'LeaveRequest',
                'object_id': 1,
                'object_repr': 'طلب إجازة - عبدالله محمد',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'url_path': '/api/hr/leaves/1/approve/',
                'old_values': {'status': 'pending'},
                'new_values': {'status': 'approved'},
                'created_at': timezone.now() - timedelta(minutes=5),
            },
            {
                'user': admin_user,
                'action': 'backup',
                'model_name': 'System',
                'object_id': None,
                'object_repr': 'نسخ احتياطي يدوي',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'url_path': '/api/maintenance/backup/create/',
                'new_values': {'backup_type': 'manual', 'status': 'completed'},
                'created_at': timezone.now() - timedelta(minutes=1),
            },
        ]

        created_count = 0
        for log_data in logs_data:
            created_at = log_data.pop('created_at', None)
            log = AuditLog.objects.create(**log_data)
            if created_at:
                log.created_at = created_at
                log.save(update_fields=['created_at'])
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Audit Logs: {created_count} created'
            )
        )
