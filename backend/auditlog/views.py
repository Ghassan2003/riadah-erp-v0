from rest_framework import generics, permissions, views, filters
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import AuditLog
from .serializers import AuditLogListSerializer
from users.permissions import IsAdmin


class AuditLogListView(generics.ListAPIView):
    """GET: قائمة سجلات التدقيق مع التصفية (للمسؤولين فقط)."""

    queryset = AuditLog.objects.select_related('user')
    serializer_class = AuditLogListSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'model_name', 'object_repr', 'action', 'ip_address']
    ordering_fields = ['created_at', 'user', 'model_name', 'action']
    ordering = ['-created_at']
    pagination_class = None

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        # Filter by action type
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        # Filter by model
        model = self.request.query_params.get('model')
        if model:
            queryset = queryset.filter(model_name=model)
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to apply result limit AFTER ordering/filtering."""
        queryset = self.filter_queryset(self.get_queryset())
        # Limit results to 500 after all filtering and ordering is applied
        queryset = queryset[:500]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AuditLogStatsView(views.APIView):
    """GET: إحصائيات سجلات التدقيق."""

    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.now()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)

        stats = {
            'total_logs': AuditLog.objects.count(),
            'today_logs': AuditLog.objects.filter(created_at__date=today.date()).count(),
            'last_7_days_logs': AuditLog.objects.filter(created_at__gte=last_7_days).count(),
            'last_30_days_logs': AuditLog.objects.filter(created_at__gte=last_30_days).count(),
            'action_breakdown': dict(
                AuditLog.objects.values('action').annotate(count=Count('id')).order_by('-count')[:10]
            ),
            'model_breakdown': dict(
                AuditLog.objects.values('model_name').annotate(count=Count('id')).order_by('-count')[:10]
            ),
            'most_active_users': list(
                AuditLog.objects.filter(user__isnull=False)
                .values('user__username')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            ),
        }
        return Response(stats)


class AuditLogClearView(views.APIView):
    """DELETE: حذف سجلات التدقيق القديمة (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def delete(self, request):
        days = int(request.query_params.get('days', 90))
        cutoff = timezone.now() - timedelta(days=days)
        deleted_count, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
        return Response({
            'message': f'تم حذف {deleted_count} سجل تدقيق أقدم من {days} يوم',
            'deleted_count': deleted_count,
        })
