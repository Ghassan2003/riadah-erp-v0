"""
Organizational Chart Views.
Provides a complete organizational hierarchy tree and organizational statistics.

- OrgChartView: GET /hr/org-chart/ — Full nested department/employee tree
- OrgStatisticsView: GET /hr/org-chart/stats/ — Structural metrics
"""

from rest_framework import permissions, views
from rest_framework.response import Response

from django.db.models import Count, Q, Avg, Max

from .models import Department, Employee


# =============================================
# Recursive tree builder
# =============================================

def _build_org_node(department, include_employees=True):
    """
    Recursively build an organizational chart node for a department.

    Each node contains:
      - Department metadata (id, name, name_en, manager info)
      - Child sub-departments (recursively built)
      - Employee list with name, position, photo placeholder, phone, email
      - Counts: total employees, sub-departments
    """
    # Manager info
    manager_data = None
    if department.manager:
        mgr = department.manager
        manager_data = {
            'المعرف': mgr.id,
            'الاسم': mgr.full_name,
            'الرقم_الوظيفي': mgr.employee_number,
            'المسمى_الوظيفي': mgr.position or '',
            'الهاتف': mgr.phone or '',
            'البريد_الإلكتروني': mgr.email or '',
            'صورة': None,  # No photo field on Employee; placeholder for future use
        }

    # Employees in this department (active, excluding the manager if they're listed separately)
    emps_qs = department.employees.filter(is_active=True)
    employees_data = []
    if include_employees:
        for emp in emps_qs:
            employees_data.append({
                'المعرف': emp.id,
                'الاسم': emp.full_name,
                'الرقم_الوظيفي': emp.employee_number,
                'المسمى_الوظيفي': emp.position or '',
                'الهاتف': emp.phone or '',
                'البريد_الإلكتروني': emp.email or '',
                'صورة': None,  # Placeholder for future photo field
            })

    # Direct children departments (active only)
    children_qs = department.children.filter(is_active=True)
    children_data = []
    for child in children_qs:
        children_data.append(
            _build_org_node(child, include_employees=include_employees)
        )

    # Counts
    direct_emp_count = emps_qs.count()
    # Recursive total employees including all nested sub-departments
    all_descendant_ids = _get_all_descendant_dept_ids(department)
    total_emp_including_subs = Employee.objects.filter(
        is_active=True,
        department_id__in=[department.id] + all_descendant_ids,
    ).count()

    node = {
        'المعرف': department.id,
        'اسم_القسم': department.name,
        'اسم_القسم_إنجليزي': department.name_en or '',
        'الوصف': department.description or '',
        'المدير': manager_data,
        'الموظفون': employees_data,
        'عدد_الموظفين_المباشرين': direct_emp_count,
        'عدد_الموظفين_بما_فيهم_الأقسام_الفرعية': total_emp_including_subs,
        'الأقسام_الفرعية': children_data,
        'عدد_الأقسام_الفرعية': len(children_data),
        'نشط': department.is_active,
    }
    return node


def _get_all_descendant_dept_ids(department):
    """Recursively collect all descendant department IDs (children, grandchildren, etc.)."""
    ids = []
    for child in department.children.filter(is_active=True):
        ids.append(child.id)
        ids.extend(_get_all_descendant_dept_ids(child))
    return ids


# =============================================
# OrgChartView
# =============================================

class OrgChartView(views.APIView):
    """
    GET /hr/org-chart/
    الهيكل التنظيمي الكامل للشركة كشجرة متداخلة.

    هيكل الاستجابة:
    {
        "الهيكل_التنظيمي": [
            {
                "المعرف": 1,
                "اسم_القسم": "الإدارة العامة",
                "المدير": { "الاسم": "...", "المسمى_الوظيفي": "...", ... },
                "الموظفون": [ { "الاسم": "...", "المسمى_الوظيفي": "...", ... } ],
                "عدد_الموظفين_المباشرين": 5,
                "الأقسام_الفرعية": [ ... ]
            }
        ]
    }

    معاملات اختيارية:
    - include_employees=true|false  (تضمين قائمة الموظفين، الافتراضي true)
    - department_id=N  (عرض شجرة قسم محدد فقط)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        params = request.query_params
        include_employees = params.get('include_employees', 'true').lower() != 'false'
        department_id = params.get('department_id')

        # Determine root departments
        if department_id:
            try:
                root_dept = Department.objects.select_related('manager').get(
                    pk=int(department_id), is_active=True
                )
                tree = [_build_org_node(root_dept, include_employees=include_employees)]
            except (Department.DoesNotExist, ValueError, TypeError):
                return Response(
                    {'خطأ': 'القسم غير موجود أو المعرّف غير صالح'},
                    status=404,
                )
        else:
            root_depts = (
                Department.objects
                .filter(parent__isnull=True, is_active=True)
                .select_related('manager')
                .prefetch_related('children', 'employees')
            )
            tree = [
                _build_org_node(dept, include_employees=include_employees)
                for dept in root_depts
            ]

        return Response({
            'الهيكل_التنظيمي': tree,
        })


# =============================================
# OrgStatisticsView
# =============================================

class OrgStatisticsView(views.APIView):
    """
    GET /hr/org-chart/stats/
    إحصائيات الهيكل التنظيمي تشمل:
    - إجمالي الأقسام والأقسام الفرعية والموظفين
    - متوسط نطاق الإشراف (عدد الموظفين لكل مدير)
    - الأقسام ذات أكبر عدد من الموظفين
    - عمق الهيكل التنظيمي (أقصى مستوى تداخل)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # --- Total counts ---
        total_departments = Department.objects.filter(is_active=True).count()
        # Root-level departments (no parent)
        root_departments = Department.objects.filter(parent__isnull=True, is_active=True).count()
        # Sub-departments (have a parent)
        sub_departments = total_departments - root_departments
        # Total active employees
        total_employees = Employee.objects.filter(is_active=True).count()
        # Employees assigned to departments
        employees_with_dept = Employee.objects.filter(is_active=True, department__isnull=False).count()
        # Employees without department
        employees_without_dept = total_employees - employees_with_dept
        # Departments that have a manager assigned
        departments_with_manager = Department.objects.filter(
            is_active=True, manager__isnull=False
        ).count()

        # --- Average span of control (employees per manager) ---
        # A "manager" is anyone who is assigned as manager of a department
        manager_ids = Department.objects.filter(
            is_active=True, manager__isnull=False
        ).values_list('manager_id', flat=True).distinct()

        if manager_ids:
            span_data = (
                Employee.objects
                .filter(is_active=True, department__manager_id__in=manager_ids)
                .values('department__manager_id')
                .annotate(report_count=Count('id'))
            )
            if span_data.exists():
                avg_span = round(
                    sum(item['report_count'] for item in span_data) / len(span_data), 1
                )
            else:
                avg_span = 0
        else:
            avg_span = 0

        # --- Departments with most employees (top 10) ---
        top_departments = (
            Department.objects
            .filter(is_active=True)
            .annotate(
                emp_count=Count('employees', filter=Q(employees__is_active=True))
            )
            .order_by('-emp_count')[:10]
        )
        departments_by_size = [
            {
                'المعرف': dept.id,
                'اسم_القسم': dept.name,
                'عدد_الموظفين': dept.emp_count,
            }
            for dept in top_departments
            if dept.emp_count > 0
        ]

        # --- Organizational depth (max nesting level) ---
        max_depth = self._calculate_max_depth()

        # --- Department tree summary by depth level ---
        depth_distribution = self._get_depth_distribution()

        report_data = {
            'الإحصائيات_التنظيمية': {
                'إجمالي_الأقسام': total_departments,
                'الأقسام_الرئيسية': root_departments,
                'الأقسام_الفرعية': sub_departments,
                'إجمالي_الموظفين': total_employees,
                'موظفون_بدون_قسم': employees_without_dept,
                'أقسام_بمدير_معين': departments_with_manager,
                'أقسام_بدون_مدير': total_departments - departments_with_manager,
            },
            'نطاق_الإشراف': {
                'متوسط_عدد_الموظفين_لكل_مدير': avg_span,
                'عدد_المديرين_المعينين': len(manager_ids),
            },
            'الأقسام_ذات_أكبر_عدد_موظفين': departments_by_size,
            'عمق_الهيكل_التنظيمي': {
                'أقصى_مستوى_تداخل': max_depth,
                'توزيع_الأقسام_حسب_المستوى': depth_distribution,
            },
        }

        return Response(report_data)

    def _calculate_max_depth(self):
        """
        Calculate the maximum nesting depth of the department tree.
        Returns 0 if there are no departments, 1 for root-only departments, etc.
        Uses iterative BFS approach for efficiency.
        """
        roots = list(
            Department.objects.filter(parent__isnull=True, is_active=True).values_list('id', flat=True)
        )
        if not roots:
            return 0

        max_depth = 0
        current_level = roots

        while current_level:
            max_depth += 1
            next_level = list(
                Department.objects.filter(
                    parent_id__in=current_level, is_active=True
                ).values_list('id', flat=True)
            )
            current_level = next_level

        return max_depth

    def _get_depth_distribution(self):
        """
        Get a distribution of departments by their depth level.
        Level 1 = root departments, Level 2 = their children, etc.
        """
        distribution = []
        roots = list(
            Department.objects.filter(parent__isnull=True, is_active=True).values_list('id', flat=True)
        )
        if not roots:
            return distribution

        level = 1
        current_level = roots

        while current_level:
            count = len(current_level)
            distribution.append({
                'المستوى': level,
                'عدد_الأقسام': count,
            })
            level += 1
            current_level = list(
                Department.objects.filter(
                    parent_id__in=current_level, is_active=True
                ).values_list('id', flat=True)
            )

        return distribution
