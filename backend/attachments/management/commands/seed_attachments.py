"""
Management command to create sample attachments for testing.
Usage: python manage.py seed_attachments
Note: This command creates metadata only (no actual files).
"""

from django.core.management.base import BaseCommand
from attachments.models import Attachment
from users.models import User
from django.utils import timezone


class Command(BaseCommand):
    help = 'Creates sample attachment metadata for testing (no actual files)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing attachments before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Attachment.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all attachments.'))

        admin_user = User.objects.filter(role='admin').first()

        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found. Create users first.'))
            return

        # Seed sample attachment metadata
        attachments_data = [
            {
                'file_name': 'عقد_خدمة_2024.pdf',
                'file_type': 'pdf',
                'file_size': 1048576,
                'description': 'عقد خدمة الصيانة السنوي للشركة',
                'category': 'عقود',
                'is_public': False,
            },
            {
                'file_name': 'تقرير_الميزانية_Q1.xlsx',
                'file_type': 'xlsx',
                'file_size': 524288,
                'description': 'تقرير الميزانية للربع الأول',
                'category': 'تقارير',
                'is_public': False,
            },
            {
                'file_name': 'دليل_المستخدم.pdf',
                'file_type': 'pdf',
                'file_size': 2097152,
                'description': 'دليل استخدام نظام ريادة ERP',
                'category': 'توثيق',
                'is_public': True,
            },
            {
                'file_name': 'محضر_اجتماع_مارس.docx',
                'file_type': 'docx',
                'file_size': 262144,
                'description': 'محضر اجتماع الإدارة الشهري',
                'category': 'اجتماعات',
                'is_public': False,
            },
            {
                'file_name': 'عرض_أسعار_أثاث.pdf',
                'file_type': 'pdf',
                'file_size': 157286,
                'description': 'عرض أسعار أثاث مكاتب جديد',
                'category': 'عروض أسعار',
                'is_public': False,
            },
        ]

        created_count = 0
        for att_data in attachments_data:
            Attachment.objects.create(
                **att_data,
                uploaded_by=admin_user,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Attachments: {created_count} created (metadata only, no files)'
            )
        )
