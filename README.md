# Urban Air Quality Intelligence Platform (ET AI Hackathon 2026)

Predictive AQI intelligence platform: forecasting, source attribution,
enforcement prioritization, and citizen advisory generation, built on
CPCB/CAAQMS-style station data.

## Run
Open `frontend/index.html` in a browser (it calls http://localhost:5000).

## Components
- `backend/preprocessing.py` - data cleaning + feature engineering
- `backend/forecasting.py` - 24-72hr AQI forecast model
- `backend/attribution.py` - pollutant-ratio source attribution
- `backend/enforcement.py` - enforcement priority scoring
- `backend/advisory.py` - citizen advisory generation (Anthropic API)
- `backend/app.py` - Flask API tying it together
- `frontend/index.html` - dashboard (map + charts)
<img width="432" height="467" alt="image" src="https://github.com/user-attachments/assets/1d1c640c-5b7d-4f00-85a6-f460d066087a" />
