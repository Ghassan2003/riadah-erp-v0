"""
Serializers for the Projects module.
Handles Project, ProjectTask, TaskComment, and ProjectExpense data transformation.
"""

from rest_framework import serializers
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from django.db.models import Value, DecimalField
from django.utils import timezone
from .models import (
    Project, ProjectTask, TaskComment, ProjectExpense,
    ProjectPhase, ProjectMilestone, BudgetItem, ProjectRisk,
    TimeEntry, ProjectContract, ProjectDocument,
)


# =============================================
# TaskComment Serializers
# =============================================

class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for listing task comments."""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = TaskComment
        fields = (
            'id', 'task', 'content', 'created_by', 'created_by_name',
            'created_at',
        )
        read_only_fields = ('id', 'task', 'created_by', 'created_at')


class TaskCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a task comment."""

    class Meta:
        model = TaskComment
        fields = ('content',)

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError('محتوى التعليق مطلوب')
        return value


# =============================================
# ProjectTask Serializers
# =============================================

class ProjectTaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing project tasks."""

    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = ProjectTask
        fields = (
            'id', 'project', 'title', 'status', 'status_display',
            'priority', 'priority_display', 'assigned_to', 'assigned_to_name',
            'due_date', 'completed_at', 'created_at',
        )
        read_only_fields = ('id', 'created_at', 'completed_at')


class ProjectTaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a project task."""

    class Meta:
        model = ProjectTask
        fields = ('project', 'title', 'description', 'priority', 'assigned_to', 'start_date', 'due_date')

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError('عنوان المهمة مطلوب')
        return value


class ProjectTaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a project task."""

    class Meta:
        model = ProjectTask
        fields = ('title', 'description', 'status', 'priority', 'assigned_to', 'start_date', 'due_date')


# =============================================
# ProjectExpense Serializers
# =============================================

class ProjectExpenseSerializer(serializers.ModelSerializer):
    """Serializer for listing project expenses."""

    expense_type_display = serializers.CharField(source='get_expense_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = ProjectExpense
        fields = (
            'id', 'project', 'title', 'expense_type', 'expense_type_display',
            'amount', 'date', 'description', 'created_by', 'created_by_name',
            'created_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at')


class ProjectExpenseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a project expense."""

    class Meta:
        model = ProjectExpense
        fields = ('project', 'title', 'expense_type', 'amount', 'date', 'description')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر')
        return value

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError('عنوان المصروف مطلوب')
        return value


# =============================================
# Project Serializers
# =============================================

class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing projects."""

    manager_name = serializers.CharField(source='manager.username', read_only=True, default='')
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'name_en', 'status', 'status_display',
            'priority', 'priority_display', 'start_date', 'end_date',
            'budget', 'spent', 'progress', 'manager', 'manager_name',
            'customer', 'customer_name', 'tasks_count', 'is_active',
            'created_at',
        )
        read_only_fields = ('id', 'spent', 'created_at')

    def get_tasks_count(self, obj):
        return obj.tasks.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new project."""

    class Meta:
        model = Project
        fields = (
            'name', 'name_en', 'description', 'status', 'priority',
            'start_date', 'end_date', 'budget', 'progress',
            'manager', 'customer',
        )

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('اسم المشروع مطلوب')
        return value

    def validate_progress(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('نسبة الإنجاز يجب أن تكون بين 0 و 100')
        return value


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating project info."""

    class Meta:
        model = Project
        fields = (
            'name', 'name_en', 'description', 'status', 'priority',
            'start_date', 'end_date', 'actual_end_date', 'budget',
            'progress', 'manager', 'customer',
        )

    def validate_progress(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('نسبة الإنجاز يجب أن تكون بين 0 و 100')
        return value


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed project serializer with tasks and expenses."""

    manager_name = serializers.CharField(source='manager.username', read_only=True, default='')
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    remaining_budget = serializers.SerializerMethodField()
    budget_usage_percent = serializers.SerializerMethodField()
    tasks = ProjectTaskListSerializer(many=True, read_only=True)
    expenses = ProjectExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'name_en', 'description', 'status', 'status_display',
            'priority', 'priority_display', 'start_date', 'end_date',
            'actual_end_date', 'budget', 'spent', 'remaining_budget',
            'budget_usage_percent', 'progress', 'manager', 'manager_name',
            'customer', 'customer_name', 'is_active', 'created_by',
            'tasks', 'expenses', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'spent', 'created_by', 'created_at', 'updated_at')

    def get_remaining_budget(self, obj):
        return obj.remaining_budget

    def get_budget_usage_percent(self, obj):
        return obj.budget_usage_percent


# =============================================
# Project Stats Serializer
# =============================================

class ProjectStatsSerializer(serializers.Serializer):
    """Serializer for projects dashboard statistics."""

    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_tasks = serializers.IntegerField()


# =============================================
# Gantt Task Serializer
# =============================================

class GanttTaskSerializer(serializers.ModelSerializer):
    """مسلسل لعرض بيانات المهمة في مخطط جانت."""

    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    depends_on = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True,
    )
    progress = serializers.SerializerMethodField()

    class Meta:
        model = ProjectTask
        fields = (
            'id', 'title', 'status', 'status_display', 'priority',
            'priority_display', 'start_date', 'due_date', 'assigned_to',
            'assigned_to_name', 'depends_on', 'progress',
            'estimated_hours', 'actual_hours',
        )

    def get_progress(self, obj):
        """حساب نسبة الإنجاز بناءً على الحالة أو المهام الفرعية."""
        if obj.status == 'done':
            return 100
        elif obj.status == 'cancelled':
            return 0
        elif obj.status == 'review':
            return 90
        elif obj.status == 'in_progress':
            return 50
        else:
            return 0


# =============================================
# ProjectPhase Serializers
# =============================================

class ProjectPhaseListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    phase_type_display = serializers.CharField(source='get_phase_type_display', read_only=True)

    class Meta:
        model = ProjectPhase
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProjectPhaseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = ('project', 'name', 'phase_type', 'status', 'start_date', 'end_date', 'progress', 'order', 'description')


# =============================================
# ProjectMilestone Serializers
# =============================================

class ProjectMilestoneListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProjectMilestone
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'completed_at')


class ProjectMilestoneCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = ('project', 'phase', 'name', 'due_date', 'status', 'description')


# =============================================
# BudgetItem Serializers
# =============================================

class BudgetItemListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    variance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    variance_percent = serializers.SerializerMethodField()

    class Meta:
        model = BudgetItem
        fields = '__all__'
        read_only_fields = ('id', 'actual_amount', 'variance', 'created_at', 'updated_at')

    def get_variance_percent(self, obj):
        if obj.planned_amount > 0:
            return round(((obj.actual_amount - obj.planned_amount) / obj.planned_amount) * 100, 1)
        return 0


class BudgetItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItem
        fields = ('project', 'category', 'name', 'planned_amount', 'description')


# =============================================
# ProjectRisk Serializers
# =============================================

class ProjectRiskListSerializer(serializers.ModelSerializer):
    risk_score = serializers.IntegerField(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    response_strategy_display = serializers.CharField(source='get_response_strategy_display', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True, default='')

    class Meta:
        model = ProjectRisk
        fields = '__all__'
        read_only_fields = ('id', 'risk_score', 'created_at', 'updated_at', 'resolved_at')


class ProjectRiskCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRisk
        fields = ('project', 'risk_name', 'category', 'probability', 'impact', 'status', 'response_strategy', 'response_plan', 'owner', 'due_date', 'notes')

    def validate_probability(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('الاحتمالية يجب أن تكون بين 1 و 5')
        return value

    def validate_impact(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('التأثير يجب أن يكون بين 1 و 5')
        return value


# =============================================
# TimeEntry Serializers
# =============================================

class TimeEntryListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True, default='')
    task_title = serializers.CharField(source='task.title', read_only=True, default='')
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = TimeEntry
        fields = '__all__'
        read_only_fields = ('id', 'total_amount', 'created_at', 'updated_at')


class TimeEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = ('project', 'task', 'user', 'date', 'hours', 'description', 'billable', 'hourly_rate')

    def validate_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError('الساعات يجب أن تكون أكبر من صفر')
        if value > 24:
            raise serializers.ValidationError('الساعات لا يمكن أن تتجاوز 24 في اليوم')
        return value


# =============================================
# ProjectContract Serializers
# =============================================

class ProjectContractListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')

    class Meta:
        model = ProjectContract
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProjectContractCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContract
        fields = ('project', 'contract_number', 'customer', 'contract_type', 'total_value', 'start_date', 'end_date', 'payment_terms', 'billing_schedule', 'status', 'notes')


# =============================================
# ProjectDocument Serializers
# =============================================

class ProjectDocumentListSerializer(serializers.ModelSerializer):
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, default='')

    class Meta:
        model = ProjectDocument
        fields = '__all__'
        read_only_fields = ('id', 'version', 'uploaded_by', 'created_at', 'updated_at')


class ProjectDocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = ('project', 'title', 'doc_type', 'file', 'description', 'version')
