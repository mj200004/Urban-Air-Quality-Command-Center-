import os

class Config:
    DATA_PATH = os.environ.get(
        "AQI_DATA_PATH",
        os.path.join(os.path.dirname(__file__), "..", "data", "processed", "combined_multi_city_aqi.csv")
    )
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    LLM_MODEL = os.environ.get("AQI_LLM_MODEL", "claude-sonnet-4-6")
    FORECAST_DEFAULT_HOURS = int(os.environ.get("AQI_FORECAST_HOURS", 24))
    LOG_LEVEL = os.environ.get("AQI_LOG_LEVEL", "INFO")
    PORT = int(os.environ.get("AQI_PORT", 5000))
