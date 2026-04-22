"""
أنماط الروابط لوحدة التصنيع.
"""

from django.urls import path
from . import views

urlpatterns = [
    # الإحصائيات
    path('stats/', views.ManufacturingStatsView.as_view(), name='manufacturing-stats'),

    # قوائم المواد
    path('boms/', views.BOMListView.as_view(), name='bom-list'),
    path('boms/<int:pk>/', views.BOMDetailView.as_view(), name='bom-detail'),

    # بنود قوائم المواد
    path('boms/items/', views.BOMItemListView.as_view(), name='bom-item-list'),
    path('boms/items/<int:pk>/', views.BOMItemDetailView.as_view(), name='bom-item-detail'),

    # أوامر الإنتاج
    path('orders/', views.ProductionOrderListView.as_view(), name='production-order-list'),
    path('orders/<int:pk>/', views.ProductionOrderDetailView.as_view(), name='production-order-detail'),
    path('orders/<int:pk>/start/', views.ProductionOrderStartView.as_view(), name='production-order-start'),
    path('orders/<int:pk>/complete/', views.ProductionOrderCompleteView.as_view(), name='production-order-complete'),
    path('orders/<int:pk>/cancel/', views.ProductionOrderCancelView.as_view(), name='production-order-cancel'),

    # سجلات الإنتاج
    path('logs/', views.ProductionLogListView.as_view(), name='production-log-list'),

    # مراكز العمل
    path('work-centers/', views.WorkCenterListView.as_view(), name='work-center-list'),
    path('work-centers/<int:pk>/', views.WorkCenterDetailView.as_view(), name='work-center-detail'),

    # خطوات مسارات الإنتاج
    path('routing-steps/', views.RoutingStepListView.as_view(), name='routing-step-list'),
    path('routing-steps/<int:pk>/', views.RoutingStepDetailView.as_view(), name='routing-step-detail'),

    # التصدير
    path('export/', views.ManufacturingExportView.as_view(), name='manufacturing-export'),
]
