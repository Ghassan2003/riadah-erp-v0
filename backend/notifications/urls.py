"""
مسارات URL لنظام الإشعارات - نظام ERP.
"""

from django.urls import path
from .views import (
    NotificationListView,
    NotificationUnreadCountView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationFilteredListAPIView,
    NotificationDetailView,
    NotificationDeleteView,
    NotificationBulkDeleteView,
    NotificationStatsView,
    NotificationAdminCreateView,
    NotificationCleanupView,
)

urlpatterns = [
    # الموجودة
    path('', NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    path('<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    # الجديدة
    path('filtered/', NotificationFilteredListAPIView.as_view(), name='notification-filtered'),
    path('<int:pk>/detail/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/delete/', NotificationDeleteView.as_view(), name='notification-delete'),
    path('bulk-delete/', NotificationBulkDeleteView.as_view(), name='notification-bulk-delete'),
    path('stats/', NotificationStatsView.as_view(), name='notification-stats'),
    path('admin/create/', NotificationAdminCreateView.as_view(), name='notification-admin-create'),
    path('admin/cleanup/', NotificationCleanupView.as_view(), name='notification-cleanup'),
]
