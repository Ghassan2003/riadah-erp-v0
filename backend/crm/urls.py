"""
أنماط الروابط (URL patterns) لوحدة إدارة علاقات العملاء (CRM).
"""

from django.urls import path
from . import views

urlpatterns = [
    # إحصائيات إدارة علاقات العملاء
    path('stats/', views.CRMStatsView.as_view(), name='crm-stats'),

    # جهات الاتصال
    path('contacts/', views.ContactListView.as_view(), name='crm-contacts'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='crm-contact-detail'),

    # فرص البيع
    path('leads/', views.LeadListView.as_view(), name='crm-leads'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='crm-lead-detail'),
    path('leads/<int:pk>/change-status/', views.LeadChangeStatusView.as_view(), name='crm-lead-change-status'),

    # أنشطة الفرص
    path('leads/<int:pk>/activities/', views.LeadActivityListView.as_view(), name='crm-lead-activities'),
    path('leads/activities/<int:pk>/complete/', views.LeadActivityCompleteView.as_view(), name='crm-lead-activity-complete'),

    # شرائح العملاء
    path('segments/', views.CustomerSegmentListView.as_view(), name='crm-segments'),
    path('segments/<int:pk>/', views.CustomerSegmentDetailView.as_view(), name='crm-segment-detail'),

    # الحملات التسويقية
    path('campaigns/', views.CampaignListView.as_view(), name='crm-campaigns'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='crm-campaign-detail'),
    path('campaigns/<int:pk>/change-status/', views.CampaignChangeStatusView.as_view(), name='crm-campaign-change-status'),

    # أنشطة الحملات
    path('campaigns/<int:pk>/activities/', views.CampaignActivityListView.as_view(), name='crm-campaign-activities'),

    # تصدير
    path('export/', views.CRMExportView.as_view(), name='crm-export'),
]
