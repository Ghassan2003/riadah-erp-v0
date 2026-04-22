"""
API views for the Accounting module - Phase 4.
Handles Chart of Accounts, Journal Entries, Financial Reports, and Sales Integration.
"""

from rest_framework import (
    generics, status, permissions, filters, views, viewsets
)
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db import transaction as db_transaction

from .models import Account, JournalEntry, Transaction, AccountType
from .serializers import (
    AccountListSerializer,
    AccountCreateSerializer,
    AccountUpdateSerializer,
    AccountDetailSerializer,
    JournalEntryListSerializer,
    JournalEntryDetailSerializer,
    CreateJournalEntrySerializer,
    TransactionSerializer,
    FinancialReportSerializer,
    BalanceSheetSerializer,
    AccountBalanceSerializer,
    AccountingStatsSerializer,
)
from users.permissions import IsAccountantOrAdmin, IsSalesOrAdmin
from core.decorators import PermissionRequiredMixin


# =============================================
# Account (Chart of Accounts) Views
# =============================================

class AccountListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List all accounts in the chart of accounts."""

    permission_module = 'accounting'
    permission_action = 'view'

    serializer_class = AccountListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'name_en']
    ordering_fields = ['code', 'name', 'account_type', 'current_balance']
    ordering = ['code']

    def get_queryset(self):
        queryset = Account.objects.filter(is_active=True)
        # Filter by account type
        account_type = self.request.query_params.get('account_type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        # Filter for top-level accounts only
        top_level = self.request.query_params.get('top_level')
        if top_level and top_level.lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)
        return queryset


class AccountDetailView(PermissionRequiredMixin, generics.RetrieveAPIView):
    """GET: Detailed view of a single account."""

    permission_module = 'accounting'
    permission_action = 'view'

    serializer_class = AccountDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(is_active=True)


class AccountCreateView(PermissionRequiredMixin, generics.CreateAPIView):
    """POST: Create a new account (accountant/admin only)."""

    permission_module = 'accounting'
    permission_action = 'create'

    serializer_class = AccountCreateSerializer
    permission_classes = [IsAccountantOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response({
            'message': 'تم إنشاء الحساب بنجاح',
            'account': AccountDetailSerializer(account).data,
        }, status=status.HTTP_201_CREATED)


class AccountUpdateView(PermissionRequiredMixin, generics.UpdateAPIView):
    """PATCH: Update account info (accountant/admin only)."""

    permission_module = 'accounting'
    permission_action = 'edit'

    serializer_class = AccountUpdateSerializer
    permission_classes = [IsAccountantOrAdmin]

    def get_queryset(self):
        return Account.objects.filter(is_active=True)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response({
            'message': 'تم تحديث الحساب بنجاح',
            'account': AccountDetailSerializer(account).data,
        })


class AccountDeleteView(views.APIView):
    """DELETE: Soft-delete (deactivate) an account."""

    permission_classes = [IsAccountantOrAdmin]

    def delete(self, request, pk):
        try:
            account = Account.objects.get(pk=pk)
        except Account.DoesNotExist:
            return Response(
                {'error': 'الحساب غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not account.is_active:
            return Response(
                {'error': 'الحساب غير مفعّل بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account.is_active = False
        account.save(update_fields=['is_active', 'updated_at'])

        return Response({'message': 'تم إلغاء تفعيل الحساب بنجاح'})


# =============================================
# Journal Entry Views
# =============================================

class JournalEntryListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List all journal entries with filtering."""

    permission_module = 'accounting'
    permission_action = 'view'

    serializer_class = JournalEntryListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['entry_number', 'description', 'reference']
    ordering_fields = ['entry_number', 'entry_date', 'is_posted', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = JournalEntry.objects.select_related('created_by').prefetch_related('transactions__account')
        # Filter by type
        entry_type = self.request.query_params.get('entry_type')
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        # Filter by posted status
        is_posted = self.request.query_params.get('is_posted')
        if is_posted is not None:
            is_posted_val = is_posted.lower() == 'true'
            queryset = queryset.filter(is_posted=is_posted_val)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(entry_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(entry_date__lte=date_to)
        # Filter by account
        account_id = self.request.query_params.get('account')
        if account_id:
            queryset = queryset.filter(transactions__account_id=account_id).distinct()
        return queryset


class JournalEntryDetailView(PermissionRequiredMixin, generics.RetrieveAPIView):
    """GET: Detailed view of a single journal entry with transactions."""

    permission_module = 'accounting'
    permission_action = 'view'

    serializer_class = JournalEntryDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.select_related(
            'created_by', 'sales_order'
        ).prefetch_related('transactions__account')


class JournalEntryCreateView(PermissionRequiredMixin, generics.CreateAPIView):
    """POST: Create a new journal entry with transactions."""

    permission_module = 'accounting'
    permission_action = 'create'

    serializer_class = CreateJournalEntrySerializer
    permission_classes = [IsAccountantOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        return Response({
            'message': 'تم إنشاء قيد اليومية بنجاح',
            'entry': JournalEntryDetailSerializer(entry).data,
        }, status=status.HTTP_201_CREATED)


class JournalEntryPostView(views.APIView):
    """POST: Post (approve) a journal entry to update account balances."""

    permission_classes = [IsAccountantOrAdmin]

    def post(self, request, pk):
        try:
            entry = JournalEntry.objects.select_related().get(pk=pk)
        except JournalEntry.DoesNotExist:
            return Response(
                {'error': 'قيد اليومية غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            entry.post_entry()
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'message': 'تم ترحيل القيد بنجاح',
            'entry': JournalEntryDetailSerializer(entry).data,
        })


class JournalEntryUpdateView(PermissionRequiredMixin, generics.UpdateAPIView):
    """PATCH: Update a journal entry (only draft/unposted entries)."""

    permission_module = 'accounting'
    permission_action = 'edit'

    serializer_class = CreateJournalEntrySerializer
    permission_classes = [IsAccountantOrAdmin]

    def get_queryset(self):
        return JournalEntry.objects.filter(
            is_posted=False
        ).select_related('created_by').prefetch_related('transactions__account')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.is_posted:
            return Response(
                {'error': 'لا يمكن تعديل قيد مرحّل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()

        return Response({
            'message': 'تم تحديث قيد اليومية بنجاح',
            'entry': JournalEntryDetailSerializer(entry).data,
        })


class JournalEntryReverseView(views.APIView):
    """POST: Reverse (cancel) a posted journal entry."""

    permission_classes = [IsAccountantOrAdmin]

    def post(self, request, pk):
        try:
            entry = JournalEntry.objects.select_related().get(pk=pk)
        except JournalEntry.DoesNotExist:
            return Response(
                {'error': 'قيد اليومية غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            entry.reverse_entry()
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'message': 'تم إلغاء ترحيل القيد بنجاح',
            'entry': JournalEntryDetailSerializer(entry).data,
        })


# =============================================
# Financial Reports Views
# =============================================

class IncomeStatementView(views.APIView):
    """GET: Generate income statement (profit and loss report)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get date range from query params
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Filter posted journal entries by date range
        entries = JournalEntry.objects.filter(is_posted=True)
        if date_from:
            entries = entries.filter(entry_date__gte=date_from)
        if date_to:
            entries = entries.filter(entry_date__lte=date_to)

        # Get income accounts
        income_accounts = Account.objects.filter(
            account_type=AccountType.INCOME,
            is_active=True,
        )
        income_data = []
        total_income = 0
        for account in income_accounts:
            total = account.transactions.filter(
                journal_entry__in=entries,
                transaction_type='credit'
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['total']
            # Subtract debits from income accounts
            total -= account.transactions.filter(
                journal_entry__in=entries,
                transaction_type='debit'
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['total']

            if total > 0:
                income_data.append({
                    'account_code': account.code,
                    'account_name': account.name,
                    'account_type': account.account_type,
                    'balance': total,
                })
                total_income += total

        # Get expense accounts
        expense_accounts = Account.objects.filter(
            account_type=AccountType.EXPENSE,
            is_active=True,
        )
        expense_data = []
        total_expenses = 0
        for account in expense_accounts:
            total = account.transactions.filter(
                journal_entry__in=entries,
                transaction_type='debit'
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['total']
            # Subtract credits from expense accounts
            total -= account.transactions.filter(
                journal_entry__in=entries,
                transaction_type='credit'
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['total']

            if total > 0:
                expense_data.append({
                    'account_code': account.code,
                    'account_name': account.name,
                    'account_type': account.account_type,
                    'balance': total,
                })
                total_expenses += total

        net_profit = total_income - total_expenses

        report_data = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'income_accounts': income_data,
            'expense_accounts': expense_data,
        }

        serializer = FinancialReportSerializer(report_data)
        return Response(serializer.data)


class BalanceSheetView(views.APIView):
    """GET: Generate balance sheet report."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all active accounts grouped by type
        asset_accounts = Account.objects.filter(
            account_type=AccountType.ASSET,
            is_active=True,
        )
        liability_accounts = Account.objects.filter(
            account_type=AccountType.LIABILITY,
            is_active=True,
        )
        equity_accounts = Account.objects.filter(
            account_type=AccountType.EQUITY,
            is_active=True,
        )

        def get_account_list(accounts):
            result = []
            for acc in accounts:
                if acc.current_balance != 0:
                    result.append({
                        'account_code': acc.code,
                        'account_name': acc.name,
                        'account_type': acc.account_type,
                        'balance': acc.current_balance,
                    })
            return result

        asset_data = get_account_list(asset_accounts)
        liability_data = get_account_list(liability_accounts)
        equity_data = get_account_list(equity_accounts)

        total_assets = sum(a['balance'] for a in asset_data)
        total_liabilities = sum(a['balance'] for a in liability_data)
        total_equity = sum(a['balance'] for a in equity_data)

        report_data = {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'asset_accounts': asset_data,
            'liability_accounts': liability_data,
            'equity_accounts': equity_data,
        }

        serializer = BalanceSheetSerializer(report_data)
        return Response(serializer.data)


# =============================================
# Accounting Stats View
# =============================================

class AccountingStatsView(views.APIView):
    """GET: Accounting statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        all_accounts = Account.objects.filter(is_active=True)

        # Income and expense totals from current balances
        total_income = all_accounts.filter(
            account_type=AccountType.INCOME
        ).aggregate(
            total=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['total']

        total_expenses = all_accounts.filter(
            account_type=AccountType.EXPENSE
        ).aggregate(
            total=Coalesce(Sum('current_balance'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
        )['total']

        stats = {
            'total_accounts': all_accounts.count(),
            'active_accounts': all_accounts.filter(is_active=True).count(),
            'total_journal_entries': JournalEntry.objects.count(),
            'posted_entries': JournalEntry.objects.filter(is_posted=True).count(),
            'pending_entries': JournalEntry.objects.filter(is_posted=False).count(),
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': total_income - total_expenses,
        }

        serializer = AccountingStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Sales-Accounting Integration
# =============================================

@db_transaction.atomic
def create_sales_journal_entry(sales_order):
    """
    Create a journal entry for a confirmed sales order.
    Automatically called when a sales order is confirmed.

    Debit: Accounts Receivable (or Cash)
    Credit: Sales Revenue
    """
    from sales.models import SalesOrder

    # Get or create default accounts
    cash_account, _ = Account.objects.get_or_create(
        code='1001',
        defaults={
            'name': 'النقدية والبنوك',
            'name_en': 'Cash & Banks',
            'account_type': AccountType.ASSET,
            'description': 'حساب النقدية والبنوك الافتراضي',
        }
    )
    receivable_account, _ = Account.objects.get_or_create(
        code='1100',
        defaults={
            'name': 'المدينون (العملاء)',
            'name_en': 'Accounts Receivable',
            'account_type': AccountType.ASSET,
            'description': 'مبالغ مستحقة من العملاء',
        }
    )
    revenue_account, _ = Account.objects.get_or_create(
        code='4000',
        defaults={
            'name': 'إيرادات المبيعات',
            'name_en': 'Sales Revenue',
            'account_type': AccountType.INCOME,
            'description': 'إيرادات المبيعات الرئيسية',
        }
    )

    # Create journal entry
    entry = JournalEntry.objects.create(
        entry_type='sale',
        description=f'إيراد أمر البيع {sales_order.order_number} - العميل: {sales_order.customer.name}',
        reference=sales_order.order_number,
        entry_date=sales_order.order_date,
        sales_order=sales_order,
        created_by=sales_order.created_by,
    )

    total_amount = sales_order.total_amount

    # Debit: Receivable account (we expect to receive payment)
    Transaction.objects.create(
        journal_entry=entry,
        account=receivable_account,
        transaction_type='debit',
        amount=total_amount,
        description=f'مبلغ مستحق من {sales_order.customer.name} - {sales_order.order_number}',
    )

    # Credit: Revenue account
    Transaction.objects.create(
        journal_entry=entry,
        account=revenue_account,
        transaction_type='credit',
        amount=total_amount,
        description=f'إيراد مبيعات - {sales_order.order_number}',
    )

    # Auto-post the entry
    entry.post_entry()

    return entry


@db_transaction.atomic
def cancel_sales_journal_entry(sales_order):
    """
    Reverse the journal entry when a sales order is cancelled.
    """

    entry = JournalEntry.objects.filter(
        sales_order=sales_order,
        is_posted=True,
    ).last()

    if entry:
        entry.reverse_entry()
        entry.description = f'[ملغى] {entry.description}'
        entry.save(update_fields=['description', 'updated_at'])


# =============================================
# PDF Report Generation Views
# =============================================

from .pdf_reports import generate_income_statement_pdf, generate_balance_sheet_pdf


class IncomeStatementPDFView(views.APIView):
    """GET: توليد تقرير قائمة الدخل بصيغة PDF."""

    permission_classes = [IsAccountantOrAdmin]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        income_data = {
            'revenue_items': [],
            'expense_items': [],
            'total_revenue': 0,
            'total_expenses': 0,
            'net_income': 0,
        }

        from .models import Account
        revenue_accounts = Account.objects.filter(account_type='income', is_active=True)
        expense_accounts = Account.objects.filter(account_type='expense', is_active=True)

        total_revenue = 0
        for account in revenue_accounts:
            balance = account.current_balance
            if balance != 0:
                income_data['revenue_items'].append({'name': account.name, 'amount': balance})
                total_revenue += balance
        income_data['total_revenue'] = total_revenue

        total_expenses = 0
        for account in expense_accounts:
            balance = abs(account.current_balance)
            if balance != 0:
                income_data['expense_items'].append({'name': account.name, 'amount': balance})
                total_expenses += balance
        income_data['total_expenses'] = total_expenses

        income_data['net_income'] = total_revenue - total_expenses

        pdf_buffer = generate_income_statement_pdf(income_data, date_from, date_to)

        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="income_statement.pdf"'
        return response


class BalanceSheetPDFView(views.APIView):
    """GET: توليد تقرير الميزانية العمومية بصيغة PDF."""

    permission_classes = [IsAccountantOrAdmin]

    def get(self, request):
        from .models import Account

        balance_data = {
            'assets': [],
            'liabilities': [],
            'equity': [],
            'total_assets': 0,
            'total_liabilities_equity': 0,
        }

        asset_accounts = Account.objects.filter(account_type='asset', is_active=True)
        liability_accounts = Account.objects.filter(account_type='liability', is_active=True)
        equity_accounts = Account.objects.filter(account_type='equity', is_active=True)

        total_assets = 0
        for account in asset_accounts:
            balance = account.current_balance
            if balance != 0:
                balance_data['assets'].append({'name': account.name, 'amount': balance})
                total_assets += balance
        balance_data['total_assets'] = total_assets

        total_le = 0
        for account in liability_accounts:
            balance = abs(account.current_balance)
            if balance != 0:
                balance_data['liabilities'].append({'name': account.name, 'amount': balance})
                total_le += balance
        for account in equity_accounts:
            balance = account.current_balance
            if balance != 0:
                balance_data['equity'].append({'name': account.name, 'amount': balance})
                total_le += balance
        balance_data['total_liabilities_equity'] = total_le

        pdf_buffer = generate_balance_sheet_pdf(balance_data)

        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="balance_sheet.pdf"'
        return response


# =============================================
# Excel Export Views
# =============================================

class AccountExportView(views.APIView):
    """GET: Export chart of accounts to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Account.objects.filter(is_active=True)
        columns = [
            ('code', 'رمز الحساب', 15),
            ('name', 'اسم الحساب', 30),
            ('account_type', 'نوع الحساب', 15),
            ('current_balance', 'الرصيد الحالي', 18),
            ('is_active', 'نشط', 10),
        ]
        data = []
        for a in queryset:
            data.append({
                'code': a.code,
                'name': a.name,
                'account_type': a.get_account_type_display(),
                'current_balance': str(a.current_balance),
                'is_active': a.is_active,
            })
        return export_to_excel(data, columns, 'الدليل المحاسبي', 'accounts.xlsx')


class JournalEntryExportView(views.APIView):
    """GET: Export journal entries to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = JournalEntry.objects.select_related('created_by')
        columns = [
            ('entry_number', 'رقم القيد', 20),
            ('entry_type', 'نوع القيد', 15),
            ('description', 'الوصف', 40),
            ('reference', 'المرجع', 20),
            ('entry_date', 'تاريخ القيد', 15),
            ('is_posted', 'مرحّل', 10),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for e in queryset:
            data.append({
                'entry_number': e.entry_number,
                'entry_type': e.get_entry_type_display(),
                'description': e.description or '',
                'reference': e.reference or '',
                'entry_date': str(e.entry_date) if e.entry_date else '',
                'is_posted': e.is_posted,
                'created_at': str(e.created_at.strftime('%Y-%m-%d %H:%M')) if e.created_at else '',
            })
        return export_to_excel(data, columns, 'قيود اليومية', 'journal_entries.xlsx')
