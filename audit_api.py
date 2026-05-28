#!/usr/bin/env python3
"""
API Consistency Audit Script for ريادة ERP v0
Cross-references frontend API calls against backend URL patterns.
"""

import re
import os
import glob

BASE_DIR = '/home/z/my-project/riadah-erp-v0'
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend/src')

# ============================================================
# 1. Extract all backend URL patterns
# ============================================================

def extract_backend_urls():
    """Extract all URL patterns from all backend urls.py files."""
    # Core URL patterns (defined directly in core/urls.py)
    core_patterns = [
        ('api/dashboard/stats/', 'GET'),
        ('api/dashboard/live-stats/', 'GET'),
        ('api/reports/pdf/<str:module>/', 'GET'),
        ('api/reports/cash-flow/pdf/', 'GET'),
        ('api/reports/cash-flow/', 'GET'),
        ('api/reports/income-statement/enhanced/pdf/', 'GET'),
        ('api/reports/balance-sheet/enhanced/pdf/', 'GET'),
        ('api/reports/sales-analytics/', 'GET'),
        ('api/reports/financial-analytics/', 'GET'),
        ('api/reports/hr-analytics/', 'GET'),
        ('api/system/info/', 'GET'),
        ('api/system/backup/', 'GET'),
    ]

    # Module prefixes
    module_prefixes = {
        'users': 'api/auth/',
        'sales': 'api/sales/',
        'purchases': 'api/purchases/',
        'accounting': 'api/accounting/',
        'hr': 'api/hr/',
        'documents': 'api/documents/',
        'projects': 'api/projects/',
        'notifications': 'api/notifications/',
        'auditlog': 'api/audit-log/',
        'maintenance': 'api/maintenance/',
        'videos': 'api/videos/',
        'payroll': 'api/payroll/',
        'invoicing': 'api/invoicing/',
        'pos': 'api/pos/',
        'payments': 'api/payments/',
        'attachments': 'api/attachments/',
        'tenders': 'api/tenders/',
        'importexport': 'api/import-export/',
        'equipmaint': 'api/equip-maint/',
        'crm': 'api/crm/',
        'analytics': 'api/analytics/',
        'chatbot': 'api/chatbot/',
        'startup_finance': 'api/startup-finance/',
    }

    # Read each module's urls.py
    all_backend_urls = set()
    all_backend_urls.update(core_patterns)

    for module, prefix in module_prefixes.items():
        urls_file = os.path.join(BACKEND_DIR, module, 'urls.py')
        if not os.path.exists(urls_file):
            continue

        with open(urls_file, 'r') as f:
            content = f.read()

        # Extract path() patterns
        paths = re.findall(r"path\(['\"]([^'\"]+)['\"]", content)
        for p in paths:
            full_path = prefix + p
            # Normalize: remove trailing slash if path is empty string
            if p == '' and prefix.endswith('/'):
                full_path = prefix.rstrip('/')
            all_backend_urls.add((full_path, 'ANY'))

        # Also check for router.register (ViewSets)
        registers = re.findall(r"router\.register\(r?'([^']+)'", content)
        for reg in registers:
            base = prefix + reg.rstrip('/')
            # DRF ViewSets generate: GET list, POST create, GET retrieve, PUT/PATCH update, DELETE destroy
            all_backend_urls.add((base + '/', 'GET'))
            all_backend_urls.add((base + '/', 'POST'))
            all_backend_urls.add((base + '/<int:pk>/', 'GET'))
            all_backend_urls.add((base + '/<int:pk>/', 'PUT'))
            all_backend_urls.add((base + '/<int:pk>/', 'PATCH'))
            all_backend_urls.add((base + '/<int:pk>/', 'DELETE'))

    # Also include sub-URLs from includes
    sub_url_files = [
        ('accounting', 'closure_urls', 'api/accounting/closure/'),
        ('accounting', 'multicurrency_urls', 'api/accounting/multi/'),
        ('accounting', 'cost_allocation_urls', 'api/accounting/cost/'),
        ('hr', 'recruitment_urls', 'api/hr/recruitment/'),
        ('hr', 'qualification_urls', 'api/hr/qualifications/'),
        ('hr', 'document_urls', 'api/hr/documents/'),
        ('hr', 'training_urls', 'api/hr/training/'),
        ('hr', 'finance_urls', 'api/hr/finances/'),
        ('hr', 'benefit_urls', 'api/hr/benefits/'),
        ('hr', 'report_urls', 'api/hr/reports/'),
        ('hr', 'orgchart_urls', 'api/hr/org-chart/'),
    ]

    for module, filename, prefix in sub_url_files:
        urls_file = os.path.join(BACKEND_DIR, module, filename + '.py')
        if not os.path.exists(urls_file):
            continue
        with open(urls_file, 'r') as f:
            content = f.read()
        paths = re.findall(r"path\(['\"]([^'\"]+)['\"]", content)
        for p in paths:
            full_path = prefix + p
            if p == '' and prefix.endswith('/'):
                full_path = prefix.rstrip('/')
            all_backend_urls.add((full_path, 'ANY'))
        registers = re.findall(r"router\.register\(r?'([^']+)'", content)
        for reg in registers:
            base = prefix + reg.rstrip('/')
            all_backend_urls.add((base + '/', 'GET'))
            all_backend_urls.add((base + '/', 'POST'))
            all_backend_urls.add((base + '/<int:pk>/', 'GET'))
            all_backend_urls.add((base + '/<int:pk>/', 'PUT'))
            all_backend_urls.add((base + '/<int:pk>/', 'PATCH'))
            all_backend_urls.add((base + '/<int:pk>/', 'DELETE'))

    return all_backend_urls


def normalize_backend_pattern(pattern):
    """Convert a backend URL pattern to a normalized form for matching."""
    # Replace <str:module> with placeholder
    p = re.sub(r'<\w+:\w+>', '{param}', pattern)
    # Replace <int:pk> with placeholder
    p = re.sub(r'<int:\w+>', '{id}', pattern)
    return p.rstrip('/')


def normalize_frontend_path(path):
    """Normalize a frontend API path for matching against backend patterns."""
    # Remove query strings
    path = path.split('?')[0]
    # Replace ${id} style interpolation
    p = re.sub(r'\$\{[^}]+\}', '{id}', path)
    # Replace ${var} style
    p = re.sub(r'\$\w+', '{id}', p)
    # Remove trailing slashes for comparison but keep at least /
    return p.rstrip('/')


def path_matches(frontend_path, backend_patterns):
    """Check if a frontend path matches any backend pattern."""
    norm_fe = normalize_frontend_path(frontend_path)

    for be_pattern, method in backend_patterns:
        norm_be = normalize_backend_pattern(be_pattern)

        # Direct match
        if norm_fe == norm_be:
            return True, be_pattern

        # Check if the frontend path is a prefix match for pattern with {param}
        # e.g., frontend: /api/auth/users/5/ matches backend: /api/auth/users/<int:pk>/
        be_parts = norm_be.split('/')
        fe_parts = norm_fe.split('/')

        if len(be_parts) == len(fe_parts):
            match = True
            for bp, fp in zip(be_parts, fe_parts):
                if bp == '{param}' or bp == '{id}':
                    continue
                if bp != fp:
                    match = False
                    break
            if match:
                return True, be_pattern

    return False, None


# ============================================================
# 2. Extract all frontend API endpoints from api/index.js
# ============================================================

def extract_frontend_api_calls():
    """Extract all API endpoints defined in api/index.js."""
    api_file = os.path.join(FRONTEND_DIR, 'api/index.js')

    with open(api_file, 'r') as f:
        content = f.read()

    # Find all api.get/post/patch/put/delete calls
    # Pattern: api.get('/path/'), api.post('/path/', data)
    pattern = r"api\.(get|post|patch|put|delete)\(['\"]([^'\"]+)['\"]"
    matches = re.findall(pattern, content)

    # Also find ${API_BASE_URL} references in the interceptor
    base_url_pattern = r"`?\$\{API_BASE_URL\}([^'\"`]+)`?"
    base_matches = re.findall(base_url_pattern, content)

    endpoints = []
    for method, path in matches:
        endpoints.append((path, method, 'api/index.js'))

    for path in base_matches:
        endpoints.append((path, 'POST', 'api/index.js (interceptor)'))

    return endpoints


# ============================================================
# 3. Search for direct API calls in frontend pages
# ============================================================

def search_direct_api_calls():
    """Search all .jsx files for direct API calls (axios/fetch/api)."""
    results = []
    jsx_files = glob.glob(os.path.join(FRONTEND_DIR, '**/*.jsx'), recursive=True)

    for filepath in jsx_files:
        rel_path = os.path.relpath(filepath, BASE_DIR)
        with open(filepath, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            # Skip imports
            if 'import ' in line and (' from ' in line or ';' in line):
                continue
            # Look for direct axios/fetch/api calls
            if re.search(r'axios\.(get|post|patch|put|delete)\s*\(', line):
                # Extract URL
                m = re.search(r'axios\.(get|post|patch|put|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]', line)
                if m:
                    results.append((rel_path, i, m.group(2), m.group(1), line.strip()))
            elif re.search(r'fetch\s*\(', line) and not re.search(r'useFetch|const fetch', line):
                # This is likely a function name, not the global fetch
                pass
            # api.get/post outside of api/index.js
            elif re.search(r'\bapi\.(get|post|patch|put|delete)\s*\(', line):
                m = re.search(r'\bapi\.(get|post|patch|put|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]', line)
                if m and 'api/index.js' not in rel_path:
                    results.append((rel_path, i, m.group(2), m.group(1), line.strip()))

    return results


# ============================================================
# 4. Cross-reference
# ============================================================

def run_audit():
    print("=" * 80)
    print("  API CONSISTENCY AUDIT — ريادة ERP v0")
    print("=" * 80)
    print()

    # Get backend URLs
    backend_urls = extract_backend_urls()
    print(f"📊 Backend: {len(backend_urls)} URL patterns found")

    # Get frontend API calls
    frontend_calls = extract_frontend_api_calls()
    print(f"📊 Frontend: {len(frontend_calls)} API calls defined in api/index.js")
    print()

    # --------------------------------------------------------
    # Cross-reference
    # --------------------------------------------------------
    matched = []
    unmatched = []
    backend_not_used = set()

    # Normalize all backend patterns for comparison
    be_patterns_normalized = set()
    for pattern, method in backend_urls:
        be_patterns_normalized.add(normalize_backend_pattern(pattern))

    for path, method, source in frontend_calls:
        found, matched_pattern = path_matches(path, backend_urls)
        if found:
            matched.append((path, method, matched_pattern))
        else:
            unmatched.append((path, method, source))

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    # Group matched by module prefix
    print("=" * 80)
    print("  ✅ MATCHED ENDPOINTS (by module)")
    print("=" * 80)

    module_counts = {}
    for path, method, be_pattern in matched:
        prefix = path.split('/')[1] if '/' in path else 'other'
        module_counts[prefix] = module_counts.get(prefix, 0) + 1

    for module in sorted(module_counts.keys()):
        print(f"  ✅ {module}: {module_counts[module]} endpoints matched")

    print()
    print(f"  Total matched: {len(matched)}")

    # --------------------------------------------------------
    # Unmatched frontend calls (CRITICAL)
    # --------------------------------------------------------
    print()
    print("=" * 80)
    print("  🔴 UNMATCHED FRONTEND CALLS (NO BACKEND ENDPOINT)")
    print("=" * 80)

    # Filter out the ones that are actually matched by backend patterns with params
    real_unmatched = []
    for path, method, source in unmatched:
        # Additional check: some patterns might be dynamic
        norm = normalize_frontend_path(path)
        # Check if this could be a ViewSet action
        possible_match = False
        for be_pattern, be_method in backend_urls:
            norm_be = normalize_backend_pattern(be_pattern)
            # Check for patterns like /videos/videos/{id}/like/
            if norm_be.endswith('/'):
                if norm.startswith(norm_be):
                    possible_match = True
                    break

        if not possible_match:
            real_unmatched.append((path, method, source))

    if not real_unmatched:
        print("  (none found — all frontend API calls have matching backend endpoints)")
    else:
        for path, method, source in real_unmatched:
            print(f"  🔴 [{method}] {path}")
            print(f"     Source: {source}")

    print()
    print(f"  Total unmatched: {len(real_unmatched)}")

    # --------------------------------------------------------
    # Frontend calls using potential non-standard ViewSet actions
    # --------------------------------------------------------
    print()
    print("=" * 80)
    print("  ⚠️ POTENTIAL VIEWSET ACTION ENDPOINTS (may need custom actions)")
    print("=" * 80)

    viewset_actions = []
    viewset_action_patterns = [
        '/featured/', '/stats/', '/like/', '/search/',
        '/review/', '/summary/',
    ]

    for path, method, source in frontend_calls:
        norm = normalize_frontend_path(path)
        for action_pattern in viewset_action_patterns:
            if norm.endswith(action_pattern.rstrip('/')):
                # Check if this is a ViewSet custom action
                matched_any = False
                for be_pattern, be_method in backend_urls:
                    if path_matches(path, backend_urls)[0]:
                        matched_any = True
                        break
                if not matched_any:
                    viewset_actions.append((path, method, source))

    if not viewset_actions:
        print("  (none)")
    else:
        for path, method, source in viewset_actions:
            print(f"  ⚠️ [{method}] {path} — custom ViewSet action?")

    # --------------------------------------------------------
    # Direct API calls in JSX pages
    # --------------------------------------------------------
    print()
    print("=" * 80)
    print("  🔍 DIRECT API CALLS IN JSX PAGES (outside api/index.js)")
    print("=" * 80)

    direct_calls = search_direct_api_calls()
    if not direct_calls:
        print("  (none — all API calls go through api/index.js)")
    else:
        for rel_path, line_num, url, method, line_text in direct_calls:
            print(f"  🔍 {rel_path}:{line_num}")
            print(f"     [{method}] {url}")
            print(f"     → {line_text[:100]}")

    print()
    print(f"  Total direct calls found: {len(direct_calls)}")

    # --------------------------------------------------------
    # Backend endpoints NOT used by frontend
    # --------------------------------------------------------
    print()
    print("=" * 80)
    print("  ℹ️ BACKEND ENDPOINTS NOT CALLED BY FRONTEND")
    print("=" * 80)

    used_be_patterns = set()
    for path, method, be_pattern in matched:
        used_be_patterns.add(be_pattern)

    unused = []
    for pattern, method in backend_urls:
        norm = normalize_backend_pattern(pattern)
        if norm not in used_be_patterns:
            unused.append(pattern)

    # Deduplicate
    unused = sorted(set(unused))
    if len(unused) > 50:
        print(f"  ({len(unused)} backend endpoints have no frontend caller)")
        print("  (Showing first 30)")
        for u in unused[:30]:
            print(f"  ℹ️ {u}")
        print(f"  ... and {len(unused) - 30} more")
    else:
        for u in unused:
            print(f"  ℹ️ {u}")

    print()
    print(f"  Total unused backend endpoints: {len(unused)}")

    # --------------------------------------------------------
    # Specific known issues verification
    # --------------------------------------------------------
    print()
    print("=" * 80)
    print("  🔧 KNOWN ISSUES VERIFICATION")
    print("=" * 80)

    # Check 1: AnalyticsPage.jsx - does it call dashboardAPI.getAnalytics()?
    analytics_page = os.path.join(FRONTEND_DIR, 'pages/AnalyticsPage.jsx')
    with open(analytics_page, 'r') as f:
        analytics_content = f.read()

    if 'getAnalytics' in analytics_content:
        print("  🔴 CONFIRMED: AnalyticsPage.jsx calls dashboardAPI.getAnalytics() — method does NOT exist in api/index.js")
    else:
        print("  ✅ AnalyticsPage.jsx does NOT call getAnalytics() (issue already fixed or not present)")

    if 'dashboardAPI.getStats()' in analytics_content:
        print("  ✅ AnalyticsPage.jsx calls dashboardAPI.getStats() — this EXISTS in api/index.js")
        print("     → Maps to backend: api/dashboard/stats/")

    # Check 2: CRMAnalyticsPage.jsx - does it use Math.random()?
    crm_analytics_page = os.path.join(FRONTEND_DIR, 'pages/CRMAnalyticsPage.jsx')
    with open(crm_analytics_page, 'r') as f:
        crm_analytics_content = f.read()

    if 'Math.random()' in crm_analytics_content:
        print("  🔴 CONFIRMED: CRMAnalyticsPage.jsx uses Math.random() for fake data")
    else:
        print("  ✅ CRMAnalyticsPage.jsx does NOT use Math.random() (already uses real API)")

    # Check what CRM API functions it imports
    crm_imports = re.findall(r'crmAPI\.(\w+)', crm_analytics_content)
    print(f"  CRMAnalyticsPage.jsx uses: {', '.join(sorted(set(crm_imports)))}")

    # Verify these exist in api/index.js
    api_file = os.path.join(FRONTEND_DIR, 'api/index.js')
    with open(api_file, 'r') as f:
        api_content = f.read()

    for func in sorted(set(crm_imports)):
        if f'{func}:' in api_content or f'{func} =' in api_content:
            print(f"  ✅ crmAPI.{func}() — EXISTS in api/index.js")
        else:
            print(f"  🔴 crmAPI.{func}() — MISSING from api/index.js")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------
    print()
    print("=" * 80)
    print("  📊 SUMMARY STATISTICS")
    print("=" * 80)
    print(f"  Backend URL patterns:        {len(backend_urls)}")
    print(f"  Frontend API definitions:     {len(frontend_calls)}")
    print(f"  ✅ Matched endpoints:         {len(matched)}")
    print(f"  🔴 Unmatched frontend:       {len(real_unmatched)}")
    print(f"  ⚠️  ViewSet action checks:   {len(viewset_actions)}")
    print(f"  🔍 Direct calls in JSX:      {len(direct_calls)}")
    print(f"  ℹ️  Unused backend endpoints: {len(unused)}")
    print()
    print("=" * 80)
    print("  END OF AUDIT")
    print("=" * 80)


if __name__ == '__main__':
    run_audit()
