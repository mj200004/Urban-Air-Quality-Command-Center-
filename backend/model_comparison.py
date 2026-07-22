"""
Compares candidate forecasting models so you can defend your model choice
with actual numbers instead of "we used RandomForest because."
"""
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from preprocessing import add_lag_features
from logger import get_logger

log = get_logger(__name__)

CANDIDATES = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42),
}

def compare_models(df):
    feat_df = add_lag_features(df)
    lags_used = feat_df.attrs.get("lags_used", (1, 2))
    features = [f"lag_{l}" for l in lags_used] + ["rolling_mean_w", "rolling_std_w", "hour", "dayofweek", "month"]

    X = feat_df[features]
    y = feat_df["AQI"]
    split = int(len(X) * 0.85)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    persistence_col = f"lag_{sorted(lags_used)[0]}"
    persistence_rmse = root_mean_squared_error(y_test, X_test[persistence_col])
    results = {
        "cadence": feat_df.attrs.get("cadence", "unknown"),
        "lags_used": list(lags_used),
        "PersistenceBaseline": round(float(persistence_rmse), 2),
    }

    for name, model in CANDIDATES.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)
        results[name] = round(float(rmse), 2)
        log.info(f"{name} RMSE: {rmse:.2f}")

    best_model = min(
        (k for k in results if k not in ("PersistenceBaseline", "cadence", "lags_used")),
        key=lambda k: results[k]
    )
    results["best_model"] = best_model
    return results

if __name__ == "__main__":
    from config import Config
    from preprocessing import load_and_clean
    df = load_and_clean(Config.DATA_PATH)
    print(compare_models(df))
