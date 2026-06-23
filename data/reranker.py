"""
Reranker — combines rating, distance, importance, and uniqueness into one
weighted score, shared across travel/food/hotel search so each domain agent
doesn't reimplement its own ranking logic.

Distance is NOT computed here — Repository methods already compute
`distance_km` in Cypher when a user location was passed in, so this module
just consumes that field if present.

Each result is annotated with `match_score` (0-1) and `match_reasons` (a short
list of which signals actually mattered) rather than just being silently
reordered — so the calling agent's LLM can explain *why* something ranked
where it did, instead of presenting an unexplained order or inventing a reason.
"""

from typing import Any, Dict, List, Optional

# Sums to 1. Redistributed proportionally over whatever signals are actually
# available for a given result set (e.g. distance drops out entirely when no
# user location was given, rather than silently scoring everything as "far").
DEFAULT_WEIGHTS = {"rating": 0.35, "distance": 0.30, "importance": 0.20, "uniqueness": 0.15}


def _rating_score(value: Any) -> float:
    # Unrated (0.0/None) is common in this dataset (OSM rarely carries ratings)
    # and means "unknown", not "bad" — score it neutral rather than burying it.
    if not value:
        return 0.5
    return min(value / 5.0, 1.0)


def _importance_score(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if value is None:
        return 0.0
    return min(float(value) / 5.0, 1.0)  # treat numeric importance as a 1-5-ish scale (e.g. stars)


def _category_key(value: Any):
    return tuple(sorted(value)) if isinstance(value, list) else value


def rerank(
    results: List[Dict[str, Any]],
    *,
    rating_field: str = "rating",
    importance_field: Optional[str] = None,
    category_field: str = "category",
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Score and reorder `results` in place (mutates and returns the same list,
    sorted best-first). Safe to call with any result shape — missing fields
    just deactivate that signal rather than erroring."""
    if not results:
        return results

    base_weights = dict(weights or DEFAULT_WEIGHTS)
    distance_active = all(r.get("distance_km") is not None for r in results)
    importance_active = importance_field is not None and any(r.get(importance_field) is not None for r in results)

    active_weights = {
        "rating": base_weights.get("rating", 0),
        "distance": base_weights.get("distance", 0) if distance_active else 0,
        "importance": base_weights.get("importance", 0) if importance_active else 0,
        "uniqueness": base_weights.get("uniqueness", 0),
    }
    total = sum(active_weights.values()) or 1
    active_weights = {k: v / total for k, v in active_weights.items()}

    category_counts: Dict[Any, int] = {}
    for r in results:
        key = _category_key(r.get(category_field))
        category_counts[key] = category_counts.get(key, 0) + 1

    for r in results:
        rating_score = _rating_score(r.get(rating_field))
        distance_score = 1 / (1 + r["distance_km"]) if distance_active else 0.0
        importance_score = _importance_score(r.get(importance_field)) if importance_active else 0.0

        category_key = _category_key(r.get(category_field))
        rarity_score = 1 - (category_counts[category_key] / len(results))

        score = (
            active_weights["rating"] * rating_score
            + active_weights["distance"] * distance_score
            + active_weights["importance"] * importance_score
            + active_weights["uniqueness"] * rarity_score
        )

        reasons = []
        if distance_active and distance_score > 0.5:
            reasons.append(f"very close ({r['distance_km']:.1f}km)")
        elif distance_active and distance_score > 0.2:
            reasons.append(f"nearby ({r['distance_km']:.1f}km)")
        if rating_score >= 0.8:
            reasons.append("highly rated")
        if importance_active and importance_score >= 0.8:
            reasons.append("flagged as a top pick")
        if rarity_score >= 0.7 and category_key:
            reasons.append(f"one of the few '{r.get(category_field)}' options here")

        r["match_score"] = round(score, 2)
        r["match_reasons"] = reasons

    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results
