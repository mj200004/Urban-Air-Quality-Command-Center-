import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from preprocessing import aqi_comment, add_lag_features

def test_aqi_comment_boundaries():
    assert aqi_comment(0) == "Good"
    assert aqi_comment(50) == "Good"
    assert aqi_comment(51) == "Satisfactory"
    assert aqi_comment(150) == "Moderate"
    assert aqi_comment(250) == "Bad"
    assert aqi_comment(350) == "Very Bad"
    assert aqi_comment(450) == "Hazardous"

def test_lag_features_no_leakage():
    df = pd.DataFrame({
        "Location": ["A"] * 30, "AQI": list(range(30)),
        "hour": [0]*30, "dayofweek": [0]*30, "month": [1]*30,
    })
    out = add_lag_features(df, cadence="hourly")
    for idx in out.index:
        original_pos = df.index.get_loc(idx)
        assert out.loc[idx, "lag_1"] == df.iloc[original_pos - 1]["AQI"]

def test_lag_features_drop_insufficient_history():
    df = pd.DataFrame({
        "Location": ["A"] * 5, "AQI": [10, 20, 30, 40, 50],
        "hour": [0]*5, "dayofweek": [0]*5, "month": [1]*5,
    })
    out = add_lag_features(df, cadence="hourly")  # needs lag_24, only 5 rows total
    assert len(out) == 0

def test_lag_features_sparse_cadence_keeps_data():
    df = pd.DataFrame({
        "Location": ["A"] * 5, "AQI": [10, 20, 30, 40, 50],
        "hour": [0]*5, "dayofweek": [0]*5, "month": [1]*5,
    })
    out = add_lag_features(df, cadence="annual")  # needs lag_1, lag_2 -> rows idx 2,3,4
    assert len(out) == 3

def test_no_nan_reaches_output():
    df = pd.DataFrame({
        "Location": ["A"] * 20, "AQI": list(range(20)),
        "hour": [0]*20, "dayofweek": [0]*20, "month": [1]*20,
    })
    out = add_lag_features(df, cadence="monthly")
    lag_cols = [c for c in out.columns if c.startswith("lag_")]
    assert not out[lag_cols + ["rolling_mean_w", "rolling_std_w"]].isna().any().any()
