"""
أمر إدارة لتشغيل المهام المجدولة المستحقة.
الاستخدام: python manage.py run_cron_jobs [--job-id ID] [--force]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Run due scheduled tasks (Cron Jobs)'

    def add_arguments(self, parser):
        parser.add_argument('--job-id', type=int, default=None, help='Run a specific job by ID')
        parser.add_argument('--force', action='store_true', help='Force run regardless of schedule')
        parser.add_argument('--all', action='store_true', help='Run all active jobs regardless of schedule')

    def handle(self, *args, **options):
        from maintenance.models import CronJob
        from maintenance.tasks import run_cron_task, run_all_due_tasks

        if options['job_id']:
            try:
                job = CronJob.objects.get(pk=options['job_id'])
                self.stdout.write(f'Running job: {job.name}...')
                result = run_cron_task(job, force=options['force'])
                self.stdout.write(self.style.SUCCESS(
                    f"Status: {result.get('status')}, Duration: {result.get('duration', 0)}s"
                ))
            except CronJob.DoesNotExist:
                self.stderr.write(self.style.ERROR('Job not found'))

        elif options['all']:
            jobs = CronJob.objects.filter(status='active')
            self.stdout.write(f'Running {jobs.count()} active jobs...')
            for job in jobs:
                self.stdout.write(f'  - {job.name}...')
                result = run_cron_task(job, force=True)
                status = result.get('status', 'unknown')
                icon = '✓' if status == 'success' else '✗'
                self.stdout.write(f'    {icon} {status} ({result.get("duration", 0)}s)')
            self.stdout.write(self.style.SUCCESS('Done!'))

        else:
            self.stdout.write('Checking due tasks...')
            results = run_all_due_tasks()
            if not results:
                self.stdout.write('No due tasks found.')
            else:
                for r in results:
                    status = r.get('status', 'unknown')
                    icon = '✓' if status == 'success' else '✗'
                    self.stdout.write(f'{icon} {r["job_name"]}: {status}')
