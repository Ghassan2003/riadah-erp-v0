"""
Core views - System info, Dashboard API, Reports API, Backup.
"""

from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, F, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from users.permissions import IsAdmin


class SystemInfoView(views.APIView):
    """GET: System information."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.contrib.auth import get_user_model
        import django
        import sys
        User = get_user_model()
        from django.conf import settings
        info = {
            'version': '2.0.0',
            'python_version': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
            'django_version': django.__version__,
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'database': settings.DATABASES['default']['ENGINE'],
            'debug': settings.DEBUG,
            'installed_apps': [
                app for app in settings.INSTALLED_APPS
                if not app.startswith('django.') and not app.startswith('rest_framework')
            ],
        }
        return Response(info)


class SystemBackupView(views.APIView):
    """POST: Create database backup."""
    permission_classes = [IsAdmin]

    def post(self, request):
        import zipfile
        import json
        from io import BytesIO
        from datetime import datetime
        from django.core.management import call_command
        from django.conf import settings
        from django.apps import apps as django_apps

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'erp_backup_{timestamp}.zip'

        local_apps = [
            'users', 'inventory', 'sales', 'accounting',
            'hr', 'purchases', 'documents', 'projects',
            'notifications', 'auditlog',
        ]
        models_to_dump = []
        for app_label in local_apps:
            try:
                app_config = django_apps.get_app_config(app_label)
                for model in app_config.get_models():
                    models_to_dump.append(f'{app_label}.{model.__name__}')
            except LookupError:
                pass

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            out = BytesIO()
            call_command('dumpdata', *models_to_dump, '--indent=2', stdout=out)
            out.seek(0)
            zf.writestr(f'erp_backup_{timestamp}.json', out.read().decode('utf-8'))

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class DashboardStatsView(views.APIView):
    """GET: Dashboard statistics with date filtering."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Inventory stats
        from inventory.models import Product
        total_products = Product.objects.count()
        low_stock = Product.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0).count()
        out_of_stock = Product.objects.filter(quantity=0).count()

        # Sales stats
        from sales.models import SalesOrder
        sales_qs = SalesOrder.objects.all()
        if date_from: sales_qs = sales_qs.filter(order_date__gte=date_from)
        if date_to: sales_qs = sales_qs.filter(order_date__lte=date_to)

        total_orders = sales_qs.count()
        total_sales = sales_qs.aggregate(
            t=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        confirmed_orders = sales_qs.filter(status='confirmed').count()
        pending_orders = sales_qs.filter(status='pending').count()

        # Monthly sales for chart (last 12 months)
        monthly_sales = []
        for i in range(11, -1, -1):
            month_date = timezone.now() - timedelta(days=i*30)
            month_start = month_date.replace(day=1)
            month_label = month_start.strftime('%Y-%m')
            month_total = SalesOrder.objects.filter(
                order_date__year=month_start.year,
                order_date__month=month_start.month,
                status='confirmed'
            ).aggregate(
                t=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['t']
            monthly_sales.append({'month': month_label, 'total': float(month_total)})

        # Purchases stats
        from purchases.models import PurchaseOrder
        purchase_qs = PurchaseOrder.objects.all()
        if date_from: purchase_qs = purchase_qs.filter(order_date__gte=date_from)
        if date_to: purchase_qs = purchase_qs.filter(order_date__lte=date_to)
        total_purchases = purchase_qs.aggregate(
            t=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        # HR stats
        from hr.models import Employee
        total_employees = Employee.objects.filter(is_active=True).count()
        total_salary = Employee.objects.filter(is_active=True).aggregate(
            t=Coalesce(Sum('salary'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        # Projects stats
        from projects.models import Project
        active_projects = Project.objects.filter(status__in=['active']).count()
        total_projects = Project.objects.count()

        # Accounting stats
        from accounting.models import Account, JournalEntry, AccountType
        total_revenue = Account.objects.filter(account_type=AccountType.INCOME).aggregate(
            t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        total_expenses = Account.objects.filter(account_type=AccountType.EXPENSE).aggregate(
            t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        # Order status distribution
        status_dist = sales_qs.values('status').annotate(count=Count('id'))

        # Recent orders
        recent_orders = SalesOrder.objects.select_related('customer').order_by('-created_at')[:5]
        recent_data = []
        for o in recent_orders:
            recent_data.append({
                'id': o.id,
                'order_number': o.order_number,
                'customer': o.customer.name if o.customer else '',
                'total': float(o.total_amount),
                'status': o.status,
                'date': str(o.order_date) if o.order_date else '',
            })

        data = {
            'inventory': {
                'total_products': total_products,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
            },
            'sales': {
                'total_orders': total_orders,
                'total_sales': float(total_sales),
                'confirmed_orders': confirmed_orders,
                'pending_orders': pending_orders,
                'monthly_sales': monthly_sales,
                'status_distribution': list(status_dist),
                'recent_orders': recent_data,
            },
            'purchases': {
                'total_purchases': float(total_purchases),
            },
            'hr': {
                'total_employees': total_employees,
                'total_salary': float(total_salary),
            },
            'projects': {
                'total_projects': total_projects,
                'active_projects': active_projects,
            },
            'accounting': {
                'total_revenue': float(total_revenue),
                'total_expenses': float(total_expenses),
                'net_profit': float(total_revenue) - float(total_expenses),
            },
        }
        return Response(data)


class DashboardLiveStatsView(views.APIView):
    """GET: Lightweight live stats for dashboard auto-refresh."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        # Orders today
        from sales.models import SalesOrder
        orders_today = SalesOrder.objects.filter(order_date=today).count()
        pending_orders = SalesOrder.objects.filter(status='pending').count()

        # Revenue this month (confirmed orders this month)
        from django.db.models import Sum, DecimalField, Value
        from django.db.models.functions import Coalesce
        revenue_this_month = SalesOrder.objects.filter(
            order_date__year=today.year,
            order_date__month=today.month,
            status='confirmed',
        ).aggregate(
            t=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        # Low stock products
        from inventory.models import Product
        from django.db.models import F
        low_stock = Product.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0).count()

        # Recent notifications count (unread)
        from notifications.models import Notification
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

        # Active users count
        from django.contrib.auth import get_user_model
        User = get_user_model()
        active_users = User.objects.filter(is_active=True).count()

        # Recent activity (last 10 audit log entries)
        from auditlog.models import AuditLog
        recent_activity = []
        for log in AuditLog.objects.select_related('user').order_by('-created_at')[:10]:
            recent_activity.append({
                'id': log.id,
                'user': log.user.get_full_name() or log.user.username if log.user else 'System',
                'action': log.action,
                'model': log.model_name,
                'object_repr': log.object_repr or '',
                'created_at': str(log.created_at),
            })

        # Sparkline data: last 7 days orders
        sparkline_orders = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            count = SalesOrder.objects.filter(order_date=day).count()
            sparkline_orders.append({'day': str(day), 'count': count})

        return Response({
            'orders_today': orders_today,
            'pending_orders': pending_orders,
            'revenue_this_month': float(revenue_this_month),
            'low_stock': low_stock,
            'unread_notifications': unread_notifications,
            'active_users': active_users,
            'recent_activity': recent_activity,
            'sparkline_orders': sparkline_orders,
            'timestamp': timezone.now().isoformat(),
        })


# ====== PDF Report Views ======

class PDFReportView(views.APIView):
    """Generic PDF report generator for all modules."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, module):
        from core.reports import (
            generate_inventory_report, generate_sales_report,
            generate_purchases_report, generate_employees_report,
            generate_projects_report,
        )

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        search = request.query_params.get('search', '')
        filters = {'date_from': date_from, 'date_to': date_to, 'search': search}

        if module == 'inventory':
            from inventory.models import Product
            qs = Product.objects.all()
            if search:
                qs = qs.filter(name__icontains=search)
            data = [{
                'sku': p.sku, 'name': p.name,
                'category_name': p.category.name if p.category else '',
                'selling_price': p.selling_price,
                'stock_quantity': p.stock_quantity,
                'total_value': float(p.selling_price * p.stock_quantity),
            } for p in qs]
            pdf = generate_inventory_report(data, filters)
            filename = 'inventory_report.pdf'

        elif module == 'sales':
            from sales.models import SalesOrder
            qs = SalesOrder.objects.select_related('customer')
            if date_from: qs = qs.filter(order_date__gte=date_from)
            if date_to: qs = qs.filter(order_date__lte=date_to)
            data = [{
                'order_number': o.order_number,
                'customer_name': o.customer.name if o.customer else '',
                'order_date': str(o.order_date) if o.order_date else '',
                'status': o.status,
                'total_amount': float(o.total_amount),
            } for o in qs]
            pdf = generate_sales_report(data, filters)
            filename = 'sales_report.pdf'

        elif module == 'purchases':
            from purchases.models import PurchaseOrder
            qs = PurchaseOrder.objects.select_related('supplier')
            if date_from: qs = qs.filter(order_date__gte=date_from)
            if date_to: qs = qs.filter(order_date__lte=date_to)
            data = [{
                'order_number': o.order_number,
                'supplier_name': o.supplier.name if o.supplier else '',
                'order_date': str(o.order_date) if o.order_date else '',
                'status': o.status,
                'total_amount': float(o.total_amount),
            } for o in qs]
            pdf = generate_purchases_report(data, filters)
            filename = 'purchases_report.pdf'

        elif module == 'employees':
            from hr.models import Employee
            qs = Employee.objects.select_related('department')
            data = [{
                'employee_number': e.employee_number,
                'first_name': e.first_name,
                'last_name': e.last_name,
                'department_name': e.department.name if e.department else '',
                'position': e.position or '',
                'salary': float(e.salary),
                'is_active': e.is_active,
            } for e in qs]
            pdf = generate_employees_report(data, filters)
            filename = 'employees_report.pdf'

        elif module == 'projects':
            from projects.models import Project
            qs = Project.objects.select_related('customer')
            data = [{
                'name': p.name,
                'customer_name': p.customer.name if p.customer else '',
                'status': p.status,
                'budget': float(p.budget or 0),
                'spent': float(p.spent or 0),
            } for p in qs]
            pdf = generate_projects_report(data, filters)
            filename = 'projects_report.pdf'

        else:
            return Response({'error': 'وحدة غير معروفة'}, status=400)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class CashFlowPDFView(views.APIView):
    """GET: Generate cash flow statement PDF."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.reports import generate_cash_flow_statement
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        pdf = generate_cash_flow_statement(date_from, date_to)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="cash_flow_statement.pdf"'
        return response


class EnhancedIncomeStatementPDFView(views.APIView):
    """GET: Enhanced income statement PDF."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.reports import generate_enhanced_income_statement
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        pdf = generate_enhanced_income_statement(date_from, date_to)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="income_statement.pdf"'
        return response


class EnhancedBalanceSheetPDFView(views.APIView):
    """GET: Enhanced balance sheet PDF."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.reports import generate_enhanced_balance_sheet
        date_to = request.query_params.get('date_to')
        pdf = generate_enhanced_balance_sheet(date_to)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="balance_sheet.pdf"'
        return response


class CashFlowAPIView(views.APIView):
    """GET: Cash flow statement data (JSON)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from accounting.models import Account, JournalEntry, AccountType
        from django.db.models import Sum, DecimalField, Value
        from django.db.models.functions import Coalesce

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        entries = JournalEntry.objects.filter(is_posted=True)
        if date_from: entries = entries.filter(entry_date__gte=date_from)
        if date_to: entries = entries.filter(entry_date__lte=date_to)

        def calc_balance(account, txn_type):
            return account.transactions.filter(
                journal_entry__in=entries, transaction_type=txn_type
            ).aggregate(
                t=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['t']

        # Operating
        operating_in = 0
        for acc in Account.objects.filter(account_type=AccountType.INCOME, is_active=True):
            bal = calc_balance(acc, 'credit') - calc_balance(acc, 'debit')
            if bal > 0: operating_in += bal

        operating_out = 0
        for acc in Account.objects.filter(account_type=AccountType.EXPENSE, is_active=True):
            bal = calc_balance(acc, 'debit') - calc_balance(acc, 'credit')
            if bal > 0: operating_out += bal

        # Investing
        investing = 0
        for acc in Account.objects.filter(account_type=AccountType.ASSET, is_active=True):
            investing += calc_balance(acc, 'debit') - calc_balance(acc, 'credit')

        # Financing
        financing = 0
        for acc in Account.objects.filter(account_type__in=[AccountType.LIABILITY, AccountType.EQUITY], is_active=True):
            financing += calc_balance(acc, 'credit') - calc_balance(acc, 'debit')

        return Response({
            'operating_in': float(operating_in),
            'operating_out': float(operating_out),
            'net_operating': float(operating_in - operating_out),
            'investing': float(investing),
            'financing': float(financing),
            'net_cash_flow': float((operating_in - operating_out) + investing + financing),
        })


# ====== Advanced Analytics Views ======

class SalesAnalyticsView(views.APIView):
    """GET /api/reports/sales-analytics/ - Monthly sales, top products, customer categories."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        from sales.models import SalesOrder, SalesOrderItem
        from inventory.models import Product
        from django.db.models import Count

        # Monthly sales comparison (this year vs last year)
        now = timezone.now()
        monthly_comparison = []
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=i * 30)
            month_start = month_date.replace(day=1)
            month_label = month_start.strftime('%Y-%m')

            this_year = SalesOrder.objects.filter(
                order_date__year=month_start.year,
                order_date__month=month_start.month,
                status='confirmed',
            ).aggregate(t=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2)))['t']

            last_year = SalesOrder.objects.filter(
                order_date__year=month_start.year - 1,
                order_date__month=month_start.month,
                status='confirmed',
            ).aggregate(t=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2)))['t']

            monthly_comparison.append({
                'month': month_label,
                'thisYear': float(this_year),
                'lastYear': float(last_year),
            })

        # Top products by sales volume
        top_products = SalesOrderItem.objects.filter(
            order__status='confirmed'
        ).values(
            product_name=F('product__name'),
        ).annotate(
            volume=Coalesce(Sum('quantity'), Value(0)),
            revenue=Coalesce(Sum(F('quantity') * F('unit_price')), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2)),
        ).order_by('-volume')[:10]

        top_products_data = [{'name': p['product_name'] or '', 'volume': int(p['volume']), 'revenue': float(p['revenue'])} for p in top_products]

        # Customer categories distribution
        customer_dist = SalesOrder.objects.filter(status='confirmed').values(
            'customer__customer_type'
        ).annotate(count=Count('id')).order_by('-count')[:5]

        customer_categories = [
            {'name': str(c['customer__customer_type'] or 'عادي'), 'value': c['count']}
            for c in customer_dist
        ]

        return Response({
            'monthly_comparison': monthly_comparison,
            'top_products': top_products_data,
            'customer_categories': customer_categories,
        })


class InventoryAnalyticsView(views.APIView):
    """GET /api/reports/inventory-analytics/ - Stock levels, low stock, distribution."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from inventory.models import Product

        # Low stock items
        low_stock = Product.objects.filter(
            quantity__lte=F('reorder_level'),
            quantity__gt=0,
            is_deleted=False,
        ).order_by('quantity')[:20]

        low_stock_data = [{
            'name': p.name,
            'sku': p.sku,
            'current': int(p.quantity),
            'reorder': int(p.reorder_level),
            'category': p.category.name if p.category else '',
        } for p in low_stock]

        # Out of stock
        out_of_stock = Product.objects.filter(quantity=0, is_deleted=False).count()

        # Stock distribution by category
        from django.db.models import Sum
        cat_dist = Product.objects.filter(is_deleted=False).values(
            'category__name'
        ).annotate(
            total_qty=Coalesce(Sum('quantity'), Value(0)),
        ).order_by('-total_qty')[:10]

        stock_distribution = [
            {'name': str(c['category__name'] or 'غير مصنف'), 'value': int(c['total_qty'])}
            for c in cat_dist
        ]

        # Total inventory value
        total_value = Product.objects.filter(is_deleted=False).aggregate(
            t=Coalesce(Sum(F('selling_price') * F('quantity')), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        return Response({
            'low_stock_items': low_stock_data,
            'out_of_stock_count': out_of_stock,
            'stock_distribution': stock_distribution,
            'total_inventory_value': float(total_value),
            'total_products': Product.objects.filter(is_deleted=False).count(),
        })


class FinancialAnalyticsView(views.APIView):
    """GET /api/reports/financial-analytics/ - Income/expenses, margins, KPIs."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from accounting.models import Account, AccountType
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Total revenue and expenses
        total_revenue = Account.objects.filter(account_type=AccountType.INCOME, is_active=True).aggregate(
            t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        total_expenses = Account.objects.filter(account_type=AccountType.EXPENSE, is_active=True).aggregate(
            t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        total_assets = Account.objects.filter(account_type=AccountType.ASSET, is_active=True).aggregate(
            t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']
        total_liabilities = Account.objects.filter(account_type=AccountType.LIABILITY, is_active=True).aggregate(
            t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['t']

        net_profit = float(total_revenue) - float(total_expenses)
        gross_margin = (net_profit / float(total_revenue) * 100) if float(total_revenue) > 0 else 0
        current_ratio = float(total_assets) / float(total_liabilities) if float(total_liabilities) > 0 else 0

        # Monthly income/expenses for chart
        now = timezone.now()
        income_expenses = []
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=i * 30)
            month_start = month_date.replace(day=1)
            month_label = month_start.strftime('%Y-%m')

            month_income = Account.objects.filter(
                account_type=AccountType.INCOME, is_active=True,
            ).aggregate(t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2)))['t']

            month_exp = Account.objects.filter(
                account_type=AccountType.EXPENSE, is_active=True,
            ).aggregate(t=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2)))['t']

            income_expenses.append({
                'month': month_label,
                'income': float(month_income) / (12 - i * 0.5),  # Rough approximation
                'expenses': float(month_exp) / (12 - i * 0.5),
            })

        # Expense category breakdown
        expense_accounts = Account.objects.filter(
            account_type=AccountType.EXPENSE, is_active=True
        ).order_by('-current_balance')[:10]

        expense_categories = [{
            'name': acc.name,
            'amount': float(acc.current_balance or 0),
        } for acc in expense_accounts]

        return Response({
            'total_revenue': float(total_revenue),
            'total_expenses': float(total_expenses),
            'net_profit': net_profit,
            'gross_margin': round(gross_margin, 1),
            'current_ratio': round(current_ratio, 2),
            'income_expenses': income_expenses,
            'expense_categories': expense_categories,
        })


class HRAnalyticsView(views.APIView):
    """GET /api/reports/hr-analytics/ - Attendance, employee distribution."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from hr.models import Employee, Attendance, Department
        from django.db.models import Avg, Count, Q

        # Attendance by department
        departments = Department.objects.filter(is_active=True)
        attendance_by_dept = []
        for dept in departments:
            emp_count = Employee.objects.filter(department=dept, is_active=True).count()
            if emp_count == 0:
                continue

            # Average attendance: count present records / (employees * working days approximation)
            present_days = Attendance.objects.filter(
                employee__department=dept,
                check_in__isnull=False,
            ).count()

            # Simple attendance rate: employees who checked in today vs total
            today = timezone.now().date()
            today_attendance = Attendance.objects.filter(
                employee__department=dept,
                check_in__date=today,
                check_in__isnull=False,
            ).count()

            rate = min(round((today_attendance / emp_count) * 100, 1), 100.0)
            attendance_by_dept.append({
                'department': dept.name,
                'rate': rate,
                'employee_count': emp_count,
            })

        # Employee distribution
        emp_dist = Employee.objects.filter(is_active=True).values(
            'department__name'
        ).annotate(count=Count('id')).order_by('-count')

        employee_distribution = [
            {'name': str(e['department__name'] or 'غير محدد'), 'value': e['count']}
            for e in emp_dist
        ]

        total_employees = Employee.objects.filter(is_active=True).count()

        return Response({
            'attendance_by_dept': attendance_by_dept,
            'employee_distribution': employee_distribution,
            'total_employees': total_employees,
        })
