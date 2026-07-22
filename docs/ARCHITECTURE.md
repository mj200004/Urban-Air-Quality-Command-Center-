# Architecture

Data Ingestion -> Preprocessing/Feature Engineering ->
  -> Forecasting Engine (RandomForest, lag+rolling features, 24-72hr horizon)
  -> Source Attribution Engine (pollutant-ratio heuristics)
  -> Enforcement Prioritization Scorer (severity x persistence x volatility)
-> Flask REST API -> Frontend (Leaflet map + Chart.js) + Citizen Advisory Agent (Anthropic API)

Evaluation alignment:
- Forecast accuracy vs persistence baseline: reported by /api/forecast (model_rmse vs persistence_baseline_rmse)
- Enforcement recommendation quality: ranked, explainable score, not a black box
- Citizen advisory: multi-language via LLM rewrite of a deterministic base template (safe fallback if no API key)
