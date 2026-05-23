"""
URL patterns for the Insurance & Pension module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Insurance & Pension statistics
    path('stats/', views.InsuranceStatsView.as_view(), name='insurance-stats'),

    # Insurance Policies
    path('policies/', views.InsurancePolicyListView.as_view(), name='insurance-policies'),
    path('policies/create/', views.InsurancePolicyCreateView.as_view(), name='insurance-policy-create'),
    path('policies/<int:pk>/', views.InsurancePolicyDetailView.as_view(), name='insurance-policy-detail'),

    # Insurance Claims
    path('claims/', views.InsuranceClaimListView.as_view(), name='insurance-claims'),
    path('claims/submit/', views.InsuranceClaimSubmitView.as_view(), name='insurance-claim-submit'),
    path('claims/<int:pk>/', views.InsuranceClaimDetailView.as_view(), name='insurance-claim-detail'),
    path('claims/<int:pk>/review/', views.InsuranceClaimReviewView.as_view(), name='insurance-claim-review'),

    # Pension Records
    path('pensions/', views.PensionRecordListView.as_view(), name='pension-records'),
    path('pensions/create/', views.PensionRecordCreateView.as_view(), name='pension-record-create'),
    path('pensions/<int:pk>/', views.PensionRecordDetailView.as_view(), name='pension-record-detail'),

    # Pension Payments
    path('pension-payments/', views.PensionPaymentListView.as_view(), name='pension-payments'),
    path('pension-payments/create/', views.PensionPaymentCreateView.as_view(), name='pension-payment-create'),

    # Export
    path('export/', views.InsuranceExportView.as_view(), name='insurance-export'),
]
