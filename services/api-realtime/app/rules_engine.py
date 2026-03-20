import os

import httpx  # pyright: ignore[reportMissingImports]

from shared_schemas.realtime import SituationEvent, PlayRecommendation

RULE_MATRIX = [
    {
        "name": "third_medium_cover3",
        "conditions": {"down": [3], "distance_min": 5, "distance_max": 9, "defense_shell": ["cover 3"]},
        "preferred_concepts": ["cross", "mesh", "dagger"],
        "concept_weights": {"cross": 0.33, "mesh": 0.28, "dagger": 0.22},
        "rationale": "Cover 3 on 3rd-and-medium is vulnerable to layered crossers and mesh traffic.",
    },
    {
        "name": "third_medium_cover2",
        "conditions": {"down": [3], "distance_min": 5, "distance_max": 9, "defense_shell": ["cover 2", "tampa 2"]},
        "preferred_concepts": ["flood", "smash", "corner"],
        "concept_weights": {"flood": 0.34, "smash": 0.27, "corner": 0.2},
        "rationale": "Cover 2 spacing favors flood and smash-style sideline stretch.",
    },
    {
        "name": "short_yardage",
        "conditions": {"distance_min": 1, "distance_max": 3},
        "preferred_concepts": ["zone", "quick", "slant"],
        "concept_weights": {"zone": 0.35, "quick": 0.26, "slant": 0.2},
        "rationale": "Short-yardage favors quick-hit runs or immediate inside access throws.",
    },
]

DEFAULT_RULE = {
    "name": "default_medium",
    "preferred_concepts": ["cross", "mesh", "flood", "inside zone"],
    "concept_weights": {"cross": 0.26, "mesh": 0.22, "flood": 0.2, "inside zone": 0.16},
    "rationale": "Balanced default when no stronger situational rule is matched.",
}

FALLBACK_RECOMMENDATIONS = [
    {"play_name": "Trips Y Cross", "formation": "Gun Trips TE", "concept": "Crossers", "confidence": 0.76},
    {"play_name": "Mesh Spot", "formation": "Gun Doubles", "concept": "Mesh", "confidence": 0.72},
    {"play_name": "PA Boot Over", "formation": "Singleback Ace", "concept": "Flood", "confidence": 0.69},
]


def fetch_candidate_plays(event: SituationEvent, preferred_concepts: list[str], limit: int = 150) -> list[dict]:
    base_url = os.getenv("CONTROL_PLANE_BASE_URL", "http://localhost:8000").rstrip("/")
    madden_version = os.getenv("MADDEN_VERSION", "")

    params: dict[str, str | int] = {
        "offense_personnel": event.offense_personnel,
        "limit": min(limit, 250),
    }

    if preferred_concepts:
        params["concepts"] = ",".join(preferred_concepts)

    if madden_version:
        params["madden_version"] = madden_version

    with httpx.Client(timeout=8, follow_redirects=True) as client:
        response = client.get(f"{base_url}/api/playbook-entries", params=params)
        response.raise_for_status()
        payload = response.json()

        rows = payload.get("results") or []
        if rows:
            return [row for row in rows if isinstance(row, dict)]

        fallback_params = dict(params)
        fallback_params.pop("concepts", None)
        response = client.get(f"{base_url}/api/playbook-entries", params=fallback_params)
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("results") or []
    return [row for row in rows if isinstance(row, dict)]


def _match_rule(event: SituationEvent, rule: dict) -> bool:
    conditions = rule.get("conditions", {})

    if "down" in conditions and event.down not in conditions["down"]:
        return False

    if "distance_min" in conditions and event.distance < conditions["distance_min"]:
        return False

    if "distance_max" in conditions and event.distance > conditions["distance_max"]:
        return False

    if "defense_shell" in conditions:
        shells = {value.lower() for value in conditions["defense_shell"]}
        if event.defense_shell.lower() not in shells:
            return False

    if "defense_front" in conditions:
        fronts = {value.lower() for value in conditions["defense_front"]}
        if event.defense_front.lower() not in fronts:
            return False

    return True


def _rule_for_event(event: SituationEvent) -> dict:
    for rule in RULE_MATRIX:
        if _match_rule(event, rule):
            return rule
    return DEFAULT_RULE


def _score_play(event: SituationEvent, play: dict, concept_weights: dict[str, float]) -> float:
    concept = (play.get("concept") or "").lower()
    formation = (play.get("formation") or "").lower()
    score = 0.45

    for keyword, weight in concept_weights.items():
        if keyword in concept:
            score += weight

    if event.distance >= 7 and "gun" in formation:
        score += 0.06

    if event.distance <= 3 and ("zone" in concept or "inside" in concept):
        score += 0.08

    return max(0.0, min(round(score, 2), 0.98))


def _rank_candidates(event: SituationEvent, rule: dict, candidates: list[dict]) -> list[PlayRecommendation]:
    rationale = rule["rationale"]
    concept_weights = rule.get("concept_weights", {})

    scored: list[PlayRecommendation] = []
    seen_names: set[str] = set()
    for play in candidates:
        play_name = (play.get("play_name") or "").strip()
        if not play_name:
            continue
        dedupe_key = play_name.lower()
        if dedupe_key in seen_names:
            continue
        seen_names.add(dedupe_key)

        scored.append(
            PlayRecommendation(
                play_name=play_name,
                formation=play.get("formation") or "Unknown",
                concept=play.get("concept") or "Unknown",
                confidence=_score_play(event, play, concept_weights),
                rationale=rationale,
            )
        )

    return sorted(scored, key=lambda item: item.confidence, reverse=True)[:3]


def _fallback(rule: dict) -> list[PlayRecommendation]:
    rationale = rule["rationale"]
    return [
        PlayRecommendation(
            play_name=item["play_name"],
            formation=item["formation"],
            concept=item["concept"],
            confidence=item["confidence"],
            rationale=rationale,
        )
        for item in FALLBACK_RECOMMENDATIONS
    ]


def suggest_plays(event: SituationEvent) -> list[PlayRecommendation]:
    rule = _rule_for_event(event)
    preferred_concepts = rule.get("preferred_concepts", [])

    try:
        candidates = fetch_candidate_plays(event, preferred_concepts)
    except Exception:
        candidates = []

    if not candidates:
        return _fallback(rule)

    ranked = _rank_candidates(event, rule, candidates)
    return ranked if ranked else _fallback(rule)
