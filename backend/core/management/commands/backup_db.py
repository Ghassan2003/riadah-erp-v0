"""
Management command to create database backup.
Usage: python manage.py backup_db
"""

import os
import zipfile
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = 'Create a database backup as JSON + ZIP file'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', type=str, default=None, help='Output directory')
        parser.add_argument('--models', type=str, default='', help='Comma-separated model list (app.Model)')
        parser.add_argument('--indent', type=int, default=2, help='JSON indent')

    def handle(self, *args, **options):
        output_dir = options['output_dir'] or os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f'erp_backup_{timestamp}'
        json_path = os.path.join(output_dir, f'{base_filename}.json')
        zip_path = os.path.join(output_dir, f'{base_filename}.zip')

        # Get all local apps
        local_apps = [
            'users', 'inventory', 'sales', 'accounting',
            'hr', 'purchases', 'documents', 'projects',
            'notifications', 'auditlog',
        ]

        # Build fixture list
        models_to_dump = []
        models_filter = options.get('models', '')
        if models_filter:
            model_list = [m.strip() for m in models_filter.split(',')]
            for m in model_list:
                models_to_dump.append(m)
        else:
            for app_label in local_apps:
                try:
                    app_config = apps.get_app_config(app_label)
                    for model in app_config.get_models():
                        models_to_dump.append(f'{app_label}.{model.__name__}')
                except LookupError:
                    pass

        # Call dumpdata
        from django.core.management import call_command
        with open(json_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', *models_to_dump, stdout=f, indent=options['indent'])

        # Create ZIP
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(json_path, os.path.basename(json_path))

        # Clean up JSON
        os.remove(json_path)

        file_size = os.path.getsize(zip_path)
        size_mb = round(file_size / (1024 * 1024), 2)

        self.stdout.write(self.style.SUCCESS(
            'تم إنشاء النسخة الاحتياطية بنجاح'
        ))
        self.stdout.write(f'المسار: {zip_path}')
        self.stdout.write(f'الحجم: {size_mb} MB')
        self.stdout.write(f'عدد النماذج: {len(models_to_dump)}')
