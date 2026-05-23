from rest_framework import serializers
from .models import (
    ForecastResult, AnomalyRecord, CustomerSegment,
    SupplierScore, ModelMetrics
)


class ForecastResultSerializer(serializers.ModelSerializer):
    model_type_display = serializers.CharField(source='get_model_type_display', read_only=True)
    forecast_date = serializers.DateField(format='%Y-%m-%d')

    class Meta:
        model = ForecastResult
        fields = [
            'id', 'model_type', 'model_type_display', 'period_type',
            'forecast_date', 'predicted_value', 'lower_bound',
            'upper_bound', 'actual_value', 'accuracy_score',
            'entity_id', 'entity_name'
        ]


class AnomalyRecordSerializer(serializers.ModelSerializer):
    anomaly_type_display = serializers.CharField(source='get_anomaly_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.get_full_name', read_only=True, default=None
    )

    class Meta:
        model = AnomalyRecord
        fields = [
            'id', 'anomaly_type', 'anomaly_type_display', 'detected_at',
            'entity_type', 'entity_id', 'expected_range_min',
            'expected_range_max', 'actual_value', 'anomaly_score',
            'severity', 'severity_display', 'description',
            'is_reviewed', 'reviewed_by', 'reviewed_by_name',
            'review_notes', 'reviewed_at'
        ]
        read_only_fields = ['detected_at', 'anomaly_score', 'created_at']


class AnomalyReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyRecord
        fields = ['is_reviewed', 'review_notes']


class CustomerSegmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    segment_display = serializers.CharField(source='get_segment_name_display', read_only=True)

    class Meta:
        model = CustomerSegment
        fields = [
            'id', 'customer', 'customer_name', 'customer_email',
            'segment_name', 'segment_display', 'r_score', 'f_score',
            'm_score', 'rfm_total', 'total_spent', 'order_count',
            'avg_order_value', 'last_order_date', 'first_order_date',
            'customer_tenure_days', 'calculated_at'
        ]


class SupplierScoreSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    rating_tier_display = serializers.CharField(source='get_rating_tier_display', read_only=True)

    class Meta:
        model = SupplierScore
        fields = [
            'id', 'supplier', 'supplier_name', 'overall_score',
            'delivery_score', 'quality_score', 'financial_score',
            'fill_rate', 'total_orders', 'total_amount',
            'rating_tier', 'rating_tier_display', 'calculated_at'
        ]


class ModelMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelMetrics
        fields = [
            'id', 'model_type', 'model_version', 'trained_at',
            'training_samples', 'training_duration_ms',
            'mape', 'mae', 'rmse', 'r2_score', 'extra_metrics', 'is_active'
        ]
