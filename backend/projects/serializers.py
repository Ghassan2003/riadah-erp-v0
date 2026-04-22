"""
Serializers for the Projects module.
Handles Project, ProjectTask, TaskComment, and ProjectExpense data transformation.
"""

from rest_framework import serializers
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from django.db.models import Value, DecimalField
from django.utils import timezone
from .models import Project, ProjectTask, TaskComment, ProjectExpense


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
        read_only_fields = ('id', 'task', 'created_at')


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
        read_only_fields = ('id', 'created_at')


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
