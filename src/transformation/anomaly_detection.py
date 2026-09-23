# src/transformation/anomaly_detector.py
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(
    df: pd.DataFrame, contamination: float = 0.01, random_state: int = 42
) -> pd.DataFrame:
    """Detect contextual anomalies in weather and energy data using Isolation Forest.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing at least date_key, hour, temp_mean_celsius,
        consumption_mw.
    contamination : float
        Proportion of expected anomalies in the dataset (default: 1%).
    random_state : int
        Seed for reproducibility.

    Returns:
    --------
    pd.DataFrame
        DataFrame with 'is_anomaly' (bool) and 'anomaly_score' (float) appended.
    """
    if df.empty or len(df) < 10:
        df["is_anomaly"] = False
        df["anomaly_score"] = 0.0
        return df

    df_proc = df.copy()

    # 1. Feature Engineering: Extract temporal components from date_key (YYYYMMDD)
    date_str = df_proc["date_key"].astype(str)
    dt_series = pd.to_datetime(date_str, format="%Y%m%d")

    df_proc["day_of_week"] = dt_series.dt.dayofweek
    df_proc["month"] = dt_series.dt.month

    # 2. Select features for ML model
    feature_cols = [
        "hour",
        "day_of_week",
        "month",
        "temp_mean_celsius",
        "consumption_mw",
    ]

    # Optional features if present in DataFrame
    for optional_col in ["precipitation_mm", "wind_speed_kmh"]:
        if optional_col in df_proc.columns:
            feature_cols.append(optional_col)

    # 3. Handle missing values for training
    X = df_proc[feature_cols].copy()
    X = X.fillna(X.median())

    # 4. Fit Isolation Forest
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
        n_jobs=-1,
    )

    # Predictions: -1 for anomalies, 1 for normal
    preds = model.fit_predict(X)

    # Decision function: lower values mean more anomalous
    scores = model.decision_function(X)

    # 5. Append results to original DataFrame
    df["is_anomaly"] = preds == -1
    df["anomaly_score"] = np.round(scores, 4)

    return df
