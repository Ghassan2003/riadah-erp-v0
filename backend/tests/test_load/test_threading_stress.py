"""
اختبارات الضغط والأداء باستخدام Python - متوافقة مع بيئة اختبار SQLite.
يمكن تشغيلها مباشرة: python manage.py test tests.test_load.test_threading_stress

ملاحظة هامة: اختبارات التزامن الحقيقي (multi-threading) تتطلب PostgreSQL.
في بيئة الاختبار مع SQLite، نستخدم اختبارات الأداء المتتالية التي تقيس
زمن الاستجابة والإنتاجية (throughput) بشكل فعال.
Note: True concurrency tests require PostgreSQL. SQLite tests use sequential
performance tests to measure response times and throughput effectively.

للتشغيل مع اختبارات الضغط الحقيقية (Locust):
    locust -f tests/test_load/locustfile.py --headless -u 50 -r 5 -t 5m
"""

import random
import pytest
import time
from rest_framework.test import APIClient


class TestPerformanceStress:
    """
    اختبارات الضغط والأداء - طلبات متتالية تحاكي الضغط على النظام.
    Performance and stress tests using sequential requests.
    These tests work with SQLite and measure response time & throughput.
    """

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """إعداد مستخدم الاختبار."""
        from users.models import User
        try:
            self.user = User.objects.get(username='stress_admin')
        except User.DoesNotExist:
            self.user = User.objects.create_superuser(
                username='stress_admin',
                email='stress@test.com',
                password='Stress@1234!',
            )
            self.user.role = 'admin'
            self.user.save()
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def test_rapid_sequential_dashboard_requests(self):
        """اختبار 50 طلب سريع متتالي للوحة التحكم."""
        client = APIClient()
        endpoint = '/api/dashboard/stats/'
        times = []
        num_requests = 50

        start_total = time.time()
        for i in range(num_requests):
            start = time.time()
            response = client.get(endpoint, **self.headers)
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        total_time = time.time() - start_total
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        throughput = num_requests / total_time

        assert avg_time < 5, f"Average {avg_time:.3f}s exceeds 5s threshold"
        assert p95_time < 8, f"P95 {p95_time:.3f}s exceeds 8s threshold"

        print(f"\n  === Sequential Dashboard Stress ({num_requests} requests) ===")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)")
        print(f"    Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        print(f"    P95: {p95_time:.3f}s")
        print(f"    Throughput: {throughput:.1f} req/s")

    def test_multi_endpoint_stress_test(self):
        """اختبار ضغط متعدد النقاط - 3 جولات من جميع نقاط النهاية الرئيسية."""
        client = APIClient()
        endpoints = [
            '/api/dashboard/stats/',
            '/api/inventory/products/',
            '/api/inventory/stats/',
            '/api/sales/orders/',
            '/api/sales/customers/',
            '/api/accounting/accounts/',
            '/api/accounting/entries/',
            '/api/hr/employees/',
            '/api/hr/departments/',
            '/api/notifications/',
            '/api/auth/profile/',
            '/api/system/info/',
            '/api/sales/stats/',
            '/api/hr/stats/',
            '/api/accounting/stats/',
        ]
        times = []
        num_requests = 45  # 3 rounds x 15 endpoints

        start_total = time.time()
        for i in range(num_requests):
            endpoint = endpoints[i % len(endpoints)]
            start = time.time()
            response = client.get(endpoint, **self.headers)
            elapsed = time.time() - start
            times.append({'endpoint': endpoint, 'time': elapsed})
            assert response.status_code == 200, f"Failed for {endpoint}: {response.status_code}"

        total_time = time.time() - start_total
        avg_time = sum(t['time'] for t in times) / len(times)
        p95_time = sorted(t['time'] for t in times)[int(len(times) * 0.95)]
        throughput = num_requests / total_time

        assert avg_time < 3, f"Average {avg_time:.3f}s exceeds 3s threshold"
        assert p95_time < 5, f"P95 {p95_time:.3f}s exceeds 5s threshold"

        print(f"\n  === Multi-Endpoint Stress ({num_requests} requests, {len(endpoints)} endpoints) ===")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)")
        print(f"    P95: {p95_time:.3f}s")
        print(f"    Throughput: {throughput:.1f} req/s")

    def test_burst_requests(self):
        """اختبار سلسلة طلبات مكثفة (burst) للوحة التحكم."""
        client = APIClient()
        endpoint = '/api/dashboard/stats/'
        burst_size = 30
        times = []

        start_total = time.time()
        for i in range(burst_size):
            start = time.time()
            response = client.get(endpoint, **self.headers)
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        total_time = time.time() - start_total
        avg_time = sum(times) / len(times)
        max_time = max(times)
        throughput = burst_size / total_time

        assert avg_time < 2, f"Average {avg_time:.3f}s exceeds 2s threshold"
        assert throughput > 5, f"Throughput {throughput:.1f} req/s below 5 req/s"

        print(f"\n  === Burst Requests ({burst_size} rapid requests) ===")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)")
        print(f"    Max: {max_time:.3f}s")
        print(f"    Throughput: {throughput:.1f} req/s")

    def test_sequential_login_stress(self):
        """اختبار 15 طلب تسجيل دخول متتالي سريع."""
        from users.models import User

        num_requests = 15
        for i in range(num_requests):
            username = f'login_stress_{i}'
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@test.com', 'role': 'sales'},
            )
            user.set_password('Stress@1234!')
            user.save()

        client = APIClient()
        times = []
        successes = 0

        start_total = time.time()
        for i in range(num_requests):
            username = f'login_stress_{i}'
            start = time.time()
            response = client.post('/api/auth/login/', {
                'username': username,
                'password': 'Stress@1234!',
            })
            elapsed = time.time() - start
            times.append(elapsed)
            if response.status_code == 200 and 'access' in response.data:
                successes += 1

        total_time = time.time() - start_total
        avg_time = sum(times) / len(times)
        throughput = num_requests / total_time

        assert successes == num_requests, f"Expected {num_requests} successful logins, got {successes}"
        assert avg_time < 3, f"Average {avg_time:.3f}s exceeds 3s threshold"

        print(f"\n  === Login Stress ({num_requests} sequential logins) ===")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)")
        print(f"    Success rate: {successes}/{num_requests} (100%)")
        print(f"    Throughput: {throughput:.1f} logins/s")

    def test_performance_baseline_all_endpoints(self):
        """اختبار خط أساس للأداء - قياس زمن الاستجابة لجميع نقاط النهاية."""
        client = APIClient()
        endpoints = {
            'dashboard': '/api/dashboard/stats/',
            'products': '/api/inventory/products/',
            'inventory_stats': '/api/inventory/stats/',
            'sales_orders': '/api/sales/orders/',
            'customers': '/api/sales/customers/',
            'sales_stats': '/api/sales/stats/',
            'accounts': '/api/accounting/accounts/',
            'journal_entries': '/api/accounting/entries/',
            'accounting_stats': '/api/accounting/stats/',
            'employees': '/api/hr/employees/',
            'departments': '/api/hr/departments/',
            'hr_stats': '/api/hr/stats/',
            'notifications': '/api/notifications/',
            'unread_count': '/api/notifications/unread-count/',
            'profile': '/api/auth/profile/',
            'my_permissions': '/api/auth/permissions/my/',
            'password_policy_info': '/api/auth/password-policy/info/',
            'system_info': '/api/system/info/',
            'audit_log': '/api/audit-log/',
            'purchase_orders': '/api/purchases/orders/',
            'suppliers': '/api/purchases/suppliers/',
            'projects': '/api/projects/',
            'project_tasks': '/api/projects/tasks/',
            'documents': '/api/documents/',
            'maintenance_settings': '/api/maintenance/maintenance/settings/',
            'backup_list': '/api/maintenance/maintenance/backups/',
            'cron_jobs': '/api/maintenance/maintenance/cron-jobs/',
        }

        results = {}
        total_requests = 0
        total_start = time.time()

        for name, endpoint in endpoints.items():
            times = []
            for _ in range(5):  # 5 requests per endpoint
                start = time.time()
                response = client.get(endpoint, **self.headers)
                elapsed = time.time() - start
                times.append(elapsed)
                total_requests += 1
                assert response.status_code == 200, f"{name}: {response.status_code}"

            avg = sum(times) / len(times)
            results[name] = avg
            assert avg < 3, f"{name} average {avg:.3f}s exceeds 3s threshold"

        total_time = time.time() - total_start
        overall_avg = sum(results.values()) / len(results)
        total_throughput = total_requests / total_time

        print(f"\n  === Performance Baseline ({len(endpoints)} endpoints, 5 requests each) ===")
        print(f"    {'Endpoint':<30} {'Avg Response':>12} {'Status':>10}")
        print(f"    {'-'*30} {'-'*12} {'-'*10}")
        for name, avg in sorted(results.items(), key=lambda x: x[1]):
            status = "FAST" if avg < 0.005 else ("OK" if avg < 0.05 else ("SLOW" if avg < 0.5 else "VERY SLOW"))
            print(f"    {name:<30} {avg*1000:>10.1f}ms  [{status:>9}]")
        print(f"\n    Overall average: {overall_avg*1000:.1f}ms")
        print(f"    Total throughput: {total_throughput:.1f} req/s")

    def test_write_operations_stress(self):
        """اختبار ضغط عمليات الكتابة - إنشاء منتجات متتالية سريعة."""
        from inventory.models import Product

        client = APIClient()
        num_items = 20
        times = []

        start_total = time.time()
        for i in range(num_items):
            data = {
                'name': f'منتج ضغط {i}',
                'sku': f'STRESS-{i:04d}',
                'quantity': 100,
                'unit_price': 10.00,
            }
            start = time.time()
            response = client.post('/api/inventory/products/', data, format='json', **self.headers)
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 201, f"Failed creating product {i}: {response.status_code}"

        total_time = time.time() - start_total
        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        throughput = num_items / total_time

        assert avg_time < 2, f"Average {avg_time:.3f}s exceeds 2s threshold"

        print(f"\n  === Write Operations Stress ({num_items} product creates) ===")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)")
        print(f"    P95: {p95_time:.3f}s")
        print(f"    Throughput: {throughput:.1f} creates/s")

    def test_full_sales_workflow_stress(self):
        """اختبار ضغط دورة مبيعات كاملة - إنشاء عملاء وأوامر بيع."""
        from sales.models import Customer, SalesOrder

        client = APIClient()
        num_orders = 10
        times = []

        # إنشاء منتج للاختبار
        product_resp = client.post('/api/inventory/products/', {
            'name': 'منتج ضغط المبيعات',
            'sku': 'SALES-STRESS-001',
            'quantity': 1000,
            'unit_price': 100.00,
        }, format='json', **self.headers)
        assert product_resp.status_code == 201
        product_id = product_resp.data.get('product', {}).get('id') or product_resp.data.get('id')

        # إنشاء عميل
        customer_resp = client.post('/api/sales/customers/', {
            'name': 'عميل ضغط',
            'email': 'stress@customer.com',
            'phone': '0500000000',
        }, format='json', **self.headers)
        assert customer_resp.status_code == 201
        customer_id = customer_resp.data.get('customer', {}).get('id') or customer_resp.data.get('id')

        start_total = time.time()
        for i in range(num_orders):
            start = time.time()
            response = client.post('/api/sales/orders/create/', {
                'customer': customer_id,
                'items': [{'product': product_id, 'quantity': 5}],
                'notes': f'أمر ضغط {i}',
            }, format='json', **self.headers)
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 201, f"Order {i}: {response.status_code}"

        total_time = time.time() - start_total
        avg_time = sum(times) / len(times)
        throughput = num_orders / total_time

        assert avg_time < 3, f"Average {avg_time:.3f}s exceeds 3s threshold"

        print(f"\n  === Sales Workflow Stress ({num_orders} orders) ===")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)")
        print(f"    Throughput: {throughput:.1f} orders/s")

    def test_mixed_read_write_stress(self):
        """اختبار ضغط مختلط - قراءة وكتابة متناوبة."""
        client = APIClient()
        times = {'read': [], 'write': []}
        num_iterations = 30

        start_total = time.time()
        for i in range(num_iterations):
            if i % 3 == 0:
                # Write operation
                start = time.time()
                response = client.post('/api/inventory/products/', {
                    'name': f'منتج مختلط {i}',
                    'sku': f'MIX-{i:04d}',
                    'quantity': 50,
                    'unit_price': 25.00,
                }, format='json', **self.headers)
                elapsed = time.time() - start
                times['write'].append(elapsed)
                assert response.status_code == 201
            else:
                # Read operations
                start = time.time()
                response = client.get('/api/inventory/products/', **self.headers)
                elapsed = time.time() - start
                times['read'].append(elapsed)
                assert response.status_code == 200

        total_time = time.time() - start_total
        avg_read = sum(times['read']) / len(times['read']) if times['read'] else 0
        avg_write = sum(times['write']) / len(times['write']) if times['write'] else 0
        throughput = num_iterations / total_time

        assert avg_read < 2, f"Average read {avg_read:.3f}s exceeds 2s"
        assert avg_write < 3, f"Average write {avg_write:.3f}s exceeds 3s"

        print(f"\n  === Mixed Read/Write Stress ({num_iterations} operations) ===")
        print(f"    Read operations: {len(times['read'])}, avg: {avg_read*1000:.1f}ms")
        print(f"    Write operations: {len(times['write'])}, avg: {avg_write*1000:.1f}ms")
        print(f"    Total throughput: {throughput:.1f} ops/s")
