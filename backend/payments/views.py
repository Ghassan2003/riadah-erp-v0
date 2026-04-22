"""
API views for the Payments module.
Handles Payment Accounts, Financial Transactions, Cheques, Reconciliations, Stats, and Export.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db import transaction as db_transaction

from .models import PaymentAccount, FinancialTransaction, Cheque, Reconciliation
from .serializers import (
    PaymentAccountListSerializer,
    PaymentAccountCreateSerializer,
    PaymentAccountUpdateSerializer,
    PaymentAccountDetailSerializer,
    FinancialTransactionListSerializer,
    FinancialTransactionCreateSerializer,
    FinancialTransactionDetailSerializer,
    ChequeListSerializer,
    ChequeCreateSerializer,
    ChequeDetailSerializer,
    ChequeStatusUpdateSerializer,
    ReconciliationListSerializer,
    ReconciliationCreateSerializer,
    ReconciliationDetailSerializer,
    PaymentStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Payment Account Views
# =============================================

class PaymentAccountListView(generics.ListCreateAPIView):
    """GET: List payment accounts. POST: Create payment account (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['account_name', 'bank_name', 'account_number']
    ordering_fields = ['account_name', 'current_balance', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentAccountCreateSerializer
        return PaymentAccountListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = PaymentAccount.objects.all()
        account_type = self.request.query_params.get('account_type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response({
            'message': 'تم إنشاء الحساب المالي بنجاح',
            'account': PaymentAccountDetailSerializer(account).data,
        }, status=status.HTTP_201_CREATED)


class PaymentAccountDetailView(generics.RetrieveUpdateAPIView):
    """GET: Payment account details. PATCH: Update payment account (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PaymentAccountUpdateSerializer
        return PaymentAccountDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return PaymentAccount.objects.prefetch_related('transactions')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response({
            'message': 'تم تحديث الحساب المالي بنجاح',
            'account': PaymentAccountDetailSerializer(account).data,
        })


class PaymentAccountCreateView(generics.CreateAPIView):
    """POST: Create a payment account (admin only)."""

    serializer_class = PaymentAccountCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response({
            'message': 'تم إنشاء الحساب المالي بنجاح',
            'account': PaymentAccountDetailSerializer(account).data,
        }, status=status.HTTP_201_CREATED)


class PaymentAccountUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a payment account (admin only)."""

    serializer_class = PaymentAccountUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return PaymentAccount.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response({
            'message': 'تم تحديث الحساب المالي بنجاح',
            'account': PaymentAccountDetailSerializer(account).data,
        })


class PaymentAccountDeleteView(views.APIView):
    """DELETE: Deactivate a payment account (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            account = PaymentAccount.objects.get(pk=pk)
        except PaymentAccount.DoesNotExist:
            return Response({'error': 'الحساب المالي غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        if account.is_default:
            return Response({'error': 'لا يمكن حذف الحساب الافتراضي'}, status=status.HTTP_400_BAD_REQUEST)
        account.is_active = False
        account.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم حذف الحساب المالي بنجاح'})


# =============================================
# Financial Transaction Views
# =============================================

class FinancialTransactionListView(generics.ListAPIView):
    """GET: List financial transactions with filtering."""

    serializer_class = FinancialTransactionListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'transaction_number', 'description', 'cheque_number',
        'customer__name', 'supplier__name',
    ]
    ordering_fields = ['transaction_date', 'amount', 'transaction_number', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = FinancialTransaction.objects.select_related(
            'account', 'to_account', 'customer', 'supplier', 'created_by'
        )
        # Filter by type
        trx_type = self.request.query_params.get('type')
        if trx_type:
            queryset = queryset.filter(transaction_type=trx_type)
        # Filter by account
        account = self.request.query_params.get('account')
        if account:
            queryset = queryset.filter(account_id=account)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        # Filter by status
        trx_status = self.request.query_params.get('status')
        if trx_status:
            queryset = queryset.filter(status=trx_status)
        # Filter by customer
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer_id=customer)
        # Filter by supplier
        supplier = self.request.query_params.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        # Filter by reference type
        reference_type = self.request.query_params.get('reference_type')
        if reference_type:
            queryset = queryset.filter(reference_type=reference_type)
        return queryset


class FinancialTransactionCreateView(generics.CreateAPIView):
    """POST: Create a financial transaction (admin only). Updates account balances."""

    serializer_class = FinancialTransactionCreateSerializer
    permission_classes = [IsAdmin]

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trx = serializer.save()

        # Update account balances based on transaction type
        account = trx.account
        trx_type = trx.transaction_type

        if trx_type == 'receipt' and account:
            account.current_balance += trx.amount
            account.save(update_fields=['current_balance', 'updated_at'])
        elif trx_type == 'payment' and account:
            account.current_balance -= trx.amount
            account.save(update_fields=['current_balance', 'updated_at'])
        elif trx_type == 'transfer' and account and trx.to_account:
            # Decrease from source account
            account.current_balance -= trx.amount
            account.save(update_fields=['current_balance', 'updated_at'])
            # Increase in destination account
            trx.to_account.current_balance += trx.amount
            trx.to_account.save(update_fields=['current_balance', 'updated_at'])

        return Response({
            'message': 'تم إنشاء العملية المالية بنجاح',
            'transaction': FinancialTransactionDetailSerializer(trx).data,
        }, status=status.HTTP_201_CREATED)


class FinancialTransactionDetailView(generics.RetrieveAPIView):
    """GET: Financial transaction details."""

    serializer_class = FinancialTransactionDetailSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return FinancialTransaction.objects.select_related(
            'account', 'to_account', 'customer', 'supplier', 'created_by'
        )


class FinancialTransactionDeleteView(views.APIView):
    """DELETE: Cancel a financial transaction (admin only)."""

    permission_classes = [IsAdmin]

    @db_transaction.atomic
    def delete(self, request, pk):
        try:
            trx = FinancialTransaction.objects.select_related(
                'account', 'to_account'
            ).get(pk=pk)
        except FinancialTransaction.DoesNotExist:
            return Response(
                {'error': 'العملية المالية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if trx.status == 'cancelled':
            return Response(
                {'error': 'العملية المالية ملغاة بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reverse the balance changes
        account = trx.account
        trx_type = trx.transaction_type

        if trx.status == 'completed':
            if trx_type == 'receipt' and account:
                account.current_balance -= trx.amount
                account.save(update_fields=['current_balance', 'updated_at'])
            elif trx_type == 'payment' and account:
                account.current_balance += trx.amount
                account.save(update_fields=['current_balance', 'updated_at'])
            elif trx_type == 'transfer' and account and trx.to_account:
                account.current_balance += trx.amount
                account.save(update_fields=['current_balance', 'updated_at'])
                trx.to_account.current_balance -= trx.amount
                trx.to_account.save(update_fields=['current_balance', 'updated_at'])

        trx.status = 'cancelled'
        trx.save(update_fields=['status', 'updated_at'])
        return Response({
            'message': 'تم إلغاء العملية المالية بنجاح',
            'transaction': FinancialTransactionDetailSerializer(trx).data,
        })


# =============================================
# Cheque Views
# =============================================

class ChequeListView(generics.ListCreateAPIView):
    """GET: List cheques. POST: Create a cheque (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cheque_number', 'bank_name', 'payer_name', 'payee_name']
    ordering_fields = ['due_date', 'amount', 'cheque_number', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChequeCreateSerializer
        return ChequeListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Cheque.objects.select_related('customer', 'supplier', 'transaction')
        cheque_type = self.request.query_params.get('cheque_type')
        if cheque_type:
            queryset = queryset.filter(cheque_type=cheque_type)
        cheque_status = self.request.query_params.get('status')
        if cheque_status:
            queryset = queryset.filter(status=cheque_status)
        bank_name = self.request.query_params.get('bank_name')
        if bank_name:
            queryset = queryset.filter(bank_name__icontains=bank_name)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cheque = serializer.save()
        return Response({
            'message': 'تم إنشاء الشيك بنجاح',
            'cheque': ChequeDetailSerializer(cheque).data,
        }, status=status.HTTP_201_CREATED)


class ChequeCreateView(generics.CreateAPIView):
    """POST: Create a cheque (admin only)."""

    serializer_class = ChequeCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cheque = serializer.save()
        return Response({
            'message': 'تم إنشاء الشيك بنجاح',
            'cheque': ChequeDetailSerializer(cheque).data,
        }, status=status.HTTP_201_CREATED)


class ChequeStatusUpdateView(views.APIView):
    """POST: Update cheque status (deposit/clear/bounce/cancel)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            cheque = Cheque.objects.select_related('transaction').get(pk=pk)
        except Cheque.DoesNotExist:
            return Response(
                {'error': 'الشيك غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChequeStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')

        status_map = {
            'deposit': 'deposited',
            'clear': 'cleared',
            'bounce': 'bounced',
            'cancel': 'cancelled',
        }

        new_status = status_map[action]

        if cheque.status == 'cancelled':
            return Response(
                {'error': 'لا يمكن تحديث شيك ملغي'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cheque.status == 'cleared' and action != 'cancel':
            return Response(
                {'error': 'الشيك مصروف بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cheque.status == 'bounced' and action not in ('cancel',):
            return Response(
                {'error': 'الشيك مرتجع بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cheque.status = new_status
        if notes:
            cheque.notes = notes
        cheque.save(update_fields=['status', 'notes', 'updated_at'])

        action_messages = {
            'deposit': 'تم إيداع الشيك بنجاح',
            'clear': 'تم صرف الشيك بنجاح',
            'bounce': 'تم ارتداد الشيك',
            'cancel': 'تم إلغاء الشيك',
        }

        return Response({
            'message': action_messages[action],
            'cheque': ChequeDetailSerializer(cheque).data,
        })


class ChequeDetailView(generics.RetrieveAPIView):
    """GET: Cheque detail."""

    serializer_class = ChequeDetailSerializer

    def get_queryset(self):
        return Cheque.objects.select_related('customer', 'supplier', 'transaction')


class ChequeDeleteView(views.APIView):
    """DELETE: Cancel a cheque (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            cheque = Cheque.objects.select_related('transaction').get(pk=pk)
        except Cheque.DoesNotExist:
            return Response({'error': 'الشيك غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        if cheque.status == 'cleared':
            return Response({'error': 'لا يمكن حذف شيك مصروف'}, status=status.HTTP_400_BAD_REQUEST)
        cheque.status = 'cancelled'
        cheque.save(update_fields=['status', 'updated_at'])
        return Response({
            'message': 'تم إلغاء الشيك بنجاح',
            'cheque': ChequeDetailSerializer(cheque).data,
        })


# =============================================
# Reconciliation Views
# =============================================

class ReconciliationListView(generics.ListAPIView):
    """GET: List reconciliations with filtering."""

    serializer_class = ReconciliationListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['period_start', 'period_end', 'system_balance', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Reconciliation.objects.select_related('account', 'reconciled_by')
        account = self.request.query_params.get('account')
        if account:
            queryset = queryset.filter(account_id=account)
        rec_status = self.request.query_params.get('status')
        if rec_status:
            queryset = queryset.filter(status=rec_status)
        return queryset


class ReconciliationCreateView(generics.CreateAPIView):
    """POST: Create a reconciliation (admin only). Auto-calculates system balance from transactions."""

    serializer_class = ReconciliationCreateSerializer
    permission_classes = [IsAdmin]

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        account = data['account']
        period_start = data['period_start']
        period_end = data['period_end']

        # Calculate system balance from transactions in the period
        receipts = FinancialTransaction.objects.filter(
            account=account,
            transaction_type='receipt',
            status='completed',
            transaction_date__gte=period_start,
            transaction_date__lte=period_end,
        ).aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)))['total']

        payments = FinancialTransaction.objects.filter(
            account=account,
            transaction_type='payment',
            status='completed',
            transaction_date__gte=period_start,
            transaction_date__lte=period_end,
        ).aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)))['total']

        transfers_out = FinancialTransaction.objects.filter(
            account=account,
            transaction_type='transfer',
            status='completed',
            transaction_date__gte=period_start,
            transaction_date__lte=period_end,
        ).aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)))['total']

        transfers_in = FinancialTransaction.objects.filter(
            to_account=account,
            transaction_type='transfer',
            status='completed',
            transaction_date__gte=period_start,
            transaction_date__lte=period_end,
        ).aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)))['total']

        adjustments = FinancialTransaction.objects.filter(
            account=account,
            transaction_type='adjustment',
            status='completed',
            transaction_date__gte=period_start,
            transaction_date__lte=period_end,
        ).aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)))['total']

        system_balance = account.current_balance + transfers_in - transfers_out
        # For reconciliation, compute net from all transaction flows in period
        system_balance = receipts + transfers_in + adjustments - payments - transfers_out

        reconciliation = Reconciliation(
            account=account,
            period_start=period_start,
            period_end=period_end,
            system_balance=system_balance,
            actual_balance=data['actual_balance'],
            notes=data.get('notes', ''),
            reconciled_by=request.user if request.user.is_authenticated else None,
        )
        reconciliation.save()

        return Response({
            'message': 'تم إنشاء التسوية بنجاح',
            'reconciliation': ReconciliationDetailSerializer(reconciliation).data,
        }, status=status.HTTP_201_CREATED)


class ReconciliationDetailView(generics.RetrieveAPIView):
    """GET: Reconciliation detail."""

    serializer_class = ReconciliationDetailSerializer

    def get_queryset(self):
        return Reconciliation.objects.select_related('account', 'reconciled_by')


class ReconciliationUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a reconciliation (admin only)."""

    serializer_class = ReconciliationCreateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Reconciliation.objects.select_related('account', 'reconciled_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        instance.actual_balance = data['actual_balance']
        instance.notes = data.get('notes', instance.notes)
        instance.difference = instance.actual_balance - instance.system_balance
        instance.status = 'reconciled' if instance.difference == 0 else 'discrepancy'
        instance.save()
        return Response({
            'message': 'تم تحديث التسوية بنجاح',
            'reconciliation': ReconciliationDetailSerializer(instance).data,
        })


class ReconciliationDeleteView(views.APIView):
    """DELETE: Delete a reconciliation (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            rec = Reconciliation.objects.get(pk=pk)
        except Reconciliation.DoesNotExist:
            return Response({'error': 'التسوية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
        rec.delete()
        return Response({'message': 'تم حذف التسوية بنجاح'})


# =============================================
# Payment Stats View
# =============================================

class PaymentStatsView(views.APIView):
    """GET: Payment statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        active_accounts = PaymentAccount.objects.filter(is_active=True)
        stats = {
            'total_accounts': PaymentAccount.objects.count(),
            'active_accounts': active_accounts.count(),
            'total_balance': active_accounts.aggregate(
                total=Coalesce(Sum('current_balance'), Value(0),
                               output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'today_receipts': FinancialTransaction.objects.filter(
                transaction_type='receipt', status='completed', transaction_date=today
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0),
                               output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'today_payments': FinancialTransaction.objects.filter(
                transaction_type='payment', status='completed', transaction_date=today
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0),
                               output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'pending_transactions': FinancialTransaction.objects.filter(
                status='pending'
            ).count(),
            'pending_cheques': Cheque.objects.filter(
                status__in=('received', 'deposited')
            ).count(),
            'bounced_cheques': Cheque.objects.filter(
                status='bounced'
            ).count(),
            'total_transactions_count': FinancialTransaction.objects.filter(
                status='completed'
            ).count(),
            'month_receipts': FinancialTransaction.objects.filter(
                transaction_type='receipt', status='completed',
                transaction_date__gte=month_start, transaction_date__lte=today
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0),
                               output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'month_payments': FinancialTransaction.objects.filter(
                transaction_type='payment', status='completed',
                transaction_date__gte=month_start, transaction_date__lte=today
            ).aggregate(
                total=Coalesce(Sum('amount'), Value(0),
                               output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
        }

        serializer = PaymentStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Excel Export View
# =============================================

class PaymentExportView(views.APIView):
    """GET: Export financial transactions to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        export_type = request.query_params.get('type', 'transactions')

        if export_type == 'transactions':
            return self._export_transactions(request)
        elif export_type == 'cheques':
            return self._export_cheques(request)
        elif export_type == 'accounts':
            return self._export_accounts(request)
        elif export_type == 'reconciliations':
            return self._export_reconciliations(request)
        else:
            return self._export_transactions(request)

    def _export_transactions(self, request):
        from core.utils import export_to_excel
        queryset = FinancialTransaction.objects.select_related(
            'account', 'to_account', 'customer', 'supplier', 'created_by'
        )
        columns = [
            ('transaction_number', 'رقم العملية', 22),
            ('transaction_type', 'نوع العملية', 15),
            ('account', 'الحساب', 25),
            ('to_account', 'حساب المستلم', 25),
            ('amount', 'المبلغ', 15),
            ('currency', 'العملة', 8),
            ('customer', 'العميل', 25),
            ('supplier', 'المورد', 25),
            ('payment_method', 'طريقة الدفع', 15),
            ('status', 'الحالة', 12),
            ('transaction_date', 'التاريخ', 15),
            ('description', 'الوصف', 40),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for t in queryset:
            data.append({
                'transaction_number': t.transaction_number,
                'transaction_type': t.get_transaction_type_display(),
                'account': t.account.account_name if t.account else '',
                'to_account': t.to_account.account_name if t.to_account else '',
                'amount': str(t.amount),
                'currency': t.currency,
                'customer': t.customer.name if t.customer else '',
                'supplier': t.supplier.name if t.supplier else '',
                'payment_method': t.get_payment_method_display(),
                'status': t.get_status_display(),
                'transaction_date': str(t.transaction_date) if t.transaction_date else '',
                'description': t.description or '',
                'created_at': str(t.created_at.strftime('%Y-%m-%d %H:%M')) if t.created_at else '',
            })
        return export_to_excel(data, columns, 'العمليات المالية', 'transactions.xlsx')

    def _export_cheques(self, request):
        from core.utils import export_to_excel
        queryset = Cheque.objects.select_related('customer', 'supplier', 'transaction')
        columns = [
            ('cheque_number', 'رقم الشيك', 22),
            ('bank_name', 'البنك', 25),
            ('branch_name', 'الفرع', 25),
            ('amount', 'المبلغ', 15),
            ('due_date', 'تاريخ الاستحقاق', 15),
            ('payer_name', 'اسم المحرر', 25),
            ('payee_name', 'اسم المستفيد', 25),
            ('cheque_type', 'نوع الشيك', 15),
            ('status', 'الحالة', 12),
            ('notes', 'ملاحظات', 40),
        ]
        data = []
        for c in queryset:
            data.append({
                'cheque_number': c.cheque_number,
                'bank_name': c.bank_name or '',
                'branch_name': c.branch_name or '',
                'amount': str(c.amount),
                'due_date': str(c.due_date) if c.due_date else '',
                'payer_name': c.payer_name or '',
                'payee_name': c.payee_name or '',
                'cheque_type': c.get_cheque_type_display(),
                'status': c.get_status_display(),
                'notes': c.notes or '',
            })
        return export_to_excel(data, columns, 'الشيكات', 'cheques.xlsx')

    def _export_accounts(self, request):
        from core.utils import export_to_excel
        queryset = PaymentAccount.objects.all()
        columns = [
            ('account_name', 'اسم الحساب', 30),
            ('account_type', 'نوع الحساب', 18),
            ('bank_name', 'البنك', 25),
            ('account_number', 'رقم الحساب', 22),
            ('iban', 'الآيبان', 28),
            ('currency', 'العملة', 8),
            ('current_balance', 'الرصيد الحالي', 18),
            ('is_default', 'افتراضي', 10),
            ('is_active', 'نشط', 10),
        ]
        data = []
        for a in queryset:
            data.append({
                'account_name': a.account_name,
                'account_type': a.get_account_type_display(),
                'bank_name': a.bank_name or '',
                'account_number': a.account_number or '',
                'iban': a.iban or '',
                'currency': a.currency,
                'current_balance': str(a.current_balance),
                'is_default': a.is_default,
                'is_active': a.is_active,
            })
        return export_to_excel(data, columns, 'الحسابات المالية', 'accounts.xlsx')

    def _export_reconciliations(self, request):
        from core.utils import export_to_excel
        queryset = Reconciliation.objects.select_related('account', 'reconciled_by')
        columns = [
            ('reconciliation_number', 'رقم التسوية', 22),
            ('account', 'الحساب', 30),
            ('period_start', 'بداية الفترة', 15),
            ('period_end', 'نهاية الفترة', 15),
            ('system_balance', 'رصيد النظام', 18),
            ('actual_balance', 'الرصيد الفعلي', 18),
            ('difference', 'الفارق', 18),
            ('status', 'الحالة', 15),
            ('reconciled_by', 'بواسطة', 20),
            ('notes', 'ملاحظات', 40),
        ]
        data = []
        for r in queryset:
            data.append({
                'reconciliation_number': r.reconciliation_number,
                'account': r.account.account_name if r.account else '',
                'period_start': str(r.period_start) if r.period_start else '',
                'period_end': str(r.period_end) if r.period_end else '',
                'system_balance': str(r.system_balance),
                'actual_balance': str(r.actual_balance),
                'difference': str(r.difference),
                'status': r.get_status_display(),
                'reconciled_by': r.reconciled_by.username if r.reconciled_by else '',
                'notes': r.notes or '',
            })
        return export_to_excel(data, columns, 'التسويات', 'reconciliations.xlsx')
