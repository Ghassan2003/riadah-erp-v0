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

from .models import Project, ProjectTask, TaskComment, ProjectExpense
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
            return [permissions.IsAdminUser]
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
            return [permissions.IsAdminUser]
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
        return Response({'message': 'تم حذف المشروع بنجاح'})


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
            return [permissions.IsAdminUser]
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
            return [permissions.IsAdminUser]
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
        return Response({'message': 'تم إلغاء المهمة بنجاح'})


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
        # Filter by task
        task_param = self.request.query_params.get('task')
        if task_param:
            queryset = queryset.filter(task_id=task_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(
            task_id=request.data.get('task'),
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
        comment.delete()
        return Response({'message': 'تم حذف التعليق بنجاح'})


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
            return [permissions.IsAdminUser]
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
        return Response({'message': 'تم حذف المصروف بنجاح'})


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
