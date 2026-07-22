def enforcement_priority(location_df):
    """Score = severity x persistence x (proxy) exposure.
    location_df: rows for one location, most recent window."""
    severity = location_df["AQI"].mean() / 500  # normalize
    persistence = (location_df["AQI"] > 200).mean()  # fraction of time in Bad+
    volatility = location_df["AQI"].std() / (location_df["AQI"].mean() + 1e-6)
    exposure_proxy = 1.0  # placeholder for population density weighting

    score = round(float(severity * 0.4 + persistence * 0.4 + volatility * 0.2) * exposure_proxy, 4)
    return {
        "priority_score": score,
        "avg_aqi": round(float(location_df["AQI"].mean()), 1),
        "pct_time_bad_or_worse": round(float(persistence) * 100, 1),
    }

def rank_locations(df):
    results = []
    for loc, sub in df.groupby("Location"):
        r = enforcement_priority(sub)
        r["Location"] = loc
        results.append(r)
    return sorted(results, key=lambda x: x["priority_score"], reverse=True)
