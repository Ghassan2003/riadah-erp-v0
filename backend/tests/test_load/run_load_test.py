#!/usr/bin/env python
"""
سكريبت تشغيل اختبارات الضغط (Locust) لنظام ERP.
Run script for ERP System Load Tests.

الاستخدام:
    python tests/test_load/run_load_test.py

الخيارات:
    --users       عدد المستخدمين المتزامنين (الافتراضي: 50)
    --spawn-rate  معدل ظهور المستخدمين (الافتراضي: 5)
    --duration    مدة الاختبار (الافتراضي: 5m)
    --url         رابط الخادم (الافتراضي: http://localhost:8000)
    --stress      تفعيل وضع الضغط الشديد
"""

import os
import sys
import subprocess
import argparse
import time


def main():
    parser = argparse.ArgumentParser(description='ERP System Load Test Runner')
    parser.add_argument('--users', type=int, default=50, help='Number of concurrent users')
    parser.add_argument('--spawn-rate', type=int, default=5, help='User spawn rate per second')
    parser.add_argument('--duration', default='5m', help='Test duration (e.g., 30s, 5m, 1h)')
    parser.add_argument('--url', default='http://localhost:8000', help='Target URL')
    parser.add_argument('--stress', action='store_true', help='Enable stress mode (high intensity)')
    args = parser.parse_args()

    # Set up Django
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    backend_dir = os.path.abspath(backend_dir)
    sys.path.insert(0, backend_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    import django
    django.setup()

    # Create test user
    from users.models import User
    user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'load@test.com',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
        },
    )
    if created:
        user.set_password('LoadTest@1234!')
        user.save()
        print(f'[INFO] Created test user: admin_test')
    else:
        print(f'[INFO] Using existing test user: admin_test')

    # Build Locust command
    locustfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locust_erp.py')

    if args.stress:
        users = args.users * 3
        spawn_rate = args.spawn_rate * 3
        print(f'\n[STRESS MODE] {users} users, {spawn_rate}/s spawn rate')
    else:
        users = args.users
        spawn_rate = args.spawn_rate
        print(f'\n[LOAD TEST] {users} users, {spawn_rate}/s spawn rate, {args.duration} duration')

    print(f'[INFO] Target: {args.url}')
    print(f'[INFO] Starting load test...\n')

    cmd = [
        sys.executable, '-m', 'locust',
        '-f', locustfile,
        '--host', args.url,
        '--headless',
        '-u', str(users),
        '-r', str(spawn_rate),
        '-t', args.duration,
        '--html', os.path.join(backend_dir, 'load_test_report.html'),
        '--csv', os.path.join(backend_dir, 'load_test_results'),
    ]

    print(f'[CMD] {" ".join(cmd)}')
    print('=' * 60)

    try:
        # Add locust to PATH
        os.environ['PATH'] = os.path.expanduser('~/.local/bin') + ':' + os.environ.get('PATH', '')
        subprocess.run(cmd, cwd=backend_dir)
    except KeyboardInterrupt:
        print('\n[INFO] Load test interrupted by user')
    except FileNotFoundError:
        print('[ERROR] Locust not found. Install with: pip install locust')
        print('[INFO] Alternatively, run threading stress tests:')
        print('  python manage.py test tests.test_load.test_threading_stress -v2')
        sys.exit(1)

    print('\n' + '=' * 60)
    print('[INFO] Load test completed!')
    print(f'[INFO] HTML report: {os.path.join(backend_dir, "load_test_report.html")}')
    print(f'[INFO] CSV results: {os.path.join(backend_dir, "load_test_results")}')


if __name__ == '__main__':
    main()
