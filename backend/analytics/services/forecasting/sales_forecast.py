"""Sales revenue forecasting using statsmodels (Holt-Winters)."""
import logging
import time
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from analytics.services.data_extractor import get_monthly_sales
from analytics.services.forecasting.base import (
    train_test_split_time_series, evaluate_forecast,
    save_model_metrics, save_forecast_results
)

logger = logging.getLogger(__name__)


def run_sales_forecast(months_ahead=6):
    """Run sales forecasting and save results.
    Uses Holt-Winters Exponential Smoothing (Additive).
    Falls back to simple moving average if insufficient data.
    """
    start_time = time.time()
    logger.info("Starting sales forecast...")

    # 1. Extract data
    df = get_monthly_sales()

    if len(df) < 3:
        logger.warning("Insufficient data for sales forecast (need at least 3 months)")
        return {'status': 'insufficient_data', 'records': len(df)}

    # 2. Prepare data for model
    df = df.rename(columns={'month': 'ds', 'total_amount': 'y'})
    df = df.set_index('ds')
    df = df.resample('MS').sum().fillna(0)  # Ensure monthly frequency

    # 3. Train/test split
    train, test = train_test_split_time_series(df.reset_index(), 'ds', 'y', test_ratio=0.15)
    train_series = train.set_index('ds')['y']

    # 4. Fit model
    try:
        if len(train_series) >= 12:  # Need at least 2 full seasonal cycles
            model = ExponentialSmoothing(
                train_series,
                trend='add',
                seasonal='add',
                seasonal_periods=12,
                damped_trend=True
            )
            fitted = model.fit(optimized=True)
            model_name = 'Holt-Winters (Additive, Damped)'
        elif len(train_series) >= 4:
            model = ExponentialSmoothing(
                train_series,
                trend='add',
                seasonal=None,
                damped_trend=True
            )
            fitted = model.fit(optimized=True)
            model_name = 'Holt-Winters (Trend Only)'
        else:
            # Fallback: simple average growth
            model_name = 'Simple Average Growth'
            avg_growth = train_series.pct_change().dropna().mean()
            last_value = train_series.iloc[-1]
            fitted = None
    except Exception as e:
        logger.warning(f"Holt-Winters failed: {e}, using simple growth")
        avg_growth = train_series.pct_change().dropna().mean()
        last_value = train_series.iloc[-1]
        fitted = None
        model_name = 'Simple Average Growth'

    # 5. Generate forecast
    future_dates = pd.date_range(
        start=df.index[-1] + pd.DateOffset(months=1),
        periods=months_ahead,
        freq='MS'
    )

    if fitted is not None:
        forecast = fitted.forecast(steps=months_ahead)
        # Confidence intervals (approximate)
        residuals = train_series - fitted.fittedvalues
        std_err = residuals.std()
        lower = forecast - 1.96 * std_err
        upper = forecast + 1.96 * std_err
    else:
        # Simple growth forecast
        forecast_values = []
        val = last_value
        for i in range(months_ahead):
            val = val * (1 + avg_growth) if not np.isnan(avg_growth) else val * 1.1
            forecast_values.append(val)
        forecast = pd.Series(forecast_values, index=future_dates)
        std_err = train_series.std()
        lower = forecast - 1.96 * std_err
        upper = forecast + 1.96 * std_err

    # Build forecast DataFrame
    forecast_df = pd.DataFrame({
        'ds': future_dates,
        'yhat': forecast.values,
        'yhat_lower': lower.values,
        'yhat_upper': upper.values,
    })

    # 6. Evaluate on test set (if available)
    metrics = {}
    if len(test) > 0 and fitted is not None:
        test_pred = fitted.forecast(steps=len(test))
        metrics = evaluate_forecast(test['y'].values, test_pred.values)

    # 7. Save results
    save_forecast_results('sales', 'monthly', forecast_df)

    # Save metrics
    duration_ms = int((time.time() - start_time) * 1000)
    save_model_metrics(
        model_type='sales_forecast',
        model_version='v1',
        training_samples=len(train),
        duration_ms=duration_ms,
        metrics_dict=metrics
    )

    logger.info(f"Sales forecast complete: {len(forecast_df)} predictions, {duration_ms}ms")

    return {
        'status': 'success',
        'model': model_name,
        'predictions': len(forecast_df),
        'metrics': metrics,
        'duration_ms': duration_ms
    }
