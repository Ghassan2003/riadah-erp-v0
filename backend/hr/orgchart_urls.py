from django.urls import path
from .org_chart import OrgChartView, OrgStatisticsView

urlpatterns = [
    path('', OrgChartView.as_view(), name='org-chart'),
    path('stats/', OrgStatisticsView.as_view(), name='org-chart-stats'),
]
