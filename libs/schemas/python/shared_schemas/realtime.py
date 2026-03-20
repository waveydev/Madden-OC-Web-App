from pydantic import BaseModel, Field
from typing import List, Literal


HashSide = Literal["left", "middle", "right"]


class SituationEvent(BaseModel):
    down: int = Field(ge=1, le=4)
    distance: int = Field(ge=1, le=99)
    yard_line: int = Field(ge=1, le=99)
    clock_seconds: int = Field(ge=0)
    offense_personnel: str
    defense_shell: str
    defense_front: str
    hash: HashSide


class PlayRecommendation(BaseModel):
    play_name: str
    formation: str
    concept: str
    confidence: float = Field(ge=0, le=1)
    rationale: str


class SuggestResponse(BaseModel):
    recommendations: List[PlayRecommendation]
