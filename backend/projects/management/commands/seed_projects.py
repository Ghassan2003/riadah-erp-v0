"""
Management command to create sample projects for testing.
Usage: python manage.py seed_projects
"""

from django.core.management.base import BaseCommand
from projects.models import Project, ProjectTask, TaskComment, ProjectExpense
from users.models import User
from sales.models import Customer
from django.utils import timezone
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Creates sample projects with tasks, comments, and expenses for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing project data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            ProjectExpense.objects.all().delete()
            TaskComment.objects.all().delete()
            ProjectTask.objects.all().delete()
            Project.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all project data.'))

        admin_user = User.objects.filter(role='admin').first()
        pm_users = list(User.objects.filter(role='project_manager'))
        other_users = list(User.objects.filter(is_active=True))

        if not pm_users:
            pm_users = [admin_user] if admin_user else []

        if not pm_users:
            self.stdout.write(self.style.ERROR('No users found. Create users first.'))
            return

        # Seed projects
        projects_data = [
            {
                'name': 'مشروع تطوير نظام ERP',
                'name_en': 'ERP System Development',
                'description': 'تطوير نظام تخطيط موارد المؤسسات المتكامل لإدارة جميع العمليات التشغيلية',
                'status': 'active',
                'priority': 'high',
                'start_date': date.today() - timedelta(days=90),
                'end_date': date.today() + timedelta(days=180),
                'budget': 500000.00,
                'spent': 125000.00,
                'progress': 35,
                'manager': pm_users[0],
            },
            {
                'name': 'مشروع إنشاء متجر إلكتروني',
                'name_en': 'E-Commerce Platform',
                'description': 'إنشاء منصة تجارة إلكترونية متكاملة مع بوابة دفع',
                'status': 'active',
                'priority': 'critical',
                'start_date': date.today() - timedelta(days=45),
                'end_date': date.today() + timedelta(days=90),
                'budget': 300000.00,
                'spent': 95000.00,
                'progress': 55,
                'manager': pm_users[0] if len(pm_users) > 0 else admin_user,
            },
            {
                'name': 'مشروع توثيق الإجراءات',
                'name_en': 'Procedures Documentation',
                'description': 'توثيق جميع الإجراءات التشغيلية والسياسات الداخلية للشركة',
                'status': 'planning',
                'priority': 'medium',
                'start_date': date.today() + timedelta(days=7),
                'end_date': date.today() + timedelta(days=60),
                'budget': 50000.00,
                'spent': 0,
                'progress': 0,
                'manager': pm_users[1] if len(pm_users) > 1 else admin_user,
            },
            {
                'name': 'مشروع ترقية البنية التحتية',
                'name_en': 'Infrastructure Upgrade',
                'description': 'ترقية خوادم وشبكة الشركة لتحسين الأداء والأمان',
                'status': 'completed',
                'priority': 'high',
                'start_date': date.today() - timedelta(days=120),
                'end_date': date.today() - timedelta(days=15),
                'budget': 200000.00,
                'spent': 185000.00,
                'progress': 100,
                'manager': pm_users[0] if len(pm_users) > 0 else admin_user,
            },
            {
                'name': 'مشروع تطبيق الموبايل',
                'name_en': 'Mobile App Development',
                'description': 'تطوير تطبيق جوال لنظام ERP للوصول السريع',
                'status': 'on_hold',
                'priority': 'low',
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=120),
                'budget': 150000.00,
                'spent': 20000.00,
                'progress': 10,
                'manager': pm_users[1] if len(pm_users) > 1 else admin_user,
            },
        ]

        created_projects = 0
        for proj_data in projects_data:
            _, created = Project.objects.get_or_create(
                name=proj_data['name'],
                defaults={
                    **proj_data,
                    'created_by': admin_user,
                },
            )
            if created:
                created_projects += 1

        self.stdout.write(f'Created {created_projects} project(s).')

        # Seed tasks for active projects
        projects = list(Project.objects.filter(status='active'))
        tasks_data = [
            {
                'project': projects[0] if len(projects) > 0 else None,
                'title': 'تصميم قاعدة البيانات',
                'description': 'تصميم مخطط قاعدة البيانات وجميع الجداول والعلاقات',
                'status': 'done',
                'priority': 'high',
                'due_date': date.today() - timedelta(days=60),
            },
            {
                'project': projects[0] if len(projects) > 0 else None,
                'title': 'تطوير واجهة المستخدم',
                'description': 'بناء واجهة المستخدم باستخدام React وTailwindCSS',
                'status': 'in_progress',
                'priority': 'high',
                'due_date': date.today() + timedelta(days=30),
            },
            {
                'project': projects[0] if len(projects) > 0 else None,
                'title': 'تطوير API الخلفية',
                'description': 'بناء واجهات API باستخدام Django REST Framework',
                'status': 'in_progress',
                'priority': 'high',
                'due_date': date.today() + timedelta(days=45),
            },
            {
                'project': projects[0] if len(projects) > 0 else None,
                'title': 'اختبار النظام',
                'description': 'كتابة وتنفيذ اختبارات الوحدة والتكامل',
                'status': 'todo',
                'priority': 'medium',
                'due_date': date.today() + timedelta(days=90),
            },
            {
                'project': projects[1] if len(projects) > 1 else None,
                'title': 'تصميم واجهة المتجر',
                'description': 'تصميم واجهات المستخدم للواجهة الأمامية والخلفية',
                'status': 'done',
                'priority': 'high',
                'due_date': date.today() - timedelta(days=20),
            },
            {
                'project': projects[1] if len(projects) > 1 else None,
                'title': 'ربط بوابة الدفع',
                'description': 'ربط بوابة الدفع الإلكتروني مع المنصة',
                'status': 'review',
                'priority': 'critical',
                'due_date': date.today() + timedelta(days=10),
            },
        ]

        created_tasks = 0
        for task_data in tasks_data:
            if task_data['project'] is None:
                continue
            project = task_data.pop('project')
            _, created = ProjectTask.objects.get_or_create(
                project=project,
                title=task_data['title'],
                defaults={
                    **task_data,
                    'assigned_to': other_users[0] if other_users else admin_user,
                    'created_by': admin_user,
                },
            )
            if created:
                created_tasks += 1

        self.stdout.write(f'Created {created_tasks} task(s).')

        # Seed expenses
        expenses_data = [
            {
                'project': projects[0] if len(projects) > 0 else None,
                'title': 'رسوم استضافة الخوادم',
                'expense_type': 'equipment',
                'amount': 15000.00,
                'date': date.today() - timedelta(days=10),
                'description': 'رسوم استضافة سحابية لمدة 6 أشهر',
            },
            {
                'project': projects[0] if len(projects) > 0 else None,
                'title': 'رواتب فريق التطوير',
                'expense_type': 'labor',
                'amount': 80000.00,
                'date': date.today() - timedelta(days=30),
                'description': 'رواتب شهرية لفريق التطوير',
            },
            {
                'project': projects[1] if len(projects) > 1 else None,
                'title': 'رسوم ترخيص التصميم',
                'expense_type': 'equipment',
                'amount': 5000.00,
                'date': date.today() - timedelta(days=15),
                'description': 'ترخيص أدوات التصميم',
            },
        ]

        created_expenses = 0
        for exp_data in expenses_data:
            if exp_data['project'] is None:
                continue
            project = exp_data.pop('project')
            _, created = ProjectExpense.objects.get_or_create(
                project=project,
                title=exp_data['title'],
                defaults={
                    **exp_data,
                    'created_by': admin_user,
                },
            )
            if created:
                created_expenses += 1

        self.stdout.write(f'Created {created_expenses} expense(s).')

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Projects: {created_projects} created\n'
                f'  Tasks: {created_tasks} created\n'
                f'  Expenses: {created_expenses} created'
            )
        )
