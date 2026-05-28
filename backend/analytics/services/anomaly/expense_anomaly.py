"""Expense anomaly detection using Isolation Forest and Z-Score."""
import logging
import time
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from analytics.services.data_extractor import get_expense_transactions, decimal_to_float
from analytics.models import AnomalyRecord

logger = logging.getLogger(__name__)


def run_expense_anomaly(contamination=0.05, z_threshold=3.0):
    """Detect expense anomalies using Isolation Forest + Z-Score."""
    start_time = time.time()
    logger.info("Starting expense anomaly detection...")

    # 1. Get daily expense data
    df = get_expense_transactions()

    if len(df) < 10:
        logger.warning("Insufficient expense data for anomaly detection")
        return {'status': 'insufficient_data', 'records': len(df)}

    # Also get individual transactions for granular detection
    from accounting.models import Transaction
    transactions = Transaction.objects.filter(
        journal_entry__is_posted=True,
        account__account_type='expense'
    ).select_related('account', 'journal_entry').order_by('-amount')

    txn_list = transactions.values_list(
        'id', 'journal_entry__entry_date', 'amount',
        'account__code', 'account__name', 'journal_entry__description'
    )
    txn_df = pd.DataFrame(list(txn_list), columns=[
        'id', 'date', 'amount', 'account_code', 'account_name', 'description'
    ])
    txn_df['date'] = pd.to_datetime(txn_df['date'])
    txn_df['amount'] = txn_df['amount'].apply(decimal_to_float)

    # 2. Aggregate to daily level for Isolation Forest
    daily = df.groupby('date')['amount'].sum().reset_index()

    # 3. Method 1: Z-Score on daily totals
    z_scores = np.abs(stats.zscore(daily['amount']))
    daily['z_score'] = z_scores

    # 4. Method 2: Isolation Forest on daily totals
    scaler = RobustScaler()
    X = scaler.fit_transform(daily[['amount']])
    iso_forest = IsolationForest(
        contamination=min(contamination, 0.1),
        random_state=42,
        n_estimators=100
    )
    daily['iso_pred'] = iso_forest.fit_predict(X)

    # 5. Combine: flag as anomaly if EITHER method flags it
    daily['is_anomaly'] = (daily['z_score'] > z_threshold) | (daily['iso_pred'] == -1)
    anomalies_daily = daily[daily['is_anomaly']].copy()

    # 6. Calculate global statistics for individual transaction z-scores
    if len(txn_df) > 5:
        txn_z_scores = np.abs(stats.zscore(txn_df['amount']))
        txn_df = txn_df.copy()
        txn_df['txn_z_score'] = txn_z_scores

    # 7. For each anomalous day, find the specific large transactions
    anomaly_records_created = 0
    mean_amount = float(daily['amount'].mean())
    std_amount = float(daily['amount'].std())

    for _, day_row in anomalies_daily.iterrows():
        day_txns = txn_df[
            txn_df['date'].dt.date == day_row['date'].date() if hasattr(day_row['date'], 'date') 
            else txn_df['date'] == day_row['date']
        ]

        for _, txn in day_txns.iterrows():
            txn_z_score = txn.get('txn_z_score', 0)
            z_val = day_row['z_score']
            iso_score = 1.0 if day_row['iso_pred'] == -1 else 0.0
            anomaly_score = max(float(min(z_val / 5.0, 1.0)), iso_score)

            if anomaly_score > 0.3 or txn_z_score > z_threshold:
                severity = 'critical' if anomaly_score > 0.8 else ('high' if anomaly_score > 0.5 else 'medium')

                exists = AnomalyRecord.objects.filter(
                    anomaly_type='expense',
                    entity_type='transaction',
                    entity_id=txn['id']
                ).exists()

                if not exists:
                    AnomalyRecord.objects.create(
                        anomaly_type='expense',
                        detected_at=txn['date'],
                        entity_type='transaction',
                        entity_id=txn['id'],
                        expected_range_min=max(0, mean_amount - 2 * std_amount),
                        expected_range_max=mean_amount + 2 * std_amount,
                        actual_value=txn['amount'],
                        anomaly_score=anomaly_score,
                        severity=severity,
                        description=f'مصروف غير طبيعي في حساب {txn["account_name"]} ({txn["account_code"]}): {txn["amount"]:,.2f} ر.س - {txn["description"]}'
                    )
                    anomaly_records_created += 1

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("Expense anomaly detection complete: %d anomalies found, %dms", anomaly_records_created, duration_ms)

    return {
        'status': 'success',
        'anomalies_found': anomaly_records_created,
        'daily_anomalies': len(anomalies_daily),
        'duration_ms': duration_ms
    }
