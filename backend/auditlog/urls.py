from django.urls import path
from .views import AuditLogListView, AuditLogStatsView, AuditLogClearView

urlpatterns = [
    path('', AuditLogListView.as_view(), name='audit-log-list'),
    path('stats/', AuditLogStatsView.as_view(), name='audit-log-stats'),
    path('clear/', AuditLogClearView.as_view(), name='audit-log-clear'),
]
