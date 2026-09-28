# ============================================================
# AGRIRESOLVE AI - CONFLICT RESOLUTION ENGINE
# ============================================================


def resolve_conflict(
    soil_moisture,
    rain_probability,
    pest_risk,
    crop_stage
):
    """
    Combines agricultural signals and produces
    one explainable recommendation.
    """

    reasons = []
    warnings = []

    # --------------------------------------------------------
    # NORMALIZE INPUTS
    # --------------------------------------------------------

    try:
        soil_moisture = float(soil_moisture)
    except:
        soil_moisture = 50

    try:
        rain_probability = float(rain_probability)
    except:
        rain_probability = 0

    pest_risk = str(pest_risk).lower()
    crop_stage = str(crop_stage).lower()

    # --------------------------------------------------------
    # SOIL ANALYSIS
    # --------------------------------------------------------

    if soil_moisture < 30:

        soil_status = "Low"
        reasons.append(
            "Soil moisture is low."
        )

    elif soil_moisture < 60:

        soil_status = "Moderate"
        reasons.append(
            "Soil moisture is at a moderate level."
        )

    else:

        soil_status = "High"
        reasons.append(
            "Soil moisture is already high."
        )

    # --------------------------------------------------------
    # WEATHER ANALYSIS
    # --------------------------------------------------------

    if rain_probability >= 70:

        weather_status = "High Rain Probability"
        reasons.append(
            "High probability of rainfall is expected."
        )

    elif rain_probability >= 40:

        weather_status = "Moderate Rain Probability"
        reasons.append(
            "Moderate rainfall probability is expected."
        )

    else:

        weather_status = "Low Rain Probability"
        reasons.append(
            "Low rainfall probability is expected."
        )

    # --------------------------------------------------------
    # PEST ANALYSIS
    # --------------------------------------------------------

    if "high" in pest_risk:

        pest_status = "High"
        warnings.append(
            "High pest risk requires attention."
        )

    elif "medium" in pest_risk:

        pest_status = "Medium"
        warnings.append(
            "Moderate pest risk should be monitored."
        )

    else:

        pest_status = "Low"

    # --------------------------------------------------------
    # CONFLICT DETECTION
    # --------------------------------------------------------

    conflict_detected = False
    conflict_type = "No major conflict"

    # Dry soil + high rainfall
    if soil_moisture < 40 and rain_probability >= 60:

        conflict_detected = True

        conflict_type = (
            "Irrigation Conflict: "
            "Low soil moisture vs high rainfall probability"
        )

    # Wet soil + low rainfall
    elif soil_moisture >= 60 and rain_probability < 40:

        conflict_detected = True

        conflict_type = (
            "Water Management Conflict: "
            "High soil moisture vs low rainfall probability"
        )

    # Pest conflict
    elif pest_status == "High":

        conflict_detected = True

        conflict_type = (
            "Crop Protection Conflict: "
            "High pest risk detected"
        )

    # --------------------------------------------------------
    # DECISION ENGINE
    # --------------------------------------------------------

    if soil_moisture < 30 and rain_probability >= 70:

        recommendation = (
            "Delay irrigation temporarily and monitor soil moisture. "
            "Reassess after the expected rainfall."
        )

        priority = "Medium"

        confidence = 82

        decision_reason = (
            "Although soil moisture is low, the high probability "
            "of rainfall creates an irrigation conflict. "
            "Waiting and reassessing can reduce unnecessary water use."
        )

    elif soil_moisture < 30 and rain_probability < 40:

        recommendation = (
            "Consider irrigation based on crop requirement "
            "and local field conditions."
        )

        priority = "High"

        confidence = 84

        decision_reason = (
            "Soil moisture is low and significant rainfall "
            "is not currently expected."
        )

    elif soil_moisture >= 60 and rain_probability >= 60:

        recommendation = (
            "Avoid additional irrigation and monitor field "
            "water conditions."
        )

        priority = "High"

        confidence = 88

        decision_reason = (
            "Both soil moisture and rainfall indicators suggest "
            "that additional irrigation may increase excess water risk."
        )

    elif pest_status == "High":

        recommendation = (
            "Prioritize crop inspection and verify pest symptoms "
            "before applying treatment."
        )

        priority = "High"

        confidence = 79

        decision_reason = (
            "The pest signal has high priority and requires "
            "field verification before treatment."
        )

    elif pest_status == "Medium":

        recommendation = (
            "Continue monitoring the crop for pest symptoms "
            "and inspect affected areas."
        )

        priority = "Medium"

        confidence = 74

        decision_reason = (
            "Moderate pest risk was detected, so continued "
            "monitoring is recommended."
        )

    else:

        recommendation = (
            "Continue normal crop monitoring and reassess "
            "when new farm data becomes available."
        )

        priority = "Low"

        confidence = 70

        decision_reason = (
            "No major conflicting agricultural signal was detected."
        )

    # --------------------------------------------------------
    # CROP STAGE ADJUSTMENT
    # --------------------------------------------------------

    if crop_stage in [
        "flowering",
        "fruiting"
    ]:

        warnings.append(
            "Crop is in a sensitive growth stage; "
            "field conditions should be monitored carefully."
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {
        "conflict_detected": conflict_detected,
        "conflict_type": conflict_type,
        "soil_status": soil_status,
        "weather_status": weather_status,
        "pest_status": pest_status,
        "recommendation": recommendation,
        "priority": priority,
        "confidence": confidence,
        "decision_reason": decision_reason,
        "evidence": reasons,
        "warnings": warnings
    }