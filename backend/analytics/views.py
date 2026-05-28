import logging

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F, DecimalField
from django.db.models.functions import TruncDate, TruncMonth, Coalesce
from django.core.cache import cache

from .models import (
    ForecastResult, AnomalyRecord, CustomerSegment,
    SupplierScore, ModelMetrics
)
from .serializers import (
    ForecastResultSerializer, AnomalyRecordSerializer,
    AnomalyReviewSerializer, CustomerSegmentSerializer,
    SupplierScoreSerializer, ModelMetricsSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'
        )


class SalesForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """Sales forecasting API"""
    serializer_class = ForecastResultSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['forecast_date', 'predicted_value']
    ordering = ['forecast_date']

    def get_queryset(self):
        return ForecastResult.objects.filter(model_type='sales')


class DemandForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """Product demand forecasting API"""
    serializer_class = ForecastResultSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = ForecastResult.objects.filter(model_type='demand')
        product_id = self.request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(entity_id=product_id)
        return qs


class CashflowForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """Cash flow forecasting API"""
    serializer_class = ForecastResultSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return ForecastResult.objects.filter(model_type='cashflow')


class AnomalyViewSet(viewsets.ModelViewSet):
    """Anomaly detection API"""
    queryset = AnomalyRecord.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['detected_at', 'severity', 'anomaly_score']
    ordering = ['-detected_at']
    search_fields = ['description']

    def get_serializer_class(self):
        if self.action == 'review':
            return AnomalyReviewSerializer
        return AnomalyRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        anomaly_type = self.request.query_params.get('type')
        severity = self.request.query_params.get('severity')
        is_reviewed = self.request.query_params.get('reviewed')
        if anomaly_type:
            qs = qs.filter(anomaly_type=anomaly_type)
        if severity:
            qs = qs.filter(severity=severity)
        if is_reviewed is not None:
            qs = qs.filter(is_reviewed=is_reviewed.lower() == 'true')
        return qs

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        anomaly = self.get_object()
        serializer = self.get_serializer(anomaly, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            is_reviewed=True
        )
        return Response(AnomalyRecordSerializer(anomaly).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get anomaly statistics"""
        stats = AnomalyRecord.objects.filter(
            is_reviewed=False
        ).values('anomaly_type', 'severity').annotate(
            count=Count('id')
        )
        total_unreviewed = AnomalyRecord.objects.filter(is_reviewed=False).count()
        total_by_type = AnomalyRecord.objects.values(
            'anomaly_type'
        ).annotate(count=Count('id'))
        return Response({
            'total_unreviewed': total_unreviewed,
            'unreviewed_by_severity': list(stats),
            'total_by_type': list(total_by_type)
        })


class CustomerSegmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Customer segmentation API"""
    queryset = CustomerSegment.objects.select_related('customer').all()
    serializer_class = CustomerSegmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['customer__name']
    ordering_fields = ['rfm_total', 'total_spent', 'order_count', 'segment_name']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get segment distribution summary"""
        summary = CustomerSegment.objects.values('segment_name').annotate(
            count=Count('id'),
            total_revenue=Coalesce(Sum('total_spent'), 0),
            avg_rfm=Avg('rfm_total')
        ).order_by('-total_revenue')
        return Response(list(summary))


class SupplierScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """Supplier scoring API"""
    queryset = SupplierScore.objects.select_related('supplier').all()
    serializer_class = SupplierScoreSerializer
    permission_classes = [IsAdminOrReadOnly]
    ordering_fields = ['overall_score', 'delivery_score', 'quality_score']
    ordering = ['-overall_score']


class ModelMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ML model performance metrics API"""
    queryset = ModelMetrics.objects.filter(is_active=True)
    serializer_class = ModelMetricsSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-trained_at']


class InvoiceRiskView(APIView):
    """Run invoice payment risk classification (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from .services.classification.invoice_risk import run_invoice_risk_classification
        try:
            results = run_invoice_risk_classification()
            return Response(results)
        except Exception as e:
            logger.error('Invoice risk classification failed: %s', e)
            return Response(
                {'error': 'فشل تصنيف مخاطر الفواتير: {}'.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


logger = logging.getLogger(__name__)


class RunForecastView(APIView):
    """Manually trigger forecasting models (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from .tasks import run_daily_forecast
        # Try Celery with short timeout to avoid 20s hang when Redis is down
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            redis_host = settings.CELERY_BROKER_URL.split('//')[-1].split('@')[-1].split(':')[0] if hasattr(settings, 'CELERY_BROKER_URL') else 'localhost'
            result = sock.connect_ex((redis_host, 6379))
            sock.close()
            if result == 0:
                async_result = run_daily_forecast.delay()
                return Response({
                    'message': 'تم تشغيل نماذج التنبؤ بنجاح',
                    'task_id': async_result.id,
                    'status': 'pending',
                })
        except Exception:
            pass
        # Fallback: run synchronously
        try:
            results = run_daily_forecast()
            return Response({
                'message': 'تم تشغيل نماذج التنبؤ بنجاح (متزامن)',
                'results': results,
                'status': 'completed',
            })
        except Exception as e:
            logger.error('Failed to run forecast: %s', e)
            return Response(
                {'error': 'فشل تشغيل التنبؤ: {}'.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RunAnomalyDetectionView(APIView):
    """Manually trigger anomaly detection (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from .tasks import run_daily_anomaly_detection
        # Try Celery with short timeout to avoid 20s hang when Redis is down
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            redis_host = settings.CELERY_BROKER_URL.split('//')[-1].split('@')[-1].split(':')[0] if hasattr(settings, 'CELERY_BROKER_URL') else 'localhost'
            result = sock.connect_ex((redis_host, 6379))
            sock.close()
            if result == 0:
                async_result = run_daily_anomaly_detection.delay()
                return Response({
                    'message': 'تم تشغيل كشف الشذوذ بنجاح',
                    'task_id': async_result.id,
                    'status': 'pending',
                })
        except Exception:
            pass
        # Fallback: run synchronously
        try:
            results = run_daily_anomaly_detection()
            return Response({
                'message': 'تم تشغيل كشف الشذوذ بنجاح (متزامن)',
                'results': results,
                'status': 'completed',
            })
        except Exception as e:
            logger.error('Failed to run anomaly detection: %s', e)
            return Response(
                {'error': 'فشل تشغيل كشف الشذوذ: {}'.format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
