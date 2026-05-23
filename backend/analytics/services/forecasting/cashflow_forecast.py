"""Cash flow forecasting."""
import logging
import time
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from analytics.services.data_extractor import get_cashflow_data
from analytics.services.forecasting.base import (
    save_model_metrics, save_forecast_results
)
from analytics.models import ForecastResult

logger = logging.getLogger(__name__)


def run_cashflow_forecast(months_ahead=6):
    """Run cash flow forecasting."""
    start_time = time.time()
    logger.info("Starting cash flow forecast...")

    df = get_cashflow_data()

    if len(df) < 3:
        logger.warning("Insufficient data for cash flow forecast")
        return {'status': 'insufficient_data', 'records': len(df)}

    df = df.rename(columns={'month': 'ds'})
    df = df.set_index('ds')
    df = df.resample('MS').sum().fillna(0)

    # Forecast each component: inflow, outflow, net
    results = {}
    for col in ['inflow', 'outflow', 'net']:
        series = df[col]

        try:
            if len(series) >= 8:
                model = ExponentialSmoothing(
                    series, trend='add', seasonal=None, damped_trend=True
                )
                fitted = model.fit()
            else:
                model = ExponentialSmoothing(series, trend='add')
                fitted = model.fit()

            forecast = fitted.forecast(steps=months_ahead)
            std_err = (series - fitted.fittedvalues).std()

            future_dates = pd.date_range(
                start=df.index[-1] + pd.DateOffset(months=1),
                periods=months_ahead, freq='MS'
            )

            forecast_df = pd.DataFrame({
                'ds': future_dates,
                'yhat': forecast.values,
                'yhat_lower': (forecast - 1.96 * std_err).values,
                'yhat_upper': (forecast + 1.96 * std_err).values,
            })

            model_type = f'cashflow_{col}'
            save_forecast_results(model_type, 'monthly', forecast_df)
            results[col] = len(forecast_df)

        except Exception as e:
            logger.warning(f"Failed to forecast {col}: {e}")
            results[col] = 0

    # Also build overall cashflow forecast DataFrame
    overall_df = None
    for col in ['inflow', 'outflow', 'net']:
        model_type = f'cashflow_{col}'
        saved = ForecastResult.objects.filter(model_type=model_type).order_by('forecast_date')
        if saved.exists():
            col_df = pd.DataFrame({
                'ds': [r.forecast_date for r in saved],
                f'yhat_{col}': [float(r.predicted_value) for r in saved],
            })
            if overall_df is None:
                overall_df = col_df
            else:
                overall_df = overall_df.merge(col_df, on='ds', how='outer')

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Cash flow forecast complete: {results}, {duration_ms}ms")

    return {
        'status': 'success',
        'components': results,
        'duration_ms': duration_ms
    }
