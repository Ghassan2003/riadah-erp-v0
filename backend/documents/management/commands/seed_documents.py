"""
Management command to create sample document categories and documents for testing.
Usage: python manage.py seed_documents
"""

from django.core.management.base import BaseCommand
from documents.models import DocumentCategory, Document
from users.models import User
from django.utils import timezone


class Command(BaseCommand):
    help = 'Creates sample document categories and documents for testing the documents module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing documents before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Document.objects.all().delete()
            DocumentCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all document data.'))

        # Seed categories
        categories_data = [
            {
                'name': 'عقود',
                'name_en': 'Contracts',
                'description': 'العقود والاتفاقيات',
            },
            {
                'name': 'تقارير مالية',
                'name_en': 'Financial Reports',
                'description': 'التقارير والبيانات المالية',
            },
            {
                'name': 'سياسات وإجراءات',
                'name_en': 'Policies & Procedures',
                'description': 'السياسات الداخلية والإجراءات التشغيلية',
            },
            {
                'name': 'محاضر اجتماعات',
                'name_en': 'Meeting Minutes',
                'description': 'محاضر الاجتماعات والاجتماعات الإدارية',
            },
            {
                'name': 'مستندات مشاريع',
                'name_en': 'Project Documents',
                'description': 'المستندات المتعلقة بالمشاريع',
            },
            {
                'name': 'سير ذاتية',
                'name_en': 'Resumes & CVs',
                'description': 'سير ذاتية للموظفين والمتقدمين',
            },
        ]

        created_categories = 0
        for cat_data in categories_data:
            _, created = DocumentCategory.objects.update_or_create(
                name=cat_data['name'],
                defaults=cat_data,
            )
            if created:
                created_categories += 1

        self.stdout.write(f'Created {created_categories} categories(s).')

        # Seed sample documents (metadata only, no actual files)
        admin_user = User.objects.filter(role='admin').first()
        categories = list(DocumentCategory.objects.all())

        if not categories:
            self.stdout.write(self.style.WARNING('No categories found.'))
            return

        documents_data = [
            {
                'title': 'دليل سياسة الأمن والسلامة',
                'description': 'دليل شامل لسياسات الأمن والسلامة في بيئة العمل',
                'category': categories[2],
                'module': 'general',
            },
            {
                'title': 'تقرير الميزانية الربع سنوي Q1',
                'description': 'تقرير الميزانية للربع الأول من العام الحالي',
                'category': categories[1],
                'module': 'accounting',
            },
            {
                'title': 'محضر اجتماع الإدارة الشهري',
                'description': 'محضر اجتماع الإدارة التنفيذية الشهري',
                'category': categories[3],
                'module': 'general',
            },
            {
                'title': 'خطة مشروع التوسعة',
                'description': 'خطة تفصيلية لمشروع توسعة مقر الشركة',
                'category': categories[4],
                'module': 'projects',
            },
            {
                'title': 'عقد خدمة الصيانة السنوي',
                'description': 'عقد صيانة الأجهزة والمعدات للعام الحالي',
                'category': categories[0],
                'module': 'general',
            },
        ]

        created_docs = 0
        for doc_data in documents_data:
            _, created = Document.objects.get_or_create(
                title=doc_data['title'],
                defaults={
                    **doc_data,
                    'uploaded_by': admin_user,
                },
            )
            if created:
                created_docs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Categories: {created_categories} created\n'
                f'  Documents: {created_docs} created (metadata only)'
            )
        )
