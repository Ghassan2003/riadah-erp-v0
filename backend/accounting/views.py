"""
API views for the Accounting module - Phase 4.
Handles Chart of Accounts, Journal Entries, Financial Reports, and Sales Integration.
"""

from rest_framework import (
    generics, status, permissions, filters, views, viewsets
)
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Sum, Count, F, DecimalField, Q, Value, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db import transaction as db_transaction
from decimal import Decimal

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
        queryset = Account.objects.filter(is_active=True).annotate(
            children_count=Count('children')
        )
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

        # Get income accounts balances in ONE bulk query (Fix 2: eliminates 4N queries)
        income_balances = Transaction.objects.filter(
            journal_entry__in=entries,
            account__account_type=AccountType.INCOME,
            account__is_active=True,
        ).values('account_id', 'account__name', 'account__code', 'account__account_type').annotate(
            total_credit=Coalesce(
                Sum(Case(
                    When(transaction_type='credit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
            total_debit=Coalesce(
                Sum(Case(
                    When(transaction_type='debit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
        )

        income_data = []
        total_income = 0
        for item in income_balances:
            net = item['total_credit'] - item['total_debit']
            if net > 0:
                income_data.append({
                    'account_code': item['account__code'],
                    'account_name': item['account__name'],
                    'account_type': item['account__account_type'],
                    'balance': net,
                })
                total_income += net

        # Get expense accounts balances in ONE bulk query (Fix 2: eliminates 4N queries)
        expense_balances = Transaction.objects.filter(
            journal_entry__in=entries,
            account__account_type=AccountType.EXPENSE,
            account__is_active=True,
        ).values('account_id', 'account__name', 'account__code', 'account__account_type').annotate(
            total_debit=Coalesce(
                Sum(Case(
                    When(transaction_type='debit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
            total_credit=Coalesce(
                Sum(Case(
                    When(transaction_type='credit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
        )

        expense_data = []
        total_expenses = 0
        for item in expense_balances:
            net = item['total_debit'] - item['total_credit']
            if net > 0:
                expense_data.append({
                    'account_code': item['account__code'],
                    'account_name': item['account__name'],
                    'account_type': item['account__account_type'],
                    'balance': net,
                })
                total_expenses += net

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
            'total_accounts': Account.objects.count(),
            'active_accounts': all_accounts.count(),
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
# Purchases-Accounting Integration
# =============================================

@db_transaction.atomic
def create_purchase_journal_entry(purchase_order):
    """
    Create a journal entry for a confirmed purchase order.
    Automatically called when a purchase order is confirmed.

    Debit: Inventory / Purchases (Asset)
    Credit: Accounts Payable (Liability)
    """
    # Get or create default accounts
    payable_account, _ = Account.objects.get_or_create(
        code='2000',
        defaults={
            'name': 'الدائنون (المورّدون)',
            'name_en': 'Accounts Payable',
            'account_type': AccountType.LIABILITY,
            'description': 'مبالغ مستحقة للمورّدين',
        }
    )
    purchases_account, _ = Account.objects.get_or_create(
        code='5000',
        defaults={
            'name': 'المشتريات',
            'name_en': 'Purchases',
            'account_type': AccountType.EXPENSE,
            'description': 'حساب المشتريات الرئيسي',
        }
    )

    # Create journal entry
    entry = JournalEntry.objects.create(
        entry_type='manual',
        description=f'أمر الشراء {purchase_order.order_number} - المورّد: {purchase_order.supplier.name}',
        reference=purchase_order.order_number,
        entry_date=purchase_order.order_date or timezone.now().date(),
        created_by=purchase_order.created_by,
    )

    total_amount = purchase_order.total_amount

    # Debit: Purchases / Inventory account (we received goods)
    Transaction.objects.create(
        journal_entry=entry,
        account=purchases_account,
        transaction_type='debit',
        amount=total_amount,
        description=f'مشتريات من {purchase_order.supplier.name} - {purchase_order.order_number}',
    )

    # Credit: Payable account (we owe the supplier)
    Transaction.objects.create(
        journal_entry=entry,
        account=payable_account,
        transaction_type='credit',
        amount=total_amount,
        description=f'مبلغ مستحق للمورّد {purchase_order.supplier.name} - {purchase_order.order_number}',
    )

    # Auto-post the entry
    entry.post_entry()

    return entry


@db_transaction.atomic
def cancel_purchase_journal_entry(purchase_order):
    """
    Reverse the journal entry when a purchase order is cancelled.
    """
    entry = JournalEntry.objects.filter(
        reference=purchase_order.order_number,
        entry_type='manual',
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


# =============================================
# Trial Balance View
# =============================================

class TrialBalanceView(views.APIView):
    """GET: Generate trial balance report."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import TrialBalanceSerializer

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Filter posted journal entries by date range
        posted_entries = JournalEntry.objects.filter(is_posted=True)
        if date_from:
            posted_entries = posted_entries.filter(entry_date__gte=date_from)
        if date_to:
            posted_entries = posted_entries.filter(entry_date__lte=date_to)

        accounts = Account.objects.filter(is_active=True).order_by('code')

        # Get ALL balances in ONE bulk query (Fix 1: eliminates 2N queries)
        balances = Transaction.objects.filter(
            journal_entry__in=posted_entries,
            account__in=accounts,
        ).values('account_id').annotate(
            total_debit=Coalesce(
                Sum(Case(
                    When(transaction_type='debit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
            total_credit=Coalesce(
                Sum(Case(
                    When(transaction_type='credit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
        )

        # Build a dict for quick lookup
        balance_map = {b['account_id']: b for b in balances}

        accounts_data = []
        grand_debit = 0
        grand_credit = 0

        for account in accounts:
            bal = balance_map.get(account.id, {
                'total_debit': Decimal('0'),
                'total_credit': Decimal('0'),
            })
            total_debit = bal['total_debit']
            total_credit = bal['total_credit']

            # Balance depends on account type
            if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                balance = total_debit - total_credit
                balance_type = 'debit' if balance >= 0 else 'credit'
            else:
                balance = total_credit - total_debit
                balance_type = 'credit' if balance >= 0 else 'debit'

            balance = abs(balance)

            # Only include accounts with activity or non-zero balance
            if total_debit > 0 or total_credit > 0 or balance > 0:
                accounts_data.append({
                    'account_code': account.code,
                    'account_name': account.name,
                    'account_type': account.account_type,
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'balance': balance,
                    'balance_type': balance_type,
                })
                grand_debit += total_debit
                grand_credit += total_credit

        report_data = {
            'date_from': date_from,
            'date_to': date_to,
            'accounts': accounts_data,
            'grand_total_debit': grand_debit,
            'grand_total_credit': grand_credit,
        }

        serializer = TrialBalanceSerializer(report_data)
        return Response(serializer.data)


# =============================================
# General Ledger View
# =============================================

class GeneralLedgerView(views.APIView):
    """GET: Generate general ledger report for a specific account."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import GeneralLedgerSerializer

        account_id = request.query_params.get('account_id')
        if not account_id:
            return Response(
                {'error': 'account_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        try:
            account = Account.objects.get(pk=account_id, is_active=True)
        except Account.DoesNotExist:
            return Response(
                {'error': 'الحساب غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate opening balance (sum of all transactions BEFORE date_from, or all if no date_from)
        all_posted = JournalEntry.objects.filter(is_posted=True)

        if date_from:
            prior_entries = all_posted.filter(entry_date__lt=date_from)
            prior_debit = account.transactions.filter(
                journal_entry__in=prior_entries,
                transaction_type='debit',
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['total']
            prior_credit = account.transactions.filter(
                journal_entry__in=prior_entries,
                transaction_type='credit',
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=16, decimal_places=2))
            )['total']
        else:
            prior_debit = 0
            prior_credit = 0

        # Opening balance based on account type
        if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
            opening_balance = prior_debit - prior_credit
        else:
            opening_balance = prior_credit - prior_debit

        # Get transactions in the date range
        period_entries = all_posted
        if date_from:
            period_entries = period_entries.filter(entry_date__gte=date_from)
        if date_to:
            period_entries = period_entries.filter(entry_date__lte=date_to)

        # Get unique journal entries that affect this account within the period
        txn_queryset = account.transactions.filter(
            journal_entry__in=period_entries,
        ).select_related('journal_entry').order_by('journal_entry__entry_date', 'journal_entry__id')

        entries_data = []
        running_balance = opening_balance
        total_debit = 0
        total_credit = 0

        for txn in txn_queryset:
            je = txn.journal_entry
            debit_amount = txn.amount if txn.transaction_type == 'debit' else 0
            credit_amount = txn.amount if txn.transaction_type == 'credit' else 0

            # Update running balance based on account type
            if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                running_balance += debit_amount - credit_amount
            else:
                running_balance += credit_amount - debit_amount

            entries_data.append({
                'entry_number': je.entry_number,
                'entry_date': je.entry_date,
                'description': txn.description or je.description,
                'debit_amount': debit_amount,
                'credit_amount': credit_amount,
                'running_balance': running_balance,
            })

            total_debit += debit_amount
            total_credit += credit_amount

        report_data = {
            'account': {
                'account_id': account.id,
                'account_code': account.code,
                'account_name': account.name,
                'account_type': account.account_type,
                'opening_balance': opening_balance,
            },
            'date_from': date_from,
            'date_to': date_to,
            'entries': entries_data,
            'closing_balance': running_balance,
            'total_debit': total_debit,
            'total_credit': total_credit,
        }

        serializer = GeneralLedgerSerializer(report_data)
        return Response(serializer.data)


# =============================================
# Cash Flow Statement View
# =============================================

class CashFlowStatementView(views.APIView):
    """GET: Generate cash flow statement report."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import CashFlowStatementSerializer

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Filter posted journal entries by date range
        posted_entries = JournalEntry.objects.filter(is_posted=True)
        if date_from:
            posted_entries = posted_entries.filter(entry_date__gte=date_from)
        if date_to:
            posted_entries = posted_entries.filter(entry_date__lte=date_to)

        # Keywords for classification
        FIXED_ASSET_KEYWORDS = ['equipment', 'vehicle', 'fixed', 'property', 'furniture', 'machine', 'building', 'land']
        DEPRECIATION_KEYWORDS = ['depreciation', 'استهلاك', 'إهلاك']
        LOAN_KEYWORDS = ['loan', 'borrowing', 'قرض', 'سلفة']
        CAPITAL_KEYWORDS = ['capital', 'equity', 'رأس مال', 'حقوق']
        DIVIDEND_KEYWORDS = ['dividend', 'distribution', 'توزيع']

        def classify_account(account_name, account_name_en, account_type):
            """Classify account into operating/investing/financing category."""
            name_lower = (account_name + ' ' + account_name_en).lower()

            # Check for financing: capital, loans, dividends
            for kw in CAPITAL_KEYWORDS:
                if kw in name_lower:
                    return 'financing'
            for kw in LOAN_KEYWORDS:
                if kw in name_lower:
                    return 'financing'
            for kw in DIVIDEND_KEYWORDS:
                if kw in name_lower:
                    return 'financing'

            # Check for investing: fixed assets + depreciation
            for kw in FIXED_ASSET_KEYWORDS:
                if kw in name_lower:
                    return 'investing'
            for kw in DEPRECIATION_KEYWORDS:
                if kw in name_lower:
                    return 'investing'

            # Income/expense defaults to operating
            if account_type in (AccountType.INCOME, AccountType.EXPENSE):
                return 'operating'

            # Asset accounts (cash/bank/receivables/inventory) → investing
            if account_type == AccountType.ASSET:
                return 'investing'

            # Remaining liabilities → financing
            if account_type == AccountType.LIABILITY:
                return 'financing'

            # Remaining equity → financing
            if account_type == AccountType.EQUITY:
                return 'financing'

            return 'operating'

        # Get ALL net movements in ONE bulk query (Fix 3: eliminates 2N queries)
        all_balances = Transaction.objects.filter(
            journal_entry__in=posted_entries,
            account__is_active=True,
        ).values(
            'account_id', 'account__name', 'account__name_en',
            'account__code', 'account__account_type',
        ).annotate(
            total_debit=Coalesce(
                Sum(Case(
                    When(transaction_type='debit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
            total_credit=Coalesce(
                Sum(Case(
                    When(transaction_type='credit', then=F('amount')),
                    output_field=DecimalField(max_digits=16, decimal_places=2)
                )),
                Value(0, output_field=DecimalField(max_digits=16, decimal_places=2))
            ),
        )

        operating_items = []
        investing_items = []
        financing_items = []

        for item in all_balances:
            net_amount = item['total_credit'] - item['total_debit']
            if net_amount == 0:
                continue

            category = classify_account(
                item['account__name'],
                item['account__name_en'],
                item['account__account_type'],
            )

            row = {
                'account_code': item['account__code'],
                'account_name': item['account__name'],
                'amount': net_amount,
            }

            if category == 'operating':
                operating_items.append(row)
            elif category == 'investing':
                investing_items.append(row)
            elif category == 'financing':
                financing_items.append(row)

        operating_net = sum(item['amount'] for item in operating_items)
        investing_net = sum(item['amount'] for item in investing_items)
        financing_net = sum(item['amount'] for item in financing_items)

        report_data = {
            'date_from': date_from,
            'date_to': date_to,
            'operating_activities': {
                'items': operating_items,
                'net_amount': operating_net,
            },
            'investing_activities': {
                'items': investing_items,
                'net_amount': investing_net,
            },
            'financing_activities': {
                'items': financing_items,
                'net_amount': financing_net,
            },
            'net_change_in_cash': operating_net + investing_net + financing_net,
        }

        serializer = CashFlowStatementSerializer(report_data)
        return Response(serializer.data)


# =============================================
# VAT Return View
# =============================================

class VATReturnView(views.APIView):
    """GET: Generate VAT return report for a specific month/year."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import VATReturnSerializer
        from sales.models import SalesOrder
        from invoicing.models import Invoice

        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if not month or not year:
            return Response(
                {'error': 'month and year are required query parameters'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month = int(month)
            year = int(year)
        except (ValueError, TypeError):
            return Response(
                {'error': 'month and year must be valid integers'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= month <= 12):
            return Response(
                {'error': 'month must be between 1 and 12'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.db.models import Sum as AggSum, Count
        from decimal import Decimal

        # Output VAT: sales invoices issued in the given month
        sales_invoices = Invoice.objects.filter(
            invoice_type='sales',
            issue_date__year=year,
            issue_date__month=month,
            is_active=True,
        ).exclude(status='cancelled')

        output_vat_data = sales_invoices.aggregate(
            total_vat=Coalesce(
                AggSum('vat_amount'),
                Value(Decimal('0')),
                output_field=DecimalField(max_digits=16, decimal_places=2)
            ),
            count=Count('id'),
        )
        total_output_vat = output_vat_data['total_vat']
        sales_invoices_count = output_vat_data['count']

        # Input VAT: purchase invoices received in the given month
        purchase_invoices = Invoice.objects.filter(
            invoice_type='purchase',
            issue_date__year=year,
            issue_date__month=month,
            is_active=True,
        ).exclude(status='cancelled')

        input_vat_data = purchase_invoices.aggregate(
            total_vat=Coalesce(
                AggSum('vat_amount'),
                Value(Decimal('0')),
                output_field=DecimalField(max_digits=16, decimal_places=2)
            ),
            count=Count('id'),
        )
        total_input_vat = input_vat_data['total_vat']
        purchase_invoices_count = input_vat_data['count']

        net_vat_payable = total_output_vat - total_input_vat

        report_data = {
            'month': month,
            'year': year,
            'total_output_vat': total_output_vat,
            'total_input_vat': total_input_vat,
            'net_vat_payable': net_vat_payable,
            'sales_invoices_count': sales_invoices_count,
            'purchase_invoices_count': purchase_invoices_count,
        }

        serializer = VATReturnSerializer(report_data)
        return Response(serializer.data)


# =============================================
# Accounts Receivable Aging View
# =============================================

class ARAgingView(views.APIView):
    """GET: Generate accounts receivable aging report."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import ARAgingSerializer
        from sales.models import SalesOrder
        from django.db.models import Sum as AggSum, Count

        from decimal import Decimal
        today = timezone.now().date()

        # Get confirmed/shipped/delivered sales orders that are not fully paid
        # Check via related invoices for payment status
        eligible_orders = SalesOrder.objects.filter(
            status__in=['confirmed', 'shipped', 'delivered'],
        ).select_related('customer').prefetch_related('invoices')

        # Group by customer
        customer_data = {}

        for order in eligible_orders:
            customer = order.customer
            customer_id = customer.id

            # Calculate unpaid amount from related invoices
            invoices = order.invoices.filter(is_active=True).exclude(status='cancelled')
            if not invoices.exists():
                # No invoices yet — full order amount is outstanding
                outstanding = order.total_amount
            else:
                # Sum total amounts minus paid amounts from all invoices
                total_invoiced = sum(inv.total_amount for inv in invoices)
                total_paid = sum(inv.paid_amount for inv in invoices)
                outstanding = max(total_invoiced - total_paid, Decimal('0'))

            if outstanding <= 0:
                continue

            # Calculate aging based on order date
            days_past = (today - order.order_date).days

            if customer_id not in customer_data:
                customer_data[customer_id] = {
                    'customer_id': customer_id,
                    'customer_name': customer.name,
                    'current': Decimal('0'),
                    'days_1_30': Decimal('0'),
                    'days_31_60': Decimal('0'),
                    'days_61_90': Decimal('0'),
                    'days_over_90': Decimal('0'),
                    'total_outstanding': Decimal('0'),
                    'orders_count': 0,
                }

            if days_past <= 0:
                customer_data[customer_id]['current'] += outstanding
            elif days_past <= 30:
                customer_data[customer_id]['days_1_30'] += outstanding
            elif days_past <= 60:
                customer_data[customer_id]['days_31_60'] += outstanding
            elif days_past <= 90:
                customer_data[customer_id]['days_61_90'] += outstanding
            else:
                customer_data[customer_id]['days_over_90'] += outstanding

            customer_data[customer_id]['total_outstanding'] += outstanding
            customer_data[customer_id]['orders_count'] += 1

        customers_list = list(customer_data.values())

        grand_totals = {
            'current': sum(c['current'] for c in customers_list),
            'days_1_30': sum(c['days_1_30'] for c in customers_list),
            'days_31_60': sum(c['days_31_60'] for c in customers_list),
            'days_61_90': sum(c['days_61_90'] for c in customers_list),
            'days_over_90': sum(c['days_over_90'] for c in customers_list),
            'outstanding': sum(c['total_outstanding'] for c in customers_list),
        }

        report_data = {
            'report_date': today,
            'customers': customers_list,
            **{f'grand_total_{k}': v for k, v in grand_totals.items()},
        }

        serializer = ARAgingSerializer(report_data)
        return Response(serializer.data)


# =============================================
# Accounts Payable Aging View
# =============================================

class APAgingView(views.APIView):
    """GET: Generate accounts payable aging report."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import APAgingSerializer
        from purchases.models import PurchaseOrder
        from django.db.models import Sum as AggSum, Count

        from decimal import Decimal
        today = timezone.now().date()

        # Get confirmed/received/partial purchase orders
        eligible_orders = PurchaseOrder.objects.filter(
            status__in=['confirmed', 'received', 'partial'],
        ).select_related('supplier').prefetch_related('invoices')

        # Group by supplier
        supplier_data = {}

        for order in eligible_orders:
            supplier = order.supplier
            supplier_id = supplier.id

            # Calculate unpaid amount from related invoices
            invoices = order.invoices.filter(is_active=True).exclude(status='cancelled')
            if not invoices.exists():
                # No invoices yet — full order amount is outstanding
                outstanding = order.total_amount
            else:
                # Sum total amounts minus paid amounts from all invoices
                total_invoiced = sum(inv.total_amount for inv in invoices)
                total_paid = sum(inv.paid_amount for inv in invoices)
                outstanding = max(total_invoiced - total_paid, Decimal('0'))

            if outstanding <= 0:
                continue

            # Calculate aging based on order date
            days_past = (today - order.order_date).days

            if supplier_id not in supplier_data:
                supplier_data[supplier_id] = {
                    'supplier_id': supplier_id,
                    'supplier_name': supplier.name,
                    'current': Decimal('0'),
                    'days_1_30': Decimal('0'),
                    'days_31_60': Decimal('0'),
                    'days_61_90': Decimal('0'),
                    'days_over_90': Decimal('0'),
                    'total_outstanding': Decimal('0'),
                    'orders_count': 0,
                }

            if days_past <= 0:
                supplier_data[supplier_id]['current'] += outstanding
            elif days_past <= 30:
                supplier_data[supplier_id]['days_1_30'] += outstanding
            elif days_past <= 60:
                supplier_data[supplier_id]['days_31_60'] += outstanding
            elif days_past <= 90:
                supplier_data[supplier_id]['days_61_90'] += outstanding
            else:
                supplier_data[supplier_id]['days_over_90'] += outstanding

            supplier_data[supplier_id]['total_outstanding'] += outstanding
            supplier_data[supplier_id]['orders_count'] += 1

        suppliers_list = list(supplier_data.values())

        grand_totals = {
            'current': sum(s['current'] for s in suppliers_list),
            'days_1_30': sum(s['days_1_30'] for s in suppliers_list),
            'days_31_60': sum(s['days_31_60'] for s in suppliers_list),
            'days_61_90': sum(s['days_61_90'] for s in suppliers_list),
            'days_over_90': sum(s['days_over_90'] for s in suppliers_list),
            'outstanding': sum(s['total_outstanding'] for s in suppliers_list),
        }

        report_data = {
            'report_date': today,
            'suppliers': suppliers_list,
            **{f'grand_total_{k}': v for k, v in grand_totals.items()},
        }

        serializer = APAgingSerializer(report_data)
        return Response(serializer.data)
