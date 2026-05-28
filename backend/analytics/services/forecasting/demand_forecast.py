"""Product demand forecasting."""
import logging
import time
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from analytics.services.data_extractor import get_product_demand
from analytics.services.forecasting.base import (
    evaluate_forecast, save_model_metrics, save_forecast_results
)

logger = logging.getLogger(__name__)


def _forecast_product(demand_series, weeks_ahead=12):
    """Forecast demand for a single product. Returns forecast DataFrame or None."""
    if len(demand_series) < 4:
        return None

    try:
        # Ensure weekly frequency
        demand_series = demand_series.asfreq('W').fillna(0)

        if len(demand_series) >= 8:
            model = ExponentialSmoothing(
                demand_series, trend='add', seasonal=None, damped_trend=True
            )
            fitted = model.fit()
        else:
            # Simple moving average fallback
            avg = demand_series.mean()
            std = demand_series.std()
            fitted = None
    except (ValueError, NotImplementedError) as e:
        avg = demand_series.mean()
        std = demand_series.std()
        fitted = None
        logger.debug("ExponentialSmoothing failed for product, using moving average: %s", e)

    future_dates = pd.date_range(
        start=demand_series.index[-1] + pd.DateOffset(weeks=1),
        periods=weeks_ahead,
        freq='W'
    )

    if fitted:
        forecast = fitted.forecast(steps=weeks_ahead)
        std_err = (demand_series - fitted.fittedvalues).std()
        if pd.isna(std_err):
            std_err = 0
    else:
        forecast = pd.Series([avg] * weeks_ahead, index=future_dates)
        std_err = std if not pd.isna(std) else (avg * 0.2 if avg else 0)

    return pd.DataFrame({
        'ds': future_dates,
        'yhat': forecast.values,
        'yhat_lower': (forecast - 1.96 * std_err).values,
        'yhat_upper': (forecast + 1.96 * std_err).values,
    })


def run_demand_forecast(top_n=20, weeks_ahead=12):
    """Run demand forecasting for top products."""
    start_time = time.time()
    logger.info("Starting demand forecast for top %d products...", top_n)

    df = get_product_demand(top_n=top_n)

    if df.empty:
        logger.warning("No demand data available")
        return {'status': 'insufficient_data'}

    total_predictions = 0

    # Forecast each product separately
    for product_id in df['product_id'].unique():
        product_df = df[df['product_id'] == product_id].copy()
        product_name = product_df['product_name'].iloc[0]

        demand_series = product_df.set_index('week')['quantity']
        forecast_df = _forecast_product(demand_series, weeks_ahead)

        if forecast_df is not None:
            save_forecast_results(
                'demand', 'weekly', forecast_df,
                entity_id=int(product_id), entity_name=str(product_name)
            )
            total_predictions += len(forecast_df)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("Demand forecast complete: %d predictions for top %d products, %dms", total_predictions, top_n, duration_ms)

    return {
        'status': 'success',
        'products_forecasted': len(df['product_id'].unique()),
        'total_predictions': total_predictions,
        'duration_ms': duration_ms
    }
