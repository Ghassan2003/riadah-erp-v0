"""
Management command to create a default admin user for initial setup.
Usage: python manage.py create_admin
"""

from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Creates a default admin user for the ERP system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', type=str, default='admin',
            help='Admin username (default: admin)'
        )
        parser.add_argument(
            '--email', type=str, default='admin@erp-system.com',
            help='Admin email (default: admin@erp-system.com)'
        )
        parser.add_argument(
            '--password', type=str, default='admin123',
            help='Admin password (default: admin123)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists. Skipping.')
            )
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='admin',
            first_name='مدير',
            last_name='النظام',
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Admin user created successfully!\n'
                f'  Username: {username}\n'
                f'  Email: {email}\n'
                f'  Password: {password}'
            )
        )
