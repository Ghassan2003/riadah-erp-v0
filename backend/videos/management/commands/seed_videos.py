"""
Management command to create sample video categories and instructions for testing.
Usage: python manage.py seed_videos
"""

from django.core.management.base import BaseCommand
from videos.models import VideoCategory, VideoInstruction
from users.models import User


class Command(BaseCommand):
    help = 'Creates sample video categories and instructions for testing the videos module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing video data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            from videos.models import VideoComment, VideoProgress
            VideoComment.objects.all().delete()
            VideoProgress.objects.all().delete()
            VideoInstruction.objects.all().delete()
            VideoCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all video data.'))

        admin_user = User.objects.filter(role='admin').first()

        # Seed categories
        categories_data = [
            {
                'name_ar': 'البدء مع النظام',
                'name_en': 'Getting Started',
                'description_ar': 'فيديوهات للبدء في استخدام نظام ريادة ERP',
                'description_en': 'Videos to get started with Riadah ERP',
                'icon': 'PlayCircle',
                'color': '#3B82F6',
                'order': 1,
            },
            {
                'name_ar': 'إدارة المخزون',
                'name_en': 'Inventory Management',
                'description_ar': 'تعلم إدارة المنتجات والمخزون',
                'description_en': 'Learn to manage products and inventory',
                'icon': 'Package',
                'color': '#10B981',
                'order': 2,
            },
            {
                'name_ar': 'المبيعات والفواتير',
                'name_en': 'Sales & Invoicing',
                'description_ar': 'إدارة المبيعات وإنشاء الفواتير',
                'description_en': 'Manage sales and create invoices',
                'icon': 'ShoppingCart',
                'color': '#F59E0B',
                'order': 3,
            },
            {
                'name_ar': 'المحاسبة والتقارير',
                'name_en': 'Accounting & Reports',
                'description_ar': 'العمليات المحاسبية والتقارير المالية',
                'description_en': 'Accounting operations and financial reports',
                'icon': 'BarChart3',
                'color': '#8B5CF6',
                'order': 4,
            },
            {
                'name_ar': 'الموارد البشرية',
                'name_en': 'Human Resources',
                'description_ar': 'إدارة الموظفين والرواتب والحضور',
                'description_en': 'Manage employees, payroll, and attendance',
                'icon': 'Users',
                'color': '#EF4444',
                'order': 5,
            },
            {
                'name_ar': 'الإعدادات المتقدمة',
                'name_en': 'Advanced Settings',
                'description_ar': 'إعدادات النظام المتقدمة والتخصيص',
                'description_en': 'Advanced system settings and customization',
                'icon': 'Settings',
                'color': '#6366F1',
                'order': 6,
            },
        ]

        created_categories = 0
        for cat_data in categories_data:
            _, created = VideoCategory.objects.update_or_create(
                name_ar=cat_data['name_ar'],
                defaults=cat_data,
            )
            if created:
                created_categories += 1

        self.stdout.write(f'Created {created_categories} categories(s).')

        # Seed video instructions
        categories = list(VideoCategory.objects.all())

        videos_data = [
            {
                'title_ar': 'مقدمة في نظام ريادة ERP',
                'title_en': 'Introduction to Riadah ERP',
                'description_ar': 'نظرة عامة على نظام ريادة ERP ومميزاته الرئيسية وكيفية التنقل فيه',
                'description_en': 'Overview of Riadah ERP, its main features, and how to navigate',
                'category': 'getting_started',
                'category_model': categories[0] if len(categories) > 0 else None,
                'duration_seconds': 300,
                'difficulty_level': 'beginner',
                'is_featured': True,
                'tags': ['مقدمة', 'تعريف', 'نظرة عامة', 'introduction'],
                'order': 1,
            },
            {
                'title_ar': 'تسجيل الدخول وإعداد الملف الشخصي',
                'title_en': 'Login and Profile Setup',
                'description_ar': 'كيفية تسجيل الدخول للمرة الأولى وإعداد الملف الشخصي والمصادقة الثنائية',
                'description_en': 'How to login for the first time, set up profile, and enable 2FA',
                'category': 'getting_started',
                'category_model': categories[0] if len(categories) > 0 else None,
                'duration_seconds': 240,
                'difficulty_level': 'beginner',
                'is_featured': True,
                'tags': ['تسجيل دخول', 'ملف شخصي', 'مصادقة ثنائية'],
                'order': 2,
            },
            {
                'title_ar': 'إضافة منتج جديد',
                'title_en': 'Adding a New Product',
                'description_ar': 'شرح مفصل لكيفية إضافة منتج جديد للمخزون مع تحديد الأسعار والمستويات',
                'description_en': 'Detailed guide on adding a new product to inventory with pricing and levels',
                'category': 'inventory',
                'category_model': categories[1] if len(categories) > 1 else None,
                'duration_seconds': 420,
                'difficulty_level': 'beginner',
                'tags': ['منتج', 'مخزون', 'إضافة', 'product'],
                'order': 1,
            },
            {
                'title_ar': 'إدارة أوامر الشراء',
                'title_en': 'Managing Purchase Orders',
                'description_ar': 'كيفية إنشاء أوامر الشراء وتأكيدها وتتبع حالة الاستلام',
                'description_en': 'How to create, confirm, and track purchase orders',
                'category': 'inventory',
                'category_model': categories[1] if len(categories) > 1 else None,
                'duration_seconds': 360,
                'difficulty_level': 'intermediate',
                'tags': ['شراء', 'أمر شراء', 'مورد', 'purchase'],
                'order': 2,
            },
            {
                'title_ar': 'إنشاء فاتورة مبيعات',
                'title_en': 'Creating a Sales Invoice',
                'description_ar': 'خطوات إنشاء فاتورة مبيعات جديدة وإرسالها للعميل',
                'description_en': 'Steps to create a new sales invoice and send it to the customer',
                'category': 'sales',
                'category_model': categories[2] if len(categories) > 2 else None,
                'duration_seconds': 300,
                'difficulty_level': 'beginner',
                'tags': ['فاتورة', 'مبيعات', 'invoice'],
                'order': 1,
            },
            {
                'title_ar': 'نقطة البيع POS',
                'title_en': 'Point of Sale (POS)',
                'description_ar': 'شرح نظام نقطة البيع وكيفية إجراء عمليات البيع والتحصيل',
                'description_en': 'POS system overview and how to process sales and payments',
                'category': 'sales',
                'category_model': categories[2] if len(categories) > 2 else None,
                'duration_seconds': 480,
                'difficulty_level': 'intermediate',
                'is_featured': True,
                'tags': ['نقطة بيع', 'POS', 'تحصيل', 'cashier'],
                'order': 2,
            },
            {
                'title_ar': 'القوائم المالية والتقارير',
                'title_en': 'Financial Statements & Reports',
                'description_ar': 'شرح القوائم المالية وقائمة الدخل والميزانية العمومية',
                'description_en': 'Financial statements explanation: income statement and balance sheet',
                'category': 'accounting',
                'category_model': categories[3] if len(categories) > 3 else None,
                'duration_seconds': 600,
                'difficulty_level': 'advanced',
                'tags': ['محاسبة', 'تقارير', 'قوائم مالية', 'reports'],
                'order': 1,
            },
            {
                'title_ar': 'إدارة الموظفين والرواتب',
                'title_en': 'Employee & Payroll Management',
                'description_ar': 'إضافة موظفين وإدارة الرواتب والحضور والإجازات',
                'description_en': 'Adding employees, managing payroll, attendance, and leaves',
                'category': 'hr',
                'category_model': categories[4] if len(categories) > 4 else None,
                'duration_seconds': 540,
                'difficulty_level': 'intermediate',
                'tags': ['موظفين', 'رواتب', 'حضور', 'HR'],
                'order': 1,
            },
        ]

        created_videos = 0
        for vid_data in videos_data:
            _, created = VideoInstruction.objects.get_or_create(
                title_ar=vid_data['title_ar'],
                defaults={
                    **vid_data,
                    'created_by': admin_user,
                },
            )
            if created:
                created_videos += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Categories: {created_categories} created\n'
                f'  Videos: {created_videos} created (metadata only, no video files)'
            )
        )
