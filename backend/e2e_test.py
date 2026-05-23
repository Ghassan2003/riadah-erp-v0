#!/usr/bin/env python3
"""
RIADAH ERP v0 — Comprehensive E2E API Testing Script v2
=======================================================
1. Static analysis: extract backend URLs from all urls.py files
2. Dynamic testing: start Django server, login, test every GET endpoint

Usage:
  python e2e_test.py                    # Full E2E (static + dynamic)
  python e2e_test.py --static-only       # Static analysis only
  python e2e_test.py --dynamic-only      # Dynamic testing only
"""

import os
import sys
import re
import json
import time
import argparse
import subprocess
import signal
import requests
from datetime import datetime
from collections import defaultdict

# ─── Colors ───────────────────────────────────────────────────────────────────
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_API_FILE = os.path.join(os.path.dirname(BASE_DIR), 'frontend', 'src', 'api', 'index.js')


class BackendURLCollector:
    """Collect all registered backend URL paths by parsing urls.py files."""

    def __init__(self):
        self.paths = set()  # Set of (method, full_path) tuples
        self._collect()

    def _collect(self):
        """Walk through all urls.py files and core/urls.py to build path map."""
        core_urls = os.path.join(BASE_DIR, 'core', 'urls.py')
        url_includes = {}  # prefix -> app_urls_file

        # Parse core/urls.py for includes
        with open(core_urls, 'r') as f:
            content = f.read()

        # Find all include() calls
        include_pattern = re.compile(r"path\('([^']+)',\s*include\('(\w+\.urls)'\)")
        direct_pattern = re.compile(r"path\('([^']+)',\s*(?:core_views|views)\.(\w+View)")

        for match in include_pattern.finditer(content):
            prefix = match.group(1)  # e.g., 'api/auth/'
            app_urls = match.group(2)  # e.g., 'users.urls'
            url_includes[prefix] = app_urls

        # Direct views from core
        core_direct_urls = []
        for match in direct_pattern.finditer(content):
            core_direct_urls.append((match.group(1), match.group(2)))

        # Now parse each app's urls.py
        for prefix, app_urls_module in url_includes.items():
            module_name = app_urls_module.split('.')[0]  # 'users' from 'users.urls'
            app_urls_file = os.path.join(BASE_DIR, module_name, 'urls.py')

            if not os.path.exists(app_urls_file):
                continue

            with open(app_urls_file, 'r') as f:
                app_content = f.read()

            # Extract URL patterns from the app's urls.py
            # Pattern: path('...', ViewName.as_view()) or path('...', view_name)
            url_pattern = re.compile(
                r"path\(\s*['\"]([^'\"]*?)['\"]\s*,\s*(.+?)\)"
            )

            for match in url_pattern.finditer(app_content):
                app_path = match.group(1)
                view_ref = match.group(2).strip()

                full_path = prefix + app_path
                full_path = full_path.replace('//', '/')

                # Try to determine allowed methods from view reference
                methods = self._extract_methods(view_ref, module_name)

                for method in methods:
                    self.paths.add((method, full_path))

        # Also add direct core views
        for url_path, view_name in core_direct_urls:
            methods = ['GET']  # Default
            for method in methods:
                self.paths.add((method, url_path))

    def _extract_methods(self, view_ref, app_name):
        """Extract allowed HTTP methods from a view reference string."""
        methods = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}

        # Check for router.register with ViewSet
        # ViewSets typically handle all CRUD methods
        view_name = view_ref.split('(')[0].strip().split('.')[-1]  # Extract class name

        # Read the views.py to determine allowed methods
        views_file = os.path.join(BASE_DIR, app_name, 'views.py')
        allowed = set()

        if os.path.exists(views_file):
            with open(views_file, 'r') as f:
                views_content = f.read()

            # Find the view class
            class_pattern = re.compile(
                rf'class\s+{re.escape(view_name)}\s*\((.+?)\):',
                re.DOTALL
            )
            class_match = class_pattern.search(views_content)

            if class_match:
                # Check what the class inherits from
                bases = class_match.group(1)
                is_viewset = 'ViewSet' in bases or 'ModelViewSet' in bases
                is_list_view = 'ListAPIView' in bases or 'ListCreateAPIView' in bases
                is_detail_view = 'RetrieveAPIView' in bases or 'RetrieveUpdateDestroyAPIView' in bases

                if is_viewset:
                    allowed = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}
                elif is_list_view:
                    allowed = {'GET', 'POST'}
                elif is_detail_view:
                    allowed = {'GET', 'PUT', 'PATCH', 'DELETE'}

                # Check if specific methods are overridden
                # Find the class body
                class_start = class_match.end()
                # Simple approach: check for method definitions within the class
                class_body = views_content[class_start:class_start + 5000]  # First 5k chars

                for method in ['get', 'post', 'put', 'patch', 'delete']:
                    if re.search(rf'^\s+def {method}\s*\(', class_body, re.MULTILINE):
                        allowed.add(method.upper())

                # Check http_method_names
                if 'http_method_names' in class_body:
                    http_match = re.search(
                        r'http_method_names\s*=\s*\[([^\]]+)\]',
                        class_body
                    )
                    if http_match:
                        allowed = {m.strip().strip("'\"").upper()
                                   for m in http_match.group(1).split(',')}
        else:
            # Fallback: check by URL pattern
            if 'create' in view_ref.lower() or 'create/' in view_ref:
                allowed = {'POST'}
            elif 'delete' in view_ref.lower() or 'delete/' in view_ref:
                allowed = {'DELETE'}
            elif 'update' in view_ref.lower() or 'update/' in view_ref:
                allowed = {'PUT', 'PATCH'}
            else:
                allowed = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}

        if not allowed:
            allowed = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}

        return allowed

    def find_match(self, frontend_path, method):
        """Check if a frontend path matches any backend URL pattern."""
        # Frontend paths are relative to /api (e.g., /auth/login/)
        # Backend paths from core/urls.py already include api/ prefix

        # Build potential full paths
        candidates = [
            'api' + frontend_path,           # Most common
            frontend_path,                     # In case already has api
            frontend_path.rstrip('/'),         # Without trailing slash
            'api' + frontend_path.rstrip('/'), # Without trailing slash
        ]

        for candidate in candidates:
            candidate = candidate.replace('//', '/')
            if (method, candidate) in self.paths:
                return candidate, 'EXACT'

        # Pattern matching for dynamic segments
        frontend_parts = [p for p in frontend_path.split('/') if p]
        for (backend_method, backend_path) in self.paths:
            if backend_method != method:
                continue

            backend_parts = [p for p in backend_path.split('/') if p]

            if len(frontend_parts) != len(backend_parts):
                continue

            match = True
            for fp, bp in zip(frontend_parts, backend_parts):
                if fp == bp:
                    continue
                # Backend uses <int:pk>, <pk>, <str:token>, etc.
                if re.match(r'^<\w+:\w+>$', bp) or re.match(r'^<\w+>$', bp):
                    continue
                # Frontend uses {id}, {pk}, etc.
                if re.match(r'^\{\w+\}$', fp):
                    continue
                match = False
                break

            if match:
                return backend_path, 'PATTERN'

        return None, 'NOT_FOUND'


class FrontendAPIParser:
    """Parse frontend/src/api/index.js to extract all API endpoints."""

    CALL_PATTERN = re.compile(
        r"api\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]*?)['\"]"
        r"|"
        r"api\.(get|post|put|patch|delete)\(\s*`([^`]*?)`",
        re.MULTILINE
    )

    def __init__(self):
        self.endpoints = []
        self._parse()

    def _parse(self):
        with open(FRONTEND_API_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        current_module = 'unknown'

        for i, line in enumerate(lines, 1):
            module_match = re.match(r'export const (\w+API) = \{', line)
            if module_match:
                current_module = module_match.group(1)
                continue

            matches = self.CALL_PATTERN.findall(line)
            for match in matches:
                method = match[0] or match[2]
                path = match[1] or match[3]
                if not path or not path.startswith('/'):
                    continue

                path = path.replace('${', '{').replace('}', '}')

                self.endpoints.append({
                    'module': current_module,
                    'method': method.upper(),
                    'path': path,
                    'line': i,
                    'raw': line.strip()
                })

    def get_unique(self):
        seen = set()
        unique = []
        for ep in self.endpoints:
            key = (ep['method'], ep['path'])
            if key not in seen:
                seen.add(key)
                unique.append(ep)
        return unique


class E2ETester:
    def __init__(self, host='127.0.0.1', port=8000):
        self.host = host
        self.port = port
        self.base_url = f'http://{host}:{port}'
        self.token = None
        self.session = requests.Session()
        self.server_proc = None

    def run_static(self):
        print(f'\n{BOLD}{"=" * 80}{RESET}')
        print(f'{BOLD}  PHASE 1: STATIC ANALYSIS — Frontend API vs Backend URL Patterns{RESET}')
        print(f'{BOLD}{"=" * 80}{RESET}\n')

        parser = FrontendAPIParser()
        backend = BackendURLCollector()
        endpoints = parser.get_unique()

        by_module = defaultdict(list)
        for ep in endpoints:
            by_module[ep['module']].append(ep)

        total = len(endpoints)
        matched = 0
        not_found = []

        print(f'  Total: {total} unique frontend API endpoints\n')

        for module in sorted(by_module.keys()):
            eps = by_module[module]
            mod_ok = 0
            mod_fail = 0
            for ep in eps:
                bp, mt = backend.find_match(ep['path'], ep['method'])
                if mt != 'NOT_FOUND':
                    mod_ok += 1
                    matched += 1
                else:
                    mod_fail += 1
                    not_found.append(ep)

            icon = f'{GREEN}✓{RESET}' if mod_fail == 0 else f'{RED}✗{RESET}'
            print(f'  {icon} {CYAN}{module:<30}{RESET} {len(eps):3d} eps  '
                  f'{GREEN}{mod_ok} ok{RESET}'
                  + (f'  {RED}{mod_fail} missing{RESET}' if mod_fail > 0 else ''))

        if not_found:
            print(f'\n{RED}{BOLD}  ⚠ {len(not_found)} ENDPOINTS WITHOUT BACKEND MATCH:{RESET}\n')
            for r in not_found:
                print(f'    {RED}✗{RESET} {r["method"]:<7} {r["path"]:<55} ({r["module"]} L{r["line"]})')
        else:
            print(f'\n{GREEN}{BOLD}  ✓ ALL {total} ENDPOINTS MATCHED!{RESET}')

        print(f'\n  Summary: {GREEN}{matched}/{total}{RESET} matched, {RED}{len(not_found)}/{total}{RESET} not found')
        return not_found

    def _start_server(self):
        """Start Django development server."""
        print(f'  Checking if server is running on {self.host}:{self.port}...')
        try:
            resp = requests.get(f'{self.base_url}/api/system/info/', timeout=3)
            if resp.status_code < 500:
                print(f'  {GREEN}✓ Server already running{RESET}')
                return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        print(f'  Starting Django server on {self.host}:{self.port}...')
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'core.settings'
        self.server_proc = subprocess.Popen(
            [sys.executable, '/home/z/my-project/riadah-erp-v0/backend/manage.py',
             'runserver', f'{self.host}:{self.port}', '--noreload'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        for _ in range(30):
            try:
                resp = requests.get(f'{self.base_url}/api/system/info/', timeout=2)
                if resp.status_code < 500:
                    print(f'  {GREEN}✓ Server started{RESET}')
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(1)
        print(f'  {RED}✗ Server failed to start{RESET}')
        self._stop_server()
        return False

    def _stop_server(self):
        if self.server_proc:
            self.server_proc.terminate()
            try:
                self.server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_proc.kill()
            self.server_proc = None

    def _login(self):
        try:
            resp = self.session.post(
                f'{self.base_url}/api/auth/login/',
                json={'username': 'admin', 'password': 'Admin@123'},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get('access')
                if self.token:
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    return True
        except Exception as e:
            print(f'  {RED}✗ Login error: {e}{RESET}')
        return False

    def run_dynamic(self, not_found_static=None):
        print(f'\n{BOLD}{"=" * 80}{RESET}')
        print(f'{BOLD}  PHASE 2: DYNAMIC TESTING — HTTP Requests to Backend{RESET}')
        print(f'{BOLD}{"=" * 80}{RESET}\n')

        started = self._start_server()
        if not started:
            print(f'{YELLOW}  ⚠ Skipping dynamic tests{RESET}')
            return

        print(f'  Logging in as admin...')
        if not self._login():
            print(f'  {YELLOW}⚠ Login failed, testing without auth{RESET}')

        parser = FrontendAPIParser()
        endpoints = parser.get_unique()

        # Collect all unique list/stats GET paths (no ID params)
        safe_gets = []
        for ep in endpoints:
            if ep['method'] != 'GET':
                continue
            if '{' in ep['path']:
                continue
            if 'export' in ep['path'] or 'download' in ep['path']:
                continue
            safe_gets.append(ep)

        print(f'\n  Testing {len(safe_gets)} safe GET endpoints...\n')

        passed = 0
        failed = 0
        failed_list = []
        error_404 = []
        error_500 = []
        error_405 = []

        for ep in safe_gets:
            url = f'{self.base_url}/api{ep["path"]}'
            try:
                resp = self.session.get(url, timeout=5)
                code = resp.status_code

                if code < 500:
                    passed += 1
                    if code == 404:
                        error_404.append(ep)
                    elif code == 405:
                        error_405.append(ep)
                else:
                    failed += 1
                    error_500.append(ep)
                    failed_list.append((ep, f'{code} Server Error'))

            except requests.exceptions.Timeout:
                failed += 1
                failed_list.append((ep, 'Timeout'))
            except Exception as e:
                failed += 1
                failed_list.append((ep, str(e)))

        # Print results grouped by category
        if error_404:
            print(f'\n  {RED}{BOLD}  404 NOT FOUND ({len(error_404)}):{RESET}')
            for ep in error_404:
                print(f'    {RED}✗{RESET} {ep["path"]:<55} ({ep["module"]})')

        if error_405:
            print(f'\n  {YELLOW}{BOLD}  405 METHOD NOT ALLOWED ({len(error_405)}):{RESET}')
            for ep in error_405:
                print(f'    {YELLOW}✗{RESET} {ep["path"]:<55} ({ep["module"]})')

        if error_500:
            print(f'\n  {RED}{BOLD}  500 SERVER ERROR ({len(error_500)}):{RESET}')
            for ep in error_500:
                print(f'    {RED}✗{RESET} {ep["path"]:<55} ({ep["module"]})')

        if failed_list and not error_404 and not error_405 and not error_500:
            for ep, err in failed_list:
                print(f'    {RED}✗{RESET} {ep["path"]:<55} ({ep["module"]}) — {err}')

        print(f'\n  {GREEN}✓ {passed} endpoints OK{RESET}')
        if failed:
            print(f'  {RED}✗ {failed} endpoints with errors{RESET}')

        # Module summary from already-collected data
        print(f'\n  {BOLD}Module Summary:{RESET}')
        module_results = defaultdict(lambda: {'ok': 0, 'fail': 0})
        for ep in safe_gets:
            url = f'{self.base_url}/api{ep["path"]}'
            is_err = ep in error_404 or ep in error_405 or ep in error_500
            err_eps = [f[0] for f in failed_list]
            if ep in err_eps:
                module_results[ep['module']]['fail'] += 1
            else:
                module_results[ep['module']]['ok'] += 1

        for mod in sorted(module_results.keys()):
            r = module_results[mod]
            icon = f'{GREEN}✓{RESET}' if r['fail'] == 0 else f'{RED}✗{RESET}'
            total_mod = r['ok'] + r['fail']
            print(f'    {icon} {CYAN}{mod:<30}{RESET} {r["ok"]:2d}/{total_mod} ok'
                  + (f'  {RED}{r["fail"]} failed{RESET}' if r['fail'] > 0 else ''))

        self._stop_server()

        # Save report
        self._save_report(passed, failed, error_404, error_405, error_500, safe_gets)

        return {
            'passed': passed,
            'failed': failed,
            'error_404': error_404,
            'error_405': error_405,
            'error_500': error_500,
        }

    def _save_report(self, passed, failed, e404, e405, e500, tested):
        report_dir = os.path.join(os.path.dirname(BASE_DIR), 'reports')
        os.makedirs(report_dir, exist_ok=True)

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(report_dir, f'e2e_report_{ts}.json')

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'tested_endpoints': len(tested),
                'passed': passed,
                'failed': failed,
                'error_404_count': len(e404),
                'error_405_count': len(e405),
                'error_500_count': len(e500),
            },
            'endpoints_404': [{'path': e['path'], 'module': e['module'], 'line': e['line']} for e in e404],
            'endpoints_405': [{'path': e['path'], 'module': e['module'], 'line': e['line']} for e in e405],
            'endpoints_500': [{'path': e['path'], 'module': e['module'], 'line': e['line']} for e in e500],
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f'\n  Report saved: {report_path}')

    def run_all(self):
        start = time.time()
        print(f'\n{BOLD}{"═" * 80}{RESET}')
        print(f'{BOLD}  RIADAH ERP v0 — E2E API Testing{RESET}')
        print(f'{BOLD}  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}{RESET}')
        print(f'{BOLD}{"═" * 80}{RESET}')

        not_found = self.run_static()
        dyn = self.run_dynamic(not_found)

        elapsed = time.time() - start
        print(f'\n{BOLD}{"═" * 80}{RESET}')
        print(f'{BOLD}  DONE — {elapsed:.1f}s{RESET}')
        print(f'{BOLD}{"═" * 80}{RESET}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--static-only', action='store_true')
    parser.add_argument('--dynamic-only', action='store_true')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()

    tester = E2ETester(host=args.host, port=args.port)

    if args.static_only:
        tester.run_static()
    elif args.dynamic_only:
        tester.run_dynamic()
    else:
        tester.run_all()


if __name__ == '__main__':
    main()
