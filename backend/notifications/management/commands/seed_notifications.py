"""
Management command to create sample notifications for testing.
Usage: python manage.py seed_notifications
"""

from django.core.management.base import BaseCommand
from notifications.models import Notification
from users.models import User
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Creates sample notifications for testing the notifications module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing notifications before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Notification.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all notifications.'))

        admin_user = User.objects.filter(role='admin').first()
        users = list(User.objects.filter(is_active=True))

        if not users:
            self.stdout.write(self.style.ERROR('No users found. Create users first.'))
            return

        # Seed sample notifications
        notifications_data = [
            {
                'recipient': users[0],
                'title': 'مرحباً بك في نظام ريادة ERP',
                'message': 'تم تفعيل حسابك بنجاح. يمكنك الآن البدء في استخدام النظام والوصول لجميع الوحدات المتاحة.',
                'notification_type': 'system',
                'priority': 'normal',
                'is_read': True,
            },
            {
                'recipient': users[0],
                'title': 'طلب شراء جديد بانتظار الموافقة',
                'message': 'تم إنشاء طلب شراء جديد من مورد شركة التقنية المتقدمة بقيمة 42,000 ريال. يرجى مراجعة والموافقة.',
                'notification_type': 'order',
                'priority': 'high',
                'link': '/purchases',
                'is_read': False,
            },
            {
                'recipient': users[0],
                'title': 'تنبيه مخزون منخفض',
                'message': 'المنتج "لوحة مفاتيح ميكانيكية Keychron K2" وصل إلى الحد الأدنى (3 وحدات). يرجى إنشاء طلب شراء.',
                'notification_type': 'inventory',
                'priority': 'urgent',
                'link': '/products',
                'is_read': False,
            },
            {
                'recipient': users[0],
                'title': 'فاتورة متأخرة عن السداد',
                'message': 'فاتورة رقم INV-2024-0015 متأخرة عن السداد منذ 15 يوماً. يرجى متابعة العميل.',
                'notification_type': 'invoice',
                'priority': 'high',
                'link': '/invoicing',
                'is_read': False,
            },
            {
                'recipient': users[0],
                'title': 'طلب إجازة جديد',
                'message': 'قدم الموظف عبدالله محمد طلب إجازة من التاريخ 2024-03-15 إلى 2024-03-20.',
                'notification_type': 'leave',
                'priority': 'normal',
                'link': '/attendance-leaves',
                'is_read': True,
            },
        ]

        # Add notifications for other users too
        for user in users[1:3]:
            notifications_data.extend([
                {
                    'recipient': user,
                    'title': 'مهمة جديدة مسندة إليك',
                    'message': 'تم اسناد مهمة "تطوير واجهة المستخدم" في مشروع ERP إليك. يرجى المراجعة والبدء.',
                    'notification_type': 'task',
                    'priority': 'high',
                    'link': '/projects',
                    'is_read': False,
                },
                {
                    'recipient': user,
                    'title': 'تم إصدار راتب شهر فبراير',
                    'message': 'تم إصدار راتب شهر فبراير 2024 بنجاح. يمكنك الاطلاع على التفاصيل في قسم الرواتب.',
                    'notification_type': 'payroll',
                    'priority': 'normal',
                    'link': '/payroll',
                    'is_read': True,
                },
            ])

        created_count = 0
        for notif_data in notifications_data:
            _, created = Notification.objects.get_or_create(
                recipient=notif_data['recipient'],
                title=notif_data['title'],
                defaults={
                    **notif_data,
                    'sender': admin_user,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Notifications: {created_count} created'
            )
        )
