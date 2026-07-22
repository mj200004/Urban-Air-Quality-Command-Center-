import os

TEMPLATES = {
    "Good": "Air quality is good. Safe for all outdoor activities.",
    "Satisfactory": "Air quality is satisfactory. Sensitive groups should limit prolonged exertion.",
    "Moderate": "Moderate pollution. People with asthma/heart conditions should reduce outdoor exertion.",
    "Bad": "Poor air quality. Avoid outdoor activity if you have respiratory issues.",
    "Very Bad": "Very poor air quality. Everyone should minimize outdoor exposure.",
    "Hazardous": "Hazardous air quality. Stay indoors, use air purifiers/masks if available.",
}

_client = None
_client_init_failed = False

def _get_client():
    """Lazily create the Anthropic client only when actually needed, and
    only once. If it fails (missing key, version mismatch, network issue),
    remember that and fall back to templates instead of crashing the app
    that imports this module."""
    global _client, _client_init_failed
    if _client is not None or _client_init_failed:
        return _client
    try:
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            _client_init_failed = True
            return None
        _client = Anthropic(api_key=api_key)
        return _client
    except Exception as e:
        print(f"WARNING: Anthropic client could not be initialized ({e}). "
              f"Falling back to template advisories.")
        _client_init_failed = True
        return None

def generate_advisory(location, aqi_value, category, language="English", use_llm=True):
    base = TEMPLATES.get(category, "Monitor local air quality updates.")

    if not use_llm:
        return {"location": location, "aqi": aqi_value, "advisory": base, "language": language, "source": "template"}

    client = _get_client()
    if client is None:
        return {"location": location, "aqi": aqi_value, "advisory": base, "language": language, "source": "template"}

    prompt = (
        f"Rewrite this air quality health advisory in {language}, keep it under 40 words, "
        f"friendly and clear for a general public audience, no medical jargon. "
        f"Location: {location}. AQI: {aqi_value} ({category}). Base message: {base}"
    )
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return {"location": location, "aqi": aqi_value, "advisory": text.strip(), "language": language, "source": "llm"}
    except Exception as e:
        print(f"WARNING: LLM call failed ({e}), using template fallback.")
        return {"location": location, "aqi": aqi_value, "advisory": base, "language": language, "source": "template"}
