"""URLs for maintenance app - Operations & Maintenance."""

from django.urls import path
from . import views

urlpatterns = [
    # ===== النسخ الاحتياطي =====
    path('maintenance/backups/', views.BackupListView.as_view(), name='backup-list'),
    path('maintenance/backups/create/', views.BackupCreateView.as_view(), name='backup-create'),
    path('maintenance/backups/stats/', views.BackupStatsView.as_view(), name='backup-stats'),
    path('maintenance/backups/<int:pk>/download/', views.BackupDownloadView.as_view(), name='backup-download'),
    path('maintenance/backups/<int:pk>/restore/', views.BackupRestoreView.as_view(), name='backup-restore'),
    path('maintenance/backups/<int:pk>/delete/', views.BackupDeleteView.as_view(), name='backup-delete'),

    # ===== سجل الأخطاء =====
    path('maintenance/errors/', views.ErrorLogListView.as_view(), name='error-log-list'),
    path('maintenance/errors/stats/', views.ErrorLogStatsView.as_view(), name='error-log-stats'),
    path('maintenance/errors/<int:pk>/', views.ErrorLogDetailView.as_view(), name='error-log-detail'),
    path('maintenance/errors/<int:pk>/resolve/', views.ErrorLogResolveView.as_view(), name='error-log-resolve'),
    path('maintenance/errors/batch-resolve/', views.ErrorLogBatchResolveView.as_view(), name='error-log-batch-resolve'),
    path('maintenance/errors/clear/', views.ErrorLogClearView.as_view(), name='error-log-clear'),

    # ===== إعدادات النظام =====
    path('maintenance/settings/', views.SystemSettingsView.as_view(), name='system-settings'),
    path('maintenance/settings/number-preview/', views.AutoNumberPreviewView.as_view(), name='number-preview'),

    # ===== المهام المجدولة =====
    path('maintenance/cron-jobs/', views.CronJobListView.as_view(), name='cron-job-list'),
    path('maintenance/cron-jobs/create/', views.CronJobCreateView.as_view(), name='cron-job-create'),
    path('maintenance/cron-jobs/stats/', views.CronJobStatsView.as_view(), name='cron-job-stats'),
    path('maintenance/cron-jobs/<int:pk>/', views.CronJobDetailView.as_view(), name='cron-job-detail'),
    path('maintenance/cron-jobs/<int:pk>/toggle/', views.CronJobToggleView.as_view(), name='cron-job-toggle'),
    path('maintenance/cron-jobs/<int:pk>/run-now/', views.CronJobRunNowView.as_view(), name='cron-job-run-now'),
]
