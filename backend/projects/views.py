"""
API views for the Projects module.
Handles Project CRUD, ProjectTask management, TaskComment, and ProjectExpense tracking.
"""

from rest_framework import generics, status, permissions, filters, views
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, Value
from django.db.models.functions import Coalesce
from django.db.models import DecimalField
from django.utils import timezone

from .models import (
    Project, ProjectTask, TaskComment, ProjectExpense,
    ProjectPhase, ProjectMilestone, BudgetItem, ProjectRisk,
    TimeEntry, ProjectContract, ProjectDocument,
)
from .serializers import (
    ProjectListSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    ProjectDetailSerializer,
    ProjectTaskListSerializer,
    ProjectTaskCreateSerializer,
    ProjectTaskUpdateSerializer,
    TaskCommentSerializer,
    TaskCommentCreateSerializer,
    ProjectExpenseSerializer,
    ProjectExpenseCreateSerializer,
    ProjectStatsSerializer,
    GanttTaskSerializer,
    ProjectPhaseListSerializer,
    ProjectPhaseCreateUpdateSerializer,
    ProjectMilestoneListSerializer,
    ProjectMilestoneCreateUpdateSerializer,
    BudgetItemListSerializer,
    BudgetItemCreateSerializer,
    ProjectRiskListSerializer,
    ProjectRiskCreateUpdateSerializer,
    TimeEntryListSerializer,
    TimeEntryCreateSerializer,
    ProjectContractListSerializer,
    ProjectContractCreateUpdateSerializer,
    ProjectDocumentListSerializer,
    ProjectDocumentCreateSerializer,
)


# =============================================
# Project Views
# =============================================

class ProjectListView(generics.ListCreateAPIView):
    """GET: List projects. POST: Create project."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en', 'description']
    ordering_fields = ['name', 'status', 'priority', 'start_date', 'budget', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectCreateSerializer
        return ProjectListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Project.objects.select_related('manager', 'customer')
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        # Filter by priority
        priority_param = self.request.query_params.get('priority')
        if priority_param:
            queryset = queryset.filter(priority=priority_param)
        # Filter by manager
        manager_param = self.request.query_params.get('manager')
        if manager_param:
            queryset = queryset.filter(manager_id=manager_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء المشروع بنجاح',
            'project': ProjectDetailSerializer(project).data,
        }, status=status.HTTP_201_CREATED)


class ProjectDetailView(generics.RetrieveUpdateAPIView):
    """GET: Project details. PATCH: Update project (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectUpdateSerializer
        return ProjectDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Project.objects.select_related(
            'manager', 'customer', 'created_by'
        ).prefetch_related('tasks', 'expenses')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        return Response({
            'message': 'تم تحديث المشروع بنجاح',
            'project': ProjectDetailSerializer(project).data,
        })


class ProjectDeleteView(views.APIView):
    """DELETE: Soft-delete a project (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response(
                {'error': 'المشروع غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        project.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# ProjectTask Views
# =============================================

class ProjectTaskListView(generics.ListCreateAPIView):
    """GET: List tasks. POST: Create task."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['status', 'priority', 'due_date', 'created_at']
    ordering = ['priority', 'due_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectTaskCreateSerializer
        return ProjectTaskListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProjectTask.objects.select_related('project', 'assigned_to', 'created_by')
        # Filter by project
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        # Filter by assigned user
        assigned_param = self.request.query_params.get('assigned_to')
        if assigned_param:
            queryset = queryset.filter(assigned_to_id=assigned_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء المهمة بنجاح',
            'task': ProjectTaskListSerializer(task).data,
        }, status=status.HTTP_201_CREATED)


class ProjectTaskDetailView(generics.RetrieveUpdateAPIView):
    """GET: Task details. PATCH: Update task (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectTaskUpdateSerializer
        return ProjectTaskListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ProjectTask.objects.select_related('project', 'assigned_to', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        # Auto-set completed_at when status changes to done
        if task.status == 'done' and not task.completed_at:
            task.completed_at = timezone.now()
            task.save(update_fields=['completed_at'])

        return Response({
            'message': 'تم تحديث المهمة بنجاح',
            'task': ProjectTaskListSerializer(task).data,
        })


class ProjectTaskDeleteView(views.APIView):
    """DELETE: Cancel a task by setting status to cancelled (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            task = ProjectTask.objects.get(pk=pk)
        except ProjectTask.DoesNotExist:
            return Response(
                {'error': 'المهمة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        task.status = 'cancelled'
        task.save(update_fields=['status', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# TaskComment Views
# =============================================

class TaskCommentListView(generics.ListCreateAPIView):
    """GET: List task comments. POST: Create task comment."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCommentCreateSerializer
        return TaskCommentSerializer

    def get_queryset(self):
        queryset = TaskComment.objects.select_related('task', 'created_by')
        # Filter by task (from URL kwargs first, then query param fallback)
        task_id = self.kwargs.get('task_id') or self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Get task_id from request body or URL kwargs
        task_id = request.data.get('task') or self.kwargs.get('task_id')
        if not task_id:
            return Response(
                {'error': 'معرف المهمة (task) مطلوب'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ProjectTask.objects.get(pk=task_id)
        except ProjectTask.DoesNotExist:
            return Response(
                {'error': 'المهمة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        comment = serializer.save(
            task_id=task_id,
            created_by=request.user,
        )
        return Response({
            'message': 'تم إضافة التعليق بنجاح',
            'comment': TaskCommentSerializer(comment).data,
        }, status=status.HTTP_201_CREATED)


class TaskCommentDetailView(generics.RetrieveAPIView):
    """GET: Task comment detail."""

    serializer_class = TaskCommentSerializer

    def get_queryset(self):
        return TaskComment.objects.select_related('task', 'created_by')


class TaskCommentUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a task comment."""

    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaskComment.objects.select_related('task', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.created_by != request.user and request.user.role != 'admin':
            return Response({'error': 'ليس لديك صلاحية تعديل هذا التعليق'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response({
            'message': 'تم تحديث التعليق بنجاح',
            'comment': TaskCommentSerializer(comment).data,
        })


class TaskCommentDeleteView(views.APIView):
    """DELETE: Delete a task comment."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            comment = TaskComment.objects.get(pk=pk)
        except TaskComment.DoesNotExist:
            return Response(
                {'error': 'التعليق غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if comment.created_by != request.user and request.user.role != 'admin':
            return Response({'error': 'ليس لديك صلاحية حذف هذا التعليق'}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# ProjectExpense Views
# =============================================

class ProjectExpenseListView(generics.ListCreateAPIView):
    """GET: List project expenses. POST: Create project expense."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'amount', 'expense_type', 'created_at']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectExpenseCreateSerializer
        return ProjectExpenseSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProjectExpense.objects.select_related('project', 'created_by')
        # Filter by project
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        # Filter by expense type
        type_param = self.request.query_params.get('expense_type')
        if type_param:
            queryset = queryset.filter(expense_type=type_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إضافة المصروف بنجاح',
            'expense': ProjectExpenseSerializer(expense).data,
        }, status=status.HTTP_201_CREATED)


class ProjectExpenseDetailView(generics.RetrieveAPIView):
    """GET: Project expense detail."""

    serializer_class = ProjectExpenseSerializer

    def get_queryset(self):
        return ProjectExpense.objects.select_related('project', 'created_by')


class ProjectExpenseUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a project expense (admin only)."""

    serializer_class = ProjectExpenseSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return ProjectExpense.objects.select_related('project', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()
        return Response({
            'message': 'تم تحديث المصروف بنجاح',
            'expense': ProjectExpenseSerializer(expense).data,
        })


class ProjectExpenseDeleteView(views.APIView):
    """DELETE: Delete expense and recalculate project spent (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            expense = ProjectExpense.objects.select_related('project').get(pk=pk)
        except ProjectExpense.DoesNotExist:
            return Response(
                {'error': 'المصروف غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        project = expense.project
        expense.delete()
        # Recalculate project spent after deletion
        project.recalculate_spent()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# Project Stats View
# =============================================

class ProjectStatsView(generics.GenericAPIView):
    """GET: Projects statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectStatsSerializer

    def get(self, request):
        today = timezone.now().date()

        stats = {
            'total_projects': Project.objects.filter(is_active=True).count(),
            'active_projects': Project.objects.filter(is_active=True, status='active').count(),
            'completed_projects': Project.objects.filter(is_active=True, status='completed').count(),
            'total_budget': Project.objects.filter(is_active=True).aggregate(
                total=Coalesce(Sum('budget'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'total_spent': Project.objects.filter(is_active=True).aggregate(
                total=Coalesce(Sum('spent'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'overdue_tasks': ProjectTask.objects.filter(
                status__in=('todo', 'in_progress'),
                due_date__lt=today,
            ).count(),
        }

        serializer = self.get_serializer(stats)
        return Response(serializer.data)


# =============================================
# Excel Export Views
# =============================================

class ProjectExportView(views.APIView):
    """GET: Export projects to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Project.objects.select_related('manager', 'customer')
        columns = [
            ('name', 'اسم المشروع', 30),
            ('status', 'الحالة', 15),
            ('priority', 'الأولوية', 15),
            ('start_date', 'تاريخ البداية', 15),
            ('end_date', 'تاريخ النهاية', 15),
            ('budget', 'الميزانية', 15),
            ('spent', 'المصروف', 15),
            ('progress', 'نسبة الإنجاز %', 15),
            ('manager', 'مدير المشروع', 20),
            ('customer', 'العميل', 20),
            ('is_active', 'نشط', 10),
        ]
        data = []
        for p in queryset:
            data.append({
                'name': p.name,
                'status': p.get_status_display(),
                'priority': p.get_priority_display(),
                'start_date': str(p.start_date) if p.start_date else '',
                'end_date': str(p.end_date) if p.end_date else '',
                'budget': str(p.budget),
                'spent': str(p.spent),
                'progress': p.progress,
                'manager': p.manager.get_full_name() if p.manager else '',
                'customer': p.customer.name if p.customer else '',
                'is_active': p.is_active,
            })
        return export_to_excel(data, columns, 'المشاريع', 'projects.xlsx')


# =============================================
# Gantt Data View
# =============================================

class GanttDataView(views.APIView):
    """GET: بيانات مخطط جانت لمشروع محدد."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': 'معرف المشروع (project_id) مطلوب'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'المشروع غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        tasks = ProjectTask.objects.filter(
            project_id=project_id,
        ).select_related(
            'assigned_to',
        ).prefetch_related(
            'depends_on',
        ).order_by('start_date', 'due_date', 'priority')

        serializer = GanttTaskSerializer(tasks, many=True)
        return Response(serializer.data)


# =============================================
# ProjectPhase Views
# =============================================

class ProjectPhaseListView(generics.ListCreateAPIView):
    """GET: قائمة المراحل. POST: إنشاء مرحلة جديدة."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'start_date', 'status', 'created_at']
    ordering = ['order', 'start_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectPhaseCreateUpdateSerializer
        return ProjectPhaseListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProjectPhase.objects.select_related('project')
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phase = serializer.save()
        return Response({
            'message': 'تم إنشاء المرحلة بنجاح',
            'phase': ProjectPhaseListSerializer(phase).data,
        }, status=status.HTTP_201_CREATED)


class ProjectPhaseDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل المرحلة. PATCH: تحديث المرحلة."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectPhaseCreateUpdateSerializer
        return ProjectPhaseListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ProjectPhase.objects.select_related('project')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        phase = serializer.save()
        return Response({
            'message': 'تم تحديث المرحلة بنجاح',
            'phase': ProjectPhaseListSerializer(phase).data,
        })


class ProjectPhaseDeleteView(views.APIView):
    """DELETE: حذف مرحلة (مدير فقط)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            phase = ProjectPhase.objects.get(pk=pk)
        except ProjectPhase.DoesNotExist:
            return Response(
                {'error': 'المرحلة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        phase.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# ProjectMilestone Views
# =============================================

class ProjectMilestoneListView(generics.ListCreateAPIView):
    """GET: قائمة المعالم. POST: إنشاء معلم جديد."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['due_date', 'status', 'created_at']
    ordering = ['due_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectMilestoneCreateUpdateSerializer
        return ProjectMilestoneListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProjectMilestone.objects.select_related('project', 'phase')
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        milestone = serializer.save()
        return Response({
            'message': 'تم إنشاء المعلم بنجاح',
            'milestone': ProjectMilestoneListSerializer(milestone).data,
        }, status=status.HTTP_201_CREATED)


class ProjectMilestoneDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل المعلم. PATCH: تحديث المعلم."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectMilestoneCreateUpdateSerializer
        return ProjectMilestoneListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ProjectMilestone.objects.select_related('project', 'phase')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        milestone = serializer.save()

        # Auto-set completed_at when status changes to achieved
        if milestone.status == 'achieved' and not milestone.completed_at:
            milestone.completed_at = timezone.now()
            milestone.save(update_fields=['completed_at'])

        return Response({
            'message': 'تم تحديث المعلم بنجاح',
            'milestone': ProjectMilestoneListSerializer(milestone).data,
        })


class ProjectMilestoneDeleteView(views.APIView):
    """DELETE: حذف معلم (مدير فقط)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            milestone = ProjectMilestone.objects.get(pk=pk)
        except ProjectMilestone.DoesNotExist:
            return Response(
                {'error': 'المعلم غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        milestone.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# BudgetItem Views
# =============================================

class BudgetItemListView(generics.ListCreateAPIView):
    """GET: قائمة بنود الميزانية. POST: إنشاء بند جديد."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['category', 'name', 'planned_amount', 'actual_amount', 'created_at']
    ordering = ['category', 'name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BudgetItemCreateSerializer
        return BudgetItemListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = BudgetItem.objects.select_related('project')
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        category_param = self.request.query_params.get('category')
        if category_param:
            queryset = queryset.filter(category=category_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({
            'message': 'تم إنشاء بند الميزانية بنجاح',
            'budget_item': BudgetItemListSerializer(item).data,
        }, status=status.HTTP_201_CREATED)


class BudgetItemDetailView(generics.RetrieveAPIView):
    """GET: تفاصيل بند الميزانية."""

    serializer_class = BudgetItemListSerializer

    def get_queryset(self):
        return BudgetItem.objects.select_related('project')


class BudgetItemDeleteView(views.APIView):
    """DELETE: حذف بند ميزانية (مدير فقط)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            item = BudgetItem.objects.get(pk=pk)
        except BudgetItem.DoesNotExist:
            return Response(
                {'error': 'بند الميزانية غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# ProjectBudgetStats View
# =============================================

class ProjectBudgetStatsView(views.APIView):
    """GET: ملخص الميزانية لمشروع (مخطط مقابل فعلي لكل فئة)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'معرف المشروع مطلوب'}, status=400)

        try:
            Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'المشروع غير موجود'}, status=404)

        budget_items = BudgetItem.objects.filter(project_id=project_id)

        # Totals
        total_planned = budget_items.aggregate(
            total=Coalesce(Sum('planned_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total']
        total_actual = budget_items.aggregate(
            total=Coalesce(Sum('actual_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total']
        total_variance = total_planned - total_actual
        variance_percent = round((total_variance / total_planned) * 100, 1) if total_planned > 0 else 0

        # Group by category
        category_summary = budget_items.values('category').annotate(
            planned=Coalesce(Sum('planned_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
            actual=Coalesce(Sum('actual_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
            items_count=Count('id'),
        ).order_by('category')

        # Add display names
        category_choices = dict(BudgetItem.CATEGORY_CHOICES)
        categories_data = []
        for cat in category_summary:
            categories_data.append({
                'category': cat['category'],
                'category_display': category_choices.get(cat['category'], cat['category']),
                'planned': cat['planned'],
                'actual': cat['actual'],
                'variance': cat['planned'] - cat['actual'],
                'items_count': cat['items_count'],
            })

        return Response({
            'project_id': int(project_id),
            'total_planned': total_planned,
            'total_actual': total_actual,
            'total_variance': total_variance,
            'variance_percent': variance_percent,
            'categories': categories_data,
        })


# =============================================
# ProjectRisk Views
# =============================================

class ProjectRiskListView(generics.ListCreateAPIView):
    """GET: قائمة المخاطر. POST: إنشاء خطر جديد."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['risk_name', 'response_plan', 'notes']
    ordering_fields = ['status', 'category', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectRiskCreateUpdateSerializer
        return ProjectRiskListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProjectRisk.objects.select_related('project', 'owner')
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        category_param = self.request.query_params.get('category')
        if category_param:
            queryset = queryset.filter(category=category_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        risk = serializer.save()
        return Response({
            'message': 'تم إنشاء الخطر بنجاح',
            'risk': ProjectRiskListSerializer(risk).data,
        }, status=status.HTTP_201_CREATED)


class ProjectRiskDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل الخطر. PATCH: تحديث الخطر."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectRiskCreateUpdateSerializer
        return ProjectRiskListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ProjectRisk.objects.select_related('project', 'owner')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        risk = serializer.save()

        # Auto-set resolved_at when status changes to closed or accepted
        if risk.status in ('closed', 'accepted') and not risk.resolved_at:
            risk.resolved_at = timezone.now()
            risk.save(update_fields=['resolved_at'])

        return Response({
            'message': 'تم تحديث الخطر بنجاح',
            'risk': ProjectRiskListSerializer(risk).data,
        })


class ProjectRiskDeleteView(views.APIView):
    """DELETE: حذف خطر (مدير فقط)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            risk = ProjectRisk.objects.get(pk=pk)
        except ProjectRisk.DoesNotExist:
            return Response(
                {'error': 'الخطر غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        risk.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# RiskMatrix View
# =============================================

class RiskMatrixView(views.APIView):
    """GET: بيانات مصفوفة المخاطر لمشروع محدد (مصفوفة 5×5)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'معرف المشروع مطلوب'}, status=400)

        try:
            Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'المشروع غير موجود'}, status=404)

        risks = ProjectRisk.objects.filter(project_id=project_id)

        # Build 5x5 matrix (probability x impact)
        matrix = [[0] * 5 for _ in range(5)]
        risk_details = {f'{p}-{i}': [] for p in range(1, 6) for i in range(1, 6)}

        for risk in risks:
            p = risk.probability
            i = risk.impact
            if 1 <= p <= 5 and 1 <= i <= 5:
                matrix[p - 1][i - 1] += 1
                risk_details[f'{p}-{i}'].append({
                    'id': risk.id,
                    'risk_name': risk.risk_name,
                    'category_display': risk.get_category_display(),
                    'status_display': risk.get_status_display(),
                    'risk_score': risk.risk_score,
                })

        # Summary stats
        total_risks = risks.count()
        high_risks = risks.filter(risk_score__gte=15).count()
        medium_risks = risks.filter(risk_score__gte=6, risk_score__lte=14).count()
        low_risks = risks.filter(risk_score__lte=5).count()

        return Response({
            'project_id': int(project_id),
            'matrix': matrix,
            'risk_details': risk_details,
            'summary': {
                'total_risks': total_risks,
                'high_risks': high_risks,
                'medium_risks': medium_risks,
                'low_risks': low_risks,
            },
        })


# =============================================
# TimeEntry Views
# =============================================

class TimeEntryListView(generics.ListCreateAPIView):
    """GET: قائمة سجلات الوقت. POST: إنشاء سجل وقت جديد."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['-date', 'user', 'project', 'created_at']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TimeEntryCreateSerializer
        return TimeEntryListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = TimeEntry.objects.select_related('project', 'task', 'user')
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        user_param = self.request.query_params.get('user')
        if user_param:
            queryset = queryset.filter(user_id=user_param)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        return Response({
            'message': 'تم إنشاء سجل الوقت بنجاح',
            'time_entry': TimeEntryListSerializer(entry).data,
        }, status=status.HTTP_201_CREATED)


class TimeEntryDetailView(generics.RetrieveAPIView):
    """GET: تفاصيل سجل الوقت."""

    serializer_class = TimeEntryListSerializer

    def get_queryset(self):
        return TimeEntry.objects.select_related('project', 'task', 'user')


class TimeEntryDeleteView(views.APIView):
    """DELETE: حذف سجل وقت (مدير فقط)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            entry = TimeEntry.objects.get(pk=pk)
        except TimeEntry.DoesNotExist:
            return Response(
                {'error': 'سجل الوقت غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# TimeEntryReport View
# =============================================

class TimeEntryReportView(views.APIView):
    """GET: تقرير الوقت لمشروع محدد (إجمالي الساعات لكل مستخدم وكل مهمة)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'معرف المشروع مطلوب'}, status=400)

        try:
            Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'المشروع غير موجود'}, status=404)

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        queryset = TimeEntry.objects.filter(project_id=project_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Total hours per user
        per_user = queryset.values('user', 'user__username').annotate(
            total_hours=Coalesce(Sum('hours'), Value(0), output_field=DecimalField(max_digits=8, decimal_places=2)),
            total_amount=Coalesce(
                Sum('hours', output_field=DecimalField(max_digits=14, decimal_places=2))
                * Coalesce(Sum('hourly_rate'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            entries_count=Count('id'),
        ).order_by('-total_hours')

        user_report = []
        for u in per_user:
            user_report.append({
                'user_id': u['user'],
                'user_name': u['user__username'],
                'total_hours': u['total_hours'],
                'entries_count': u['entries_count'],
            })

        # Total hours per task
        per_task = queryset.exclude(task__isnull=True).values('task', 'task__title').annotate(
            total_hours=Coalesce(Sum('hours'), Value(0), output_field=DecimalField(max_digits=8, decimal_places=2)),
            entries_count=Count('id'),
        ).order_by('-total_hours')

        task_report = []
        for t in per_task:
            task_report.append({
                'task_id': t['task'],
                'task_title': t['task__title'],
                'total_hours': t['total_hours'],
                'entries_count': t['entries_count'],
            })

        # Overall totals
        total_hours = queryset.aggregate(
            total=Coalesce(Sum('hours'), Value(0), output_field=DecimalField(max_digits=8, decimal_places=2))
        )['total']
        total_billable = queryset.filter(billable=True).aggregate(
            total=Coalesce(Sum('hours'), Value(0), output_field=DecimalField(max_digits=8, decimal_places=2))
        )['total']
        total_entries = queryset.count()

        return Response({
            'project_id': int(project_id),
            'total_hours': total_hours,
            'total_billable_hours': total_billable,
            'total_entries': total_entries,
            'per_user': user_report,
            'per_task': task_report,
        })


# =============================================
# ProjectContract Views
# =============================================

class ProjectContractListView(generics.ListCreateAPIView):
    """GET: قائمة العقود. POST: إنشاء عقد جديد."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['contract_number', 'notes']
    ordering_fields = ['contract_number', 'status', 'start_date', 'total_value', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectContractCreateUpdateSerializer
        return ProjectContractListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProjectContract.objects.select_related('project', 'customer')
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()
        return Response({
            'message': 'تم إنشاء العقد بنجاح',
            'contract': ProjectContractListSerializer(contract).data,
        }, status=status.HTTP_201_CREATED)


class ProjectContractDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل العقد. PATCH: تحديث العقد."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectContractCreateUpdateSerializer
        return ProjectContractListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ProjectContract.objects.select_related('project', 'customer')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()
        return Response({
            'message': 'تم تحديث العقد بنجاح',
            'contract': ProjectContractListSerializer(contract).data,
        })


class ProjectContractDeleteView(views.APIView):
    """DELETE: حذف عقد (مدير فقط)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            contract = ProjectContract.objects.get(pk=pk)
        except ProjectContract.DoesNotExist:
            return Response(
                {'error': 'العقد غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        contract.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# ProjectDocument Views
# =============================================

class ProjectDocumentListView(generics.ListCreateAPIView):
    """GET: قائمة المستندات. POST: إنشاء مستند جديد."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['doc_type', 'title', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectDocumentCreateSerializer
        return ProjectDocumentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProjectDocument.objects.select_related('project', 'uploaded_by')
        project_param = self.request.query_params.get('project')
        if project_param:
            queryset = queryset.filter(project_id=project_param)
        doc_type_param = self.request.query_params.get('doc_type')
        if doc_type_param:
            queryset = queryset.filter(doc_type=doc_type_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(uploaded_by=request.user)
        return Response({
            'message': 'تم إنشاء المستند بنجاح',
            'document': ProjectDocumentListSerializer(document).data,
        }, status=status.HTTP_201_CREATED)


class ProjectDocumentDetailView(generics.RetrieveAPIView):
    """GET: تفاصيل المستند."""

    serializer_class = ProjectDocumentListSerializer

    def get_queryset(self):
        return ProjectDocument.objects.select_related('project', 'uploaded_by')


class ProjectDocumentDeleteView(views.APIView):
    """DELETE: حذف مستند (مدير فقط)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            document = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            return Response(
                {'error': 'المستند غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
