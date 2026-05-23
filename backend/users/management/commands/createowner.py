"""
Dedicated command to create the business owner (admin superuser).

Usage:
    python manage.py createowner --username admin --email admin@riadah.com
"""

import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a business owner account with full admin role and superuser privileges'

    def add_arguments(self, parser):
        parser.add_argument('--username', dest='username', required=True, type=str)
        parser.add_argument('--email', dest='email', default='', type=str)
        parser.add_argument('--password', dest='password', default=None, type=str)
        parser.add_argument('--phone', dest='phone', default='', type=str)
        parser.add_argument('--first_name', dest='first_name', default='', type=str)
        parser.add_argument('--last_name', dest='last_name', default='', type=str)

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists!')

        if not password:
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            if password != password_confirm:
                raise CommandError('Passwords do not match!')
            if len(password) < 8:
                raise CommandError('Password must be at least 8 characters.')

        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=options.get('first_name', ''),
                last_name=options.get('last_name', ''),
                phone=options.get('phone', ''),
            )
        except Exception as e:
            raise CommandError(f'Error creating user: {e}')

        if user.role != 'admin':
            user.role = 'admin'
            user.save(update_fields=['role'])

        user.record_password_change(password)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('  Business owner created successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'  Username : {user.username}'))
        self.stdout.write(self.style.SUCCESS(f'  Email    : {user.email or "-"}'))
        self.stdout.write(self.style.SUCCESS(f'  Role     : {user.get_role_display()}'))
        self.stdout.write(self.style.SUCCESS(f'  Superuser: Yes'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
