"""
URL patterns for the Equipment Maintenance module.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Equipment Maintenance statistics
    path('stats/', views.EquipmentMaintStatsView.as_view(), name='equipmaint-stats'),

    # Equipment
    path('equipment/', views.EquipmentListView.as_view(), name='equipment-list'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment-create'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment-detail'),

    # Maintenance Schedules
    path('schedules/', views.MaintenanceScheduleListView.as_view(), name='maintenance-schedules'),
    path('schedules/<int:pk>/', views.MaintenanceScheduleDetailView.as_view(), name='maintenance-schedule-detail'),

    # Work Orders
    path('work-orders/', views.WorkOrderListView.as_view(), name='work-orders'),
    path('work-orders/create/', views.WorkOrderCreateView.as_view(), name='work-order-create'),
    path('work-orders/<int:pk>/', views.WorkOrderDetailView.as_view(), name='work-order-detail'),
    path('work-orders/<int:pk>/approve/', views.WorkOrderApproveView.as_view(), name='work-order-approve'),
    path('work-orders/<int:pk>/start/', views.WorkOrderStartView.as_view(), name='work-order-start'),
    path('work-orders/<int:pk>/complete/', views.WorkOrderCompleteView.as_view(), name='work-order-complete'),

    # Maintenance Parts
    path('parts/', views.MaintenancePartListView.as_view(), name='maintenance-parts'),
    path('parts/<int:pk>/', views.MaintenancePartDetailView.as_view(), name='maintenance-part-detail'),

    # Equipment Inspections
    path('inspections/', views.EquipmentInspectionListView.as_view(), name='equipment-inspections'),
    path('inspections/create/', views.EquipmentInspectionCreateView.as_view(), name='equipment-inspection-create'),

    # Export
    path('export/', views.EquipmentMaintExportView.as_view(), name='equipmaint-export'),
]
