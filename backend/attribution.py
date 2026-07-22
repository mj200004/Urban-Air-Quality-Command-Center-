def attribute_source(row):
    """Heuristic pollutant-ratio source attribution.
    Real system would train this against ground-truth emission inventories;
    this is a transparent, explainable rule-based first pass."""
    so2 = row.get("SO2 µg/m3", 0) or 0
    nox = row.get("Nox µg/m3", 0) or 0
    rspm = row.get("RSPM µg/m3", 0) or 0
    spm = row.get("SPM", 0) or 0
    hour = row.get("hour", 12)

    scores = {
        "Industrial (SO2-dominant)": so2 * 2.0,
        "Vehicular (NOx + rush hour)": nox * (1.5 if hour in [7,8,9,17,18,19,20] else 0.8),
        "Construction/Dust (SPM-dominant)": spm * 1.3,
        "Mixed/Regional (RSPM-dominant)": rspm * 1.0,
    }
    total = sum(scores.values()) or 1
    confidence = {k: round(v / total, 3) for k, v in scores.items()}
    top_source = max(confidence, key=confidence.get)
    return {"attributed_source": top_source, "confidence_scores": confidence}
