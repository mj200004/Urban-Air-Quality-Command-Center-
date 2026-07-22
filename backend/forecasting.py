import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error
from preprocessing import add_lag_features

class AQIForecaster:
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=300, max_depth=12, random_state=42, n_jobs=-1
        )
        self.trained = False
        self.features = []
        self.lags = ()
        self.small_lags = []
        self.seasonal_lags = []

    def _build_feature_list(self, feat_df):
        lags_used = feat_df.attrs.get("lags_used", (1, 2))
        feats = [f"lag_{l}" for l in lags_used] + ["rolling_mean_w", "rolling_std_w", "hour", "dayofweek", "month"]
        return feats, lags_used

    def train(self, df):
        feat_df = add_lag_features(df)
        self.features, self.lags = self._build_feature_list(feat_df)
        self.small_lags = sorted([l for l in self.lags if l <= 3])
        self.seasonal_lags = sorted([l for l in self.lags if l > 3])

        X = feat_df[self.features]
        y = feat_df["AQI"]
        split = int(len(X) * 0.85)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]

        self.model.fit(X_train, y_train)
        preds = self.model.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)

        persistence_col = f"lag_{self.small_lags[0]}" if self.small_lags else self.features[0]
        persistence_rmse = root_mean_squared_error(y_test, X_test[persistence_col])

        self.trained = True
        return {
            "cadence": feat_df.attrs.get("cadence", "unknown"),
            "lags_used": list(self.lags),
            "model_rmse": round(float(rmse), 2),
            "persistence_baseline_rmse": round(float(persistence_rmse), 2),
            "improvement_pct": round(100 * (persistence_rmse - rmse) / persistence_rmse, 2) if persistence_rmse else 0,
            "n_test_samples": len(X_test)
        }

    def forecast_location(self, df, location, horizon_steps=24):
        """horizon_steps is in units of the detected cadence
        (hours if hourly, days if daily, weeks if weekly, months if monthly)."""
        loc_df = add_lag_features(df[df["Location"] == location].copy())
        if loc_df.empty or not self.trained:
            return []
        current = loc_df.iloc[-1:].copy()
        forecasts = []
        for step in range(1, horizon_steps + 1):
            pred = float(self.model.predict(current[self.features])[0])
            forecasts.append({"step_ahead": step, "predicted_aqi": round(pred, 1)})

            # Roll the short-term lags forward with the new prediction.
            # Seasonal/long lags (e.g. lag_24, lag_12) are held at their last
            # observed value during the walk-forward - a documented
            # approximation, not a bug: those represent "same time last
            # cycle" and updating them requires data we don't have yet.
            for i in range(len(self.small_lags) - 1, 0, -1):
                current[f"lag_{self.small_lags[i]}"] = current[f"lag_{self.small_lags[i-1]}"].values
            if self.small_lags:
                current[f"lag_{self.small_lags[0]}"] = pred
        return forecasts
