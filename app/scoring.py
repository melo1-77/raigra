# app/scoring.py

from collections import defaultdict
from typing import Dict, Tuple

from config import CATEGORY_WEIGHTS, READINESS_BANDS
from questions import QUESTIONS, LIKERT_OPTIONS, YESNO_OPTIONS

def normalise_category_score(raw_sum: float, max_sum: float) -> float:
    if max_sum == 0:
        return 0.0
    return (raw_sum / max_sum) * 100.0

def classify_band(overall_score: float) -> Tuple[str, str]:
    """
    Map a numeric score to a qualitative band.
    Uses inclusive lower bounds and open upper bounds for non-top band.
    """
    if overall_score >= 80:
        return "AI Ready", "Strong governance and controls; low regulatory risk."
    elif overall_score >= 60:
        return "Near Ready", "Solid foundation with clear areas to strengthen."
    elif overall_score >= 40:
        return "Emerging", "Foundational elements in place but significant weaknesses."
    else:
        return "High Risk", "Limited governance; urgent remediation required."

from typing import Dict, Tuple
from questions import CATEGORIES


def get_category_weights(org_type: str | None, industry: str | None) -> Dict[str, float]:
    """
    Return category weights that adapt to organisation type AND sector.

    Base mapping (by category order in CATEGORIES):
        0: Governance & Policy
        1: Data Privacy & Protection
        2: Technical Controls & Monitoring
        3: Ethics & Societal Impact
        4: Organisational Readiness & Capability
    """
    # Base weights
    weights = {
        CATEGORIES[0]: 0.30,  # Governance
        CATEGORIES[1]: 0.25,  # Privacy
        CATEGORIES[2]: 0.20,  # Technical controls
        CATEGORIES[3]: 0.15,  # Ethics & impact
        CATEGORIES[4]: 0.10,  # Org readiness
    }

    t = (org_type or "").lower()
    ind = (industry or "").lower()

    # --- 1. Organisation type adjustments (broad risk posture) ---

    # Public sector / government / NGO – governance + privacy more important
    if any(k in t for k in ["public", "government", "gov", "ngo", "non-profit", "charity"]):
        weights[CATEGORIES[0]] += 0.05  # governance
        weights[CATEGORIES[1]] += 0.05  # privacy
        weights[CATEGORIES[2]] -= 0.05  # technical
        weights[CATEGORIES[4]] -= 0.05  # org capability

    # Startup / scaleup – technical + organisational readiness more important
    if any(k in t for k in ["startup", "scaleup", "scale-up", "high growth"]):
        weights[CATEGORIES[2]] += 0.05  # technical
        weights[CATEGORIES[4]] += 0.05  # org readiness
        weights[CATEGORIES[0]] -= 0.03  # governance
        weights[CATEGORIES[3]] -= 0.02  # ethics

    # --- 2. Industry-specific adjustments (more granular) ---

    # Healthcare / life sciences – privacy + ethics heavily weighted
    if "health" in ind or "life science" in ind or "pharma" in ind:
        weights[CATEGORIES[1]] += 0.06  # privacy
        weights[CATEGORIES[3]] += 0.04  # ethics
        weights[CATEGORIES[2]] -= 0.05  # technical
        weights[CATEGORIES[4]] -= 0.05  # org

    # Financial services – governance + privacy dominant
    if "financ" in ind or "bank" in ind or "insur" in ind or "asset" in ind:
        weights[CATEGORIES[0]] += 0.05  # governance
        weights[CATEGORIES[1]] += 0.05  # privacy
        weights[CATEGORIES[2]] -= 0.05
        weights[CATEGORIES[3]] -= 0.05

    # Retail / e-commerce – technical + org capability dominant
    if "retail" in ind or "commerce" in ind or "e-commerce" in ind or "ecommerce" in ind:
        weights[CATEGORIES[2]] += 0.06  # technical
        weights[CATEGORIES[4]] += 0.04  # org
        weights[CATEGORIES[0]] -= 0.05
        weights[CATEGORIES[3]] -= 0.05

    # Education – governance, ethics, and org readiness more important
    if "educat" in ind or "school" in ind or "university" in ind or "college" in ind:
        weights[CATEGORIES[0]] += 0.04  # governance
        weights[CATEGORIES[3]] += 0.04  # ethics
        weights[CATEGORIES[4]] += 0.02  # org
        weights[CATEGORIES[1]] -= 0.05
        weights[CATEGORIES[2]] -= 0.05

    # Technology / AI / software vendors – technical + governance
    if "tech" in ind or "software" in ind or "ai" in ind or "digital" in ind:
        weights[CATEGORIES[2]] += 0.05  # technical
        weights[CATEGORIES[0]] += 0.03  # governance
        weights[CATEGORIES[3]] -= 0.03
        weights[CATEGORIES[1]] -= 0.05

    # Normalise back to sum to 1.0
    total = sum(weights.values())
    if total <= 0:
        # Fallback to equal weights in a weird edge case
        n = len(CATEGORIES)
        return {cat: 1.0 / n for cat in CATEGORIES}

    return {k: v / total for k, v in weights.items()}

def compute_scores(
    responses: Dict[str, float],
    org_type: str | None = None,
    industry: str | None = None,
) -> Tuple[float, Dict[str, float], Tuple[str, str]]:
    """
    Compute per-category scores and an overall readiness score.
    Weights adapt based on organisation type and sector.
    """
    # Initialise totals per category
    category_totals: Dict[str, float] = {cat: 0.0 for cat in CATEGORIES}
    category_counts: Dict[str, int] = {cat: 0 for cat in CATEGORIES}

    # Aggregate responses per category
    from questions import QUESTIONS  # local import to avoid circulars
    for q in QUESTIONS:
        if q.id in responses:
            category_totals[q.category] += responses[q.id]
            category_counts[q.category] += 1

    # Average scores per category (0–100)
    category_scores: Dict[str, float] = {}
    for cat in CATEGORIES:
        if category_counts[cat] > 0:
            # Each question is on a 0–4 scale; scale up to 0–100
            avg = category_totals[cat] / category_counts[cat]
            category_scores[cat] = (avg / 4.0) * 100.0
        else:
            category_scores[cat] = 0.0

    # Get dynamic weights based on org_type / industry
    weights = get_category_weights(org_type, industry)

    # Weighted overall score
    overall = 0.0
    for cat in CATEGORIES:
        overall += category_scores[cat] * weights.get(cat, 0.0)

    band_label, band_desc = classify_band(overall)
    return overall, category_scores, (band_label, band_desc)

def generate_recommendations(category_scores: Dict[str, float]) -> Dict[str, str]:
    recs = {}
    for cat, score in category_scores.items():
        if score >= 80:
            recs[cat] = "Maintain current practices and document them clearly for internal and external audits."
        elif score >= 60:
            recs[cat] = "Strengthen governance and monitoring processes to move from 'near ready' to 'ready'."
        elif score >= 40:
            recs[cat] = "Prioritise building basic policies, controls, and clear ownership in this area."
        else:
            recs[cat] = "Treat this as a high-risk area and establish minimum compliant processes in the next 3–6 months."
    return recs
