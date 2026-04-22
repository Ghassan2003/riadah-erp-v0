"""
API views for the Budget Management module.
Handles Budgets, BudgetCategories, BudgetItems, BudgetTransfers,
BudgetExpenses, stats, and export.
"""

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    Budget,
    BudgetCategory,
    BudgetItem,
    BudgetTransfer,
    BudgetExpense,
)
from .serializers import (
    BudgetListSerializer,
    BudgetCreateSerializer,
    BudgetUpdateSerializer,
    BudgetDetailSerializer,
    BudgetCategoryListSerializer,
    BudgetCategoryCreateSerializer,
    BudgetCategoryUpdateSerializer,
    BudgetItemListSerializer,
    BudgetItemCreateSerializer,
    BudgetItemUpdateSerializer,
    BudgetTransferListSerializer,
    BudgetTransferCreateSerializer,
    BudgetTransferApproveSerializer,
    BudgetExpenseListSerializer,
    BudgetExpenseCreateSerializer,
    BudgetExpenseApproveSerializer,
    BudgetStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Budget Stats View
# =============================================

class BudgetStatsView(views.APIView):
    """GET: Budget statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = {
            'total_budgets': Budget.objects.count(),
            'total_allocated': Budget.objects.aggregate(
                total=Coalesce(
                    Sum('total_budget'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_utilized': Budget.objects.aggregate(
                total=Coalesce(
                    Sum('utilized_amount'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'active_budgets_count': Budget.objects.filter(
                status='active'
            ).count(),
        }

        serializer = BudgetStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Budget Views
# =============================================

class BudgetListView(generics.ListCreateAPIView):
    """GET: List budgets. POST: Create budget (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'fiscal_year', 'status', 'total_budget', 'created_at']
    ordering = ['-fiscal_year', 'name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BudgetCreateSerializer
        return BudgetListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Budget.objects.select_related('department', 'created_by')
        # Filter by status
        budget_status = self.request.query_params.get('status')
        if budget_status:
            queryset = queryset.filter(status=budget_status)
        # Filter by fiscal year
        fiscal_year = self.request.query_params.get('fiscal_year')
        if fiscal_year:
            queryset = queryset.filter(fiscal_year=fiscal_year)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        budget = serializer.save(
            created_by=request.user,
            remaining_amount=serializer.validated_data['total_budget'],
        )
        return Response({
            'message': 'تم إنشاء الميزانية بنجاح',
            'budget': BudgetDetailSerializer(budget).data,
        }, status=status.HTTP_201_CREATED)


class BudgetDetailView(generics.RetrieveUpdateAPIView):
    """GET: Budget details. PATCH: Update budget (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return BudgetUpdateSerializer
        return BudgetDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Budget.objects.select_related('department', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        budget = serializer.save()
        return Response({
            'message': 'تم تحديث الميزانية بنجاح',
            'budget': BudgetDetailSerializer(budget).data,
        })


class BudgetDeleteView(views.APIView):
    """DELETE: Delete a budget (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            budget = Budget.objects.get(pk=pk)
        except Budget.DoesNotExist:
            return Response(
                {'error': 'الميزانية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if budget.status not in ('draft',):
            return Response(
                {'error': 'لا يمكن حذف ميزانية ليست في حالة مسودة'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        budget.delete()
        return Response({'message': 'تم حذف الميزانية بنجاح'})


# =============================================
# Budget Category Views
# =============================================

class BudgetCategoryListView(generics.ListCreateAPIView):
    """GET: List budget categories. POST: Create budget category (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'allocated_amount', 'utilized_amount', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BudgetCategoryCreateSerializer
        return BudgetCategoryListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = BudgetCategory.objects.select_related('budget', 'account')
        # Filter by budget
        budget = self.request.query_params.get('budget')
        if budget:
            queryset = queryset.filter(budget_id=budget)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save(
            remaining_amount=serializer.validated_data['allocated_amount'],
        )
        return Response({
            'message': 'تم إنشاء فئة الميزانية بنجاح',
            'category': BudgetCategoryListSerializer(category).data,
        }, status=status.HTTP_201_CREATED)


class BudgetCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: Budget category details. PATCH: Update. DELETE: Delete (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return BudgetCategoryUpdateSerializer
        return BudgetCategoryListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return BudgetCategory.objects.select_related('budget', 'account')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response({
            'message': 'تم تحديث فئة الميزانية بنجاح',
            'category': BudgetCategoryListSerializer(category).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'تم حذف فئة الميزانية بنجاح'})


# =============================================
# Budget Item Views
# =============================================

class BudgetItemListView(generics.ListCreateAPIView):
    """GET: List budget items. POST: Create budget item (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'notes']
    ordering_fields = ['description', 'planned_amount', 'actual_amount', 'status', 'created_at']
    ordering = ['description']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BudgetItemCreateSerializer
        return BudgetItemListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = BudgetItem.objects.select_related('category__budget')
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        # Filter by budget (through category)
        budget = self.request.query_params.get('budget')
        if budget:
            queryset = queryset.filter(category__budget_id=budget)
        # Filter by status
        item_status = self.request.query_params.get('status')
        if item_status:
            queryset = queryset.filter(status=item_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({
            'message': 'تم إنشاء بند الميزانية بنجاح',
            'item': BudgetItemListSerializer(item).data,
        }, status=status.HTTP_201_CREATED)


class BudgetItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: Budget item details. PATCH: Update. DELETE: Delete (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return BudgetItemUpdateSerializer
        return BudgetItemListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return BudgetItem.objects.select_related('category__budget')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({
            'message': 'تم تحديث بند الميزانية بنجاح',
            'item': BudgetItemListSerializer(item).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'تم حذف بند الميزانية بنجاح'})


# =============================================
# Budget Transfer Views
# =============================================

class BudgetTransferListView(generics.ListCreateAPIView):
    """GET: List budget transfers. POST: Create budget transfer (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reason']
    ordering_fields = ['amount', 'status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BudgetTransferCreateSerializer
        return BudgetTransferListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = BudgetTransfer.objects.select_related('from_budget', 'to_budget', 'approved_by')
        # Filter by status
        transfer_status = self.request.query_params.get('status')
        if transfer_status:
            queryset = queryset.filter(status=transfer_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transfer = serializer.save()
        return Response({
            'message': 'تم إنشاء طلب تحويل الميزانية بنجاح',
            'transfer': BudgetTransferListSerializer(transfer).data,
        }, status=status.HTTP_201_CREATED)


class BudgetTransferApproveView(views.APIView):
    """POST: Approve or reject a budget transfer (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            transfer = BudgetTransfer.objects.select_related('from_budget', 'to_budget').get(pk=pk)
        except BudgetTransfer.DoesNotExist:
            return Response(
                {'error': 'طلب تحويل الميزانية غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BudgetTransferApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if transfer.status != 'pending':
            return Response(
                {'error': 'يمكن الموافقة أو الرفض فقط على الطلبات المعلقة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from decimal import Decimal

        if action == 'approve':
            transfer.status = 'approved'
            transfer.approved_by = request.user

            # Update budget amounts
            from_budget = transfer.from_budget
            to_budget = transfer.to_budget
            amount = transfer.amount

            from_budget.total_budget -= amount
            from_budget.remaining_amount = max(Decimal('0'), from_budget.remaining_amount - amount)
            from_budget.save()

            to_budget.total_budget += amount
            to_budget.remaining_amount += amount
            to_budget.save()

            transfer.save()

            return Response({
                'message': 'تمت الموافقة على تحويل الميزانية',
                'transfer': BudgetTransferListSerializer(transfer).data,
            })
        else:
            transfer.status = 'rejected'
            transfer.approved_by = request.user
            transfer.save()

            return Response({
                'message': 'تم رفض طلب تحويل الميزانية',
                'transfer': BudgetTransferListSerializer(transfer).data,
            })


# =============================================
# Budget Expense Views
# =============================================

class BudgetExpenseListView(generics.ListCreateAPIView):
    """GET: List budget expenses. POST: Create budget expense (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'reference_number']
    ordering_fields = ['amount', 'status', 'expense_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BudgetExpenseCreateSerializer
        return BudgetExpenseListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = BudgetExpense.objects.select_related('budget', 'category', 'approved_by')
        # Filter by budget
        budget = self.request.query_params.get('budget')
        if budget:
            queryset = queryset.filter(budget_id=budget)
        # Filter by status
        expense_status = self.request.query_params.get('status')
        if expense_status:
            queryset = queryset.filter(status=expense_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()
        return Response({
            'message': 'تم إنشاء مصروف الميزانية بنجاح',
            'expense': BudgetExpenseListSerializer(expense).data,
        }, status=status.HTTP_201_CREATED)


class BudgetExpenseApproveView(views.APIView):
    """POST: Approve or reject a budget expense (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            expense = BudgetExpense.objects.select_related('budget', 'category').get(pk=pk)
        except BudgetExpense.DoesNotExist:
            return Response(
                {'error': 'مصروف الميزانية غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BudgetExpenseApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if expense.status != 'pending':
            return Response(
                {'error': 'يمكن الموافقة أو الرفض فقط على المصروفات المعلقة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from decimal import Decimal

        if action == 'approve':
            expense.status = 'approved'
            expense.approved_by = request.user

            # Update budget utilized amount
            budget = expense.budget
            budget.utilized_amount += expense.amount
            budget.remaining_amount = max(Decimal('0'), budget.remaining_amount - expense.amount)
            budget.save()

            # Update category utilized amount if category exists
            if expense.category:
                category = expense.category
                category.utilized_amount += expense.amount
                category.remaining_amount = max(Decimal('0'), category.remaining_amount - expense.amount)
                category.save()

            expense.save()

            return Response({
                'message': 'تمت الموافقة على مصروف الميزانية',
                'expense': BudgetExpenseListSerializer(expense).data,
            })
        else:
            expense.status = 'rejected'
            expense.approved_by = request.user
            expense.save()

            return Response({
                'message': 'تم رفض مصروف الميزانية',
                'expense': BudgetExpenseListSerializer(expense).data,
            })


# =============================================
# Budget Export View
# =============================================

class BudgetExportView(views.APIView):
    """GET: Export budget data to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        queryset = Budget.objects.select_related('department').order_by('-fiscal_year', 'name')

        # Filter by fiscal year
        fiscal_year = self.request.query_params.get('fiscal_year')
        if fiscal_year:
            queryset = queryset.filter(fiscal_year=fiscal_year)

        columns = [
            ('name', 'اسم الميزانية', 30),
            ('fiscal_year', 'السنة المالية', 15),
            ('department', 'القسم', 20),
            ('total_budget', 'إجمالي الميزانية', 16),
            ('utilized_amount', 'المبلغ المستخدم', 16),
            ('remaining_amount', 'المبلغ المتبقي', 16),
            ('status', 'الحالة', 15),
            ('start_date', 'تاريخ البداية', 15),
            ('end_date', 'تاريخ النهاية', 15),
            ('description', 'الوصف', 40),
        ]
        data = []
        for b in queryset:
            data.append({
                'name': b.name,
                'fiscal_year': b.fiscal_year,
                'department': b.department.name if b.department else '',
                'total_budget': str(b.total_budget),
                'utilized_amount': str(b.utilized_amount),
                'remaining_amount': str(b.remaining_amount),
                'status': b.get_status_display(),
                'start_date': str(b.start_date),
                'end_date': str(b.end_date),
                'description': b.description,
            })
        return export_to_excel(data, columns, 'تقرير الميزانيات', 'budget.xlsx')
