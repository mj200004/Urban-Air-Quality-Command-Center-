"""
Generates realistic synthetic multi-city AQI data, statistically calibrated
against public 2024-25 CPCB/media-reported averages. Clearly-labeled
SIMULATED data used only to demonstrate multi-city scalability; Pune data
is real. All paths are anchored to this script's own folder, so it works
no matter which directory you run it from.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CITY_PROFILES = {
    "Delhi":      {"base_aqi": 218, "std": 90,  "locations": ["Anand Vihar", "RK Puram", "Punjabi Bagh", "Dwarka"]},
    "Mumbai":     {"base_aqi": 140, "std": 70,  "locations": ["Bandra", "Andheri", "Colaba", "Chembur"]},
    "Kolkata":    {"base_aqi": 160, "std": 60,  "locations": ["Rabindra Sarobar", "Ballygunge", "Victoria"]},
    "Bengaluru":  {"base_aqi": 95,  "std": 40,  "locations": ["Silk Board", "Hebbal", "Jayanagar"]},
    "Chennai":    {"base_aqi": 85,  "std": 35,  "locations": ["Manali", "T Nagar", "Alandur"]},
}

def seasonal_multiplier(month):
    if month in [11, 12, 1, 2]: return 1.35
    if month in [6, 7, 8, 9]: return 0.6
    return 1.0

def diurnal_multiplier(hour):
    if hour in [7, 8, 9, 18, 19, 20, 21]: return 1.25
    if hour in [2, 3, 4, 13, 14]: return 0.8
    return 1.0

def generate_city(city, profile, start, periods):
    rows = []
    for loc in profile["locations"]:
        loc_bias = np.random.uniform(0.85, 1.15)
        dt = start
        for i in range(periods):
            month, hour = dt.month, dt.hour
            aqi = max(5, np.random.normal(
                profile["base_aqi"] * loc_bias * seasonal_multiplier(month) * diurnal_multiplier(hour),
                profile["std"] * 0.4
            ))
            so2 = max(0, np.random.normal(aqi * 0.04, 2))
            nox = max(0, np.random.normal(aqi * 0.12, 5))
            rspm = max(0, np.random.normal(aqi * 0.35, 15))
            spm = max(0, np.random.normal(aqi * 0.25, 10))
            rows.append({
                "Date": dt.strftime("%d-%m-%Y %H:%M"),
                "Location": f"{loc} ({city})",
                "City": city,
                "SO2 µg/m3": round(so2, 2),
                "Nox µg/m3": round(nox, 2),
                "RSPM µg/m3": round(rspm, 2),
                "SPM": round(spm, 2),
                "AQI": round(aqi, 1),
            })
            dt += timedelta(hours=1)
    return rows

def main():
    out_dir = os.path.join(SCRIPT_DIR, "raw")
    os.makedirs(out_dir, exist_ok=True)   # <-- the actual fix: create dir regardless of cwd
    out_path = os.path.join(out_dir, "synthetic_multi_city_aqi.csv")

    start = datetime(2025, 1, 1, 0, 0)
    periods = 24 * 120
    all_rows = []
    for city, profile in CITY_PROFILES.items():
        all_rows.extend(generate_city(city, profile, start, periods))
    df = pd.DataFrame(all_rows)
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} synthetic rows across {len(CITY_PROFILES)} cities -> {out_path}")

if __name__ == "__main__":
    main()
