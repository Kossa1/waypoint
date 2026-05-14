import numpy as np
from sqlalchemy.orm import Session
from app.models import City, UserComparison
from app.schemas import PreferenceVector

FEATURE_FIELDS = [
    "cost_index",
    "safety_index",
    "tourism_volume",
    "warmth_index",
    "outdoor_score",
    "food_score",
    "nightlife_score",
    "walkability",
    "english_friendly",
]

# High tourism volume dilutes the recommendation score — popular ≠ best fit.
TOURISM_PENALTY_WEIGHT = 0.15


def city_to_vector(city: City) -> np.ndarray:
    return np.array([getattr(city, f) for f in FEATURE_FIELDS], dtype=float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def recommend(
    prefs: PreferenceVector,
    db: Session,
    top_n: int = 5,
    exclude_ids: list[int] | None = None,
) -> list[tuple[City, float]]:
    pref_vec = np.array([getattr(prefs, f) for f in FEATURE_FIELDS], dtype=float)

    cities = db.query(City).all()
    scored: list[tuple[City, float]] = []

    for city in cities:
        if exclude_ids and city.id in exclude_ids:
            continue
        city_vec = city_to_vector(city)
        sim = cosine_similarity(pref_vec, city_vec)
        penalty = TOURISM_PENALTY_WEIGHT * city.tourism_volume
        score = max(0.0, sim - penalty)
        scored.append((city, round(score, 4)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


def infer_preferences_from_comparisons(session_id: str, db: Session) -> PreferenceVector:
    """Derive a preference vector by averaging the vectors of all preferred cities."""
    comparisons = (
        db.query(UserComparison)
        .filter(UserComparison.session_id == session_id)
        .all()
    )
    if not comparisons:
        return PreferenceVector()

    preferred_ids = {c.preferred_city_id for c in comparisons}
    cities = db.query(City).filter(City.id.in_(preferred_ids)).all()
    if not cities:
        return PreferenceVector()

    vectors = np.array([city_to_vector(c) for c in cities])
    mean_vec = vectors.mean(axis=0)

    kwargs = {field: float(mean_vec[i]) for i, field in enumerate(FEATURE_FIELDS)}
    return PreferenceVector(**kwargs)
