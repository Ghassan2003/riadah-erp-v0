"""
Admin configuration for Projects models.
"""

from django.contrib import admin
from .models import Project, ProjectTask, TaskComment, ProjectExpense


class ProjectTaskInline(admin.TabularInline):
    """Inline editor for project tasks."""
    model = ProjectTask
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('title', 'status', 'priority', 'assigned_to', 'start_date', 'due_date', 'completed_at')


class ProjectExpenseInline(admin.TabularInline):
    """Inline editor for project expenses."""
    model = ProjectExpense
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('title', 'expense_type', 'amount', 'date', 'description', 'created_by')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'status', 'priority', 'start_date', 'end_date',
        'budget', 'spent', 'progress', 'manager', 'is_active', 'created_at',
    )
    list_filter = ('status', 'priority', 'is_active', 'created_at')
    search_fields = ('name', 'name_en', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('spent', 'created_at', 'updated_at')
    inlines = [ProjectTaskInline, ProjectExpenseInline]

    fieldsets = (
        ('معلومات المشروع', {
            'fields': ('name', 'name_en', 'description', 'status', 'priority')
        }),
        ('التواريخ', {
            'fields': ('start_date', 'end_date', 'actual_end_date')
        }),
        ('الميزانية والتقدم', {
            'fields': ('budget', 'spent', 'progress')
        }),
        ('الارتباطات', {
            'fields': ('manager', 'customer', 'created_by')
        }),
    )


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'project', 'status', 'priority',
        'assigned_to', 'due_date', 'completed_at', 'created_at',
    )
    list_filter = ('status', 'priority', 'project', 'created_at')
    search_fields = ('title', 'description', 'project__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'content_preview', 'created_by', 'created_at')
    list_filter = ('task__project', 'created_at')
    search_fields = ('content', 'task__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    def content_preview(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'المحتوى'


@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'project', 'expense_type', 'amount',
        'date', 'created_by', 'created_at',
    )
    list_filter = ('expense_type', 'project', 'date', 'created_at')
    search_fields = ('title', 'description', 'project__name')
    ordering = ('-date',)
    readonly_fields = ('created_at',)
