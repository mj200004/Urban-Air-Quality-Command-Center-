import pandas as pd
import numpy as np
from dateutil import parser as dateutil_parser

POLLUTANTS = ["SO2 µg/m3", "Nox µg/m3", "RSPM µg/m3", "SPM", "AQI"]

def aqi_comment(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Satisfactory"
    elif aqi <= 200: return "Moderate"
    elif aqi <= 300: return "Bad"
    elif aqi <= 400: return "Very Bad"
    elif aqi <= 500: return "Hazardous"
    return "Invalid AQI"

def _read_csv_robust(csv_path):
    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            if any("µg" in c or "Âµg" in c for c in df.columns):
                return df, enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return pd.read_csv(csv_path, encoding="latin-1"), "latin-1"

def _normalize_columns(df):
    rename_map = {}
    for col in df.columns:
        cleaned = col.replace("Âµ", "µ").strip()
        rename_map[col] = cleaned
    return df.rename(columns=rename_map)

def _parse_one_date(raw):
    if pd.isna(raw):
        return pd.NaT
    s = str(raw).strip()
    if not s:
        return pd.NaT
    try:
        return dateutil_parser.parse(s, dayfirst=True, yearfirst=False)
    except (ValueError, OverflowError, TypeError):
        return pd.NaT

def parse_dates_robust(date_series):
    parsed = date_series.apply(_parse_one_date)
    n_total = len(date_series)
    n_failed = parsed.isna().sum()
    if n_failed > 0:
        failed_samples = date_series[parsed.isna()].astype(str).unique()[:5]
        print(f"WARNING: {n_failed}/{n_total} dates failed to parse. Sample: {list(failed_samples)}")
    return parsed

def load_and_clean(csv_path):
    df, used_encoding = _read_csv_robust(csv_path)
    df = _normalize_columns(df)

    for col in POLLUTANTS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            print(f"WARNING: expected column '{col}' not found (encoding={used_encoding}). Columns: {list(df.columns)}")

    present_pollutants = [c for c in POLLUTANTS if c in df.columns]
    means = df[present_pollutants].mean()
    df = df.fillna(means)

    df["Date"] = parse_dates_robust(df["Date"])
    before = len(df)
    df = df.dropna(subset=["Date"])
    after = len(df)
    print(f"Date parsing: kept {after}/{before} rows ({round(100*after/max(before,1),1)}%)")

    df["Comment"] = df["AQI"].apply(aqi_comment)
    df["hour"] = df["Date"].dt.hour
    df["dayofweek"] = df["Date"].dt.dayofweek
    df["month"] = df["Date"].dt.month

    if "City" not in df.columns:
        df["City"] = "Pune"

    return df.sort_values(["Location", "Date"])

def detect_cadence(df, group_col="Location"):
    gaps = []
    for _, sub in df.groupby(group_col):
        sub = sub.drop_duplicates(subset="Date").sort_values("Date")
        if len(sub) > 1:
            d = sub["Date"].diff().dropna().dt.total_seconds()
            d = d[d > 0]
            gaps.extend(d.tolist())
    if not gaps:
        return "sparse"
    median_gap_days = float(np.median(gaps)) / 86400
    if median_gap_days < 0.25:
        return "hourly"
    elif median_gap_days < 3:
        return "daily"
    elif median_gap_days < 10:
        return "weekly"
    elif median_gap_days < 45:
        return "monthly"
    else:
        return "annual"

def add_lag_features(df, group_col="Location", target="AQI", cadence=None):
    df = df.copy()
    if cadence is None:
        cadence = detect_cadence(df, group_col)

    if cadence == "hourly":
        lags, window = (1, 2, 3, 24), 6
    elif cadence == "daily":
        lags, window = (1, 2, 3, 7), 5
    elif cadence == "weekly":
        lags, window = (1, 2, 4), 4
    elif cadence == "monthly":
        lags, window = (1, 2, 3, 12), 3
    else:
        lags, window = (1, 2), 3

    for lag in lags:
        df[f"lag_{lag}"] = df.groupby(group_col)[target].shift(lag)

    df["rolling_mean_w"] = df.groupby(group_col)[target].transform(
        lambda s: s.shift(1).rolling(window, min_periods=1).mean()
    )
    df["rolling_std_w"] = df.groupby(group_col)[target].transform(
        lambda s: s.shift(1).rolling(window, min_periods=1).std()
    )
    # Std of a single value is undefined (NaN) - fill with 0 rather than
    # dropping the row, since that would only ever affect a location's
    # very first few observations.
    df["rolling_std_w"] = df["rolling_std_w"].fillna(0)

    df.attrs["cadence"] = cadence
    df.attrs["lags_used"] = lags

    # THE ACTUAL FIX: require ALL lag columns to be non-null, not just
    # the first one. A row missing a longer lag (e.g. lag_24) must not
    # survive just because lag_1 happened to be populated.
    lag_cols = [f"lag_{l}" for l in lags]
    return df.dropna(subset=lag_cols)
