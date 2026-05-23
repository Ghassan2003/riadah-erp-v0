"""Base forecasting utilities."""
import logging
import time
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from analytics.models import ModelMetrics, ForecastResult

logger = logging.getLogger(__name__)


def train_test_split_time_series(df, date_col, value_col, test_ratio=0.15):
    """Split time series data into train/test sets chronologically."""
    cutoff_idx = int(len(df) * (1 - test_ratio))
    train = df.iloc[:cutoff_idx].copy()
    test = df.iloc[cutoff_idx:].copy()
    return train, test


def evaluate_forecast(actual, predicted):
    """Calculate forecast evaluation metrics."""
    actual = np.array(actual, dtype=float)
    predicted = np.array(predicted, dtype=float)

    # Remove NaN pairs
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    actual = actual[mask]
    predicted = predicted[mask]

    if len(actual) < 2:
        return {}

    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(np.sqrt(mean_squared_error(actual, predicted)))

    # MAPE - handle zeros
    nonzero_mask = actual != 0
    if nonzero_mask.sum() > 0:
        mape = float(mean_absolute_percentage_error(actual[nonzero_mask], predicted[nonzero_mask])) * 100
    else:
        mape = None

    # R2
    if len(actual) >= 3:
        r2 = float(r2_score(actual, predicted))
    else:
        r2 = None

    return {'mae': mae, 'rmse': rmse, 'mape': mape, 'r2': r2}


def save_model_metrics(model_type, model_version, training_samples, duration_ms, metrics_dict):
    """Save model performance metrics to database."""
    ModelMetrics.objects.create(
        model_type=model_type,
        model_version=model_version,
        training_samples=training_samples,
        training_duration_ms=duration_ms,
        mape=metrics_dict.get('mape'),
        mae=metrics_dict.get('mae'),
        rmse=metrics_dict.get('rmse'),
        r2_score=metrics_dict.get('r2'),
    )


def save_forecast_results(model_type, period_type, forecast_df, date_col='ds',
                          pred_col='yhat', lower_col='yhat_lower', upper_col='yhat_upper',
                          entity_id=None, entity_name=''):
    """Save forecast results to database."""
    from decimal import Decimal

    # Bulk create new results
    objs = []
    for _, row in forecast_df.iterrows():
        objs.append(ForecastResult(
            model_type=model_type,
            period_type=period_type,
            forecast_date=pd.to_datetime(row[date_col]).date(),
            predicted_value=Decimal(str(round(row[pred_col], 2))),
            lower_bound=Decimal(str(round(row[lower_col], 2))) if lower_col in row.index else None,
            upper_bound=Decimal(str(round(row[upper_col], 2))) if upper_col in row.index else None,
            entity_id=entity_id,
            entity_name=entity_name,
        ))

    if objs:
        ForecastResult.objects.bulk_create(objs, batch_size=500, ignore_conflicts=True)

    logger.info(f"Saved {len(objs)} {model_type} forecast results")
    return len(objs)
