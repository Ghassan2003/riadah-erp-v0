from django.db import models
from django.conf import settings


class ForecastResult(models.Model):
    """Stores ML forecasting results"""
    MODEL_TYPES = [
        ('sales', 'تنبؤ المبيعات'),
        ('demand', 'تنبؤ الطلب'),
        ('cashflow', 'تنبؤ التدفق النقدي'),
        ('expense', 'تنبؤ المصروفات'),
    ]
    PERIOD_TYPES = [
        ('daily', 'يومي'),
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
    ]

    model_type = models.CharField(max_length=20, choices=MODEL_TYPES, db_index=True)
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, default='daily')
    forecast_date = models.DateField(db_index=True)
    predicted_value = models.DecimalField(max_digits=16, decimal_places=2)
    lower_bound = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    upper_bound = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    actual_value = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    accuracy_score = models.FloatField(null=True, blank=True)
    entity_id = models.IntegerField(null=True, blank=True, help_text='e.g. product_id for demand forecast')
    entity_name = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['forecast_date']
        indexes = [
            models.Index(fields=['model_type', 'forecast_date']),
            models.Index(fields=['model_type', 'entity_id']),
        ]

    def __str__(self):
        return f"{self.get_model_type_display()} - {self.forecast_date}: {self.predicted_value}"


class AnomalyRecord(models.Model):
    """Stores detected anomalies"""
    ANOMALY_TYPES = [
        ('expense', 'مصروفات شاذة'),
        ('sales', 'مبيعات شاذة'),
        ('payment', 'مدفوعات شاذة'),
        ('purchase', 'مشتريات شاذة'),
        ('payroll', 'رواتب شاذة'),
    ]
    SEVERITY_LEVELS = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('critical', 'حرج'),
    ]

    anomaly_type = models.CharField(max_length=20, choices=ANOMALY_TYPES, db_index=True)
    detected_at = models.DateTimeField(db_index=True)
    entity_type = models.CharField(max_length=50, help_text='e.g. transaction, order, invoice')
    entity_id = models.IntegerField(null=True, blank=True)
    expected_range_min = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    expected_range_max = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    actual_value = models.DecimalField(max_digits=16, decimal_places=2)
    anomaly_score = models.FloatField(help_text='0.0 = normal, 1.0 = extreme anomaly')
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium', db_index=True)
    description = models.TextField(blank=True, default='')
    is_reviewed = models.BooleanField(default=False, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    review_notes = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['anomaly_type', 'severity', 'is_reviewed']),
            models.Index(fields=['-detected_at']),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.get_anomaly_type_display()}: {self.actual_value} at {self.detected_at}"


class CustomerSegment(models.Model):
    """Stores RFM customer segmentation results"""
    SEGMENT_NAMES = [
        ('VIP', 'عميل مميز'),
        ('Loyal', 'عميل وفّي'),
        ('Regular', 'عميل عادي'),
        ('At Risk', 'عميل مهدد'),
        ('Lost', 'عميل فاقد'),
    ]

    customer = models.OneToOneField(
        'sales.Customer', on_delete=models.CASCADE, related_name='segment'
    )
    segment_name = models.CharField(max_length=20, choices=SEGMENT_NAMES, db_index=True)
    r_score = models.IntegerField(help_text='Recency score (1-5)')
    f_score = models.IntegerField(help_text='Frequency score (1-5)')
    m_score = models.IntegerField(help_text='Monetary score (1-5)')
    rfm_total = models.IntegerField(help_text='Total RFM score (3-15)')
    total_spent = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    order_count = models.IntegerField(default=0)
    avg_order_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    last_order_date = models.DateField(null=True, blank=True)
    first_order_date = models.DateField(null=True, blank=True)
    customer_tenure_days = models.IntegerField(default=0)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-rfm_total']
        indexes = [
            models.Index(fields=['segment_name']),
        ]

    def __str__(self):
        return f"{self.customer.name} → {self.segment_name} ({self.rfm_total})"


class SupplierScore(models.Model):
    """Stores supplier evaluation scores"""
    supplier = models.OneToOneField(
        'purchases.Supplier', on_delete=models.CASCADE, related_name='ml_score'
    )
    overall_score = models.FloatField(default=0, help_text='0-100')
    delivery_score = models.FloatField(default=0, help_text='On-time delivery rate 0-100')
    quality_score = models.FloatField(default=0, help_text='Technical quality score 0-100')
    financial_score = models.FloatField(default=0, help_text='Financial score 0-100')
    fill_rate = models.FloatField(default=0, help_text='Order fill rate 0-100')
    total_orders = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    rating_tier = models.CharField(
        max_length=20,
        choices=[('excellent', 'ممتاز'), ('good', 'جيد'), ('average', 'متوسط'), ('poor', 'ضعيف')],
        default='average'
    )
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-overall_score']

    def __str__(self):
        return f"{self.supplier.name} → {self.overall_score:.1f}/100 ({self.rating_tier})"


class ModelMetrics(models.Model):
    """Tracks ML model performance metrics"""
    model_type = models.CharField(max_length=50, db_index=True)
    model_version = models.CharField(max_length=20, default='v1')
    trained_at = models.DateTimeField(auto_now_add=True)
    training_samples = models.IntegerField(default=0)
    training_duration_ms = models.IntegerField(default=0, help_text='Training time in milliseconds')
    mape = models.FloatField(null=True, blank=True, help_text='Mean Absolute Percentage Error')
    mae = models.FloatField(null=True, blank=True, help_text='Mean Absolute Error')
    rmse = models.FloatField(null=True, blank=True, help_text='Root Mean Squared Error')
    r2_score = models.FloatField(null=True, blank=True, help_text='R-squared')
    extra_metrics = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-trained_at']
        indexes = [
            models.Index(fields=['model_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.model_type} {self.model_version} - MAPE: {self.mape}"
