"""
Merges the real Pune CSV with the synthetic multi-city CSV. Paths anchored
to this script's own folder so it works from any working directory.
"""
import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REAL_PUNE_PATH = os.path.join(SCRIPT_DIR, "PUNE_AQI.csv")
SYNTHETIC_PATH = os.path.join(SCRIPT_DIR, "raw", "synthetic_multi_city_aqi.csv")
OUT_DIR = os.path.join(SCRIPT_DIR, "processed")
OUT_PATH = os.path.join(OUT_DIR, "combined_multi_city_aqi.csv")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    frames = []

    if os.path.exists(REAL_PUNE_PATH):
        for enc in ["utf-8", "cp1252", "latin-1"]:
            try:
                pune = pd.read_csv(REAL_PUNE_PATH, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        pune.columns = [c.replace("Âµ", "µ").strip() for c in pune.columns]
        if "CO2 µg/m3" in pune.columns:
            pune = pune.drop(columns=["CO2 µg/m3"])
        pune["City"] = "Pune"
        pune["DataSource"] = "real"
        frames.append(pune)
        print(f"Loaded real Pune data: {len(pune)} rows")
    else:
        print(f"WARNING: {REAL_PUNE_PATH} not found. Drop your real Pune CSV there first.")

    if os.path.exists(SYNTHETIC_PATH):
        synth = pd.read_csv(SYNTHETIC_PATH)
        synth["DataSource"] = "synthetic"
        frames.append(synth)
        print(f"Loaded synthetic data: {len(synth)} rows")
    else:
        print(f"WARNING: {SYNTHETIC_PATH} not found. Run generate_synthetic_cities.py first.")

    if not frames:
        raise SystemExit("No data available to merge.")

    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined.to_csv(OUT_PATH, index=False)
    print(f"Combined dataset written to {OUT_PATH} ({len(combined)} rows, {combined['City'].nunique()} cities)")

if __name__ == "__main__":
    main()
