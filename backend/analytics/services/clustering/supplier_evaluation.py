"""Supplier evaluation and scoring."""
import logging
import time
import pandas as pd
import numpy as np

from analytics.services.data_extractor import get_supplier_evaluation_data, decimal_to_float
from analytics.models import SupplierScore

logger = logging.getLogger(__name__)


def run_supplier_evaluation():
    """Evaluate suppliers and save scores."""
    start_time = time.time()
    logger.info("Starting supplier evaluation...")

    df = get_supplier_evaluation_data()

    if df.empty:
        logger.warning("No supplier data available for evaluation")
        return {'status': 'insufficient_data'}

    # Delivery score based on fill rate (already 0-100 scale)
    df['delivery_score'] = np.where(
        df['fill_rate'] > 0,
        df['fill_rate'],
        50  # default if no data
    )

    # Quality score: based on tender evaluations if available
    try:
        from tenders.models import TenderBid
        from django.db.models import Avg

        tender_scores = TenderBid.objects.filter(
            status__in=['submitted', 'qualified', 'selected']
        ).values('supplier__id').annotate(
            avg_tech=Avg('technical_score')
        )
        tender_score_map = {}
        for item in tender_scores:
            if item['avg_tech'] is not None:
                tender_score_map[item['supplier__id']] = float(item['avg_tech'])

        df['quality_score'] = df['supplier_id'].map(tender_score_map)
        df['quality_score'] = df['quality_score'].fillna(
            df['quality_score'].mean() if df['quality_score'].notna().any() else 70
        )
    except Exception:
        # Fallback if tenders module not available
        df['quality_score'] = 70.0

    # Financial score: based on total purchase amount (normalize to 0-100)
    if df['total_amount'].max() > 0:
        df['financial_score'] = (1 - df['total_amount'] / df['total_amount'].max()) * 40 + 60
    else:
        df['financial_score'] = 70.0  # default

    # Overall score: weighted average
    df['overall_score'] = (
        df['delivery_score'] * 0.40 +
        df['quality_score'] * 0.35 +
        df['financial_score'] * 0.25
    )

    # Rating tier
    def assign_tier(score):
        if score >= 85: return 'excellent'
        if score >= 70: return 'good'
        if score >= 50: return 'average'
        return 'poor'

    df['rating_tier'] = df['overall_score'].apply(assign_tier)

    # Save results
    updated_count = 0
    created_count = 0

    for _, row in df.iterrows():
        defaults = {
            'overall_score': round(float(row['overall_score']), 1),
            'delivery_score': round(float(row['delivery_score']), 1),
            'quality_score': round(float(row['quality_score']), 1),
            'financial_score': round(float(row['financial_score']), 1),
            'fill_rate': round(float(row['fill_rate']), 1),
            'total_orders': int(row['total_orders']),
            'total_amount': row['total_amount'],
            'rating_tier': row['rating_tier'],
        }

        obj, created = SupplierScore.objects.update_or_create(
            supplier_id=int(row['supplier_id']),
            defaults=defaults
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    tier_summary = df['rating_tier'].value_counts().to_dict()

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Supplier evaluation complete: {created_count} created, {updated_count} updated, {duration_ms}ms")

    return {
        'status': 'success',
        'suppliers_evaluated': len(df),
        'created': created_count,
        'updated': updated_count,
        'tiers': tier_summary,
        'duration_ms': duration_ms
    }
