"""
أنماط الروابط (URL patterns) لوحدة إدارة علاقات العملاء (CRM).
"""

from django.urls import path
from . import views

urlpatterns = [
    # إحصائيات إدارة علاقات العملاء
    path('stats/', views.CRMStatsView.as_view(), name='crm-stats'),

    # الشركات / الحسابات
    path('companies/', views.CompanyListView.as_view(), name='crm-companies'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='crm-company-detail'),
    path('companies/<int:pk>/contacts/', views.CompanyContactsView.as_view(), name='crm-company-contacts'),
    path('companies/<int:pk>/stats/', views.CompanyStatsView.as_view(), name='crm-company-stats'),

    # جهات الاتصال
    path('contacts/', views.ContactListView.as_view(), name='crm-contacts'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='crm-contact-detail'),

    # فرص البيع
    path('leads/', views.LeadListView.as_view(), name='crm-leads'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='crm-lead-detail'),
    path('leads/<int:pk>/detail/', views.LeadDetailWithActivitiesView.as_view(), name='crm-lead-detail-with-activities'),
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

    # تحويل فرصة بيع إلى عميل
    path('leads/<int:pk>/convert/', views.LeadConvertToCustomerView.as_view(), name='crm-lead-convert'),

    # بيانات قمع خط المبيعات
    path('pipeline/funnel/', views.PipelineFunnelView.as_view(), name='crm-pipeline-funnel'),

    # التنبؤ بالمبيعات
    path('sales-forecast/', views.SalesForecastView.as_view(), name='crm-sales-forecast'),

    # تحليلات مراحل المبيعات
    path('sales-stage-analytics/', views.SalesStageAnalyticsView.as_view(), name='crm-sales-stage-analytics'),

    # سياسات اتفاقية مستوى الخدمة (SLA)
    path('sla-policies/', views.SLAPolicyListView.as_view(), name='crm-sla-policies'),
    path('sla-policies/<int:pk>/', views.SLAPolicyDetailView.as_view(), name='crm-sla-policy-detail'),
    path('sla-policies/<int:pk>/delete/', views.SLAPolicyDeleteView.as_view(), name='crm-sla-policy-delete'),

    # تذاكر الدعم
    path('tickets/', views.TicketListView.as_view(), name='crm-tickets'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='crm-ticket-detail'),
    path('tickets/<int:pk>/delete/', views.TicketDeleteView.as_view(), name='crm-ticket-delete'),
    path('tickets/<int:pk>/assign/', views.TicketAssignView.as_view(), name='crm-ticket-assign'),
    path('tickets/<int:pk>/resolve/', views.TicketResolveView.as_view(), name='crm-ticket-resolve'),
    path('ticket-stats/', views.TicketStatsView.as_view(), name='crm-ticket-stats'),

    # تعليقات التذاكر
    path('tickets/<int:ticket_id>/comments/', views.TicketCommentListView.as_view(), name='crm-ticket-comments'),

    # عروض الأسعار
    path('quotations/', views.QuotationListView.as_view(), name='crm-quotations'),
    path('quotations/<int:pk>/', views.QuotationDetailView.as_view(), name='crm-quotation-detail'),
    path('quotations/<int:pk>/delete/', views.QuotationDeleteView.as_view(), name='crm-quotation-delete'),
    path('quotations/<int:pk>/convert/', views.QuotationConvertView.as_view(), name='crm-quotation-convert'),

    # العمولات
    path('commissions/', views.CommissionListView.as_view(), name='crm-commissions'),
    path('commissions/<int:pk>/', views.CommissionDetailView.as_view(), name='crm-commission-detail'),
    path('commissions/<int:pk>/delete/', views.CommissionDeleteView.as_view(), name='crm-commission-delete'),
    path('commission-stats/', views.CommissionStatsView.as_view(), name='crm-commission-stats'),
]
