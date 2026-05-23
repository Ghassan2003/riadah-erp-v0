"""
Serializers for the Budget Management module.
Handles Budget, BudgetCategory, BudgetItem, BudgetTransfer, and BudgetExpense
data transformation.
"""

from rest_framework import serializers
from .models import (
    Budget,
    BudgetCategory,
    BudgetItem,
    BudgetTransfer,
    BudgetExpense,
)


# =============================================
# Budget Serializers
# =============================================

class BudgetListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing budgets."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = Budget
        fields = (
            'id', 'name', 'fiscal_year', 'department', 'department_name',
            'total_budget', 'utilized_amount', 'remaining_amount', 'status',
            'status_display', 'start_date', 'end_date', 'description',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class BudgetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a budget."""

    class Meta:
        model = Budget
        fields = (
            'name', 'fiscal_year', 'department', 'total_budget',
            'start_date', 'end_date', 'description',
        )

    def validate(self, attrs):
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
        return attrs


class BudgetUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a budget."""

    class Meta:
        model = Budget
        fields = (
            'name', 'department', 'total_budget', 'status',
            'start_date', 'end_date', 'description',
        )

    def validate(self, attrs):
        if 'start_date' in attrs and 'end_date' in attrs:
            if attrs['start_date'] >= attrs['end_date']:
                raise serializers.ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
        return attrs


class BudgetDetailSerializer(BudgetListSerializer):
    """Detailed budget serializer with categories count."""

    categories_count = serializers.SerializerMethodField()

    class Meta(BudgetListSerializer.Meta):
        fields = BudgetListSerializer.Meta.fields + ('categories_count',)

    def get_categories_count(self, obj):
        return obj.categories.count()


# =============================================
# Budget Category Serializers
# =============================================

class BudgetCategoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing budget categories."""

    budget_name = serializers.CharField(source='budget.name', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True, default=None)

    class Meta:
        model = BudgetCategory
        fields = (
            'id', 'budget', 'budget_name', 'name', 'allocated_amount',
            'utilized_amount', 'remaining_amount', 'account', 'account_name',
            'description', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class BudgetCategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a budget category."""

    class Meta:
        model = BudgetCategory
        fields = ('budget', 'name', 'allocated_amount', 'account', 'description')

    def validate_allocated_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ المخصص يجب أن يكون أكبر من صفر')
        return value


class BudgetCategoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a budget category."""

    class Meta:
        model = BudgetCategory
        fields = ('name', 'allocated_amount', 'account', 'description')


# =============================================
# Budget Item Serializers
# =============================================

class BudgetItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing budget items."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    budget_name = serializers.CharField(source='category.budget.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    variance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = BudgetItem
        fields = (
            'id', 'category', 'category_name', 'budget_name', 'description',
            'planned_amount', 'actual_amount', 'variance', 'status',
            'status_display', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class BudgetItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a budget item."""

    class Meta:
        model = BudgetItem
        fields = ('category', 'description', 'planned_amount', 'actual_amount', 'notes')

    def validate_planned_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ المخطط يجب أن يكون أكبر من صفر')
        return value


class BudgetItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a budget item."""

    class Meta:
        model = BudgetItem
        fields = ('description', 'planned_amount', 'actual_amount', 'status', 'notes')


# =============================================
# Budget Transfer Serializers
# =============================================

class BudgetTransferListSerializer(serializers.ModelSerializer):
    """Serializer for listing budget transfers."""

    from_budget_name = serializers.CharField(source='from_budget.name', read_only=True)
    to_budget_name = serializers.CharField(source='to_budget.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = BudgetTransfer
        fields = (
            'id', 'from_budget', 'from_budget_name', 'to_budget',
            'to_budget_name', 'amount', 'reason', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class BudgetTransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a budget transfer."""

    class Meta:
        model = BudgetTransfer
        fields = ('from_budget', 'to_budget', 'amount', 'reason')

    def validate(self, attrs):
        if attrs['from_budget'] == attrs['to_budget']:
            raise serializers.ValidationError('لا يمكن التحويل من وإلى نفس الميزانية')
        if attrs['amount'] <= 0:
            raise serializers.ValidationError('مبلغ التحويل يجب أن يكون أكبر من صفر')
        return attrs


class BudgetTransferApproveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting budget transfers."""

    action = serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح (approve أو reject)'},
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Budget Expense Serializers
# =============================================

class BudgetExpenseListSerializer(serializers.ModelSerializer):
    """Serializer for listing budget expenses."""

    budget_name = serializers.CharField(source='budget.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = BudgetExpense
        fields = (
            'id', 'budget', 'budget_name', 'category', 'category_name',
            'amount', 'description', 'expense_date', 'reference_number',
            'status', 'status_display', 'approved_by', 'approved_by_name',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class BudgetExpenseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a budget expense."""

    class Meta:
        model = BudgetExpense
        fields = ('budget', 'category', 'amount', 'description', 'expense_date', 'reference_number')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('مبلغ المصروف يجب أن يكون أكبر من صفر')
        return value


class BudgetExpenseApproveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting budget expenses."""

    action = serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح (approve أو reject)'},
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Budget Stats Serializer
# =============================================

class BudgetStatsSerializer(serializers.Serializer):
    """Serializer for Budget dashboard statistics."""

    total_budgets = serializers.IntegerField()
    total_allocated = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_utilized = serializers.DecimalField(max_digits=14, decimal_places=2)
    active_budgets_count = serializers.IntegerField()
