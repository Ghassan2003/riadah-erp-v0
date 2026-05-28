"""Invoice payment risk classification."""
import logging
import time
import pandas as pd
import numpy as np
from datetime import datetime

from analytics.models import AnomalyRecord

logger = logging.getLogger(__name__)


def run_invoice_risk_classification():
    """Classify invoice payment risk based on historical patterns.
    Creates anomaly records for high-risk invoices.
    """
    start_time = time.time()
    logger.info("Starting invoice risk classification...")

    from invoicing.models import Invoice
    from django.utils import timezone

    today = timezone.now().date()

    # Get all unpaid/partially paid invoices
    at_risk_invoices = Invoice.objects.filter(
        payment_status__in=['unpaid', 'partially_paid', 'overdue']
    ).select_related('customer')

    if not at_risk_invoices.exists():
        logger.info("No at-risk invoices found")
        return {'status': 'no_risk_invoices'}

    # Calculate risk score for each invoice
    risk_records_created = 0

    for invoice in at_risk_invoices:
        if not invoice.due_date:
            continue

        days_overdue = (today - invoice.due_date).days if today > invoice.due_date else 0
        remaining = float(invoice.total_amount - (invoice.paid_amount or 0))

        # Risk factors
        risk_score = 0.0

        # Factor 1: Days overdue (max 40 points)
        if days_overdue > 60:
            risk_score += 40
        elif days_overdue > 30:
            risk_score += 30
        elif days_overdue > 15:
            risk_score += 20
        elif days_overdue > 0:
            risk_score += 10

        # Factor 2: Payment status (max 30 points)
        if invoice.payment_status == 'overdue':
            risk_score += 30
        elif invoice.payment_status == 'partially_paid':
            paid_ratio = float(invoice.paid_amount or 0) / float(invoice.total_amount) if invoice.total_amount > 0 else 0
            risk_score += 30 * (1 - paid_ratio)
        elif invoice.payment_status == 'unpaid':
            risk_score += 25

        # Factor 3: Invoice amount (max 15 points - larger = more risk)
        if remaining > 100000:
            risk_score += 15
        elif remaining > 50000:
            risk_score += 10
        elif remaining > 10000:
            risk_score += 5

        # Factor 4: Customer history (max 15 points)
        if invoice.customer:
            customer_overdue = Invoice.objects.filter(
                customer=invoice.customer,
                payment_status='overdue'
            ).count()
            risk_score += min(customer_overdue * 5, 15)

        risk_score = min(risk_score, 100)  # Cap at 100

        if risk_score >= 50:  # Only flag medium+ risk
            severity = 'critical' if risk_score >= 80 else ('high' if risk_score >= 65 else 'medium')

            exists = AnomalyRecord.objects.filter(
                anomaly_type='payment',
                entity_type='invoice',
                entity_id=invoice.id
            ).exists()

            if not exists:
                customer_name = invoice.customer.name if invoice.customer else "\u063a\u064a\u0631 \u0645\u062d\u062f\u062f"
                description = f'\u0641\u0627\u062a\u0648\u0631\u0629 {invoice.invoice_number} - {customer_name}: \u0645\u062e\u0627\u0637\u0631 \u0639\u062f\u0645 \u0627\u0644\u0633\u062f\u0627\u062f {risk_score:.0f}%'
                if days_overdue > 0:
                    description += f' (\u0645\u062a\u0623\u062e\u0631 {days_overdue} \u064a\u0648\u0645\u060c \u0627\u0644\u0645\u0628\u0644\u063a \u0627\u0644\u0645\u062a\u0628\u0642\u064a: {remaining:,.2f} \u0631.\u0633)'

                AnomalyRecord.objects.create(
                    anomaly_type='payment',
                    detected_at=today,
                    entity_type='invoice',
                    entity_id=invoice.id,
                    actual_value=remaining,
                    anomaly_score=risk_score / 100,
                    severity=severity,
                    description=description
                )
                risk_records_created += 1

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("Invoice risk classification complete: %d high-risk invoices, %dms", risk_records_created, duration_ms)

    return {
        'status': 'success',
        'at_risk_count': at_risk_invoices.count(),
        'flagged_count': risk_records_created,
        'duration_ms': duration_ms
    }
