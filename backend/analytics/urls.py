from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'forecast/sales', views.SalesForecastViewSet, basename='sales-forecast')
router.register(r'forecast/demand', views.DemandForecastViewSet, basename='demand-forecast')
router.register(r'forecast/cashflow', views.CashflowForecastViewSet, basename='cashflow-forecast')
router.register(r'anomalies', views.AnomalyViewSet, basename='anomaly')
router.register(r'segments/customers', views.CustomerSegmentViewSet, basename='customer-segment')
router.register(r'suppliers/scores', views.SupplierScoreViewSet, basename='supplier-score')
router.register(r'models/metrics', views.ModelMetricsViewSet, basename='model-metrics')

urlpatterns = router.urls + [
    path('run-forecast/', views.RunForecastView.as_view(), name='run-forecast'),
    path('run-anomaly-detection/', views.RunAnomalyDetectionView.as_view(), name='run-anomaly-detection'),
    path('classification/invoice-risk/', views.InvoiceRiskView.as_view(), name='invoice-risk'),
]
