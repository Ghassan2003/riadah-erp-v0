import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def run_daily_forecast(self):
    """Run all forecasting models daily"""
    try:
        from .services.forecasting.sales_forecast import run_sales_forecast
        from .services.forecasting.demand_forecast import run_demand_forecast
        from .services.forecasting.cashflow_forecast import run_cashflow_forecast

        results = {}
        results['sales'] = run_sales_forecast()
        results['demand'] = run_demand_forecast()
        results['cashflow'] = run_cashflow_forecast()

        logger.info(f"Daily forecast completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Daily forecast failed: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=2)
def run_daily_anomaly_detection(self):
    """Run anomaly detection daily"""
    try:
        from .services.anomaly.expense_anomaly import run_expense_anomaly
        from .services.anomaly.sales_anomaly import run_sales_anomaly

        results = {}
        results['expenses'] = run_expense_anomaly()
        results['sales'] = run_sales_anomaly()

        logger.info(f"Daily anomaly detection completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=2)
def run_weekly_clustering(self):
    """Run clustering tasks weekly"""
    try:
        from .services.clustering.customer_segmentation import run_customer_segmentation
        from .services.clustering.supplier_evaluation import run_supplier_evaluation

        results = {}
        results['customer_segments'] = run_customer_segmentation()
        results['supplier_scores'] = run_supplier_evaluation()

        logger.info(f"Weekly clustering completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Weekly clustering failed: {e}")
        raise self.retry(exc=e, countdown=300)
