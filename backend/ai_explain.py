def explain(summary: dict, steps: list[dict] | None = None) -> dict:
    """
    Generate risk explanation from TA summary data.
    Rule-based, no LLM, fully deterministic.

    :param summary: {"mean", "std", "cpk", "percent_ok", "percent_nok"}
    :param steps: optional list of {"name", "mean", "tol_plus"}
    :return: {"risk_level", "summary", "recommendations"}
    """
    cpk = summary.get("cpk")
    percent_nok = summary.get("percent_nok", 0) or 0
    std = summary.get("std", 0) or 0
    mean = summary.get("mean", 0) or 0
    step_count = len(steps) if steps else 0

    # Risk level
    if cpk is None:
        risk_level = "UNKNOWN"
    elif cpk < 1.0:
        risk_level = "HIGH"
    elif cpk < 1.33:
        risk_level = "MEDIUM"
    elif cpk < 1.67:
        risk_level = "LOW"
    else:
        risk_level = "VERY_LOW"

    # Summary
    summary_parts = [
        f"Stack-up result: mean = {mean:.4f}, std = {std:.4f}.",
    ]

    if cpk is not None:
        summary_parts.append(f"Process capability Cpk = {cpk:.2f}.")
    else:
        summary_parts.append("Cpk could not be calculated (specification limits not provided).")

    if percent_nok > 0:
        summary_parts.append(f"{percent_nok:.2f}% of assemblies fall outside specification limits.")
    elif percent_nok == 0 and cpk is not None:
        summary_parts.append("All samples are within specification limits.")

    if step_count > 0:
        summary_parts.append(f"Chain consists of {step_count} dimension(s).")

    summary_text = " ".join(summary_parts)

    # Recommendations
    recommendations = []

    if risk_level == "HIGH":
        recommendations.append("CRITICAL: Cpk < 1.0 indicates the process cannot meet specifications. Immediate action required.")
        recommendations.append("Consider widening specification limits or tightening individual tolerances.")
        if step_count > 4:
            recommendations.append(f"Long tolerance chain ({step_count} steps). Consider reducing the number of stacked dimensions.")

    elif risk_level == "MEDIUM":
        recommendations.append("Cpk is between 1.0 and 1.33. Marginal capability — monitor closely in production.")
        recommendations.append("Consider reviewing the largest contributors to tolerance variation.")

    elif risk_level == "LOW":
        recommendations.append("Cpk is between 1.33 and 1.67. Adequate capability for most applications.")

    else:
        recommendations.append("Cpk > 1.67. Excellent process capability.")

    # Identify largest tolerance contributor
    if steps:
        largest = max(steps, key=lambda s: s.get("tol_plus", 0))
        recommendations.append(
            f"Largest tolerance contributor: '{largest['name']}' (±{largest.get('tol_plus', 0):.3f})."
        )

    if cpk is None:
        recommendations.append("Provide LSL and USL to enable full risk assessment.")

    return {
        "risk_level": risk_level,
        "summary": summary_text,
        "recommendations": recommendations,
    }
