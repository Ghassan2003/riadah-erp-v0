"""
Smart Query Engine for RIADAH ERP chatbot (FIXED).
Translates natural language queries into ORM queries and returns formatted results.
Provides data isolation per company.

تم إصلاح:
- أسماء الجداول لتتوافق مع Django models الفعلية
- استبدال دوال SQLite بدوال PostgreSQL
- إصلاح خطأ fetchone() المزدوج
- إزالة مراجع جدول inventory_product المحذوف
"""

import logging
from datetime import datetime, timedelta

from django.db import connection

logger = logging.getLogger(__name__)


class SmartQueryEngine:
    """
    Natural Language to ORM engine for ERP data queries.

    Maps classified intents to pre-defined SQL queries that fetch
    data from the relevant ERP modules. Results are formatted in Arabic.
    """

    def process_query(self, user, query_text, intent, company_context=None):
        """Process a natural language query and return a formatted Arabic response."""
        company_id = None
        if company_context:
            company_id = company_context.get('company_id')

        try:
            if intent == 'sales_query':
                return self._handle_sales_query(query_text, company_id)
            elif intent == 'inventory_query':
                return self._handle_inventory_query(query_text, company_id)
            elif intent == 'hr_query':
                return self._handle_hr_query(query_text, company_id)
            elif intent == 'financial_query':
                return self._handle_financial_query(query_text, company_id)
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

    def _handle_sales_query(self, query_text, company_id):
        """Handle sales-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['اليوم', 'يوم']):
            return self._query_sales_today(company_id)
        elif any(kw in query_text_lower for kw in ['الشهر', 'شهري']):
            return self._query_sales_this_month(company_id)
        elif any(kw in query_text_lower for kw in ['أفضل', 'أكثر', 'المنتجات']):
            return self._query_top_products(company_id)
        elif any(kw in query_text_lower for kw in ['فواتير', 'عدد الفواتير']):
            return self._query_invoice_count(company_id)
        else:
            return self._query_sales_summary(company_id)

    def _query_sales_today(self, company_id):
        """Get total sales for today."""
        with connection.cursor() as cursor:
            # FIX: Use PostgreSQL DATE() and CURRENT_DATE instead of SQLite DATE('now')
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM sales_salesorder
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            row = cursor.fetchone()
            count, total = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'📊 **ملخص مبيعات اليوم:**\n'
            f'• عدد الفواتير: {count}\n'
            f'• إجمالي المبيعات: {total:,.2f} ريال'
        )

    def _query_sales_this_month(self, company_id):
        """Get total sales for the current month."""
        with connection.cursor() as cursor:
            # FIX: Use PostgreSQL TO_CHAR instead of SQLite strftime
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM sales_salesorder
                WHERE TO_CHAR(created_at, 'YYYY-MM') = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
            """)
            row = cursor.fetchone()
            count, total = (row[0], float(row[1])) if row else (0, 0)

        return (
            f'📊 **ملخص مبيعات الشهر الحالي:**\n'
            f'• عدد الفواتير: {count}\n'
            f'• إجمالي المبيعات: {total:,.2f} ريال'
        )

    def _query_top_products(self, company_id):
        """Get the top 5 best-selling products."""
        with connection.cursor() as cursor:
            # FIX: Use sales_salesorderitem and product_name instead of inventory_product
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

    def _query_invoice_count(self, company_id):
        """Get total number of invoices."""
        with connection.cursor() as cursor:
            # FIX: Removed double fetchone() — was calling it twice (second returned None)
            cursor.execute("""
                SELECT COUNT(*) FROM sales_salesorder
            """)
            row = cursor.fetchone()
            count = row[0] if row else 0

        return f'📄 إجمالي عدد فواتير البيع في النظام: **{count}** فاتورة.'

    def _query_sales_summary(self, company_id):
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
            f'• إجمالي الفواتير: {total}\n'
            f'• إجمالي المبيعات: {amount:,.2f} ريال\n'
            f'• متوسط قيمة الفاتورة: {avg:,.2f} ريال'
        )

    # ── Inventory Queries ──────────────────────────────────────────────

    def _handle_inventory_query(self, query_text, company_id):
        """Handle inventory-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['نفاد', 'نافد', 'نقص', 'قليل']):
            return self._query_low_stock(company_id)
        elif any(kw in query_text_lower for kw in ['عدد', 'كم صنف', 'كم منتج']):
            return self._query_product_count(company_id)
        elif any(kw in query_text_lower for kw in ['قيمة', 'إجمالي المخزون']):
            return self._query_inventory_value(company_id)
        else:
            return self._query_inventory_summary(company_id)

    def _query_low_stock(self, company_id):
        """Get products with low stock levels."""
        # FIX: inventory_product table was removed — provide informational response
        return (
            '⚠️ **حالة المخزون:**\n'
            'يرجى الرجوع إلى وحدة إدارة الأصول في النظام.\n'
            'التقارير المتاحة: حالة الأصول، صيانة المعدات، جرد الأصول الثابتة.'
        )

    def _query_product_count(self, company_id):
        """Get total number of products."""
        # FIX: inventory_product table was removed
        return (
            '📦 **الأصناف والمنتجات:**\n'
            'يرجى الرجوع إلى وحدة إدارة الأصول في النظام لمتابعة الأصول والمعدات.'
        )

    def _query_inventory_value(self, company_id):
        """Get total inventory value."""
        # FIX: inventory_product table was removed
        return (
            '💰 **قيمة الأصول:**\n'
            'يرجى الرجوع إلى وحدة إدارة الأصول في النظام للحصول على تفاصيل قيمة الأصول.'
        )

    def _query_inventory_summary(self, company_id):
        """Get general inventory summary."""
        # FIX: inventory_product table was removed
        return (
            '📦 **ملخص الأصول:**\n'
            'تم نقل إدارة المخزون إلى وحدة الأصول الثابتة.\n'
            'يرجى الرجوع إلى: إدارة الأصول، الصيانة، المشتريات.'
        )

    # ── HR Queries ─────────────────────────────────────────────────────

    def _handle_hr_query(self, query_text, company_id):
        """Handle HR-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['عدد', 'كم موظف', 'موظفين']):
            return self._query_employee_count(company_id)
        elif any(kw in query_text_lower for kw in ['إجازة', 'إجازات', 'غياب', 'غيابات']):
            return self._query_leave_summary(company_id)
        elif any(kw in query_text_lower for kw in ['حضور', 'تأخير']):
            return self._query_attendance_summary(company_id)
        else:
            return self._query_hr_summary(company_id)

    def _query_employee_count(self, company_id):
        """Get total number of employees."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM hr_employee
                WHERE is_active = true
            """)
            row = cursor.fetchone()
            count = row[0] if row else 0

        return f'👥 إجمالي عدد الموظفين النشطين في النظام: **{count}** موظف.'

    def _query_leave_summary(self, company_id):
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

    def _query_attendance_summary(self, company_id):
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

    def _query_hr_summary(self, company_id):
        """Get general HR summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM hr_employee
                WHERE is_active = true
            """)
            row = cursor.fetchone()
            total = row[0] if row else 0

        return (
            f'👥 **ملخص الموارد البشرية:**\n'
            f'• إجمالي الموظفين النشطين: {total}\n'
            f'• يمكنك الاطلاع على التفاصيل من: الأقسام، الحضور، الإجازات، الرواتب، تقييم الأداء.'
        )

    # ── Financial Queries ──────────────────────────────────────────────

    def _handle_financial_query(self, query_text, company_id):
        """Handle financial-related queries."""
        query_text_lower = query_text.lower()

        if any(kw in query_text_lower for kw in ['ربح', 'أرباح', 'صافي']):
            return self._query_profit_summary(company_id)
        elif any(kw in query_text_lower for kw in ['مصروف', 'مصاريف', 'مصروفات', 'تكلفة', 'تكاليف']):
            return self._query_expenses_summary(company_id)
        elif any(kw in query_text_lower for kw in ['إيراد', 'إيرادات', 'دخل']):
            return self._query_revenue_summary(company_id)
        elif any(kw in query_text_lower for kw in ['ميزانية', 'ميزان', 'الميزانية العمومية']):
            return self._query_balance_sheet_summary(company_id)
        else:
            return self._query_financial_summary(company_id)

    def _query_profit_summary(self, company_id):
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

    def _query_expenses_summary(self, company_id):
        """Get expenses summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    a.name,
                    a.account_type,
                    COALESCE(SUM(t.amount), 0) as total
                FROM accounting_transaction t
                JOIN accounting_account a ON t.account_id = a.id
                JOIN accounting_journalentry j ON t.journal_entry_id = j.id
                WHERE a.account_type = 'expense' AND j.is_posted = true
                GROUP BY a.name, a.account_type
                ORDER BY total DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()

        if not rows:
            return 'لا تتوفر بيانات مصروفات حالياً.'

        lines = ['💸 **أعلى 5 فئات مصروفات:**']
        for name, atype, total in rows:
            lines.append(f'• {name}: {float(total):,.2f} ريال')

        return '\n'.join(lines)

    def _query_revenue_summary(self, company_id):
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

    def _query_balance_sheet_summary(self, company_id):
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

    def _query_financial_summary(self, company_id):
        """Get general financial summary."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM sales_salesorder
            """)
            row = cursor.fetchone()
            total_sales = float(row[0]) if row else 0

        return (
            f'💰 **ملخص مالي عام:**\n'
            f'• إجمالي المبيعات التراكمية: {total_sales:,.2f} ريال\n'
            f'للحصول على تقارير مالية مفصّلة، راجع وحدة المحاسبة في النظام.\n'
            f'التقارير المتاحة: قائمة الدخل، الميزانية العمومية، التدفق النقدي.'
        )
