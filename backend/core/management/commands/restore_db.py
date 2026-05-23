"""
Management command to restore database from backup.
Usage: python manage.py restore_db /path/to/backup.zip
"""

import os
import zipfile

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Restore database from a backup ZIP file'

    def add_arguments(self, parser):
        parser.add_argument('backup_file', type=str, help='Path to backup ZIP file')

    def handle(self, *args, **options):
        backup_file = options['backup_file']

        if not os.path.exists(backup_file):
            self.stderr.write(self.style.ERROR(f'الملف غير موجود: {backup_file}'))
            return

        # Extract ZIP
        extracted = False
        json_file = None
        os.makedirs('/tmp/erp_restore/', exist_ok=True)
        with zipfile.ZipFile(backup_file, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.json'):
                    zf.extract(name, '/tmp/erp_restore/')
                    json_file = f'/tmp/erp_restore/{name}'
                    extracted = True
                    break

        if not extracted or not json_file:
            self.stderr.write(self.style.ERROR('لم يتم العثور على ملف JSON في الأرشيف'))
            return

        self.stdout.write(self.style.WARNING('سيتم استبدال جميع البيانات الحالية'))
        confirm = input('هل أنت متأكد؟ (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write('تم الإلغاء')
            return

        from django.core.management import call_command
        call_command('loaddata', json_file)

        # Clean up
        if os.path.exists(json_file):
            os.remove(json_file)
        if os.path.exists('/tmp/erp_restore/'):
            try:
                os.rmdir('/tmp/erp_restore/')
            except OSError:
                pass

        self.stdout.write(self.style.SUCCESS('تم استعادة البيانات بنجاح'))
