"""
واجهات API لنظام الإشعارات - نظام ERP.
يوفر عرض قائمة الإشعارات، عدد غير المقروءة، وتحديد كمقروء.
"""

from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count
from .models import Notification
from .serializers import (
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationCreateSerializer,
)


# =============================================
# Existing Notification Views
# =============================================

class NotificationListView(generics.ListAPIView):
    """GET: عرض قائمة الإشعارات للمستخدم الحالي."""

    serializer_class = NotificationListSerializer
    pagination_class = None  # Return all, no pagination for notifications

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)[:50]


class NotificationUnreadCountView(views.APIView):
    """GET: عدد الإشعارات غير المقروءة."""

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})


class NotificationMarkReadView(views.APIView):
    """POST: تحديد إشعار كمقروء."""

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient=request.user)
            notif.mark_as_read()
            return Response({'message': 'تم تحديد الإشعار كمقروء'})
        except Notification.DoesNotExist:
            return Response({'error': 'الإشعار غير موجود'}, status=404)


class NotificationMarkAllReadView(views.APIView):
    """POST: تحديد جميع الإشعارات كمقروءة."""

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'تم تحديد جميع الإشعارات كمقروءة'})


# =============================================
# New Advanced Notification Views
# =============================================

class NotificationFilteredListAPIView(generics.ListAPIView):
    """GET: عرض إشعارات مع فلترة وتصنيف."""
    serializer_class = NotificationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)

        # فلترة بالنوع
        notif_type = self.request.query_params.get('type')
        if notif_type:
            qs = qs.filter(notification_type=notif_type)

        # فلترة بالحالة
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == 'true')

        # فلترة بالأولوية
        priority = self.request.query_params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        # فلترة بالتاريخ
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # ترتيب
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering in ('created_at', '-created_at', 'priority', '-priority'):
            qs = qs.order_by(ordering)

        return qs


class NotificationDetailView(views.APIView):
    """GET: تفاصيل إشعار محدد."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient=request.user)
            if not notif.is_read:
                notif.mark_as_read()
            serializer = NotificationListSerializer(notif)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response({'error': 'الإشعار غير موجود'}, status=404)


class NotificationDeleteView(views.APIView):
    """DELETE: حذف إشعار."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient=request.user)
            notif.delete()
            return Response({'message': 'تم حذف الإشعار'})
        except Notification.DoesNotExist:
            return Response({'error': 'الإشعار غير موجود'}, status=404)


class NotificationBulkDeleteView(views.APIView):
    """POST: حذف إشعارات محددة."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'لم يتم تحديد إشعارات'}, status=400)
        deleted = Notification.objects.filter(id__in=ids, recipient=request.user).delete()
        return Response({'message': f'تم حذف {deleted[0]} إشعار'})


class NotificationStatsView(views.APIView):
    """GET: إحصائيات الإشعارات."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total = Notification.objects.filter(recipient=user).count()
        unread = Notification.objects.filter(recipient=user, is_read=False).count()
        by_type = dict(
            Notification.objects.filter(recipient=user, is_read=False)
            .values_list('notification_type', flat=True)
            .annotate(count=Count('id'))
        )
        urgent = Notification.objects.filter(
            recipient=user, is_read=False, priority='urgent'
        ).count()
        return Response({
            'total': total,
            'unread': unread,
            'by_type': by_type,
            'urgent_count': urgent,
        })


class NotificationAdminCreateView(views.APIView):
    """POST: إنشاء إشعار (للمدير فقط)."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = NotificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            notif = serializer.save()
            return Response(NotificationListSerializer(notif).data, status=201)
        return Response(serializer.errors, status=400)


class NotificationCleanupView(views.APIView):
    """POST: تنظيف الإشعارات القديمة (للمدير)."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        days = request.data.get('days', 90)
        deleted = Notification.cleanup_old(days=days)
        expired = Notification.cleanup_expired()
        return Response({
            'message': 'تم التنظيف',
            'old_deleted': deleted[0],
            'expired_deleted': expired[0],
        })
