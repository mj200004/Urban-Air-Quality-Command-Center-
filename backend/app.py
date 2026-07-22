from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from config import Config
from logger import get_logger
from preprocessing import load_and_clean
from forecasting import AQIForecaster
from attribution import attribute_source
from enforcement import rank_locations
from advisory import generate_advisory

log = get_logger(__name__)
app = Flask(__name__)
CORS(app)

df = None
forecasters = {}   # one forecaster per city, since pollution dynamics differ by city
train_metrics = {}

def init_data():
    global df, forecasters, train_metrics
    if not os.path.exists(Config.DATA_PATH):
        raise SystemExit(
            f"Combined dataset not found at {Config.DATA_PATH}. "
            f"Run data/generate_synthetic_cities.py then data/merge_datasets.py first."
        )
    df = load_and_clean(Config.DATA_PATH)
    if "City" not in df.columns:
        df["City"] = "Pune"

    for city in df["City"].unique():
        city_df = df[df["City"] == city]
        if len(city_df) < 100:
            log.warning(f"Skipping forecaster for {city}: insufficient rows ({len(city_df)})")
            continue
        fc = AQIForecaster()
        try:
            metrics = fc.train(city_df)
            forecasters[city] = fc
            train_metrics[city] = metrics
            log.info(f"Trained forecaster for {city}: {metrics}")
        except Exception as e:
            log.error(f"Failed to train forecaster for {city}: {e}")

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "cities_loaded": list(forecasters.keys())})

@app.route("/api/cities")
def cities():
    return jsonify(sorted(df["City"].dropna().unique().tolist()))

@app.route("/api/locations")
def locations():
    city = request.args.get("city")
    sub = df if not city else df[df["City"] == city]
    return jsonify(sorted(sub["Location"].dropna().unique().tolist()))

@app.route("/api/forecast/<location>")
def forecast(location):
    horizon = int(request.args.get("hours", Config.FORECAST_DEFAULT_HOURS))
    row = df[df["Location"] == location]
    if row.empty:
        return jsonify({"error": "location not found"}), 404
    city = row.iloc[0]["City"]
    fc = forecasters.get(city)
    if fc is None:
        return jsonify({"error": f"no trained model for city {city}"}), 400
    result = fc.forecast_location(df, location, horizon)
    return jsonify({"location": location, "city": city, "metrics": train_metrics.get(city, {}), "forecast": result})

@app.route("/api/attribution/<location>")
def attribution(location):
    sub = df[df["Location"] == location]
    if sub.empty:
        return jsonify({"error": "location not found"}), 404
    latest = sub.iloc[-1].to_dict()
    return jsonify(attribute_source(latest))

@app.route("/api/enforcement")
def enforcement():
    city = request.args.get("city")
    sub = df if not city else df[df["City"] == city]
    return jsonify(rank_locations(sub))

@app.route("/api/advisory/<location>")
def advisory(location):
    lang = request.args.get("lang", "English")
    sub = df[df["Location"] == location]
    if sub.empty:
        return jsonify({"error": "location not found"}), 404
    latest = sub.iloc[-1]
    return jsonify(generate_advisory(location, float(latest["AQI"]), latest["Comment"], lang))

if __name__ == "__main__":
    init_data()
    app.run(debug=True, port=Config.PORT)
