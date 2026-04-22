"""URLs for maintenance app - Operations & Maintenance."""

from django.urls import path
from . import views

urlpatterns = [
    # ===== النسخ الاحتياطي =====
    path('backups/', views.BackupListView.as_view(), name='backup-list'),
    path('backups/create/', views.BackupCreateView.as_view(), name='backup-create'),
    path('backups/stats/', views.BackupStatsView.as_view(), name='backup-stats'),
    path('backups/<int:pk>/download/', views.BackupDownloadView.as_view(), name='backup-download'),
    path('backups/<int:pk>/restore/', views.BackupRestoreView.as_view(), name='backup-restore'),
    path('backups/<int:pk>/delete/', views.BackupDeleteView.as_view(), name='backup-delete'),

    # ===== سجل الأخطاء =====
    path('errors/', views.ErrorLogListView.as_view(), name='error-log-list'),
    path('errors/stats/', views.ErrorLogStatsView.as_view(), name='error-log-stats'),
    path('errors/<int:pk>/', views.ErrorLogDetailView.as_view(), name='error-log-detail'),
    path('errors/<int:pk>/resolve/', views.ErrorLogResolveView.as_view(), name='error-log-resolve'),
    path('errors/batch-resolve/', views.ErrorLogBatchResolveView.as_view(), name='error-log-batch-resolve'),
    path('errors/clear/', views.ErrorLogClearView.as_view(), name='error-log-clear'),

    # ===== إعدادات النظام =====
    path('settings/', views.SystemSettingsView.as_view(), name='system-settings'),
    path('settings/number-preview/', views.AutoNumberPreviewView.as_view(), name='number-preview'),

    # ===== المهام المجدولة =====
    path('cron-jobs/', views.CronJobListView.as_view(), name='cron-job-list'),
    path('cron-jobs/create/', views.CronJobCreateView.as_view(), name='cron-job-create'),
    path('cron-jobs/stats/', views.CronJobStatsView.as_view(), name='cron-job-stats'),
    path('cron-jobs/<int:pk>/', views.CronJobDetailView.as_view(), name='cron-job-detail'),
    path('cron-jobs/<int:pk>/toggle/', views.CronJobToggleView.as_view(), name='cron-job-toggle'),
    path('cron-jobs/<int:pk>/run-now/', views.CronJobRunNowView.as_view(), name='cron-job-run-now'),
]
