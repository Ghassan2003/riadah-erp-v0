import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# Non-retryable errors: retrying won't help
NON_RETRYABLE_ERRORS = (
    ImportError,      # missing module / dependency
    ValueError,        # invalid input data
    TypeError,         # type mismatch
    LookupError,       # missing DB records
)


def _should_retry(exc):
    """Return True if the exception is transient and worth retrying."""
    if isinstance(exc, NON_RETRYABLE_ERRORS):
        return False
    exc_name = type(exc).__name__
    # Known transient error patterns
    transient_keywords = ('connection', 'timeout', 'temporary', 'network', 'service')
    return any(kw in exc_name.lower() or kw in str(exc).lower() for kw in transient_keywords)


def _backoff_countdown(task, base=120, multiplier=2, max_countdown=600):
    """Calculate exponential backoff countdown."""
    attempt = task.request.retries + 1
    return min(base * (multiplier ** attempt), max_countdown)


@shared_task(bind=True, max_retries=2)
def run_daily_forecast(self):
    """Run all forecasting models daily."""
    try:
        from .services.forecasting.sales_forecast import run_sales_forecast
        from .services.forecasting.demand_forecast import run_demand_forecast
        from .services.forecasting.cashflow_forecast import run_cashflow_forecast

        results = {}
        results['sales'] = run_sales_forecast()
        results['demand'] = run_demand_forecast()
        results['cashflow'] = run_cashflow_forecast()

        logger.info("Daily forecast completed: %s", results)
        return results
    except NON_RETRYABLE_ERRORS as e:
        logger.error("Daily forecast failed (non-retryable): %s: %s", type(e).__name__, e)
        return {'status': 'error', 'error': str(e)}
    except Exception as e:
        if not _should_retry(e):
            logger.error("Daily forecast failed (permanent): %s: %s", type(e).__name__, e)
            return {'status': 'error', 'error': str(e)}
        countdown = _backoff_countdown(self)
        logger.warning("Daily forecast failed (retry %d in %ds): %s", self.request.retries + 1, countdown, e)
        raise self.retry(exc=e, countdown=countdown)


@shared_task(bind=True, max_retries=2)
def run_daily_anomaly_detection(self):
    """Run anomaly detection daily."""
    try:
        from .services.anomaly.expense_anomaly import run_expense_anomaly
        from .services.anomaly.sales_anomaly import run_sales_anomaly

        results = {}
        results['expenses'] = run_expense_anomaly()
        results['sales'] = run_sales_anomaly()

        logger.info("Daily anomaly detection completed: %s", results)
        return results
    except NON_RETRYABLE_ERRORS as e:
        logger.error("Anomaly detection failed (non-retryable): %s: %s", type(e).__name__, e)
        return {'status': 'error', 'error': str(e)}
    except Exception as e:
        if not _should_retry(e):
            logger.error("Anomaly detection failed (permanent): %s: %s", type(e).__name__, e)
            return {'status': 'error', 'error': str(e)}
        countdown = _backoff_countdown(self)
        logger.warning("Anomaly detection failed (retry %d in %ds): %s", self.request.retries + 1, countdown, e)
        raise self.retry(exc=e, countdown=countdown)


@shared_task(bind=True, max_retries=2)
def run_weekly_clustering(self):
    """Run clustering tasks weekly."""
    try:
        from .services.clustering.customer_segmentation import run_customer_segmentation
        from .services.clustering.supplier_evaluation import run_supplier_evaluation

        results = {}
        results['customer_segments'] = run_customer_segmentation()
        results['supplier_scores'] = run_supplier_evaluation()

        logger.info("Weekly clustering completed: %s", results)
        return results
    except NON_RETRYABLE_ERRORS as e:
        logger.error("Weekly clustering failed (non-retryable): %s: %s", type(e).__name__, e)
        return {'status': 'error', 'error': str(e)}
    except Exception as e:
        if not _should_retry(e):
            logger.error("Weekly clustering failed (permanent): %s: %s", type(e).__name__, e)
            return {'status': 'error', 'error': str(e)}
        countdown = _backoff_countdown(self)
        logger.warning("Weekly clustering failed (retry %d in %ds): %s", self.request.retries + 1, countdown, e)
        raise self.retry(exc=e, countdown=countdown)
