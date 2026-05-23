"""
Smart Query Engine for RIADAH ERP chatbot (v2).
Translates natural language queries into SQL queries and returns formatted results.
Updated to match the current 23-app structure after removing contracts, assets,
insurance, budget, and internalaudit modules.
"""

import logging
from datetime import datetime, timedelta

from django.db import connection

logger = logging.getLogger(__name__)


class SmartQueryEngine:
    """
    Natural Language to SQL engine for ERP data queries.

    Maps classified intents to pre-defined SQL queries that fetch
    data from the relevant ERP modules. Results are formatted in Arabic.

    Supported domains:
        - Sales: فواتير البيع، المنتجات الأكثر مبيعاً، ملخص المبيعات
        - HR: الموظفين، الحضور، الإجازات
        - Financial: الأرباح، المصروفات، الإيرادات، الميزانية العمومية
        - Purchases: المشتريات، الموردين، أوامر الشراء
        - CRM: العملاء، الفرص، خط أنبوب المبيعات
        - Projects: المشاريع، المخاطر، التقدم
        - POS: نقاط البيع، المبيعات المباشرة
        - Payroll: الرواتب، كشف المرتبات
    """

    def process_query(self, user, query_text, intent, company_context=None):
        """Process a natural language query and return a formatted Arabic response."""
        try:
            if intent == 'sales_query':
                return self._handle_sales_query(query_text)
            elif intent == 'hr_query':
                return self._handle_hr_query(query_text)
            elif intent == 'financial_query':
                return self._handle_financial_query(query_text)
            elif intent == 'purchases_query':
                return self._handle_purchases_query(query_text)
            elif intent == 'crm_query':
                return self._handle_crm_query(query_text)
            elif intent == 'projects_query':
                return self._handle_projects_query(query_text)
            elif intent == 'pos_query':
                return self._handle_pos_query(query_text)
            elif intent == 'payroll_query':
                return self._handle_payroll_query(query_text)
            else:
                return 'عذراً، لم أتمكن من معالجة هذا الاستعلام. يرجى التواصل مع المسؤول.'

        except Exception as exc:
            logger.error(
                'SmartQueryEngine error for user %s, intent %s: %s',
                user.username if user else 'anonymous',
                intent,
                str(exc),
                exc_info=True,
            )
            return 'عذراً، حدث خطأ أثناء تنفيذ الاستعلام. يرجى المحاولة لاحقاً.'

    # ── Sales Queries ──────────────────────────────────────────────────

    def _handle_sales_query(self, query_text):
        """Handle sales-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['اليوم', 'يوم']):
            return self._query_sales_today()
        elif any(kw in query_text_lower for kw in ['الشهر', 'شهري']):
            return self._query_sales_this_month()
        elif any(kw in query_text_lower for kw in ['أفضل', 'أكثر', 'المنتجات']):
            return self._query_top_products()
        elif any(kw in query_text_lower for kw in ['فواتير', 'عدد الفواتير']):
            return self._query_invoice_count()
        elif any(kw in query_text_lower for kw in ['عميل', 'عملاء']):
            return self._query_customers_count()
        else:
            return self._query_sales_summary()

    def _query_sales_today(self):
        """Get total sales for today."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM sales_salesorder
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            row = cursor.fetchone()
            count, total = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'📊 **ملخص مبيعات اليوم:**\n'
            f'• عدد أوامر البيع: {count}\n'
            f'• إجمالي المبيعات: {total:,.2f} ريال'
        )

    def _query_sales_this_month(self):
        """Get total sales for the current month."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM sales_salesorder
                WHERE TO_CHAR(created_at, 'YYYY-MM') = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
            """)
            row = cursor.fetchone()
            count, total = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'📊 **ملخص مبيعات الشهر الحالي:**\n'
            f'• عدد أوامر البيع: {count}\n'
            f'• إجمالي المبيعات: {total:,.2f} ريال'
        )

    def _query_top_products(self):
        """Get the top 5 best-selling products."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT product_name, COALESCE(SUM(quantity), 0) as qty
                FROM sales_salesorderitem
                GROUP BY product_name
                ORDER BY qty DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()

        if not rows or (len(rows) == 1 and rows[0][1] == 0):
            return 'لا تتوفر بيانات كافية عن المنتجات الأكثر مبيعاً حالياً.'

        lines = ['🏆 **أفضل 5 منتجات مبيعاً:**']
        for i, (name, qty) in enumerate(rows, 1):
            lines.append(f'{i}. {name} — {int(qty)} وحدة')

        return '\n'.join(lines)

    def _query_invoice_count(self):
        """Get total number of invoices."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sales_salesorder")
            row = cursor.fetchone()
            count = row[0] if row else 0

        return f'📄 إجمالي عدد أوامر البيع في النظام: **{count}** أمر.'

    def _query_customers_count(self):
        """Get total number of customers."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sales_customer")
            row = cursor.fetchone()
            count = row[0] if row else 0

        return f'👥 إجمالي عدد العملاء في النظام: **{count}** عميل.'

    def _query_sales_summary(self):
        """Get general sales summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_amount,
                    COALESCE(AVG(total_amount), 0) as avg_amount
                FROM sales_salesorder
            """)
            row = cursor.fetchone()
            if row:
                total, amount, avg = row[0], float(row[1]), float(row[2])
            else:
                total, amount, avg = 0, 0, 0

        return (
            f'📊 **ملخص المبيعات العام:**\n'
            f'• إجمالي الأوامر: {total}\n'
            f'• إجمالي المبيعات: {amount:,.2f} ريال\n'
            f'• متوسط قيمة الأمر: {avg:,.2f} ريال'
        )

    # ── HR Queries ─────────────────────────────────────────────────────

    def _handle_hr_query(self, query_text):
        """Handle HR-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['عدد', 'كم موظف', 'موظفين']):
            return self._query_employee_count()
        elif any(kw in query_text_lower for kw in ['إجازة', 'إجازات', 'غياب', 'غيابات']):
            return self._query_leave_summary()
        elif any(kw in query_text_lower for kw in ['حضور', 'تأخير', 'حاضر']):
            return self._query_attendance_summary()
        elif any(kw in query_text_lower for kw in ['قسم', 'أقسام', 'هيكل']):
            return self._query_departments_summary()
        else:
            return self._query_hr_summary()

    def _query_employee_count(self):
        """Get total number of employees."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM hr_employee
                WHERE is_active = true
            """)
            row = cursor.fetchone()
            count = row[0] if row else 0

        return f'👥 إجمالي عدد الموظفين النشطين في النظام: **{count}** موظف.'

    def _query_leave_summary(self):
        """Get leave/absence summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE approval_status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE approval_status = 'approved') as approved,
                    COUNT(*) FILTER (WHERE approval_status = 'rejected') as rejected
                FROM hr_leaverequest
            """)
            row = cursor.fetchone()
            if row:
                pending, approved, rejected = row
            else:
                pending = approved = rejected = 0

        return (
            f'📋 **ملخص الإجازات:**\n'
            f'• قيد الانتظار: {pending}\n'
            f'• موافق عليها: {approved}\n'
            f'• مرفوضة: {rejected}'
        )

    def _query_attendance_summary(self):
        """Get attendance summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'present') as present,
                    COUNT(*) FILTER (WHERE status = 'absent') as absent,
                    COUNT(*) FILTER (WHERE status = 'late') as late
                FROM hr_attendance
                WHERE DATE(date) = CURRENT_DATE
            """)
            row = cursor.fetchone()
            if row:
                present, absent, late = row
            else:
                present = absent = late = 0

        today = datetime.now().strftime('%Y-%m-%d')
        return (
            f'📋 **ملخص الحضور لليوم ({today}):**\n'
            f'• حاضر: {present}\n'
            f'• غائب: {absent}\n'
            f'• متأخر: {late}'
        )

    def _query_departments_summary(self):
        """Get departments summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT d.name, COUNT(e.id) as emp_count
                FROM hr_department d
                LEFT JOIN hr_employee e ON e.department_id = d.id AND e.is_active = true
                GROUP BY d.name
                ORDER BY emp_count DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر بيانات عن الأقسام حالياً.'

        lines = ['🏢 **الأقسام وعدد الموظفين:**']
        for name, count in rows:
            lines.append(f'• {name}: {count} موظف')

        return '\n'.join(lines)

    def _query_hr_summary(self):
        """Get general HR summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM hr_employee WHERE is_active = true
            """)
            row = cursor.fetchone()
            total = row[0] if row else 0

        return (
            f'👥 **ملخص الموارد البشرية:**\n'
            f'• إجمالي الموظفين النشطين: {total}\n'
            f'• يمكنك الاطلاع على التفاصيل من: الأقسام، الحضور، الإجازات، الرواتب، تقييم الأداء، التوظيف، التدريب.'
        )

    # ── Financial Queries ──────────────────────────────────────────────

    def _handle_financial_query(self, query_text):
        """Handle financial-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['ربح', 'أرباح', 'صافي']):
            return self._query_profit_summary()
        elif any(kw in query_text_lower for kw in ['مصروف', 'مصاريف', 'مصروفات', 'تكلفة', 'تكاليف']):
            return self._query_expenses_summary()
        elif any(kw in query_text_lower for kw in ['إيراد', 'إيرادات', 'دخل']):
            return self._query_revenue_summary()
        elif any(kw in query_text_lower for kw in ['ميزانية', 'ميزان', 'الميزانية العمومية']):
            return self._query_balance_sheet_summary()
        else:
            return self._query_financial_summary()

    def _query_profit_summary(self):
        """Get profit summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN a.account_type = 'income' THEN t.amount ELSE 0 END), 0) as income,
                    COALESCE(SUM(CASE WHEN a.account_type = 'expense' THEN t.amount ELSE 0 END), 0) as expenses
                FROM accounting_transaction t
                JOIN accounting_account a ON t.account_id = a.id
                JOIN accounting_journalentry j ON t.journal_entry_id = j.id
                WHERE j.is_posted = true
            """)
            row = cursor.fetchone()
            if row:
                income, expenses = float(row[0]), float(row[1])
                profit = income - expenses
            else:
                income = expenses = profit = 0

        return (
            f'💰 **ملخص الأرباح:**\n'
            f'• إجمالي الإيرادات: {income:,.2f} ريال\n'
            f'• إجمالي المصروفات: {expenses:,.2f} ريال\n'
            f'• صافي الربح: {profit:,.2f} ريال'
        )

    def _query_expenses_summary(self):
        """Get expenses summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    a.name,
                    COALESCE(SUM(t.amount), 0) as total
                FROM accounting_transaction t
                JOIN accounting_account a ON t.account_id = a.id
                JOIN accounting_journalentry j ON t.journal_entry_id = j.id
                WHERE a.account_type = 'expense' AND j.is_posted = true
                GROUP BY a.name
                ORDER BY total DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر بيانات مصروفات حالياً.'

        lines = ['💸 **أعلى 5 فئات مصروفات:**']
        for name, total in rows:
            lines.append(f'• {name}: {float(total):,.2f} ريال')

        return '\n'.join(lines)

    def _query_revenue_summary(self):
        """Get revenue summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM sales_salesorder
                WHERE TO_CHAR(created_at, 'YYYY-MM') = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
            """)
            row = cursor.fetchone()
            revenue = float(row[0]) if row else 0

        return (
            f'📈 **ملخص الإيرادات (الشهر الحالي):**\n'
            f'• إجمالي الإيرادات من المبيعات: {revenue:,.2f} ريال\n'
            f'لمزيد من التفاصيل، راجع وحدة المحاسبة في النظام.'
        )

    def _query_balance_sheet_summary(self):
        """Get balance sheet summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    a.account_type,
                    COALESCE(SUM(t.amount), 0) as total
                FROM accounting_transaction t
                JOIN accounting_account a ON t.account_id = a.id
                JOIN accounting_journalentry j ON t.journal_entry_id = j.id
                WHERE j.is_posted = true
                GROUP BY a.account_type
                ORDER BY a.account_type
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر بيانات مالية حالياً.'

        type_labels = {
            'asset': 'الأصول',
            'liability': 'الخصوم',
            'equity': 'حقوق الملكية',
            'income': 'الإيرادات',
            'expense': 'المصروفات',
        }

        lines = ['📊 **ملخص الميزانية العمومية:**']
        for atype, total in rows:
            label = type_labels.get(atype, atype)
            lines.append(f'• {label}: {float(total):,.2f} ريال')

        return '\n'.join(lines)

    def _query_financial_summary(self):
        """Get general financial summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) FROM sales_salesorder
            """)
            row = cursor.fetchone()
            total_sales = float(row[0]) if row else 0

        return (
            f'💰 **ملخص مالي عام:**\n'
            f'• إجمالي المبيعات التراكمية: {total_sales:,.2f} ريال\n'
            f'للحصول على تقارير مالية مفصّلة، راجع وحدة المحاسبة.\n'
            f'التقارير المتاحة: قائمة الدخل، الميزانية العمومية، التدفق النقدي، الفوترة، المدفوعات.'
        )

    # ── Purchases Queries ──────────────────────────────────────────────

    def _handle_purchases_query(self, query_text):
        """Handle purchases-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['مورد', 'موردين', 'الموردين']):
            return self._query_suppliers_summary()
        elif any(kw in query_text_lower for kw in ['معلقة', 'معلق', 'قيد الانتظار']):
            return self._query_pending_purchase_orders()
        elif any(kw in query_text_lower for kw in ['مستلمة', 'مستلم', 'تم الاستلام']):
            return self._query_received_purchase_orders()
        else:
            return self._query_purchases_summary()

    def _query_purchases_summary(self):
        """Get general purchases summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_amount), 0) as total_amount
                FROM purchases_purchaseorder
            """)
            row = cursor.fetchone()
            if row:
                total, amount = row[0], float(row[1])
            else:
                total, amount = 0, 0

        return (
            f'🛒 **ملخص المشتريات:**\n'
            f'• إجمالي أوامر الشراء: {total}\n'
            f'• إجمالي قيمة المشتريات: {amount:,.2f} ريال\n'
            f'• راجع وحدة المشتريات والاستيراد والتصدير لمزيد من التفاصيل.'
        )

    def _query_suppliers_summary(self):
        """Get suppliers summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM purchases_supplier WHERE is_active = true
            """)
            row = cursor.fetchone()
            count = row[0] if row else 0

        return (
            f'🏭 **ملخص الموردين:**\n'
            f'• إجمالي الموردين النشطين: **{count}** مورد\n'
            f'• يمكنك الاطلاع على التقييمات في وحدة التحليلات الذكية.'
        )

    def _query_pending_purchase_orders(self):
        """Get pending purchase orders."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
                FROM purchases_purchaseorder
                WHERE status = 'pending'
            """)
            row = cursor.fetchone()
            count, amount = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'⏳ **أوامر الشراء المعلقة:**\n'
            f'• عدد الأوامر: {count}\n'
            f'• إجمالي القيمة: {amount:,.2f} ريال'
        )

    def _query_received_purchase_orders(self):
        """Get received purchase orders."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
                FROM purchases_purchaseorder
                WHERE status IN ('received', 'partial')
            """)
            row = cursor.fetchone()
            count, amount = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'✅ **أوامر الشراء المستلمة:**\n'
            f'• عدد الأوامر: {count}\n'
            f'• إجمالي القيمة: {amount:,.2f} ريال'
        )

    # ── CRM Queries ───────────────────────────────────────────────────

    def _handle_crm_query(self, query_text):
        """Handle CRM-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['فرص', 'فرصة', 'خط أنبوب']):
            return self._query_crm_pipeline()
        elif any(kw in query_text_lower for kw in ['تذك', 'دعم', 'شكوى', 'مشكلة']):
            return self._query_crm_tickets()
        elif any(kw in query_text_lower for kw in ['عميل', 'عملاء', 'محتمل', 'segment']):
            return self._query_crm_leads()
        else:
            return self._query_crm_summary()

    def _query_crm_pipeline(self):
        """Get CRM sales pipeline summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COALESCE(stage, 'غير محدد') as stage,
                    COUNT(*) as count,
                    COALESCE(SUM(estimated_value), 0) as value
                FROM crm_lead
                WHERE is_active = true
                GROUP BY stage
                ORDER BY value DESC
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر بيانات عن خط أنبوب المبيعات حالياً.'

        stage_labels = {
            'new': 'جديد',
            'contacted': 'تم التواصل',
            'qualified': 'مؤهل',
            'proposal': 'عرض سعر',
            'negotiation': 'تفاوض',
            'won': 'مكتسب',
            'lost': 'مفقود',
        }

        lines = ['🎯 **خط أنبوب المبيعات:**']
        total_value = 0
        for stage, count, value in rows:
            label = stage_labels.get(stage, stage)
            total_value += float(value)
            lines.append(f'• {label}: {count} فرصة — {float(value):,.2f} ريال')

        lines.append(f'\n💰 **إجمالي قيمة الفرص: {total_value:,.2f} ريال**')
        return '\n'.join(lines)

    def _query_crm_tickets(self):
        """Get CRM support tickets summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COALESCE(status, 'open') as status,
                    COUNT(*) as count
                FROM crm_ticket
                GROUP BY status
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر تذاكر دعم حالياً.'

        status_labels = {
            'open': 'مفتوحة',
            'in_progress': 'قيد التنفيذ',
            'resolved': 'محلولة',
            'closed': 'مغلقة',
        }

        lines = ['🎫 **تذاكر الدعم:**']
        for status, count in rows:
            label = status_labels.get(status, status)
            lines.append(f'• {label}: {count} تذكرة')

        return '\n'.join(lines)

    def _query_crm_leads(self):
        """Get CRM leads summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_active = true) as active,
                    COALESCE(SUM(estimated_value), 0) as total_value
                FROM crm_lead
            """)
            row = cursor.fetchone()
            if row:
                total, active, value = row
            else:
                total = active = 0
                value = 0

        return (
            f'👤 **ملخص العملاء المحتملين (CRM):**\n'
            f'• إجمالي العملاء المحتملين: {total}\n'
            f'• النشطين: {active}\n'
            f'• إجمالي القيمة المقدرة: {float(value):,.2f} ريال'
        )

    def _query_crm_summary(self):
        """Get general CRM summary."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM crm_lead WHERE is_active = true")
            row = cursor.fetchone()
            leads = row[0] if row else 0

        return (
            f'🤝 **ملخص إدارة العلاقات (CRM):**\n'
            f'• العملاء المحتملين النشطين: {leads}\n'
            f'• الوحدات المتاحة: الفرص، التذاكر، عروض الأسعار، خط الأنابيب، تحليلات العملاء.'
        )

    # ── Projects Queries ───────────────────────────────────────────────

    def _handle_projects_query(self, query_text):
        """Handle projects-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['نشط', 'نشطة', 'جاري', 'قيد التنفيذ']):
            return self._query_active_projects()
        elif any(kw in query_text_lower for kw in ['مخاطر', 'خطر']):
            return self._query_project_risks()
        elif any(kw in query_text_lower for kw in ['ميزانية', 'تكلفة', 'تكلفة المشروع']):
            return self._query_project_budgets()
        else:
            return self._query_projects_summary()

    def _query_active_projects(self):
        """Get active projects."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'on_hold') as on_hold
                FROM projects_project
            """)
            row = cursor.fetchone()
            if row:
                active, completed, on_hold = row
            else:
                active = completed = on_hold = 0

        return (
            f'📋 **حالة المشاريع:**\n'
            f'• نشطة: {active}\n'
            f'• مكتملة: {completed}\n'
            f'• متوقفة: {on_hold}'
        )

    def _query_project_risks(self):
        """Get project risks summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COALESCE(severity, 'medium') as severity,
                    COUNT(*) as count
                FROM projects_risk
                GROUP BY severity
                ORDER BY count DESC
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر بيانات عن مخاطر المشاريع حالياً.'

        severity_labels = {'low': 'منخفض', 'medium': 'متوسط', 'high': 'عالي', 'critical': 'حرج'}
        lines = ['⚠️ **مخاطر المشاريع:**']
        for severity, count in rows:
            label = severity_labels.get(severity, severity)
            lines.append(f'• {label}: {count} خطر')

        return '\n'.join(lines)

    def _query_project_budgets(self):
        """Get project budget overview."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COALESCE(SUM(budget), 0) as total_budget,
                    COALESCE(SUM(spent), 0) as total_spent
                FROM projects_project
            """)
            row = cursor.fetchone()
            if row:
                total, budget, spent = row[0], float(row[1]), float(row[2])
            else:
                total = 0
                budget = spent = 0

        remaining = budget - spent
        return (
            f'💵 **ملخص ميزانيات المشاريع:**\n'
            f'• عدد المشاريع: {total}\n'
            f'• إجمالي الميزانيات: {budget:,.2f} ريال\n'
            f'• إجمالي المصروف: {spent:,.2f} ريال\n'
            f'• المتبقي: {remaining:,.2f} ريال'
        )

    def _query_projects_summary(self):
        """Get general projects summary."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM projects_project")
            row = cursor.fetchone()
            total = row[0] if row else 0

        return (
            f'📁 **ملخص المشاريع:**\n'
            f'• إجمالي المشاريع: {total}\n'
            f'• يمكنك الاطلاع على: المخاطر، الميزانيات، الوثائق، المناقصات.'
        )

    # ── POS Queries ───────────────────────────────────────────────────

    def _handle_pos_query(self, query_text):
        """Handle POS-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['اليوم', 'يوم']):
            return self._query_pos_today()
        elif any(kw in query_text_lower for kw in ['منتج', 'أكثر طلب']):
            return self._query_pos_top_products()
        else:
            return self._query_pos_summary()

    def _query_pos_today(self):
        """Get POS sales for today."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as count,
                    COALESCE(SUM(total_amount), 0) as total
                FROM pos_sale
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            row = cursor.fetchone()
            count, total = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'🏪 **مبيعات نقاط البيع اليوم:**\n'
            f'• عدد الفواتير: {count}\n'
            f'• إجمالي المبيعات: {total:,.2f} ريال'
        )

    def _query_pos_top_products(self):
        """Get POS top selling products."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    product_name,
                    COALESCE(SUM(quantity), 0) as qty
                FROM pos_saleitem
                GROUP BY product_name
                ORDER BY qty DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر بيانات عن المنتجات الأكثر طلباً في نقاط البيع.'

        lines = ['🛍️ **أفضل 5 منتجات في نقاط البيع:**']
        for i, (name, qty) in enumerate(rows, 1):
            lines.append(f'{i}. {name} — {int(qty)} وحدة')

        return '\n'.join(lines)

    def _query_pos_summary(self):
        """Get general POS summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as count,
                    COALESCE(SUM(total_amount), 0) as total
                FROM pos_sale
            """)
            row = cursor.fetchone()
            count, total = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'🏪 **ملخص نقاط البيع:**\n'
            f'• إجمالي الفواتير: {count}\n'
            f'• إجمالي المبيعات: {total:,.2f} ريال'
        )

    # ── Payroll Queries ───────────────────────────────────────────────

    def _handle_payroll_query(self, query_text):
        """Handle payroll-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['شهر', 'الشهر']):
            return self._query_payroll_current_month()
        else:
            return self._query_payroll_summary()

    def _query_payroll_current_month(self):
        """Get payroll for current month."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as employees,
                    COALESCE(SUM(net_pay), 0) as total_net,
                    COALESCE(SUM(gross_pay), 0) as total_gross,
                    COALESCE(SUM(total_deductions), 0) as total_deductions
                FROM payroll_payslip
                WHERE TO_CHAR(pay_period_start, 'YYYY-MM') = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
            """)
            row = cursor.fetchone()
            if row:
                employees, net, gross, deductions = row
                employees = employees or 0
                net = float(net) if net else 0
                gross = float(gross) if gross else 0
                deductions = float(deductions) if deductions else 0
            else:
                employees = net = gross = deductions = 0

        return (
            f'💰 **كشف رواتب الشهر الحالي:**\n'
            f'• عدد الموظفين: {employees}\n'
            f'• إجمالي الرواتب الأساسية: {gross:,.2f} ريال\n'
            f'• إجمالي الاستقطاعات: {deductions:,.2f} ريال\n'
            f'• صافي الرواتب: {net:,.2f} ريال'
        )

    def _query_payroll_summary(self):
        """Get general payroll summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT employee_id) as employees,
                    COALESCE(SUM(net_pay), 0) as total_net
                FROM payroll_payslip
            """)
            row = cursor.fetchone()
            if row:
                employees, net = (row[0] or 0, float(row[1]) if row[1] else 0)
            else:
                employees = net = 0

        return (
            f'💰 **ملخص الرواتب:**\n'
            f'• إجمالي الموظفين: {employees}\n'
            f'• إجمالي صافي الرواتب المدفوعة: {net:,.2f} ريال\n'
            f'• راجع وحدة الرواتب للحصول على كشوف تفصيلية.'
        )
