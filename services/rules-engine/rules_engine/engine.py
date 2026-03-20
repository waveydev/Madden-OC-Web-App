from shared_schemas.realtime import PlayRecommendation, SituationEvent


def recommend(event: SituationEvent) -> list[PlayRecommendation]:
    if event.distance <= 3:
        return [
            PlayRecommendation(
                play_name="HB Stretch",
                formation="Singleback Wing",
                concept="Outside Zone",
                confidence=0.79,
                rationale="Short yardage favors quick-developing runs if box count is neutral.",
            )
        ]

    return [
        PlayRecommendation(
            play_name="Trips Y Cross",
            formation="Gun Trips TE",
            concept="Crossers",
            confidence=0.82,
            rationale="Default medium/long recommendation against common zone shells.",
        )
    ]
