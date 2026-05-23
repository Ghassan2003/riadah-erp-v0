"""Sales anomaly detection."""
import logging
import time
import pandas as pd
import numpy as np
from scipy import stats

from analytics.services.data_extractor import get_daily_sales, decimal_to_float
from analytics.models import AnomalyRecord

logger = logging.getLogger(__name__)


def run_sales_anomaly(z_threshold=2.5):
    """Detect sales anomalies using Z-Score on daily totals.
    """
    start_time = time.time()
    logger.info("Starting sales anomaly detection...")

    df = get_daily_sales()

    if len(df) < 14:
        logger.warning("Insufficient data for sales anomaly detection")
        return {'status': 'insufficient_data', 'records': len(df)}

    # Calculate rolling statistics
    df['rolling_mean'] = df['total_amount'].rolling(window=30, min_periods=7).mean()
    df['rolling_std'] = df['total_amount'].rolling(window=30, min_periods=7).std()
    df['z_score'] = np.abs((df['total_amount'] - df['rolling_mean']) / df['rolling_std'])

    # Find anomalies
    anomalies = df[df['z_score'] > z_threshold].copy()

    records_created = 0
    for _, row in anomalies.iterrows():
        if pd.isna(row['rolling_mean']):
            continue

        anomaly_score = min(float(row['z_score'] / 5.0), 1.0)
        severity = 'critical' if anomaly_score > 0.8 else ('high' if anomaly_score > 0.5 else 'medium')

        # Check for anomalous individual orders on this day
        from sales.models import SalesOrder
        day_orders = SalesOrder.objects.filter(
            order_date=row['date'],
            status__in=['confirmed', 'delivered']
        ).order_by('-total_amount')

        for order in day_orders[:3]:  # Check top 3 orders of anomalous day
            order_z = abs(float(order.total_amount) - float(row['rolling_mean'])) / float(row['rolling_std']) if row['rolling_std'] > 0 else 0

            if order_z > z_threshold:
                exists = AnomalyRecord.objects.filter(
                    anomaly_type='sales',
                    entity_type='sales_order',
                    entity_id=order.id
                ).exists()

                if not exists:
                    customer_name = order.customer.name if order.customer else "\u0639\u0645\u064a\u0644 \u0646\u0642\u062f\u064a"
                    AnomalyRecord.objects.create(
                        anomaly_type='sales',
                        detected_at=row['date'],
                        entity_type='sales_order',
                        entity_id=order.id,
                        expected_range_min=max(0, float(row['rolling_mean'] - 2 * row['rolling_std'])),
                        expected_range_max=float(row['rolling_mean'] + 2 * row['rolling_std']),
                        actual_value=float(order.total_amount),
                        anomaly_score=anomaly_score,
                        severity=severity,
                        description=f'\u0645\u0628\u064a\u0639\u0627\u062a \u063a\u064a\u0631 \u0645\u0639\u062a\u0627\u062f\u0629: {float(order.total_amount):,.2f} \u0631.\u0633 - {customer_name} - \u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u064a\u0648\u0645: {float(row["rolling_mean"]):,.2f} \u0631.\u0633'
                    )
                    records_created += 1

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Sales anomaly detection complete: {records_created} anomalies found, {duration_ms}ms")

    return {
        'status': 'success',
        'anomalies_found': records_created,
        'anomalous_days': len(anomalies),
        'duration_ms': duration_ms
    }
