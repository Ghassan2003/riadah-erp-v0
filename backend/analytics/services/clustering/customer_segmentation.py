"""Customer segmentation using RFM (Recency, Frequency, Monetary) analysis."""
import logging
import time
import pandas as pd
import numpy as np
from datetime import timedelta

from analytics.services.data_extractor import get_customer_rfm_data
from analytics.models import CustomerSegment

logger = logging.getLogger(__name__)

# RFM score thresholds for segmentation
SEGMENT_RULES = {
    'VIP': {'min_rfm': 12, 'label': '\u0639\u0645\u064a\u0644 \u0645\u0645\u064a\u0632'},
    'Loyal': {'min_rfm': 9, 'label': '\u0639\u0645\u064a\u0644 \u0648\u0641\u0651\u064a'},
    'Regular': {'min_rfm': 6, 'label': '\u0639\u0645\u064a\u0644 \u0639\u0627\u062f\u064a'},
    'At Risk': {'min_rfm': 4, 'label': '\u0639\u0645\u064a\u0644 \u0645\u0647\u062f\u062f'},
    'Lost': {'min_rfm': 0, 'label': '\u0639\u0645\u064a\u0644 \u0641\u0627\u0642\u062f'},
}


def _calculate_rfm_scores(df):
    """Calculate RFM scores using quartile-based scoring."""
    df = df.copy()

    # Handle customers with zero frequency
    if df['frequency'].max() == 0:
        df['f_score'] = 1
    else:
        df['f_score'] = pd.qcut(df['frequency'], q=4, labels=[1, 2, 3, 4], duplicates='drop').astype(int)

    # Handle customers with zero monetary
    if df['monetary'].max() == 0:
        df['m_score'] = 1
    else:
        df['m_score'] = pd.qcut(df['monetary'], q=4, labels=[1, 2, 3, 4], duplicates='drop').astype(int)

    # Recency: lower is better (invert)
    df['r_score'] = pd.qcut(df['recency_days'], q=4, labels=[4, 3, 2, 1], duplicates='drop').astype(int)

    df['rfm_total'] = df['r_score'] + df['f_score'] + df['m_score']

    # Segment assignment
    def assign_segment(rfm):
        if rfm >= 12: return 'VIP'
        if rfm >= 9: return 'Loyal'
        if rfm >= 6: return 'Regular'
        if rfm >= 4: return 'At Risk'
        return 'Lost'

    df['segment_name'] = df['rfm_total'].apply(assign_segment)

    # Boost score to 5-point scale for display
    df['r_score'] = ((df['r_score'] / 4) * 5).round().astype(int).clip(1, 5)
    df['f_score'] = ((df['f_score'] / 4) * 5).round().astype(int).clip(1, 5)
    df['m_score'] = ((df['m_score'] / 4) * 5).round().astype(int).clip(1, 5)

    return df


def run_customer_segmentation():
    """Run RFM customer segmentation and save results."""
    start_time = time.time()
    logger.info("Starting customer segmentation...")

    df = get_customer_rfm_data()

    if df.empty:
        logger.warning("No customer data available for segmentation")
        return {'status': 'insufficient_data'}

    # Calculate RFM scores
    df = _calculate_rfm_scores(df)

    # Add derived fields
    df['avg_order_value'] = np.where(
        df['frequency'] > 0,
        df['monetary'] / df['frequency'],
        0
    )
    df['customer_tenure_days'] = (pd.Timestamp.now().tz_localize(None) - pd.to_datetime(df['first_order'])).dt.days.fillna(0).astype(int)

    # Save results
    updated_count = 0
    created_count = 0

    for _, row in df.iterrows():
        # Map DataFrame column names to model field names
        last_order_val = row['last_order']
        first_order_val = row['first_order']

        defaults = {
            'segment_name': row['segment_name'],
            'r_score': int(row['r_score']),
            'f_score': int(row['f_score']),
            'm_score': int(row['m_score']),
            'rfm_total': int(row['rfm_total']),
            'total_spent': row['monetary'],
            'order_count': int(row['frequency']),
            'avg_order_value': round(float(row['avg_order_value']), 2),
            'last_order_date': pd.to_datetime(last_order_val).date() if pd.notna(last_order_val) else None,
            'first_order_date': pd.to_datetime(first_order_val).date() if pd.notna(first_order_val) else None,
            'customer_tenure_days': int(row['customer_tenure_days']) if not pd.isna(row['customer_tenure_days']) else 0,
        }

        obj, created = CustomerSegment.objects.update_or_create(
            customer_id=row['customer_id'],
            defaults=defaults
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    # Summary stats
    segment_summary = df['segment_name'].value_counts().to_dict()

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Customer segmentation complete: {created_count} created, {updated_count} updated, {duration_ms}ms")

    return {
        'status': 'success',
        'customers_segmented': len(df),
        'created': created_count,
        'updated': updated_count,
        'segments': segment_summary,
        'duration_ms': duration_ms
    }
