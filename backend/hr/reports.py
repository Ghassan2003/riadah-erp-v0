"""
HR Reports & Analytics Views.
Provides comprehensive workforce, turnover, cost, leave, attendance,
and performance reporting with CSV/JSON export support.

All text in Arabic for display purposes.
"""

import csv
import io
from datetime import date, timedelta

from django.db.models import (
    Sum, Count, Avg, F, Q, Value, DecimalField,
    IntegerField, Case, When, ExpressionWrapper,
)
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.http import HttpResponse
from rest_framework import permissions, views, status
from rest_framework.response import Response

from .models import (
    Department, Employee, Attendance, LeaveRequest,
    LeaveBalance, PerformanceReview, EmploymentHistory, Payslip,
)


def _parse_date(params, key):
    """Parse a YYYY-MM-DD date from query params. Returns date or None."""
    val = params.get(key)
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def _parse_int(params, key, default=None):
    """Parse an integer from query params."""
    val = params.get(key)
    if not val:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# =============================================
# 1. Workforce Report
# =============================================

class WorkforceReportView(views.APIView):
    """
    GET /hr/reports/workforce/
    تقرير شامل عن القوى العاملة يشمل:
    - إجمالي الموظفين حسب الحالة (نشط، إجازة، موقوف، منتهي الخدمة)
    - توزيع الموظفين حسب الأقسام والجنس
    - متوسط فترة الخدمة ومتوسط الراتب
    - التعيينات الجديدة والإنهاءات خلال فترة محددة
    يدعم تصدير CSV عبر ?format=csv
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        params = request.query_params
        date_from = _parse_date(params, 'date_from')
        date_to = _parse_date(params, 'date_to')
        export_format = params.get('format', 'json')

        # --- Base counts ---
        all_active = Employee.objects.filter(is_active=True)

        total = all_active.count()
        active = all_active.filter(status='active').count()
        on_leave = all_active.filter(status='on_leave').count()
        suspended = all_active.filter(status='suspended').count()
        terminated = Employee.objects.filter(status='terminated').count()

        # --- Count by department ---
        dept_counts = (
            all_active
            .values('department__id', 'department__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        by_department = [
            {'قسم': item['department__name'] or 'بدون قسم', 'عدد الموظفين': item['count']}
            for item in dept_counts
        ]

        # --- Count by gender ---
        gender_counts = (
            all_active
            .values('gender')
            .annotate(count=Count('id'))
        )
        gender_map = dict(Employee.GENDER_CHOICES)
        by_gender = [
            {'الجنس': gender_map.get(g, g or 'غير محدد'), 'العدد': item['count']}
            for item in gender_counts
        ]

        # --- Count by nationality (using national_id as proxy) ---
        # Since there's no explicit nationality field, we group by whether
        # national_id starts with '1' (Saudi) or not.
        saudi_count = all_active.filter(
            national_id__regex=r'^1'
        ).count()
        non_saudi_count = all_active.filter(
            national_id__regex=r'^2'
        ).count()
        unknown_nationality = total - saudi_count - non_saudi_count
        by_nationality = [
            {'الجنسية': 'سعودي', 'العدد': saudi_count},
            {'الجنسية': 'غير سعودي', 'العدد': non_saudi_count},
            {'الجنسية': 'غير محدد', 'العدد': max(unknown_nationality, 0)},
        ]

        # --- Average tenure (days from hire_date to today) ---
        today = date.today()
        tenure_result = all_active.filter(hire_date__isnull=False).aggregate(
            avg_days=Avg(
                ExpressionWrapper(
                    today - F('hire_date'),
                    output_field=IntegerField()
                )
            )
        )
        avg_tenure_days = tenure_result['avg_days']
        avg_tenure_years = round((avg_tenure_days or 0) / 365.25, 1) if avg_tenure_days else 0

        # --- Average salary ---
        salary_result = all_active.aggregate(
            avg_salary=Coalesce(Avg('salary'), Value(0), output_field=DecimalField(max_digits=12, decimal_places=2)),
            avg_total_salary=Coalesce(
                Avg(F('salary') + F('housing_allowance') + F('transport_allowance')),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

        # --- New hires in period ---
        new_hires_qs = EmploymentHistory.objects.filter(action_type='hire')
        if date_from:
            new_hires_qs = new_hires_qs.filter(effective_date__gte=date_from)
        if date_to:
            new_hires_qs = new_hires_qs.filter(effective_date__lte=date_to)
        new_hires = new_hires_qs.count()

        # --- Terminations in period ---
        terminations_qs = EmploymentHistory.objects.filter(action_type='termination')
        if date_from:
            terminations_qs = terminations_qs.filter(effective_date__gte=date_from)
        if date_to:
            terminations_qs = terminations_qs.filter(effective_date__lte=date_to)
        terminations = terminations_qs.count()

        report_data = {
            'ملخص_القوى_العاملة': {
                'إجمالي_الموظفين': total,
                'نشط': active,
                'في_إجازة': on_leave,
                'موقوف': suspended,
                'منتهي_الخدمة': terminated,
            },
            'توزيع_حسب_الأقسام': by_department,
            'توزيع_حسب_الجنس': by_gender,
            'توزيع_حسب_الجنسية': by_nationality,
            'متوسط_فترة_الخدمة': {
                'بالأيام': int(avg_tenure_days) if avg_tenure_days else 0,
                'بالسنوات': avg_tenure_years,
            },
            'متوسط_الراتب': {
                'الراتب_الأساسي': str(salary_result['avg_salary']),
                'إجمالي_التعويضات': str(salary_result['avg_total_salary']),
            },
            'التعيينات_الجديدة': new_hires,
            'الإنهاءات': terminations,
            'فترة_التقرير': {
                'من': str(date_from) if date_from else None,
                'إلى': str(date_to) if date_to else None,
            },
        }

        # --- CSV Export ---
        if export_format == 'csv':
            return self._export_csv(report_data, 'تقرير_القوى_العاملة')

        return Response(report_data)

    def _export_csv(self, data, title):
        """Export report data as CSV download."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        # Header
        writer.writerow(['تقرير', title])

        # Summary section
        summary = data['ملخص_القوى_العاملة']
        writer.writerow([])
        writer.writerow(['ملخص القوى العاملة'])
        for k, v in summary.items():
            writer.writerow([k, v])

        # By department
        writer.writerow([])
        writer.writerow(['توزيع حسب الأقسام'])
        writer.writerow(['القسم', 'عدد الموظفين'])
        for row in data['توزيع_حسب_الأقسام']:
            writer.writerow([row['قسم'], row['عدد الموظفين']])

        # By gender
        writer.writerow([])
        writer.writerow(['توزيع حسب الجنس'])
        writer.writerow(['الجنس', 'العدد'])
        for row in data['توزيع_حسب_الجنس']:
            writer.writerow([row['الجنس'], row['العدد']])

        # By nationality
        writer.writerow([])
        writer.writerow(['توزيع حسب الجنسية'])
        writer.writerow(['الجنسية', 'العدد'])
        for row in data['توزيع_حسب_الجنسية']:
            writer.writerow([row['الجنسية'], row['العدد']])

        # Tenure & salary
        writer.writerow([])
        writer.writerow(['متوسط فترة الخدمة (بالسنوات)', data['متوسط_فترة_الخدمة']['بالسنوات']])
        writer.writerow(['متوسط الراتب الأساسي', data['متوسط_الراتب']['الراتب_الأساسي']])
        writer.writerow(['متوسط إجمالي التعويضات', data['متوسط_الراتب']['إجمالي_التعويضات']])

        # Period stats
        writer.writerow([])
        writer.writerow(['التعيينات الجديدة', data['التعيينات_الجديدة']])
        writer.writerow(['الإنهاءات', data['الإنهاءات']])

        # Response
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="workforce_report.csv"'
        return response


# =============================================
# 2. Turnover Report
# =============================================

class TurnoverReportView(views.APIView):
    """
    GET /hr/reports/turnover/
    تقرير معدل دوران العمالة يشمل:
    - معدل الدوران الشهري/ربع سنوي/سنوي
    - الدوران الطوعي مقابل غير الطوعي
    - الدوران حسب الأقسام
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        params = request.query_params
        date_from = _parse_date(params, 'date_from')
        date_to = _parse_date(params, 'date_to')

        # Default to last 12 months if not specified
        today = date.today()
        if not date_from:
            date_from = today - timedelta(days=365)
        if not date_to:
            date_to = today

        terminations_qs = EmploymentHistory.objects.filter(
            action_type='termination',
            effective_date__gte=date_from,
            effective_date__lte=date_to,
        ).select_related('employee__department')

        total_terminations = terminations_qs.count()

        # Average employee count during the period (simplified: use current active + terminated)
        avg_headcount = Employee.objects.filter(is_active=True).count()
        if avg_headcount == 0:
            avg_headcount = 1

        # Overall turnover rate
        days_in_period = (date_to - date_from).days
        months_in_period = max(days_in_period / 30.44, 1)
        annualized_turnover = round((total_terminations / avg_headcount) * 100, 2)

        # Voluntary vs Involuntary
        # We use the reason field to distinguish: "استقالة" = voluntary, rest = involuntary
        voluntary = terminations_qs.filter(reason__icontains='استقالة').count()
        involuntary = total_terminations - voluntary

        # Turnover by department
        dept_turnover = (
            terminations_qs
            .values('department__id', 'department__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        by_department = [
            {
                'قسم': item['department__name'] or 'بدون قسم',
                'عدد_الإنهاءات': item['count'],
                'نسبة_الدوران': round((item['count'] / avg_headcount) * 100, 2),
            }
            for item in dept_turnover
        ]

        # Monthly turnover breakdown
        monthly_qs = (
            terminations_qs
            .annotate(month=ExtractMonth('effective_date'), year=ExtractYear('effective_date'))
            .values('year', 'month')
            .annotate(count=Count('id'))
            .order_by('year', 'month')
        )
        monthly_turnover = [
            {
                'السنة': item['year'],
                'الشهر': item['month'],
                'عدد_الإنهاءات': item['count'],
            }
            for item in monthly_qs
        ]

        # Quarterly turnover breakdown
        quarter_map = {1: 'الربع الأول', 2: 'الربع الثاني', 3: 'الربع الثالث', 4: 'الربع الرابع'}
        quarterly_data = {}
        for item in terminations_qs:
            m = item.effective_date.month
            y = item.effective_date.year
            q = (m - 1) // 3 + 1
            key = (y, q)
            quarterly_data[key] = quarterly_data.get(key, 0) + 1

        quarterly_turnover = [
            {'السنة': k[0], 'الربع': k[1], 'اسم_الربع': quarter_map.get(k[1], f'ربع {k[1]}'), 'عدد_الإنهاءات': v}
            for k, v in sorted(quarterly_data.items())
        ]

        report_data = {
            'ملخص_الدوران': {
                'إجمالي_الإنهاءات': total_terminations,
                'معدل_الدوران_السنوي_المعادل': f'{annualized_turnover}%',
                'متوسط_عدد_الموظفين_خلال_الفترة': avg_headcount,
            },
            'الدوران_الطوعي_وغير_الطوعي': {
                'طوعي_استقالة': voluntary,
                'غير_طوعي': involuntary,
            },
            'الدوران_حسب_الأقسام': by_department,
            'الدوران_الشهري': monthly_turnover,
            'الدوران_الربع_سنوي': quarterly_turnover,
            'فترة_التقرير': {
                'من': str(date_from),
                'إلى': str(date_to),
                'بالأشهر': round(months_in_period, 1),
            },
        }

        export_format = params.get('format', 'json')
        if export_format == 'csv':
            return self._export_csv(report_data)

        return Response(report_data)

    def _export_csv(self, data):
        """Export turnover report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        writer.writerow(['تقرير معدل دوران العمالة'])

        summary = data['ملخص_الدوران']
        writer.writerow([])
        for k, v in summary.items():
            writer.writerow([k, v])

        writer.writerow([])
        vol = data['الدوران_الطوعي_وغير_الطوعي']
        writer.writerow(['النوع', 'العدد'])
        for k, v in vol.items():
            writer.writerow([k, v])

        writer.writerow([])
        writer.writerow(['الدوران حسب الأقسام'])
        writer.writerow(['القسم', 'عدد الإنهاءات', 'نسبة الدوران %'])
        for row in data['الدوران_حسب_الأقسام']:
            writer.writerow([row['قسم'], row['عدد_الإنهاءات'], row['نسبة_الدوران']])

        writer.writerow([])
        writer.writerow(['الدوران الشهري'])
        writer.writerow(['السنة', 'الشهر', 'عدد الإنهاءات'])
        for row in data['الدوران_الشهري']:
            writer.writerow([row['السنة'], row['الشهر'], row['عدد_الإنهاءات']])

        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="turnover_report.csv"'
        return response


# =============================================
# 3. Employee Cost Report
# =============================================

class EmployeeCostReportView(views.APIView):
    """
    GET /hr/reports/employee-cost/
    تقرير تكلفة الموظفين يشمل:
    - التكلفة الإجمالية لكل موظف (راتب + بدلات + تأمينات + مستحقات)
    - التوزيع حسب الأقسام
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        params = request.query_params
        date_from = _parse_date(params, 'date_from')
        date_to = _parse_date(params, 'date_to')

        # --- Individual employee costs from Payslip data ---
        payslip_qs = Payslip.objects.all()
        if date_from:
            payslip_qs = payslip_qs.filter(year__gte=date_from.year)
            if date_from.year == date_to.year if date_to else True:
                payslip_qs = payslip_qs.filter(month__gte=date_from.month)
        if date_to:
            payslip_qs = payslip_qs.filter(year__lte=date_to.year)
            if date_from and date_from.year == date_to.year:
                payslip_qs = payslip_qs.filter(month__lte=date_to.month)

        employee_costs = (
            payslip_qs
            .values('employee__id', 'employee__first_name', 'employee__last_name',
                    'employee__employee_number', 'employee__department__name')
            .annotate(
                total_basic=Coalesce(Sum('basic_salary'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
                total_housing=Coalesce(Sum('housing_allowance'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
                total_transport=Coalesce(Sum('transport_allowance'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
                total_overtime=Coalesce(Sum('overtime_pay'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
                total_bonuses=Coalesce(Sum('bonuses'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
                total_insurance=Coalesce(Sum('insurance_deduction'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
                total_deductions=Coalesce(
                    Sum('deductions') + Sum('tax_deduction') + Sum('loan_deduction')
                    + Sum('advance_deduction') + Sum('other_deduction'),
                    Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                months_count=Count('id'),
            )
            .order_by('-total_basic')
        )

        per_employee = []
        for item in employee_costs:
            total_cost = (
                item['total_basic'] + item['total_housing'] + item['total_transport']
                + item['total_overtime'] + item['total_bonuses']
            )
            per_employee.append({
                'رقم_الموظف': item['employee__employee_number'],
                'اسم_الموظف': f"{item['employee__first_name']} {item['employee__last_name']}",
                'القسم': item['employee__department__name'] or 'بدون قسم',
                'الراتب_الأساسي': str(item['total_basic']),
                'بدل_السكن': str(item['total_housing']),
                'بدل_النقل': str(item['total_transport']),
                'أجر_إضافي': str(item['total_overtime']),
                'مكافآت': str(item['total_bonuses']),
                'خصم_التأمينات': str(item['total_insurance']),
                'إجمالي_الخصومات': str(item['total_deductions']),
                'إجمالي_التكلفة': str(total_cost),
                'عدد_الأشهر': item['months_count'],
            })

        # --- Department-wise cost breakdown ---
        dept_costs = (
            payslip_qs
            .values('employee__department__name')
            .annotate(
                employees_count=Count('employee__id', distinct=True),
                total_salary=Coalesce(
                    Sum('basic_salary') + Sum('housing_allowance') + Sum('transport_allowance')
                    + Sum('overtime_pay') + Sum('bonuses'),
                    Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                total_deductions=Coalesce(
                    Sum('deductions') + Sum('insurance_deduction') + Sum('tax_deduction')
                    + Sum('loan_deduction') + Sum('advance_deduction') + Sum('other_deduction'),
                    Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            )
            .order_by('-total_salary')
        )

        by_department = [
            {
                'القسم': item['employee__department__name'] or 'بدون قسم',
                'عدد_الموظفين': item['employees_count'],
                'إجمالي_التكاليف': str(item['total_salary']),
                'إجمالي_الخصومات': str(item['total_deductions']),
                'صافي_التكلفة': str(item['total_salary'] - item['total_deductions']),
            }
            for item in dept_costs
        ]

        # --- Grand totals ---
        grand_totals = payslip_qs.aggregate(
            total_salary=Coalesce(
                Sum('basic_salary') + Sum('housing_allowance') + Sum('transport_allowance')
                + Sum('overtime_pay') + Sum('bonuses'),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            total_deductions=Coalesce(
                Sum('deductions') + Sum('insurance_deduction') + Sum('tax_deduction')
                + Sum('loan_deduction') + Sum('advance_deduction') + Sum('other_deduction'),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            total_employees=Count('employee__id', distinct=True),
        )

        report_data = {
            'الإجماليات': {
                'إجمالي_التكاليف': str(grand_totals['total_salary']),
                'إجمالي_الخصومات': str(grand_totals['total_deductions']),
                'صافي_التكلفة': str(grand_totals['total_salary'] - grand_totals['total_deductions']),
                'عدد_الموظفين': grand_totals['total_employees'],
            },
            'تكلفة_الموظفين': per_employee,
            'التوزيع_حسب_الأقسام': by_department,
            'فترة_التقرير': {
                'من': str(date_from) if date_from else None,
                'إلى': str(date_to) if date_to else None,
            },
        }

        export_format = params.get('format', 'json')
        if export_format == 'csv':
            return self._export_csv(report_data)

        return Response(report_data)

    def _export_csv(self, data):
        """Export employee cost report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        writer.writerow(['تقرير تكلفة الموظفين'])

        totals = data['الإجماليات']
        writer.writerow([])
        for k, v in totals.items():
            writer.writerow([k, v])

        writer.writerow([])
        writer.writerow(['تكلفة الموظفين'])
        fields = ['رقم_الموظف', 'اسم_الموظف', 'القسم', 'الراتب_الأساسي', 'بدل_السكن',
                   'بدل_النقل', 'أجر_إضافي', 'مكافآت', 'خصم_التأمينات', 'إجمالي_الخصومات',
                   'إجمالي_التكلفة', 'عدد_الأشهر']
        writer.writerow(fields)
        for emp in data['تكلفة_الموظفين']:
            writer.writerow([emp[f] for f in fields])

        writer.writerow([])
        writer.writerow(['التوزيع حسب الأقسام'])
        writer.writerow(['القسم', 'عدد الموظفين', 'إجمالي التكاليف', 'إجمالي الخصومات', 'صافي التكلفة'])
        for dept in data['التوزيع_حسب_الأقسام']:
            writer.writerow([
                dept['القسم'], dept['عدد_الموظفين'], dept['إجمالي_التكاليف'],
                dept['إجمالي_الخصومات'], dept['صافي_التكلفة'],
            ])

        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="employee_cost_report.csv"'
        return response


# =============================================
# 4. Leave Report
# =============================================

class LeaveReportView(views.APIView):
    """
    GET /hr/reports/leaves/
    تقرير الإجازات يشمل:
    - ملخص أرصدة الإجازات لجميع الموظفين
    - أكثر أنواع الإجازات استخداماً
    - تحليل أنماط الإجازات (الأقسام ذات أعلى غياب)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        params = request.query_params
        date_from = _parse_date(params, 'date_from')
        date_to = _parse_date(params, 'date_to')
        year = _parse_int(params, 'year', default=date.today().year)

        # --- Leave balance summary ---
        balance_qs = LeaveBalance.objects.filter(year=year).select_related('employee')

        balance_summary = (
            balance_qs
            .values('employee__id', 'employee__first_name', 'employee__last_name',
                    'employee__employee_number', 'leave_type')
            .annotate(
                total=Coalesce(Sum('total_days'), 0),
                used=Coalesce(Sum('used_days'), 0),
                remaining=Coalesce(Sum('remaining_days'), 0),
            )
            .order_by('employee__first_name', 'leave_type')
        )

        leave_type_map = dict(LeaveRequest.LEAVE_TYPE_CHOICES)
        employee_balances = []
        for item in balance_summary:
            employee_balances.append({
                'رقم_الموظف': item['employee__employee_number'],
                'اسم_الموظف': f"{item['employee__first_name']} {item['employee__last_name']}",
                'نوع_الإجازة': leave_type_map.get(item['leave_type'], item['leave_type']),
                'الرصيد_الإجمالي': item['total'],
                'الأيام_المستخدمة': item['used'],
                'الأيام_المتبقية': item['remaining'],
            })

        # --- Most used leave types (approved leaves) ---
        leave_type_usage = (
            LeaveRequest.objects
            .filter(approval_status='approved')
            .values('leave_type')
            .annotate(
                total_days=Coalesce(Sum('days'), 0),
                request_count=Count('id'),
            )
            .order_by('-total_days')
        )
        most_used_types = [
            {
                'نوع_الإجازة': leave_type_map.get(item['leave_type'], item['leave_type']),
                'إجمالي_الأيام': item['total_days'],
                'عدد_الطلبات': item['request_count'],
            }
            for item in leave_type_usage
        ]

        # --- Leave pattern analysis: departments with most absence ---
        absence_qs = LeaveRequest.objects.filter(approval_status='approved')
        if date_from:
            absence_qs = absence_qs.filter(start_date__gte=date_from)
        if date_to:
            absence_qs = absence_qs.filter(end_date__lte=date_to)

        dept_absence = (
            absence_qs
            .values('employee__department__id', 'employee__department__name')
            .annotate(
                total_leave_days=Coalesce(Sum('days'), 0),
                leave_requests_count=Count('id'),
                affected_employees=Count('employee__id', distinct=True),
            )
            .order_by('-total_leave_days')
        )
        dept_patterns = [
            {
                'القسم': item['employee__department__name'] or 'بدون قسم',
                'إجمالي_أيام_الغياب': item['total_leave_days'],
                'عدد_طلبات_الإجازة': item['leave_requests_count'],
                'عدد_الموظفين_المتأثرين': item['affected_employees'],
            }
            for item in dept_absence
        ]

        # --- Pending leave requests ---
        pending_count = LeaveRequest.objects.filter(approval_status='pending').count()

        # --- Monthly leave trend ---
        monthly_leaves = (
            absence_qs
            .annotate(month=ExtractMonth('start_date'))
            .values('month')
            .annotate(total_days=Coalesce(Sum('days'), 0), count=Count('id'))
            .order_by('month')
        )
        leave_trend = [
            {'الشهر': item['month'], 'إجمالي_الأيام': item['total_days'], 'عدد_الطلبات': item['count']}
            for item in monthly_leaves
        ]

        report_data = {
            'أرصدة_الإجازات': employee_balances,
            'أكثر_أنواع_الإجازات_استخداماً': most_used_types,
            'تحليل_أنماط_الإجازات_حسب_الأقسام': dept_patterns,
            'اتجاه_الإجازات_الشهري': leave_trend,
            'طلبات_الإجازة_المعلقة': pending_count,
            'فترة_التقرير': {
                'السنة': year,
                'من': str(date_from) if date_from else None,
                'إلى': str(date_to) if date_to else None,
            },
        }

        export_format = params.get('format', 'json')
        if export_format == 'csv':
            return self._export_csv(report_data)

        return Response(report_data)

    def _export_csv(self, data):
        """Export leave report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        writer.writerow(['تقرير الإجازات'])

        writer.writerow([])
        writer.writerow(['أرصدة الإجازات'])
        fields = ['رقم_الموظف', 'اسم_الموظف', 'نوع_الإجازة', 'الرصيد_الإجمالي',
                  'الأيام_المستخدمة', 'الأيام_المتبقية']
        writer.writerow(fields)
        for row in data['أرصدة_الإجازات']:
            writer.writerow([row[f] for f in fields])

        writer.writerow([])
        writer.writerow(['أكثر أنواع الإجازات استخداماً'])
        writer.writerow(['نوع الإجازة', 'إجمالي الأيام', 'عدد الطلبات'])
        for row in data['أكثر_أنواع_الإجازات_استخداماً']:
            writer.writerow([row['نوع_الإجازة'], row['إجمالي_الأيام'], row['عدد_الطلبات']])

        writer.writerow([])
        writer.writerow(['تحليل أنماط الإجازات حسب الأقسام'])
        writer.writerow(['القسم', 'إجمالي أيام الغياب', 'عدد الطلبات', 'عدد الموظفين المتأثرين'])
        for row in data['تحليل_أنماط_الإجازات_حسب_الأقسام']:
            writer.writerow([
                row['القسم'], row['إجمالي_أيام_الغياب'],
                row['عدد_طلبات_الإجازة'], row['عدد_الموظفين_المتأثرين'],
            ])

        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="leave_report.csv"'
        return response


# =============================================
# 5. Attendance Report
# =============================================

class AttendanceReportView(views.APIView):
    """
    GET /hr/reports/attendance/
    تقرير الحضور والانصراف يشمل:
    - ملخص الحضور اليومي/الأسبوعي/الشهري
    - عدد التأخرات
    - أكثر الموظفين غياباً
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        params = request.query_params
        date_from = _parse_date(params, 'date_from')
        date_to = _parse_date(params, 'date_to')

        today = date.today()
        if not date_from:
            date_from = today - timedelta(days=30)
        if not date_to:
            date_to = today

        attendance_qs = Attendance.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
        ).select_related('employee__department')

        total_records = attendance_qs.count()
        days_in_period = (date_to - date_from).days + 1

        # --- Daily attendance summary ---
        daily_summary = (
            attendance_qs
            .values('date')
            .annotate(
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                half_day=Count('id', filter=Q(status='half_day')),
                holiday=Count('id', filter=Q(status='holiday')),
            )
            .order_by('date')
        )
        daily_data = [
            {
                'التاريخ': str(item['date']),
                'حاضر': item['present'],
                'غائب': item['absent'],
                'متأخر': item['late'],
                'نصف_يوم': item['half_day'],
                'إجازة_رسمية': item['holiday'],
            }
            for item in daily_summary
        ]

        # --- Weekly summary (ISO week) ---
        from django.db.models.functions import ExtractWeek, ExtractIsoWeekYear
        weekly_summary = (
            attendance_qs
            .annotate(
                week=ExtractIsoWeek('date'),
                iso_year=ExtractIsoWeekYear('date'),
            )
            .values('iso_year', 'week')
            .annotate(
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                total=Count('id'),
            )
            .order_by('iso_year', 'week')
        )
        weekly_data = [
            {
                'السنة': item['iso_year'],
                'الأسبوع': item['week'],
                'حاضر': item['present'],
                'غائب': item['absent'],
                'متأخر': item['late'],
                'إجمالي': item['total'],
            }
            for item in weekly_summary
        ]

        # --- Monthly summary ---
        monthly_summary = (
            attendance_qs
            .annotate(month=ExtractMonth('date'), year=ExtractYear('date'))
            .values('year', 'month')
            .annotate(
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                half_day=Count('id', filter=Q(status='half_day')),
                total=Count('id'),
            )
            .order_by('year', 'month')
        )
        monthly_data = [
            {
                'السنة': item['year'],
                'الشهر': item['month'],
                'حاضر': item['present'],
                'غائب': item['absent'],
                'متأخر': item['late'],
                'نصف_يوم': item['half_day'],
                'إجمالي_السجلات': item['total'],
            }
            for item in monthly_summary
        ]

        # --- Late arrivals ---
        total_late = attendance_qs.filter(status='late').count()

        # Late by department
        late_by_dept = (
            attendance_qs
            .filter(status='late')
            .values('employee__department__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        late_by_department = [
            {'القسم': item['employee__department__name'] or 'بدون قسم', 'عدد_التأخرات': item['count']}
            for item in late_by_dept
        ]

        # --- Most absent employees ---
        most_absent = (
            attendance_qs
            .filter(status='absent')
            .values('employee__id', 'employee__first_name', 'employee__last_name',
                    'employee__employee_number', 'employee__department__name')
            .annotate(absent_days=Count('id'))
            .order_by('-absent_days')[:20]
        )
        absent_employees = [
            {
                'رقم_الموظف': item['employee__employee_number'],
                'اسم_الموظف': f"{item['employee__first_name']} {item['employee__last_name']}",
                'القسم': item['employee__department__name'] or 'بدون قسم',
                'أيام_الغياب': item['absent_days'],
            }
            for item in most_absent
        ]

        # --- Overall attendance rate ---
        total_present = attendance_qs.filter(status='present').count()
        attendance_rate = round((total_present / total_records * 100), 2) if total_records > 0 else 0

        report_data = {
            'ملخص_الحضور': {
                'إجمالي_السجلات': total_records,
                'أيام_الفترة': days_in_period,
                'نسبة_الحضور': f'{attendance_rate}%',
                'إجمالي_الحاضرين': total_present,
                'إجمالي_الغائبين': attendance_qs.filter(status='absent').count(),
                'إجمالي_التأخرات': total_late,
                'إجمالي_نصف_الأيام': attendance_qs.filter(status='half_day').count(),
            },
            'الملخص_اليومي': daily_data,
            'الملخص_الأسبوعي': weekly_data,
            'الملخص_الشهري': monthly_data,
            'التأخرات_حسب_الأقسام': late_by_department,
            'أكثر_الموظفين_غياباً': absent_employees,
            'فترة_التقرير': {
                'من': str(date_from),
                'إلى': str(date_to),
            },
        }

        export_format = params.get('format', 'json')
        if export_format == 'csv':
            return self._export_csv(report_data)

        return Response(report_data)

    def _export_csv(self, data):
        """Export attendance report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        writer.writerow(['تقرير الحضور والانصراف'])

        summary = data['ملخص_الحضور']
        writer.writerow([])
        for k, v in summary.items():
            writer.writerow([k, v])

        writer.writerow([])
        writer.writerow(['الملخص اليومي'])
        writer.writerow(['التاريخ', 'حاضر', 'غائب', 'متأخر', 'نصف يوم', 'إجازة رسمية'])
        for row in data['الملخص_اليومي']:
            writer.writerow([
                row['التاريخ'], row['حاضر'], row['غائب'], row['متأخر'],
                row['نصف_يوم'], row['إجازة_رسمية'],
            ])

        writer.writerow([])
        writer.writerow(['أكثر الموظفين غياباً'])
        writer.writerow(['رقم الموظف', 'اسم الموظف', 'القسم', 'أيام الغياب'])
        for row in data['أكثر_الموظفين_غياباً']:
            writer.writerow([row['رقم_الموظف'], row['اسم_الموظف'], row['القسم'], row['أيام_الغياب']])

        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
        return response


# =============================================
# 6. Performance Report
# =============================================

class PerformanceReportView(views.APIView):
    """
    GET /hr/reports/performance/
    تقرير تقييم الأداء يشمل:
    - متوسط التقييمات حسب الأقسام
    - توزيع الأداء (كم عدد 1-5)
    - اتجاه الأداء عبر الفترات
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        params = request.query_params
        year = _parse_int(params, 'year', default=date.today().year)

        performance_qs = PerformanceReview.objects.filter(
            year=year,
            status='completed',
            overall_rating__isnull=False,
        ).select_related('employee__department')

        total_reviews = performance_qs.count()

        # --- Average ratings by department ---
        dept_ratings = (
            performance_qs
            .values('employee__department__id', 'employee__department__name')
            .annotate(
                avg_overall=Coalesce(Avg('overall_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
                avg_goals=Coalesce(Avg('goals_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
                avg_competencies=Coalesce(Avg('competencies_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
                avg_teamwork=Coalesce(Avg('teamwork_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
                avg_communication=Coalesce(Avg('communication_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
                avg_initiative=Coalesce(Avg('initiative_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
                review_count=Count('id'),
            )
            .order_by('-avg_overall')
        )
        by_department = [
            {
                'القسم': item['employee__department__name'] or 'بدون قسم',
                'متوسط_التقييم_العام': str(item['avg_overall']),
                'متوسط_تقييم_الأهداف': str(item['avg_goals']),
                'متوسط_تقييم_الكفاءات': str(item['avg_competencies']),
                'متوسط_العمل_الجماعي': str(item['avg_teamwork']),
                'متوسط_التواصل': str(item['avg_communication']),
                'متوسط_المبادرة': str(item['avg_initiative']),
                'عدد_التقييمات': item['review_count'],
            }
            for item in dept_ratings
        ]

        # --- Performance distribution (1-5 scale) ---
        distribution = []
        for rating_val in range(1, 6):
            count = performance_qs.filter(
                overall_rating__gte=rating_val - 0.5,
                overall_rating__lt=rating_val + 0.5,
            ).count()
            # More precise: round to nearest integer
            count = performance_qs.filter(
                overall_rating__gte=float(rating_val),
                overall_rating__lt=float(rating_val) + 1.0,
            ).count()
            # Actually let's bucket by rounding
            count = sum(
                1 for r in performance_qs.values_list('overall_rating', flat=True)
                if round(float(r)) == rating_val
            )
            distribution.append({
                'التقييم': rating_val,
                'الوصف': self._rating_label(rating_val),
                'العدد': count,
            })

        # Recalculate using proper ORM
        rating_labels = {1: 'ضعيف', 2: 'مقبول', 3: 'جيد', 4: 'جيد جداً', 5: 'ممتاز'}
        distribution = []
        for r in range(1, 6):
            count = performance_qs.filter(overall_rating__gte=r, overall_rating__lt=r + 1).count()
            distribution.append({
                'التقييم': r,
                'الوصف': rating_labels.get(r, str(r)),
                'العدد': count,
                'النسبة': f'{round(count / total_reviews * 100, 1)}%' if total_reviews > 0 else '0%',
            })

        # --- Trend over periods ---
        # Group by review_period and quarter
        trend_qs = (
            PerformanceReview.objects
            .filter(year=year, status='completed', overall_rating__isnull=False)
            .annotate(month=ExtractMonth('start_date'))
            .values('review_period', 'quarter', 'month')
            .annotate(
                avg_rating=Coalesce(Avg('overall_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
                count=Count('id'),
            )
            .order_by('review_period', 'quarter', 'month')
        )
        period_map = dict(PerformanceReview.REVIEW_PERIOD_CHOICES)
        trend_data = [
            {
                'فترة_التقييم': period_map.get(item['review_period'], item['review_period']),
                'الربع': item['quarter'],
                'الشهر': item['month'],
                'متوسط_التقييم': str(item['avg_rating']),
                'عدد_التقييمات': item['count'],
            }
            for item in trend_qs
        ]

        # --- Overall averages ---
        overall_avgs = performance_qs.aggregate(
            avg_overall=Coalesce(Avg('overall_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
            avg_goals=Coalesce(Avg('goals_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
            avg_competencies=Coalesce(Avg('competencies_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
            avg_teamwork=Coalesce(Avg('teamwork_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
            avg_communication=Coalesce(Avg('communication_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
            avg_initiative=Coalesce(Avg('initiative_rating'), Value(0), output_field=DecimalField(max_digits=3, decimal_places=1)),
        )

        # --- Top and bottom performers ---
        top_performers = (
            performance_qs
            .values('employee__id', 'employee__first_name', 'employee__last_name',
                    'employee__employee_number', 'employee__department__name')
            .annotate(avg_rating=Avg('overall_rating'))
            .order_by('-avg_rating')[:10]
        )
        bottom_performers = (
            performance_qs
            .values('employee__id', 'employee__first_name', 'employee__last_name',
                    'employee__employee_number', 'employee__department__name')
            .annotate(avg_rating=Avg('overall_rating'))
            .order_by('avg_rating')[:10]
        )

        report_data = {
            'ملخص_الأداء': {
                'إجمالي_التقييمات': total_reviews,
                'السنة': year,
                'متوسط_التقييم_العام': str(overall_avgs['avg_overall']),
                'متوسط_تقييم_الأهداف': str(overall_avgs['avg_goals']),
                'متوسط_تقييم_الكفاءات': str(overall_avgs['avg_competencies']),
                'متوسط_العمل_الجماعي': str(overall_avgs['avg_teamwork']),
                'متوسط_التواصل': str(overall_avgs['avg_communication']),
                'متوسط_المبادرة': str(overall_avgs['avg_initiative']),
            },
            'متوسطات_حسب_الأقسام': by_department,
            'توزيع_الأداء': distribution,
            'اتجاه_الأداء_عبر_الفترات': trend_data,
            'أفضل_الموظفين_أداءً': [
                {
                    'رقم_الموظف': item['employee__employee_number'],
                    'اسم_الموظف': f"{item['employee__first_name']} {item['employee__last_name']}",
                    'القسم': item['employee__department__name'] or 'بدون قسم',
                    'متوسط_التقييم': str(item['avg_rating']),
                }
                for item in top_performers
            ],
            'أقل_الموظفين_أداءً': [
                {
                    'رقم_الموظف': item['employee__employee_number'],
                    'اسم_الموظف': f"{item['employee__first_name']} {item['employee__last_name']}",
                    'القسم': item['employee__department__name'] or 'بدون قسم',
                    'متوسط_التقييم': str(item['avg_rating']),
                }
                for item in bottom_performers
            ],
        }

        export_format = params.get('format', 'json')
        if export_format == 'csv':
            return self._export_csv(report_data)

        return Response(report_data)

    @staticmethod
    def _rating_label(rating):
        """Return Arabic label for a rating value."""
        labels = {1: 'ضعيف', 2: 'مقبول', 3: 'جيد', 4: 'جيد جداً', 5: 'ممتاز'}
        return labels.get(rating, str(rating))

    def _export_csv(self, data):
        """Export performance report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        writer.writerow(['تقرير تقييم الأداء'])

        summary = data['ملخص_الأداء']
        writer.writerow([])
        for k, v in summary.items():
            writer.writerow([k, v])

        writer.writerow([])
        writer.writerow(['توزيع الأداء'])
        writer.writerow(['التقييم', 'الوصف', 'العدد', 'النسبة'])
        for row in data['توزيع_الأداء']:
            writer.writerow([row['التقييم'], row['الوصف'], row['العدد'], row['النسبة']])

        writer.writerow([])
        writer.writerow(['متوسطات حسب الأقسام'])
        writer.writerow(['القسم', 'متوسط التقييم العام', 'عدد التقييمات'])
        for row in data['متوسطات_حسب_الأقسام']:
            writer.writerow([row['القسم'], row['متوسط_التقييم_العام'], row['عدد_التقييمات']])

        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="performance_report.csv"'
        return response
